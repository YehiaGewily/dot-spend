# Configuration Guide

## Config File Location

| OS | Path |
|----|------|
| Windows | `%LOCALAPPDATA%\Personal\dot-spend\settings.json` |
| Linux | `~/.local/share/dot-spend/settings.json` |

## Available Settings

### Storage Backend

```bash
spend config get storage_backend
spend config set storage_backend sqlite  # or json
```

### View All Settings

```bash
spend config get
```

## Settings Reference

| Setting | Values | Default | Description |
|---------|--------|---------|-------------|
| `storage_backend` | `json`, `sqlite` | `json` | Data storage format |

## Environment Variables

Currently, all configuration is file-based. Environment variable support planned for future releases.

## Custom Categories

Categories are created automatically when you add expenses. Common categories:

- Food
- Transport
- Entertainment
- Shopping
- Utilities
- Healthcare
- Groceries

## Data Files

| File | Purpose |
|------|---------|
| `expenses.json` | Expense data (JSON backend) |
| `expenses.db` | Expense data (SQLite backend) |
| `budgets.json` | Budget configurations |
| `history.json` | Undo/redo history |
| `settings.json` | App settings |
| `sync_config.json` | Sync configuration |
