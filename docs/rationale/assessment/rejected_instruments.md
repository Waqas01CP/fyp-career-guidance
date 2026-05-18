# Rejected Instruments — Why We Did Not Use Them

**Component:** Assessment instrument selection
**Decided:** Architecture Chat v4-v5 (May 2026)
**Status:** Locked in CLAUDE.md v2.5

---

## MBTI — Myers-Briggs Type Indicator

### Decision: Rejected permanently

**Reason 1 — Scientific validity:**
The National Academy of Sciences (1991) found insufficient research basis
for using MBTI in career counselling. A 2024 large-scale study confirmed
Big Five is 2× more accurate than MBTI for career outcome prediction.

**Reason 2 — Binary categories:**
MBTI assigns students to one of 16 types using binary I/E, N/S, T/F, J/P
categories. A student who scores 51% I and 49% E is classified identically
to one who scores 90% I — losing ~38% of the measurement variance. Big Five
continuous scores preserve this information.

**Reason 3 — Redundancy:**
Adding MBTI to a system that already uses Big Five (Conscientiousness +
Neuroticism) and CAAS (Curiosity, Confidence, Control, Cooperation,
Concern) provides approximately zero incremental predictive value — the
dimensions overlap almost entirely.

**Viva response if asked:** "MBTI was evaluated and rejected. The National
Academy of Sciences (1991) found insufficient empirical support for career
counselling use. A 2024 large-scale meta-analysis confirmed Big Five is
twice as accurate. Our system uses Big Five dimensions (Conscientiousness
and Neuroticism) which subsume the relevant MBTI dimensions with
continuous scoring rather than binary type assignment."

---

## EQ-i Youth — Emotional Intelligence

### Decision: Deferred to Sprint 4, not permanently rejected

**Why it was considered:**
Emotional intelligence predicts success in Social-RIASEC careers (Medicine,
Teaching, Social Work, Psychology) where RIASEC fit alone is insufficient.
A student who scores high S on RIASEC may lack the emotional regulation
and empathy needed for clinical patient care.

**Why it was deferred:**
1. Adding EQ-i Youth increases the assessment stack by ~42-45 questions
   (after overlap removal with existing instruments). This puts total
   question count above 300 — a significant administration burden.
2. At the current Karachi university coverage, Social-RIASEC degrees
   are a minority of the recommendation pool. The marginal value of
   EQ-i Youth does not justify the question burden until the pool is larger.

**Reinstatement triggers:**
- Social-RIASEC degrees exceed 30% of the recommendation pool
- Disproportionate mismatch rate in user feedback for Social-type degrees
- When reinstated: place in Tier 2, reduce to ~42-45 questions after
  overlap removal with CAAS Cooperation and Big Five Agreeableness

---

## Dropped Big Five Dimensions

Three of the five Big Five dimensions were evaluated and dropped:

**Openness (to experience):**
CAAS Curiosity covers approximately 40% of Openness variance. The
remaining variance in Openness (aesthetic sensitivity, preference for
abstract thinking) does not have a clear routing use case in the current
system. Adding 6 Openness questions would increase assessment burden
without improving routing decisions. Dropped.

**Extraversion:**
CAAS Cooperation covers the interpersonal dimension of Extraversion
adequately for career routing purposes. The remaining Extraversion
variance (positive affect, social dominance) is not a meaningful
discriminator between degree programmes in the Pakistani context.
Dropped.

**Agreeableness:**
Agreeableness predicts workplace harmony and interpersonal relationships
on the job — not degree suitability or academic success. No routing use
case exists in the current system. Dropped.

---

## Minnesota Importance Questionnaire (MIQ)

### Decision: Rejected on licensing grounds

The MIQ (Rounds, Henly, Dawis, Lofquist, & Weiss, 1981) is the standard
instrument for measuring TWA-based work values. It was the first choice
for the values assessment layer.

**Rejection reason:** CC BY-NC license (Creative Commons
Attribution-NonCommercial). The FYP system may be commercialised
post-viva. Using MIQ content under CC BY-NC creates licensing risk
even for academic use when commercial potential exists.

**Resolution:** The original VNA (Vocational Needs Assessment) instrument
was written based on TWA theory (Dawis & Lofquist, 1964 — fully public
domain), covering the same construct space with original question text.

---

## Strong Interest Inventory (SII)

### Decision: Rejected on licensing and relevance grounds

The SII (CPP Inc.) is the most widely used career interest instrument
globally and uses Holland's 30 Basic Interest Scales — the theoretical
basis for KCIS.

**Rejection reason 1 — Licensing:** The SII is proprietary. Question text
is copyrighted by CPP Inc. Using adapted versions without a license
constitutes infringement.

**Rejection reason 2 — Cultural fit:** The SII is designed for the US
labour market. Sub-scales like "Athletics," "Military Activities," and
"Culinary Arts" are not meaningful discriminators for Pakistani university
degrees in Karachi.

**Resolution:** KCIS (Karachi Career Interest Sub-Scale) was written as
an original instrument using the same theoretical framework (Holland's
Basic Interest Scale concept) with Pakistani-specific sub-scales and
original question text.
