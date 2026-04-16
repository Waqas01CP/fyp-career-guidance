"""
config.py — All tunable system constants.
Never hardcode these values in nodes, endpoints, or services.
All scoring weights, thresholds, and pool sizes live here.
"""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://fyp_user:fyp_password@localhost:5432/fyp_db"

    # JWT
    SECRET_KEY: str = "change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 60

    # LLM
    GEMINI_API_KEY: str = ""
    LLM_MODEL_NAME: str = "gemini-2.0-flash"

    # LangSmith (dev only)
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "fyp-career-guidance"

    # Rate limiting
    CHAT_RATE_LIMIT: str = "10/minute"

    # Assessment quiz draw config (capability assessment — NOT RIASEC)
    ASSESSMENT_QUESTIONS_PER_SESSION: dict = Field(
        default_factory=lambda: {"easy": 3, "medium": 5, "hard": 4}
    )

    # Capability blend (ScoringNode)
    CAPABILITY_BLEND_THRESHOLD: int = 25       # abs gap (points) before blend triggers
    CAPABILITY_BLEND_WEIGHT: float = 0.25      # weight of capability in blended grade
    CAPABILITY_BLEND_MAX_SHIFT: int = 10       # max points effective grade can shift

    # Scoring weights
    SCORING_WEIGHTS: dict = Field(default_factory=lambda: {
        "inter":           {"match": 0.6, "future": 0.4},
        "matric_planning": {"match": 0.7, "future": 0.3},
    })

    # FutureValue layer weights by lag category
    # layer1=pak_now, layer2=pak_future, layer3a=world_now, layer3b=world_future
    # All rows sum to 1.0 — layer3 split into layer3a/layer3b to fix double-counting bug.
    FUTURE_VALUE_WEIGHTS: dict = Field(default_factory=lambda: {
        "LEAPFROG": {"layer1": 0.30, "layer2": 0.20, "layer3a": 0.30, "layer3b": 0.20},
        "FAST":     {"layer1": 0.35, "layer2": 0.25, "layer3a": 0.24, "layer3b": 0.16},
        "MEDIUM":   {"layer1": 0.40, "layer2": 0.30, "layer3a": 0.18, "layer3b": 0.12},
        "SLOW":     {"layer1": 0.45, "layer2": 0.35, "layer3a": 0.12, "layer3b": 0.08},
        "LOCAL":    {"layer1": 0.60, "layer2": 0.40, "layer3a": 0.00, "layer3b": 0.00},
    })

    LAG_CONFIDENCE: dict = Field(default_factory=lambda: {
        "LEAPFROG": 1.00,
        "FAST":     0.95,
        "MEDIUM":   0.85,
        "SLOW":     0.70,
        "LOCAL":    1.00,
    })

    # Filter thresholds
    MERIT_STRETCH_THRESHOLD: int = 5        # % below cutoff_min to qualify as stretch
    FILTER_MINIMUM_RESULTS_SHOWN: int = 5   # always show at least this many degrees

    # Mismatch notice thresholds
    MISMATCH_SCORE_GAP_THRESHOLD: int = 20       # min score gap to trigger mismatch
    MISMATCH_FUTURE_VALUE_CEILING: float = 6.0   # pref FV must be below this too

    # Roadmap diff threshold
    ROADMAP_SIGNIFICANT_CHANGE_COUNT: int = 2    # min top-5 changes to show "What Changed"

    # Profiler required fields
    PROFILER_REQUIRED_FIELDS: list = Field(
        default_factory=lambda: ["budget_per_semester", "transport_willing", "home_zone"]
    )
    PROFILER_OPTIONAL_FIELDS: list = Field(
        default_factory=lambda: ["stated_preferences", "family_constraints", "career_goal", "student_notes"]
    )


settings = Settings()
