#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import dotenv_values

from hft_wallets.loader import get_config_dir


def _env_key(name: str) -> str:
    return name.replace("-", "_").upper()


def _truncate(s: str, head: int = 8, tail: int = 4) -> str:
    if len(s) <= head + tail + 3:
        return s
    return f"{s[:head]}...{s[-tail:]}"


def _load_env() -> dict:
    path = os.path.join(get_config_dir(), "wallets.env")
    if not os.path.isfile(path):
        print(f"Error: {path} not found. Run 'hft-wallets init' first.")
        sys.exit(1)
    return dotenv_values(path)


def _config_path() -> str:
    return os.path.join(get_config_dir(), "wallet_config.json")


def _load_config() -> dict:
    p = _config_path()
    if os.path.isfile(p):
        with open(p) as f:
            return json.load(f)
    return {}


def _save_config(config: dict) -> None:
    with open(_config_path(), "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")


def _valid_kalshi(env: dict) -> list[tuple[str, str]]:
    raw = env.get("KALSHI_WALLETS", "") or ""
    result = []
    for w in (n.strip() for n in raw.split(",") if n.strip()):
        kid = (env.get(f"KALSHI_{_env_key(w)}_KEYID") or "").strip()
        if kid:
            result.append((w, _truncate(kid)))
    return result


def _valid_polymarket(env: dict) -> list[tuple[str, str]]:
    raw = env.get("POLYMARKET_WALLETS", "") or ""
    result = []
    for w in (n.strip() for n in raw.split(",") if n.strip()):
        pk = (env.get(f"POLYMARKET_{_env_key(w)}_PRIVATE_KEY") or "").strip()
        if not pk:
            continue
        funder = (env.get(f"POLYMARKET_{_env_key(w)}_FUNDER") or "").strip()
        hint = _truncate(funder) if funder else _truncate(pk)
        result.append((w, hint))
    return result


