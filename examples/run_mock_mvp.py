from __future__ import annotations

from eval.regression_suite import CORE_REGRESSION_MODES, run_core_regression_suite_sync
from reports.report_writer import write_beginner_summary


def main() -> None:
    result = run_core_regression_suite_sync()
    print(
        write_beginner_summary(
            result.scorecard,
            regression_case_count=len(result.cases),
            modes_tested=CORE_REGRESSION_MODES,
        )
    )


if __name__ == "__main__":
    main()
