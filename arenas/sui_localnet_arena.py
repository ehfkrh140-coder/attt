from arenas.mock_arena import MockArena


class SuiLocalnetArena(MockArena):
    """Gated Sui localnet placeholder.

    Executable support remains disabled until a real isolated Move adapter exists.
    """

    runtime = "sui_move"
    rpc_url = "http://127.0.0.1:9000"
    chain_id = 900
    is_local = True
    adapter_ready = False
