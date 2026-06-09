from arenas.mock_arena import MockArena


class EvmForkArena(MockArena):
    runtime = "evm"
    rpc_url = "http://127.0.0.1:8545"
    chain_id = 31337
    is_local = True
