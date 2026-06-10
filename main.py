from __future__ import annotations

from reports.report_writer import write_protocol_twin_summary
from simulation.auto_runner import AutoSimulationRequest, run_auto_simulation_sync


def main() -> None:
    result = run_auto_simulation_sync(AutoSimulationRequest(protocol="mock_lending"))
    print(write_protocol_twin_summary(result))


if __name__ == "__main__":
    main()
