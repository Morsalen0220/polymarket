from web3 import Web3

# Known Polymarket router
POLY_ROUTER = Web3.to_checksum_address(
    "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E"
)

# Common Polymarket CLOB function selectors
# (observed in real txs)
KNOWN_SELECTORS = {
    "0x7c025200": "placeOrder",
    "0xb6f9de95": "matchOrders",
    "0x3f62192e": "fillOrder",
}


def decode_polymarket_tx(w3, tx_hash):
    """
    PHASE-A:
    tx_hash -> { token_id, side, function }
    """
    try:
        tx = w3.eth.get_transaction(tx_hash)

        if not tx or not tx["to"]:
            return None

        to_addr = Web3.to_checksum_address(tx["to"])
        if to_addr != POLY_ROUTER:
            return None

        input_data = tx["input"]
        if input_data == "0x" or len(input_data) < 10:
            return None

        selector = input_data[:10]
        fn = KNOWN_SELECTORS.get(selector)

        if not fn:
            return None

        # --- heuristic decoding ---
        # tokenId usually appears in first 2–3 params
        # grab first uint256-looking chunk
        data = input_data[10:]
        chunks = [data[i:i+64] for i in range(0, len(data), 64)]

        token_id = int(chunks[0], 16)

        # side inference (heuristic but works well)
        # YES tokenId is usually even, NO odd (Polymarket convention)
        side = "YES" if token_id % 2 == 0 else "NO"

        return {
            "function": fn,
            "token_id": token_id,
            "side": side
        }

    except Exception as e:
        return None
