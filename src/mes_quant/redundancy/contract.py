"""Proposed Stage B constants; freeze the policy before implementing the analyzer."""

POLICY_VERSION = "MES_V1_REDUNDANCY_1.0"
POLICY_STATUS = "PROVISIONAL_NOT_EXECUTABLE"

CELL14_FEATURE_FILE_SHA256 = (
    "aaf606e3d8869a414f0e687835c44529303a9b4e98f0092da39631ab2fc53452"
)
CELL14_FEATURE_CONTENT_SHA256 = (
    "dbee5a9607f05de8460e4738fa8c288368be9afabba58fc53a1ff373fbb2074d"
)
EXPECTED_DEVELOPMENT_ROWS = 31_193
FINAL_TEST_START_YEAR = 2025
FOLD_ROLE_COLUMNS = ("role_wf_2022", "role_wf_2023", "role_wf_2024")

ALLOWED_INPUT_CELLS = (8, 14)
FORBIDDEN_INPUT_CELLS = (9, 10, 11, 12, 13)

# Proposed thresholds from the independently audited Stage B design. They are
# deliberately non-executable until the policy is promoted from PROVISIONAL.
HARD_REDUNDANCY_PEARSON_ABS = 0.95
HARD_REDUNDANCY_SPEARMAN_ABS = 0.95
REVIEW_CORRELATION_ABS = 0.90
SEMANTIC_IDENTITY_TOLERANCE = 1e-12

REPRESENTATIVE_TIE_BREAK = (
    "HIGHER_CAUSAL_AVAILABILITY",
    "SHORTER_SAFER_LOOKBACK",
    "TRAIN_HISTORY_STABILITY",
    "SIMPLER_INTERPRETATION",
    "LEXICAL_FEATURE_NAME",
)
# ------------------------------------------------------------
# Stage B cohort / missingness policy
# ------------------------------------------------------------

COMMON_COHORT_POLICY = "FULL_29_COMPLETE_CASE_TRAIN_PER_FOLD"

PAIRWISE_COVERAGE_POLICY = "REPORT_ONLY_NOT_FOR_SELECTION"

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