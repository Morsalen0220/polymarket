from web3 import Web3
from collections import defaultdict

# Polygon USDC
USDC_ADDRESS = Web3.to_checksum_address(
    "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
)

# Polymarket core contracts (CONFIRMED)
POLY_CLOB = Web3.to_checksum_address(
    "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E"
)
POLY_VAULT = Web3.to_checksum_address(
    "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"
)

TRANSFER_SIG = Web3.keccak(text="Transfer(address,address,uint256)").hex()

def _parse_amount(data):
    if isinstance(data, bytes):
        return int.from_bytes(data, "big")
    return int(data, 16)

def extract_usdc_transfer(log):
    if Web3.to_checksum_address(log["address"]) != USDC_ADDRESS:
        return None
    if log["topics"][0].hex() != TRANSFER_SIG:
        return None

    from_addr = Web3.to_checksum_address("0x" + log["topics"][1].hex()[-40:])
    to_addr = Web3.to_checksum_address("0x" + log["topics"][2].hex()[-40:])
    amount = _parse_amount(log["data"]) / 1e6

    return from_addr, to_addr, amount


def decode_block_polymarket_trades(logs):
    """
    Returns list of CONFIRMED Polymarket trades in this block.
    Each trade is aggregated per TX hash.
    """
    tx_map = defaultdict(lambda: {
        "total_usd": 0.0,
        "has_clob": False,
        "has_vault": False,
        "user": None
    })

    for log in logs:
        parsed = extract_usdc_transfer(log)
        if not parsed:
            continue

        from_addr, to_addr, amount = parsed
        txh = log["transactionHash"].hex()
        entry = tx_map[txh]

        entry["total_usd"] += amount

        if from_addr == POLY_CLOB or to_addr == POLY_CLOB:
            entry["has_clob"] = True
        if from_addr == POLY_VAULT or to_addr == POLY_VAULT:
            entry["has_vault"] = True

        # user = address that is NOT polymarket contract
        if from_addr not in (POLY_CLOB, POLY_VAULT):
            entry["user"] = from_addr

    confirmed = []
    for txh, data in tx_map.items():
        if data["has_clob"] and data["has_vault"] and data["user"]:
            confirmed.append({
                "tx_hash": txh,
                "trader": data["user"],
                "usd_size": round(data["total_usd"], 2)
            })

    return confirmed
