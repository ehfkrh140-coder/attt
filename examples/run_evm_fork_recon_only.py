from recon.recon_engine import ReconEngine
from targets.target_schema import mock_target

if __name__ == "__main__":
    print(ReconEngine().run(mock_target(scope_confirmed=True)))
