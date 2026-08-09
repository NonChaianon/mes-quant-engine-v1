from __future__ import annotations

from collections.abc import Iterable


class FinalTestSealError(RuntimeError):
    pass


def assert_no_final_test_rows(
    frame: object,
    *,
    partition_column: str = "outer_partition",
    final_test_value: str = "FINAL_TEST",
    session_date_column: str = "nyse_session_date",
    decision_time_column: str = "decision_time",
    final_test_start_year: int = 2025,
) -> None:
    import pandas as pd

    if partition_column in frame.columns and frame[partition_column].eq(final_test_value).any():
        raise FinalTestSealError("FINAL_TEST row escaped into a Development-only artifact")
    if session_date_column in frame.columns:
        session_dates = pd.to_datetime(frame[session_date_column], errors="raise")
        if session_dates.isna().any():
            raise FinalTestSealError("Null session date found in Development-only artifact")
        years = session_dates.dt.year
        if years.ge(final_test_start_year).any():
            raise FinalTestSealError("2025+ session escaped into a Development-only artifact")
    if decision_time_column in frame.columns:
        decision_times = pd.to_datetime(
            frame[decision_time_column], utc=True, errors="raise"
        )
        if decision_times.isna().any():
            raise FinalTestSealError("Null decision_time found in Development-only artifact")
        cutoff = pd.Timestamp(f"{final_test_start_year}-01-01", tz="UTC")
        if decision_times.ge(cutoff).any():
            raise FinalTestSealError(
                "Decision time at or after the Final Test cutoff escaped into Development"
            )


def assert_target_columns_absent(frame: object, forbidden_tokens: Iterable[str]) -> None:
    lowered = {str(column).lower() for column in frame.columns}
    violations = sorted(
        column for column in lowered if any(token.lower() in column for token in forbidden_tokens)
    )
    if violations:
        raise FinalTestSealError("Target-like columns found in feature output: " + ", ".join(violations))
