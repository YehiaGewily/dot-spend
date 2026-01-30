# User Guide

## Installation

```bash
git clone https://github.com/YehiaGewily/dot-spend.git
cd dot-spend
pip install -r requirements.txt
```

## First-Time Setup

Run any command to initialize storage:

```bash
spend list
```

## Basic Commands

### Adding Expenses

```bash
spend add -a 25.00 -c "Groceries" -n "Weekly shopping"
spend add --amount 10 --category "Transport"
```

### Viewing Expenses

```bash
spend list                    # All expenses
spend list --last 10          # Last 10
spend list --category Food    # Filter by category
spend list --from 2024-01-01  # Date range
```

### Deleting & Editing

```bash
spend delete abc123           # Delete by ID
spend edit abc123 --amount 30 # Edit amount
```

## Interactive Mode (TUI)

```bash
spend tui
```

**Keyboard Shortcuts:**

- `D` - Dashboard
- `A` - Add expense
- `L` - List view
- `Q` - Quit

## Command Reference

| Command | Options | Description |
|---------|---------|-------------|
| `add` | `-a`, `-c`, `-n`, `--date` | Add expense |
| `list` | `--last`, `--category`, `--from`, `--to` | View expenses |
| `delete` | `ID` | Remove expense |
| `edit` | `ID`, `--amount`, `--category`, `--note` | Modify expense |
| `budget set` | `CATEGORY`, `AMOUNT` | Set budget |
| `budget status` | - | View budget status |
| `insights` | `--period`, `--category` | Analytics |
| `import` | `FILE`, `--preview`, `--interactive` | Import statements |
| `export` | `--format`, `--output` | Export data |
| `sync setup` | `PROVIDER` | Configure sync |
| `sync now` | - | Manual sync |

## Troubleshooting

**"Command not found"**: Add Python/dist folder to PATH.

**"Permission denied"**: Run terminal as administrator (Windows) or use sudo (Linux).

**Data not showing**: Check storage backend with `spend config get storage_backend`.
