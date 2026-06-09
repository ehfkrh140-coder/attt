from __future__ import annotations

import asyncio

from arenas.local_mempool_arena import LocalMempoolArena
from eval.evaluation_harness import EvaluationHarness
from recon.recon_engine import ReconEngine
from redteam.drills.oracle_divergence_drill import ExecutableOracleDivergenceDrill
from targets.target_schema import mock_target


async def run() -> object:
    target = mock_target(scope_confirmed=True)
    recon = ReconEngine().run(target)
    arena = LocalMempoolArena()
    drill = ExecutableOracleDivergenceDrill()
    return await EvaluationHarness().run(target, recon, arena, drill)


def main() -> None:
    result = asyncio.run(run())
    print(result)


if __name__ == "__main__":
    main()
