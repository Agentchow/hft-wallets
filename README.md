# hft-wallets

Shared wallet configuration for HFT trading bots. Manages Kalshi and Polymarket wallet credentials and bot-to-wallet assignments from a single location (`~/.hft-wallets/`).

## Install

```bash
pip3 install git+https://github.com/Agentchow/hft-wallets.git
```

If `hft-wallets` is not found after installing, add the Python scripts directory to your PATH (one-time setup):

```bash
# macOS
echo 'export PATH="$PATH:$HOME/Library/Python/3.9/bin"' >> ~/.zshrc && source ~/.zshrc

# Linux
echo 'export PATH="$PATH:$HOME/.local/bin"' >> ~/.bashrc && source ~/.bashrc
```

## First-time setup

```bash
hft-wallets init
```

This creates `~/.hft-wallets/` with:
- `wallets.env` -- template for wallet credentials (fill in your keys)
- `keys/` -- directory for Kalshi PEM files
- `wallet_config.json` -- bot-to-wallet assignments (initially empty)

After filling in credentials and copying PEM files:

```bash
hft-wallets select
```

Interactively assign wallets to your bots.

## CLI commands

| Command | Description |
|---------|-------------|
| `hft-wallets init` | Create config directory with templates |
| `hft-wallets select` | Interactively assign wallets to bots |
| `hft-wallets list` | Show available wallets and current assignments |

## Python usage

```python
from hft_wallets import load_wallets, load_wallet_for_bot

load_wallets()  # loads ~/.hft-wallets/wallets.env into os.environ

creds = load_wallet_for_bot("ladder")
# creds = {
#     "kalshi": {
#         "key_id": "30e802f6-...",
#         "keyfile": "/Users/you/.hft-wallets/keys/kalshi_main.pem",
#     }
# }
```

## Go usage

The Go project reads from the same config directory. Set `HFT_WALLETS_DIR` or
default to `~/.hft-wallets/`:

```go
walletsDir := os.Getenv("HFT_WALLETS_DIR")
if walletsDir == "" {
    home, _ := os.UserHomeDir()
    walletsDir = filepath.Join(home, ".hft-wallets")
}
godotenv.Load(".env", filepath.Join(walletsDir, "wallets.env"))
```

## Custom config directory

Set `HFT_WALLETS_DIR` to override the default location:

```bash
export HFT_WALLETS_DIR=/opt/hft-wallets
```
