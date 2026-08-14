"""Stage B V1.2 locked-control pins with production execution disabled."""

POLICY_VERSION = "MES_V1_REDUNDANCY_1.2"
# This existing sentinel remains PROVISIONAL so the production gate stays
# closed. Issue #13 locks policy controls; it does not enable execution.
POLICY_STATUS = "PROVISIONAL"

# Issue #9 was a bounded remediation from this exact accepted baseline.
REMEDIATION_BASE_COMMIT = "a5d3f40e7edc26d950010401654ce4d6b7822e86"

# STEP_14G1_SERIALIZATION_POLICY_IDS_V1_2
#
# These identifiers define the deterministic Stage B
# production-output byte profiles required by the locked
# Markdown contract. They do not open the production gate.
STAGE_B_CSV_SERIALIZATION_POLICY_ID = "MES_V1_CSV_UTF8_LF_SCHEMA_ROW_ORDER_V1"
STAGE_B_JSON_SERIALIZATION_POLICY_ID = "MES_V1_JSON_CANONICAL_UTF8_LF_V1"
STAGE_B_AUDIT_HASH_POLICY_ID = "MES_V1_AUDIT_HASH_NON_RECURSIVE_EXTERNAL_MANIFEST_V1"

# STEP_14G1B_PARQUET_AND_MULTI_VALUE_POLICY_IDS_V1_2
#
# Explicit Stage B deterministic serialization profiles.
# These constants do not open the production gate.
STAGE_B_PARQUET_SERIALIZATION_POLICY_ID = "MES_V1_PARQUET_PYARROW_ZSTD_SORTED_NO_INDEX_V1"
STAGE_B_MULTI_VALUE_SERIALIZATION_POLICY_ID = "MES_V1_MULTI_ID_PIPE_ORDERED_V1"



# Exact historical V1.1 locked-control provenance from Section 46 Steps 10-11.
PRIOR_V1_1_LOCKED_CONTROL_COMMIT = (
    "bd9e38c11e01bae18a5ffa0a6a0405a008273d27"
)

# Exact V1.2 locked-control provenance and byte bindings. The control commit
# precedes this pin update, avoiding self-referential commit provenance. These
# bindings do not open the production execution gate.
LOCKED_CONTROL_COMMIT = "a60d2498754df641e9c8a3308d330f3c4e05fb74"
MARKDOWN_CONTRACT_PATH = "docs/STAGE_B_REDUNDANCY_CONTRACT.md"
MARKDOWN_CONTRACT_SHA256 = "b672124603d6f4057c3aa54dc98b04ac056ccf9bbf3d82fb31b4d856f729e33f"
SEMANTIC_REGISTRY_PATH = "configs/v1/stage_b_semantic_registry_v1.json"
SEMANTIC_REGISTRY_SHA256 = "9c50ed834bf82d66115ab54757d1d04d0a03c2afab1fe7a81d9fcaf8293f91e1"

CELL14_FEATURE_FILE_SHA256 = (
    "aaf606e3d8869a414f0e687835c44529303a9b4e98f0092da39631ab2fc53452"
)
CELL14_FEATURE_CONTENT_SHA256 = (
    "dbee5a9607f05de8460e4738fa8c288368be9afabba58fc53a1ff373fbb2074d"
)
EXPECTED_DEVELOPMENT_ROWS = 31_193
FINAL_TEST_START_YEAR = 2025

# STEP_14G3B1_FROZEN_PROVENANCE_PINS
#
# Enforcement pins derived from the already byte-frozen
# canonical Cell 14 release control. These are production
# firewall pins, not a new Stage B methodology authority.
CELL14_RELEASE_MANIFEST_PATH = "manifests/releases/cell14_local_release_v1.json"
CELL14_RELEASE_MANIFEST_SHA256 = "74bd9d009cca43368488eea245b7b3b64918edc354091ba82172aaab6803a197"
CELL14_REGISTRY_FILE_SHA256 = "7df68538d3e4a1447f1bca01396e3e141389decd196ba32faf04e34913107d95"
CELL14_AUDIT_FILE_SHA256 = "2adca2642c423ff634cb99de50f8fb5d0fc5f49d70188213021b9ee006ffdcd3"
CELL8_ASSIGNMENTS_FILE_SHA256 = "2e13ee7d1e7de321411604c3500c73e68a080b02fa2983288d41d399aeb43035"
CELL8_AUDIT_FILE_SHA256 = "add3186cb6265d49f96946ced1752f4ed0059b9fd5451f106f5d29f24fb5862a"

FOLD_ROLE_COLUMNS = ("role_wf_2022", "role_wf_2023", "role_wf_2024")

ALLOWED_INPUT_CELLS = (8, 14)
FORBIDDEN_INPUT_CELLS = (9, 10, 11, 12, 13)

# Locked V1.1 target-blind thresholds.
# Real-data execution remains forbidden until the required tests,
# analyzer/runtime, orchestration, and clean-checkout gates pass.
HARD_REDUNDANCY_PEARSON_ABS = 0.95
HARD_REDUNDANCY_SPEARMAN_ABS = 0.95
REVIEW_CORRELATION_ABS = 0.90
SEMANTIC_IDENTITY_TOLERANCE = 1e-12

# ------------------------------------------------------------
# Stage B V1.2 generic exact-rank discovery authority
# ------------------------------------------------------------

GENERIC_RANK_DIRECT_DROP_AUTHORIZED = False
GENERIC_RANK_ENVIRONMENT_CHANGE_RESOLVES_OPEN = False

GENERIC_RANK_OPEN_STATUSES = (
    "STABLE_LOCALIZED_UNEXPLAINED_EXACT_DEPENDENCY",
    "COHORT_CONDITIONAL_LOCALIZED_EXACT_DEPENDENCY",
)

GENERIC_RANK_HARD_FAIL_STATUSES = (
    "UNSTABLE_EXACT_DEPENDENCY",
    "UNLOCALIZABLE_EXACT_DEPENDENCY",
    "TOLERANCE_INCONSISTENT_EXACT_DEPENDENCY",
    "NUMERICALLY_INCONSISTENT_EXACT_DEPENDENCY",
)

# ------------------------------------------------------------
# Stage B cohort / missingness policy
# ------------------------------------------------------------

COMMON_COHORT_POLICY = "FULL_29_COMPLETE_CASE_TRAIN_PER_FOLD"


MISSINGNESS_POLICY = (
    "NO_IMPUTATION",
    "NO_FORWARD_FILL",
    "NO_MEDIAN_FILL",
    "NO_SILENT_ROW_DROP",
)

# ------------------------------------------------------------
# Operational fallback policy
#
# If a future model cannot produce a valid score because required
# information is unavailable, the decision must remain in the
# full universe and map to FLAT rather than disappearing.
# ------------------------------------------------------------

UNUSABLE_DECISION_ACTION = "FLAT"

NO_SCORE_POSITION = 0

COVERAGE_DENOMINATOR_POLICY = "FULL_DECISION_UNIVERSE"

UNUSABLE_DECISION_MUST_REMAIN_IN_COVERAGE = True