def _prompt_wallet(choices: list[tuple[str, str]], current: str, label: str) -> str:
    print(f"\n  {label}:")
    if not choices:
        print("    (no valid wallets)")
        return current
    for i, (name, hint) in enumerate(choices, 1):
        mark = " [current]" if name == current else ""
        print(f"    {i}) {name}  ({hint}){mark}")
    print(f"    Enter) keep current" + (f" ({current})" if current else " (none)"))
    while True:
        try:
            s = input("  Choice: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return current
        if not s:
            return current
        if s.isdigit() and 1 <= int(s) <= len(choices):
            return choices[int(s) - 1][0]
        print("  Invalid choice.")


# ── Commands ──────────────────────────────────────────────────────────────


def cmd_init(_args: argparse.Namespace) -> None:
    d = get_config_dir()
    keys_dir = os.path.join(d, "keys")
    os.makedirs(keys_dir, exist_ok=True)

    wallets_path = os.path.join(d, "wallets.env")
    if not os.path.isfile(wallets_path):
        template = """\
# ── Wallet Registry ──────────────────────────────────────
KALSHI_WALLETS=main,sports_hft,beni_hft
POLYMARKET_WALLETS=main,sports_hft,copy_hft

# ── Kalshi: main ─────────────────────────────────────────
KALSHI_MAIN_KEYID=
KALSHI_MAIN_KEYFILE=keys/kalshi_main.pem

# ── Kalshi: sports_hft ───────────────────────────────────
KALSHI_SPORTS_HFT_KEYID=
KALSHI_SPORTS_HFT_KEYFILE=keys/kalshi_sports_hft.pem

# ── Kalshi: beni_hft ─────────────────────────────────────
KALSHI_BENI_HFT_KEYID=
KALSHI_BENI_HFT_KEYFILE=keys/kalshi_beni_hft.pem

# ── Polymarket: main ─────────────────────────────────────
POLYMARKET_MAIN_PRIVATE_KEY=
POLYMARKET_MAIN_API_KEY=
POLYMARKET_MAIN_SECRET=
POLYMARKET_MAIN_PASSPHRASE=
POLYMARKET_MAIN_FUNDER=
POLYMARKET_MAIN_SIG_TYPE=2
POLYMARKET_MAIN_RELAYER_API_KEY=

# ── Polymarket: sports_hft ───────────────────────────────
POLYMARKET_SPORTS_HFT_PRIVATE_KEY=
POLYMARKET_SPORTS_HFT_API_KEY=
POLYMARKET_SPORTS_HFT_SECRET=
POLYMARKET_SPORTS_HFT_PASSPHRASE=
POLYMARKET_SPORTS_HFT_FUNDER=
POLYMARKET_SPORTS_HFT_SIG_TYPE=2
POLYMARKET_SPORTS_HFT_RELAYER_API_KEY=

# ── Polymarket: copy_hft ─────────────────────────────────
POLYMARKET_COPY_HFT_PRIVATE_KEY=
POLYMARKET_COPY_HFT_API_KEY=
POLYMARKET_COPY_HFT_SECRET=
POLYMARKET_COPY_HFT_PASSPHRASE=
POLYMARKET_COPY_HFT_FUNDER=
POLYMARKET_COPY_HFT_SIG_TYPE=2
POLYMARKET_COPY_HFT_RELAYER_API_KEY=
"""
        with open(wallets_path, "w") as f:
            f.write(template)
        print(f"Created {wallets_path} (fill in your credentials)")
    else:
        print(f"{wallets_path} already exists")

    config_path = os.path.join(d, "wallet_config.json")
    if not os.path.isfile(config_path):
        _save_config({})
        print(f"Created {config_path}")
    else:
        print(f"{config_path} already exists")

    print(f"\nConfig directory: {d}")
    print(f"  1. Paste credentials into {wallets_path}")
    print(f"  2. Copy PEM files into {keys_dir}/")
    print(f"  3. Run 'hft-wallets select' to assign wallets to bots")


def cmd_list(_args: argparse.Namespace) -> None:
    env = _load_env()
    kalshi = _valid_kalshi(env)
    poly = _valid_polymarket(env)
    config = _load_config()

    print()
    print("╔══════════════════════════════════════╗")
    print("║        AVAILABLE WALLETS             ║")
    print("╚══════════════════════════════════════╝")
    if kalshi:
        print("  Kalshi:")
        for i, (name, hint) in enumerate(kalshi, 1):
            print(f"    {i}. {name}  ({hint})")
    if poly:
        print("  Polymarket:")
        for i, (name, hint) in enumerate(poly, 1):
            print(f"    {i}. {name}  ({hint})")
    print()
    print("╔══════════════════════════════════════╗")
    print("║        CURRENT ASSIGNMENTS           ║")
    print("╚══════════════════════════════════════╝")
    if not config:
        print("  (none -- run 'hft-wallets select' to assign)")
    for bot, assignment in config.items():
        parts = []
        if "kalshi" in assignment:
            parts.append(f"kalshi={assignment['kalshi']}")
        if "polymarket" in assignment:
            parts.append(f"polymarket={assignment['polymarket']}")
        print(f"  {bot}: {', '.join(parts)}")
    print()


def cmd_select(_args: argparse.Namespace) -> None:
    env = _load_env()
    kalshi = _valid_kalshi(env)
    poly = _valid_polymarket(env)
    config = _load_config()

    print()
    print("╔══════════════════════════════════════╗")
    print("║        AVAILABLE WALLETS             ║")
    print("╚══════════════════════════════════════╝")
    if kalshi:
        print("  Kalshi:")
        for i, (name, hint) in enumerate(kalshi, 1):
            print(f"    {i}. {name}  ({hint})")
    if poly:
        print("  Polymarket:")
        for i, (name, hint) in enumerate(poly, 1):
            print(f"    {i}. {name}  ({hint})")
    print()
    print("╔══════════════════════════════════════╗")
    print("║        CURRENT ASSIGNMENTS           ║")
    print("╚══════════════════════════════════════╝")
    if not config:
        print("  (none)")
    for bot, assignment in config.items():
        parts = []
        if "kalshi" in assignment:
            parts.append(f"kalshi={assignment['kalshi']}")
        if "polymarket" in assignment:
            parts.append(f"polymarket={assignment['polymarket']}")
        print(f"  {bot}: {', '.join(parts)}")

    # Edit existing bots
    for bot in list(config.keys()):
        assignment = config[bot]
        print(f"\n╔══ {bot.upper()} {'═' * (33 - len(bot))}╗")
        if "kalshi" in assignment:
            w = _prompt_wallet(kalshi, assignment.get("kalshi", ""), "Kalshi wallet")
            if w:
                assignment["kalshi"] = w
        if "polymarket" in assignment:
            w = _prompt_wallet(poly, assignment.get("polymarket", ""), "Polymarket wallet")
            if w:
                assignment["polymarket"] = w

    # Add new bots
    while True:
        print("\n  Add a new bot? (type name, or Enter to finish)")
        try:
            name = input("  Bot name: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not name:
            break
        if name in config:
            print(f"  '{name}' already exists (edit it above)")
            continue
        config[name] = {}
        print(f"\n╔══ {name.upper()} {'═' * (33 - len(name))}╗")

        print("  Does this bot need Kalshi? (y/n, default n)")
        try:
            if input("  ").strip().lower() in ("y", "yes"):
                w = _prompt_wallet(kalshi, "", "Kalshi wallet")
                if w:
                    config[name]["kalshi"] = w
        except (EOFError, KeyboardInterrupt):
            print()

        print("  Does this bot need Polymarket? (y/n, default n)")
        try:
            if input("  ").strip().lower() in ("y", "yes"):
                w = _prompt_wallet(poly, "", "Polymarket wallet")
                if w:
                    config[name]["polymarket"] = w
        except (EOFError, KeyboardInterrupt):
            print()

        if not config[name]:
            del config[name]
            print(f"  Skipped '{name}' (no wallets assigned)")

    _save_config(config)
    print(f"\nSaved {_config_path()}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="hft-wallets",
        description="Manage wallet assignments for HFT trading bots",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init", help="Create config directory with template files")
    sub.add_parser("list", help="Show available wallets and current assignments")
    sub.add_parser("select", help="Interactively assign wallets to bots")

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(1)

    {"init": cmd_init, "list": cmd_list, "select": cmd_select}[args.command](args)


if __name__ == "__main__":
    main()
