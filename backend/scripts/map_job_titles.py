"""
Script C — Job title → field_id mapping via Gemini.
Maps free-text LinkedIn job titles to canonical HEC degree field_ids.
Output: backend/data/job_title_mapping.json
Human review required before committing the mapping file.
No project imports. stdlib + google.genai + dotenv only.
"""

import os
import json
import pathlib
import time
import re
import sys
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai import errors as genai_errors

load_dotenv("backend/.env")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
DATA_DIR = REPO_ROOT / "backend" / "data"
APP_DATA_DIR = REPO_ROOT / "backend" / "app" / "data"

INPUT_FILE = DATA_DIR / "linkedin_raw_jobs.json"
MAPPING_FILE = DATA_DIR / "job_title_mapping.json"
AFFINITY_FILE = APP_DATA_DIR / "affinity_matrix.json"

MODEL_NAME = "gemini-3.1-flash-lite-preview"
BATCH_SIZE = 15
REQUEST_DELAY = 4
MAX_RETRIES = 3
RETRY_WAIT = 60

# When True: needs_review entries are reprocessed by Gemini on the next run,
# giving medium-confidence entries a second chance at higher confidence.
# Reset to False after running — never commit as True.
FORCE_REMAP_NEEDS_REVIEW = False

# Stable, well-known canonical title anchors. Titles that are noise variants
# of these are pointed at the matching anchor as their canonical_form.
# process_engineer, lecturer, research_associate deliberately excluded —
# context-dependent, always resolved via company/industry fields.
HARDCODED_ANCHORS = {
    # Software Development
    "software_engineer",
    "frontend_engineer",
    "frontend_designer",
    "backend_developer",
    "fullstack_developer",
    "mobile_developer",
    "android_developer",
    "ios_developer",
    "web_developer",
    "wordpress_developer",
    "shopify_developer",
    "game_developer",
    # Data and AI
    "data_analyst",
    "data_scientist",
    "data_engineer",
    "ml_engineer",
    "ai_engineer",
    "business_analyst",
    "power_bi_developer",
    "database_administrator",
    # QA and DevOps
    "qa_engineer",
    "devops_engineer",
    "cloud_engineer",
    "network_engineer",
    "systems_administrator",
    # Management and Business
    "project_manager",
    "product_manager",
    "business_development_manager",
    "sales_executive",
    "marketing_manager",
    "account_manager",
    "hr_manager",
    "operations_manager",
    "customer_service_representative",
    "recruitment_consultant",
    # Finance and Accounting
    "accountant",
    "financial_analyst",
    "audit_officer",
    "tax_consultant",
    # Engineering (non-software)
    "mechanical_engineer",
    "civil_engineer",
    "electrical_engineer",
    "chemical_engineer",
    "structural_engineer",
    "quantity_surveyor",
    "hse_officer",
    # Design and Media
    "graphic_designer",
    "ui_ux_designer",
    "motion_graphics_designer",
    "content_writer",
    "social_media_manager",
    "video_editor",
    # Healthcare and Sciences
    "pharmacist",
    "lab_technician",
    "biomedical_engineer",
    # Education
    "teacher",
}

LOG_FILE = REPO_ROOT / "logs" / f"map_job_titles_{datetime.now().strftime('%Y_%m_%d_%H%M')}.log"


# ---------------------------------------------------------------------------
# STEP 2 — Load canonical field_ids from affinity_matrix
# ---------------------------------------------------------------------------

def load_canonical_field_ids():
    """
    Load the authoritative field_id list from affinity_matrix.json.
    Returns a dict: field_id → one-line description for Gemini context.
    """
    with open(AFFINITY_FILE, encoding="utf-8") as f:
        affinity = json.load(f)

    field_map = {}
    for entry in affinity:
        fid = entry.get("field_id")
        if not fid or fid in field_map:
            continue  # skip duplicates (petroleum_engineering appears twice)
        desc = entry.get("riasec_description", "")
        short_desc = desc.split(".")[0] if desc else ""
        field_map[fid] = short_desc

    return field_map


# ---------------------------------------------------------------------------
# STEP 3 — Extract unique titles with context from raw jobs
# ---------------------------------------------------------------------------

