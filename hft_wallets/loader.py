from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

_loaded = False


def get_config_dir() -> str:
    d = os.getenv("HFT_WALLETS_DIR", "")
    if d:
        return d
    return str(Path.home() / ".hft-wallets")


def load_wallets() -> None:
    """Load wallets.env from the config directory into os.environ. Idempotent."""
    global _loaded
    if _loaded:
        return
    wallets_path = os.path.join(get_config_dir(), "wallets.env")
    if os.path.isfile(wallets_path):
        load_dotenv(wallets_path)
    _loaded = True


def load_wallet_for_bot(bot_key: str) -> dict:
    """Read wallet_config.json and return resolved credentials for *bot_key*.

    Returns a dict with optional keys ``kalshi`` and ``polymarket``, each
    containing credential fields from the corresponding named env vars.
    Keyfile paths are resolved to absolute paths relative to the config dir.
    """
    load_wallets()

    config_path = os.path.join(get_config_dir(), "wallet_config.json")
    with open(config_path) as f:
        cfg = json.load(f)
    if bot_key not in cfg:
        raise KeyError(f"Bot {bot_key!r} not found in wallet_config.json")

    result: dict = {}
    bc = cfg[bot_key]
    config_dir = get_config_dir()

    if "kalshi" in bc:
        name = bc["kalshi"]
        prefix = "KALSHI_" + name.upper().replace("-", "_")
        keyfile = os.getenv(f"{prefix}_KEYFILE", "")
        if keyfile and not os.path.isabs(keyfile):
            keyfile = os.path.join(config_dir, keyfile)
        result["kalshi"] = {
            "key_id": os.getenv(f"{prefix}_KEYID", ""),
            "keyfile": keyfile,
        }

    if "polymarket" in bc:
        name = bc["polymarket"]
        prefix = "POLYMARKET_" + name.upper().replace("-", "_")
        result["polymarket"] = {
            "private_key": os.getenv(f"{prefix}_PRIVATE_KEY", ""),
            "api_key": os.getenv(f"{prefix}_API_KEY", ""),
            "secret": os.getenv(f"{prefix}_SECRET", ""),
            "passphrase": os.getenv(f"{prefix}_PASSPHRASE", ""),
            "funder": os.getenv(f"{prefix}_FUNDER", ""),
            "sig_type": os.getenv(f"{prefix}_SIG_TYPE", "2"),
            "relayer_api_key": os.getenv(f"{prefix}_RELAYER_API_KEY", ""),
        }

    return result


def get_first_kalshi_wallet() -> dict:
    """Return credentials for the first available Kalshi wallet.

    Iterates KALSHI_WALLETS and returns the first entry with a non-empty KEYID.
    Useful for utility scripts that don't have a specific bot assignment.
    """
    load_wallets()

    config_dir = get_config_dir()
    wallets = os.getenv("KALSHI_WALLETS", "").split(",")
    for name in wallets:
        name = name.strip()
        if not name:
            continue
        prefix = "KALSHI_" + name.upper().replace("-", "_")
        kid = os.getenv(f"{prefix}_KEYID", "")
        kf = os.getenv(f"{prefix}_KEYFILE", "")
        if kid:
            if kf and not os.path.isabs(kf):
                kf = os.path.join(config_dir, kf)
            return {"key_id": kid, "keyfile": kf}
    return {"key_id": "", "keyfile": ""}
