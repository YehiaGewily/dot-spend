# dot-spend

A powerful, cross-platform CLI expense tracker for users who prefer managing finances from the terminal.

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Zero Friction Entry** | Add expenses quickly via simple command flags |
| **Interactive TUI** | Full-screen terminal dashboard with `spend tui` |
| **Budget Tracking** | Set and monitor category budgets |
| **Analytics & Insights** | Spending trends, top categories, predictions |
| **Bank Import** | Import CSV, Excel, OFX statements |
| **Cloud Sync** | Sync via Git, Google Drive, or Dropbox |
| **Multiple Backends** | JSON (default) or SQLite storage |
| **Terminal Graphs** | ASCII visualizations in console |
| **Export Options** | CSV, Excel, PDF reports |

## 🚀 Quick Start

```bash
# Install
pip install -r requirements.txt

# Add an expense
spend add -a 12.50 -c "Food" -n "Lunch"

# View history
spend list

# Launch interactive mode
spend tui

# Set a budget
spend budget set Food 500

# Import bank statement
spend import statement.csv
```

## 📦 Installation

### From Source

```bash
git clone https://github.com/YehiaGewily/dot-spend.git
cd dot-spend
pip install -r requirements.txt
python main.py --help
```

### Build Executable

```bash
pyinstaller --onefile --name spend main.py
# Add dist/spend to PATH
```

## 📖 Documentation

- [User Guide](docs/user-guide.md) - Getting started, commands
- [Advanced Features](docs/advanced.md) - Budgets, insights, sync
- [Configuration](docs/configuration.md) - Settings, customization

## 🔧 Commands

| Command | Description |
|---------|-------------|
| `add` | Add new expense |
| `list` | View expenses |
| `delete` | Remove expense by ID |
| `edit` | Modify existing expense |
| `budget` | Manage category budgets |
| `insights` | Spending analytics |
| `import` | Import bank statements |
| `export` | Export to CSV/Excel/PDF |
| `tui` | Interactive dashboard |
| `sync` | Cloud synchronization |
| `graph` | Terminal visualizations |

## 📊 Data Storage

| OS | Location |
|----|----------|
| Windows | `%LOCALAPPDATA%\Personal\dot-spend\` |
| Linux | `~/.local/share/dot-spend/` |

## 🧪 Testing

```bash
pip install -r requirements-dev.txt
pytest tests/ --cov=. --cov-report=term
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