def extract_unique_titles(raw_jobs):
    """
    Extract all unique job titles from linkedin_raw_jobs.json.
    For each unique title, collect representative company, industry, job_functions.
    Returns: list of dicts sorted by count descending.
    Titles are lowercased for deduplication — preserves company/industry casing.
    """
    title_groups = {}

    for job_id, job in raw_jobs.items():
        title = job.get("title")
        if not title:
            continue
        title = " ".join(title.split()).lower()

        if title not in title_groups:
            title_groups[title] = {
                "title": title,
                "count": 0,
                "companies": [],
                "industries": [],
                "job_functions": [],
            }

        title_groups[title]["count"] += 1
        company = job.get("company")
        industry = job.get("industry")
        job_funcs = job.get("job_functions", [])

        if company and company not in title_groups[title]["companies"]:
            title_groups[title]["companies"].append(company)
        if industry and industry not in title_groups[title]["industries"]:
            title_groups[title]["industries"].append(industry)
        for jf in job_funcs:
            if jf and jf not in title_groups[title]["job_functions"]:
                title_groups[title]["job_functions"].append(jf)

    return sorted(title_groups.values(), key=lambda x: x["count"], reverse=True)


# ---------------------------------------------------------------------------
# STEP 4 — Gemini system prompt
# ---------------------------------------------------------------------------

