from arenas.mock_arena import MockArena


class SuiLocalnetArena(MockArena):
    runtime = "sui_move"
    rpc_url = "http://127.0.0.1:9000"
    chain_id = 900
    is_local = True