GEMINI_SYSTEM_PROMPT = """
You are an expert Pakistani job market analyst mapping LinkedIn job
titles to HEC-recognised bachelor's degree fields.

Your task: For each job title provided, determine which degree field(s)
produce graduates who typically fill that role in Pakistan's job market.

---
## CANONICAL DEGREE FIELD_IDs

These are the ONLY valid field_ids. Use EXACTLY these strings.
Map every title to one or more of these. If none apply, mark unmapped.

{field_id_block}

---
## OUTPUT SCHEMA

For each title in the input batch, output EXACTLY this JSON structure:

{{
  "title": "the exact title string from input",
  "canonical_title": "snake_case normalized version",
  "primary_field_id": "the single most relevant field_id or null",
  "secondary_field_ids": ["other relevant field_ids"],
  "sub_specialisation": "freeform sub-type label or null",
  "confidence": "high|medium|low",
  "unmapped": false,
  "canonical_form": "snake_case base title this maps to",
  "is_noise_variant": false,
  "llm_reasoning": "Your explanation of the mapping decision"
}}

Rules:
- primary_field_id must be a valid field_id from the list above or null
- secondary_field_ids must only contain valid field_ids
- If unmapped is true: primary_field_id must be null,
  secondary_field_ids must be [], confidence must be "low"
- llm_reasoning is MANDATORY. Minimum 1 sentence. Never empty string.
- confidence "high": title maps clearly to one field, no ambiguity
- confidence "medium": 2-3 plausible fields, partially resolved by context
- confidence "low": genuinely ambiguous, Urdu title, or unknown role
- canonical_form: always the base title with noise stripped, in snake_case.
  If the title itself is already canonical, canonical_form equals
  canonical_title.
- is_noise_variant: true ONLY when ALL of:
  1. primary_field_id is identical to the canonical_form entry's field_id
  2. secondary_field_ids are identical or a subset
  3. sub_specialisation is null or identical
  4. The only difference from canonical_form is: location, company name,
     seniority prefix, work arrangement, or posting metadata
  is_noise_variant: false when ANY of:
  - sub_specialisation differs meaningfully
  - secondary_field_ids differ
  - Title represents a distinct technology or domain even within the same
    primary_field_id

---
## DISAMBIGUATION RULES FOR PAKISTAN

### RULE 1 — Title alone is insufficient. Use company + industry context.
"Process Engineer at Engro" → chemical_engineering
"Process Engineer at Sapphire Textile" → textile_engineering
"Process Engineer at Lucky Cement" → civil_engineering or
  construction_engineering
Always consider the company sector when provided.

### RULE 2 — CS vs SE: these are DISTINCT fields in Pakistan.
computer_science:
  - Academic CS roles, algorithm research, CS graduate hiring
  - "CS Graduate", "Computer Scientist", "Algorithm Engineer"
  - Research labs, universities, HEC-funded projects
  - Companies: NCAI, academic institutions, R&D labs

software_engineering:
  - Applied development roles, product companies
  - "Software Engineer", "SWE", "SE", "Software Developer",
    "Backend Developer", "Frontend Developer", "Full Stack"
  - Pakistani tech companies: Systems Limited, 10Pearls, Arbisoft,
    Netsol, Techlogix, VentureDive, Avanza Solutions

Key rule: "Software Engineer" → software_engineering (primary),
computer_science (secondary). Never map "Software Engineer" to
computer_science as primary unless company explicitly says research.

### RULE 3 — Multi-role titles: split proportionally.
"Backend + AI Engineer" →
  primary: software_engineering
  secondary: [artificial_intelligence]
  sub_specialisation: "backend_ai_hybrid"

"Data Engineer / ML Developer" →
  primary: data_science
  secondary: [software_engineering, artificial_intelligence]

"DevOps + Cloud Engineer" →
  primary: software_engineering
  secondary: []
  sub_specialisation: "devops_cloud"
  (DevOps is SE-adjacent in Pakistan — EE or telecom rarely fills it)

### RULE 4 — Pakistani title conventions.
"Executive" in Pakistan = mid-level employee, NOT C-suite or senior.
  "IT Executive" → information technology support, NOT IT leadership
  "Sales Executive" → sales representative, NOT VP Sales

"Officer" in Pakistan = entry-level formal role.
  "HR Officer" → business_bba or psychology
  "Finance Officer" → finance_accounting

"Associate" at a Pakistani bank/firm = entry to mid level.
  "Research Associate" at a university → computer_science or relevant field
  "Associate Engineer" → relevant engineering field

### RULE 5 — Data/Analytics cluster disambiguation.
data_science:
  - "Data Scientist", "ML Engineer", "Machine Learning Engineer",
    "AI Engineer" (when at tech company)
  - Heavy statistics, model building, Python/R

business_analytics:
  - "Business Analyst", "BI Developer", "Analytics Engineer",
    "Data Analyst" (when at corporate/bank)
  - Dashboards, Power BI, Tableau, SQL reports

finance_accounting:
  - "Financial Analyst", "Credit Analyst", "Risk Analyst"
    (when at bank or financial institution)
  - "Data Analyst" at a bank is often finance_accounting primary

Key: "Data Analyst" confidence is "medium" — must check company/industry.

### RULE 6 — Engineering cluster disambiguation.
electrical_engineering:
  - Power generation, WAPDA/LESCO/KESC jobs, power plants
  - "Electrical Engineer at WAPDA" → electrical_engineering (certain)

electronics_engineering:
  - Consumer electronics, PCB design, embedded consumer products
  - "Electronics Engineer at Samsung" → electronics_engineering

telecommunications_engineering:
  - Telecom companies: PTCL, Jazz, Telenor, Zong, Ufone
  - "Network Engineer at PTCL" → telecommunications_engineering

robotics_iot:
  - Embedded systems for automation, IoT devices
  - "Embedded Engineer" → electronics_engineering (primary),
     robotics_iot (secondary)
  - Rare in Pakistan LinkedIn — very low count expected

### RULE 7 — Business cluster disambiguation.
business_bba:
  - "HR Manager", "Marketing Manager", "Operations Manager",
    "Brand Manager", "Supply Chain Executive"
  - General management and business functions

finance_accounting:
  - "Accountant", "Finance Manager", "CA", "ACCA", "Tax Consultant",
    "Internal Auditor", "Treasury Officer"

economics:
  - "Economist", "Policy Analyst", "Research Economist"
  - State Bank, World Bank, IMF roles
  - Very few Pakistan LinkedIn postings — treat as low count

fintech:
  - "Fintech Product Manager", "Payment Systems Engineer",
    "Digital Banking Officer"
  - Digital payment companies: EasyPaisa, JazzCash, HBL Pay

### RULE 8 — Health sciences disambiguation.
medicine_mbbs: doctors, medical officers, clinical roles
pharmacy: pharmacists, drug regulatory roles
dentistry_bds: dentists only
nursing: registered nurses, ward staff
physical_therapy: DPT graduates, rehabilitation roles
biomedical_engineering: medical device technicians, hospital equipment

Key: "Medical Officer" → medicine_mbbs. "Clinical Pharmacist" → pharmacy.
Never map "Biomedical Engineer" to medicine_mbbs.

### RULE 9 — Civil/Construction cluster.
civil_engineering:
  - Structural design, highways, dams, bridges
  - "Structural Engineer", "Civil Design Engineer"

construction_engineering:
  - Site management, project execution, quantity surveying
  - "Site Engineer", "Construction Manager", "QS Engineer"
  - Large Pakistani construction firms: Descon, FWO, NLC projects

architecture:
  - Building and interior design
  - "Architect", "Architectural Designer", "Urban Designer"
  - Confusion point: "CAD Designer" could be architecture OR
    mechanical_engineering depending on company

urban_infrastructure_engineering:
  - City planning, utilities design
  - Very rare in Pakistan LinkedIn

### RULE 10 — Chemical/Material/Textile cluster.
chemical_engineering: Engro, ICI, Bayer, BASF, refinery roles
textile_engineering: textile mills, fabric manufacturing
food_engineering: Nestlé, Unilever, Shan Foods, PEL
polymer_petrochemical_engineering: PARCO, OGDCL, PPL
metallurgical_engineering: Pakistan Steel, foundry roles
materials_engineering: research labs, cement plants

### RULE 11 — Urdu/Mixed titles.
If title contains Urdu script or Roman Urdu terminology:
- Attempt mapping if the role is recognisable
- Set confidence "low" regardless of how clear the mapping seems
- Include the original Urdu in llm_reasoning

### RULE 12 — Unmapped roles.
Mark unmapped: true for:
- Blue collar: Driver, Cook, Cleaner, Security Guard, Peon,
  Domestic Worker, Electrician (not electrical engineer),
  Plumber, Tailor, Cashier, Waiter, Delivery Rider
- Roles requiring no bachelor's degree in Pakistan's formal market
- Military/paramilitary specific roles with no civilian degree path
- Completely unrecognisable strings

Do NOT mark unmapped for:
- Any role that could plausibly be filled by a degree graduate,
  even if unusual (e.g. "Freelance Content Writer" → mass_communication)

### RULE 13 — Sub-specialisation guidance.
sub_specialisation is a freeform label, not a field_id. Examples:
software_engineering sub-types: backend_development, frontend_development,
  fullstack_development, mobile_development, devops_cloud, embedded_systems,
  game_development, qa_testing
data_science sub-types: data_analysis, ml_engineering, data_engineering,
  bi_analytics, nlp, computer_vision
artificial_intelligence sub-types: ml_research, ai_product,
  generative_ai, robotics_ai
medicine_mbbs sub-types: clinical_medicine, medical_officer, gp,
  specialist_training
business_bba sub-types: hr_management, marketing, supply_chain,
  operations, project_management

Use null if the title is generic and no clear sub-type applies.

### RULE 14 — Canonical form and noise variant detection.

Every title must specify its canonical_form — the base title this maps
to, stripped of noise, in snake_case.

ANCHOR TITLES — stable well-known canonical forms. When a title is a
noise variant of an anchor, set canonical_form to the matching anchor:
{anchor_block}

MEMORY — non-anchor canonical titles already confirmed in this system.
When a title is a noise variant of a memory entry, set canonical_form
to that entry:
{memory_block}

NOISE — strip these from title to get canonical_form:
  Locations: "- Karachi", "- Lahore", "- Islamabad", "- Remote",
    "- Onsite", "| Hybrid", city names
  Company names: "- Safepay HQ", "at Systems Limited", "| VentureDive",
    "| Arbisoft", company suffixes
  Posting metadata: "- $3000/month", "| JumpStart 3.0", "- Ref: 12345",
    salary ranges, cohort names
  Work arrangement: "(Remote)", "(Onsite)", "| WFH", "(Hybrid)"
  Seniority alone when it does NOT change the sub_specialisation:
    "Senior", "Junior", "Lead", "Associate", "Principal", "Sr.", "Jr."

NOT NOISE — keep in canonical_form:
  Technical domain: "- Backend", "- AI/ML", "- Embedded Systems",
    "- iOS", "- React"
  Specialisation: "- Data Warehousing", "- Django", "- SAP",
    "- Salesforce", technology stacks
  Industry that changes secondary_field_ids: "- Banking",
    "- Healthcare", "- Fintech", "- Manufacturing"

EXAMPLES:
  "Frontend Engineer - Safepay HQ"
    → canonical_form: "frontend_engineer"
    → is_noise_variant: true (company name only, no field signal change)

  "React Developer"
    → canonical_form: "react_developer"
    → is_noise_variant: false (distinct technology, different
      sub_specialisation from frontend_engineer)

  "Senior Software Engineer - AI/ML"
    → canonical_form: "senior_software_engineer_ai_ml"
    → is_noise_variant: false (AI/ML changes secondary_field_ids)

  "Software Engineer - Karachi"
    → canonical_form: "software_engineer"
    → is_noise_variant: true (location only, no field signal change)

  "SQA Engineer"
    → canonical_form: "qa_engineer"
    → is_noise_variant: true (naming convention variant, identical
      field mapping to qa_engineer anchor)

  "Django Developer"
    → canonical_form: "django_developer"
    → is_noise_variant: false (specific framework, distinct
      sub_specialisation)

  "Frontend Engineer - Karachi - Remote"
    → canonical_form: "frontend_engineer"
    → is_noise_variant: true (location + work arrangement only)

---
## RESPONSE FORMAT

Respond with a JSON array containing one object per title in the batch.
The array must have exactly as many objects as titles in the input.

Start your response with [ and end with ].
No text before [ or after ].
No markdown code fences.
No explanation outside the JSON array.
""".strip()


# ---------------------------------------------------------------------------
# STEP 5 — Build field_id block for system prompt injection
# ---------------------------------------------------------------------------

def build_field_id_block(field_map):
    """Build compact field_id reference block for injection into system prompt."""
    lines = []
    for fid, desc in sorted(field_map.items()):
        if desc:
            lines.append(f"- {fid}: {desc[:80]}")
        else:
            lines.append(f"- {fid}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# STEP 6 — Gemini API call with retry
# ---------------------------------------------------------------------------

def call_gemini(client, batch, system_prompt, anchor_block, memory_block, log_func):
    """
    Send a batch of titles to Gemini for mapping.
    system_prompt is already fully formatted — do not call .format() here.
    Returns parsed list of mapping dicts, or None on failure.
    """
    anchor_section = (
        "ANCHOR TITLES (always exist — use as canonical_form targets "
        "when applicable):\n"
        + anchor_block
        + "\n\n"
    ) if anchor_block else ""

    memory_section = (
        "MEMORY (confirmed non-anchor canonical titles — use as "
        "canonical_form targets when applicable):\n"
        + memory_block
        + "\n\n"
    ) if memory_block else ""

    user_message = (
        anchor_section
        + memory_section
        + "Map these job titles:\n\n"
        + json.dumps(batch, indent=2)
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.0,
                    top_p=0.9,
                    max_output_tokens=8192,
                )
            )
            raw_text = response.text.strip()

            # Strip accidental markdown fences
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```[a-z]*\n?", "", raw_text)
                raw_text = re.sub(r"\n?```$", "", raw_text)
                raw_text = raw_text.strip()

            parsed = json.loads(raw_text)
            if not isinstance(parsed, list):
                log_func(f"WARN | Gemini returned non-list: {type(parsed)}")
                return None

            return parsed

        except json.JSONDecodeError as e:
            log_func(f"WARN | JSON parse failed attempt {attempt}: {e}")
            log_func(f"WARN | Raw response (first 200 chars): {raw_text[:200]}")
            if attempt < MAX_RETRIES:
                time.sleep(REQUEST_DELAY)

        except Exception as e:
            error_str = str(e).lower()
            if any(x in error_str for x in [
                "quota", "429", "resource_exhausted",
                "clienterror", "rate_limit", "too_many_requests"
            ]):
                log_func(f"WARN | Rate limited attempt {attempt} — waiting {RETRY_WAIT}s")
                time.sleep(RETRY_WAIT)
            else:
                log_func(f"WARN | Gemini error attempt {attempt}: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(REQUEST_DELAY)

    log_func(f"ERROR | All {MAX_RETRIES} attempts failed for batch")
    return None


# ---------------------------------------------------------------------------
# STEP 7 — Validate and enrich a single mapping result
# ---------------------------------------------------------------------------

def validate_mapping(result, valid_field_ids, title_item, log_func):
    """
    Validate one Gemini mapping result.
    Fix common errors. Flag invalid field_ids.
    Returns cleaned result dict, or None if unrecoverable.
    """
    if not isinstance(result, dict):
        log_func(f"WARN | Non-dict result for '{title_item['title']}': {result}")
        return None

    result.setdefault("title", title_item["title"])
    result.setdefault("canonical_title", "")
    result.setdefault("primary_field_id", None)
    result.setdefault("secondary_field_ids", [])
    result.setdefault("sub_specialisation", None)
    result.setdefault("confidence", "low")
    result.setdefault("unmapped", False)
    result.setdefault("canonical_form", result.get("canonical_title", ""))
    result.setdefault("is_noise_variant", False)
    result.setdefault("llm_reasoning", "")

    result["count_in_dataset"] = title_item["count"]

    # Validate primary_field_id
    if result["primary_field_id"] and result["primary_field_id"] not in valid_field_ids:
        log_func(
            f"WARN | Invalid primary_field_id '{result['primary_field_id']}' "
            f"for title '{result['title']}' — setting to null"
        )
        result["primary_field_id"] = None
        result["confidence"] = "low"
        result["llm_reasoning"] += " [VALIDATION: primary_field_id was invalid, nulled]"

    # Validate secondary_field_ids
    cleaned_secondary = []
    for fid in result.get("secondary_field_ids", []):
        if fid in valid_field_ids:
            cleaned_secondary.append(fid)
        else:
            log_func(f"WARN | Invalid secondary_field_id '{fid}' for '{result['title']}' — removed")
    result["secondary_field_ids"] = cleaned_secondary

    # Enforce unmapped logic
    if result["unmapped"]:
        result["primary_field_id"] = None
        result["secondary_field_ids"] = []
        result["confidence"] = "low"

    # Validate is_noise_variant type
    if not isinstance(result.get("is_noise_variant"), bool):
        result["is_noise_variant"] = False
        log_func(
            f"WARN | is_noise_variant not bool for "
            f"'{result['title']}' — defaulted to False"
        )

    # canonical_form must be non-empty string
    if not result.get("canonical_form"):
        result["canonical_form"] = result.get("canonical_title", "")

    # Flag empty reasoning
    if not result["llm_reasoning"]:
        result["llm_reasoning"] = "[MISSING — Gemini did not provide reasoning]"
        result["confidence"] = "low"

    return result


# ---------------------------------------------------------------------------
# STEP 8 — Load existing mapping and find new titles
# ---------------------------------------------------------------------------

def load_existing_mapping():
    """Load existing job_title_mapping.json if it exists."""
    if MAPPING_FILE.exists():
        try:
            with open(MAPPING_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"confirmed": {}, "needs_review": {}, "metadata": {}}


def migrate_keys_to_lowercase(mapping, log_func):
    """
    One-time migration: lowercase all title keys in confirmed and
    needs_review sections. The 'title' field inside each entry keeps
    its original casing for human readability. Idempotent — safe to
    run on already-migrated data. Does not change any field_id values
    or entry content — only the dict keys.
    """
    migrated = 0
    for section in ("confirmed", "needs_review"):
        old = dict(mapping.get(section, {}))
        mapping[section] = {}
        for title_key, entry in old.items():
            new_key = title_key.lower()
            mapping[section][new_key] = entry
            if new_key != title_key:
                migrated += 1
    if migrated > 0:
        log_func(f"INFO | Migrated {migrated} keys to lowercase")
    else:
        log_func("INFO | Keys already lowercase — no migration needed")
    return mapping


def find_new_titles(title_items, existing_mapping):
    """
    Find titles not yet in the existing mapping.
    Makes Script C incremental — only new titles are sent to Gemini.
    Respects FORCE_REMAP_NEEDS_REVIEW flag.
    """
    already_confirmed = set(existing_mapping.get("confirmed", {}).keys())
    already_review = set(existing_mapping.get("needs_review", {}).keys())

    if FORCE_REMAP_NEEDS_REVIEW:
        # Reprocess needs_review entries — give them a second chance at
        # higher confidence with the improved v2 prompt
        skip_set = already_confirmed
    else:
        # Standard behaviour — skip both sections
        skip_set = already_confirmed | already_review

    new_titles = [t for t in title_items if t["title"] not in skip_set]

    if FORCE_REMAP_NEEDS_REVIEW:
        remap_count = len(
            [t for t in title_items if t["title"] in already_review]
        )
        # Note: remap_count logged in main() after this call
        return new_titles, remap_count

    return new_titles, 0


def compute_dynamic_anchors(confirmed_mapping, threshold=5):
    """
    Auto-promote canonical_forms to anchor status for this run.

    A canonical_form is promoted when:
    1. It exists as a direct confirmed entry where is_noise_variant=False
       AND confidence="high" AND primary_field_id is not null
    2. At least {threshold} DISTINCT noise variant titles in confirmed
       point to it as their canonical_form

    Returns set of canonical_form strings. On first run (before any
    entry has canonical_form) this correctly returns an empty set.
    """
    from collections import defaultdict

    # Only canonical_forms that are themselves stable high-confidence
    # direct entries are eligible
    eligible_canonicals = {
        entry.get("canonical_form")
        for entry in confirmed_mapping.values()
        if (
            not entry.get("is_noise_variant", False)
            and entry.get("confidence") == "high"
            and entry.get("canonical_form")
            and entry.get("primary_field_id")
        )
    }
    eligible_canonicals.discard(None)

    # Count distinct noise variant titles per canonical
    citation_count = defaultdict(int)
    for entry in confirmed_mapping.values():
        cf = entry.get("canonical_form")
        if entry.get("is_noise_variant", False) and cf in eligible_canonicals:
            citation_count[cf] += 1

    promoted = {cf for cf, count in citation_count.items() if count >= threshold}
    return promoted


def build_memory_index(confirmed_mapping, effective_anchors):
    """
    Build the compact memory index sent to Gemini per batch.

    Contains all unique canonical_forms from confirmed entries where:
    - is_noise_variant is False (only canonical originals)
    - canonical_form is not already in effective_anchors
    - primary_field_id is not null (real mapping)

    On first run (before any entry has canonical_form) this correctly
    returns an empty list.

    Returns sorted list of canonical_form strings.
    """
    memory = set()
    for entry in confirmed_mapping.values():
        cf = entry.get("canonical_form")
        if (
            cf
            and not entry.get("is_noise_variant", False)
            and cf not in effective_anchors
            and entry.get("primary_field_id")
        ):
            memory.add(cf)
    return sorted(memory)


# ---------------------------------------------------------------------------
# STEP 9 — Save mapping file
# ---------------------------------------------------------------------------

def save_mapping(mapping, log_func):
    """Atomic write to job_title_mapping.json."""
    mapping["metadata"]["last_updated"] = datetime.now().isoformat()
    mapping["metadata"]["confirmed_count"] = len(mapping["confirmed"])
    mapping["metadata"]["needs_review_count"] = len(mapping["needs_review"])

    tmp = MAPPING_FILE.with_suffix(".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)
        tmp.replace(MAPPING_FILE)
        log_func(
            f"INFO | Saved mapping — "
            f"confirmed: {mapping['metadata']['confirmed_count']} | "
            f"needs_review: {mapping['metadata']['needs_review_count']}"
        )
    except Exception as e:
        log_func(f"ERROR | Failed to save mapping: {e}")
        raise


# ---------------------------------------------------------------------------
# STEP 10 — Main execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    LOG_FILE.parent.mkdir(exist_ok=True)
    log_handle = open(LOG_FILE, "a", encoding="utf-8", buffering=1)

    def log_func(message):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {message}"
        print(line)
        log_handle.write(line + "\n")
        log_handle.flush()

    log_func(f"INFO | Script C starting — {datetime.now().isoformat()}")

    # Load data
    log_func("INFO | Loading affinity_matrix field_ids...")
    field_map = load_canonical_field_ids()
    valid_field_ids = set(field_map.keys())
    log_func(f"INFO | Canonical field_ids loaded: {len(valid_field_ids)}")

    log_func("INFO | Loading raw jobs...")
    try:
        with open(INPUT_FILE, encoding="utf-8") as f:
            raw_jobs = json.load(f)
    except FileNotFoundError:
        log_func(f"ERROR | {INPUT_FILE} not found — pull from data-branch first")
        log_handle.close()
        sys.exit(1)
    log_func(f"INFO | Raw jobs: {len(raw_jobs)}")

    log_func("INFO | Extracting unique titles...")
    title_items = extract_unique_titles(raw_jobs)
    log_func(f"INFO | Unique titles found: {len(title_items)}")

    # Load existing mapping, migrate keys to lowercase, find new titles
    mapping = load_existing_mapping()
    mapping = migrate_keys_to_lowercase(mapping, log_func)
    save_mapping(mapping, log_func)

    new_titles, remap_count = find_new_titles(title_items, mapping)
    log_func(
        f"INFO | Already mapped: "
        f"{len(mapping['confirmed']) + len(mapping['needs_review'])}"
    )
    log_func(f"INFO | New titles to map this run: {len(new_titles)}")

    if FORCE_REMAP_NEEDS_REVIEW:
        log_func(
            f"INFO | FORCE_REMAP_NEEDS_REVIEW=True — "
            f"{remap_count} needs_review titles will be reprocessed"
        )

    # Refresh count_in_dataset for already-mapped titles.
    # Keeps the field accurate for human review prioritisation
    # as new jobs accumulate between Script C runs.
    count_refreshed = 0
    title_count_map = {item["title"]: item["count"] for item in title_items}
    for section in ("confirmed", "needs_review"):
        for title, entry in mapping[section].items():
            if title in title_count_map:
                new_count = title_count_map[title]
                if entry.get("count_in_dataset") != new_count:
                    entry["count_in_dataset"] = new_count
                    count_refreshed += 1
    if count_refreshed > 0:
        save_mapping(mapping, log_func)
        log_func(
            f"INFO | Refreshed count_in_dataset for "
            f"{count_refreshed} existing titles"
        )
    else:
        log_func("INFO | count_in_dataset up to date — no refresh needed")

    if not new_titles:
        log_func("INFO | No new titles found — mapping is up to date. Exiting.")
        log_handle.close()
        sys.exit(0)

    # Build system prompt components
    field_id_block = build_field_id_block(field_map)

    # Compute effective anchors for this run
    dynamic_anchors = compute_dynamic_anchors(mapping["confirmed"], threshold=5)
    effective_anchors = HARDCODED_ANCHORS | dynamic_anchors
    if dynamic_anchors:
        log_func(
            f"INFO | Dynamic anchors promoted: "
            f"{len(dynamic_anchors)} — {sorted(dynamic_anchors)}"
        )
    log_func(f"INFO | Effective anchors: {len(effective_anchors)} total")

    # Build memory index
    memory_titles = build_memory_index(mapping["confirmed"], effective_anchors)
    log_func(f"INFO | Memory index: {len(memory_titles)} canonical titles")

    # Build anchor and memory block strings for prompt
    anchor_block = "\n".join(sorted(effective_anchors))
    memory_block = "\n".join(memory_titles)

    # Single format() call — all three placeholders filled
    system_prompt = GEMINI_SYSTEM_PROMPT.format(
        field_id_block=field_id_block,
        anchor_block=anchor_block,
        memory_block=memory_block,
    )

    # Process in batches
    batches = [
        new_titles[i:i + BATCH_SIZE]
        for i in range(0, len(new_titles), BATCH_SIZE)
    ]
    log_func(f"INFO | Processing {len(batches)} batches of up to {BATCH_SIZE}")

    total_mapped = 0
    total_failed = 0
    failed_titles = []

    for batch_num, batch in enumerate(batches, 1):
        log_func(f"INFO | Batch {batch_num}/{len(batches)} — {len(batch)} titles")

        results = call_gemini(
            client, batch, system_prompt,
            anchor_block, memory_block, log_func
        )

        if results is None:
            log_func(f"ERROR | Batch {batch_num} failed — titles queued for retry on next run")
            failed_titles.extend(batch)
            total_failed += len(batch)
            continue

        if len(results) < len(batch):
            log_func(
                f"WARN | Gemini returned {len(results)} results for "
                f"{len(batch)} titles — {len(batch) - len(results)} titles "
                f"will be retried on next run (find_new_titles catches them)"
            )

        for i, title_item in enumerate(batch):
            if i >= len(results):
                failed_titles.append(title_item)
                total_failed += 1
                continue

            result = results[i]
            cleaned = validate_mapping(result, valid_field_ids, title_item, log_func)
            if cleaned is None:
                failed_titles.append(title_item)
                total_failed += 1
                continue

            if cleaned["confidence"] == "high" and not cleaned["unmapped"]:
                mapping["confirmed"][cleaned["title"]] = cleaned
            else:
                mapping["needs_review"][cleaned["title"]] = cleaned

            total_mapped += 1

        # Incremental save after every batch
        save_mapping(mapping, log_func)

        if batch_num < len(batches):
            time.sleep(REQUEST_DELAY)

    # Final summary
    log_func(
        f"INFO | Script C complete\n"
        f"  Total new titles processed:  {total_mapped}\n"
        f"  Failed (will need retry):     {total_failed}\n"
        f"  Total confirmed mappings:     {len(mapping['confirmed'])}\n"
        f"  Total needs_review:           {len(mapping['needs_review'])}\n"
        f"  Output: {MAPPING_FILE}"
    )

    if failed_titles:
        log_func(f"WARN | {total_failed} titles failed. Re-run Script C to retry.")

    log_func("INFO | NEXT STEPS:")
    log_func("INFO | 1. Review backend/data/job_title_mapping.json needs_review section")
    log_func("INFO | 2. Move correct mappings to confirmed section manually")
    log_func("INFO | 3. Commit job_title_mapping.json after review")
    log_func("INFO | 4. Then run Script D to aggregate counts into lag_model")

    log_handle.close()
