<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/python-3.10+-green?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-orange?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=for-the-badge" alt="Platform">
</p>

<h1 align="center">💸 dot-spend</h1>

<p align="center">
  <strong>A powerful, feature-rich CLI expense tracker for developers who live in the terminal</strong>
</p>

<p align="center">
  Track expenses • Visualize spending • Sync across devices • Import bank statements
</p>

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 📊 **Smart Tracking**

- Zero-friction expense entry
- Category budgets with alerts
- Recurring expense automation
- Multi-currency support

</td>
<td width="50%">

### 🎨 **Beautiful Visuals**

- Interactive TUI dashboard
- Terminal ASCII graphs
- Rich formatted tables
- Color-coded insights

</td>
</tr>
<tr>
<td width="50%">

### 🔄 **Seamless Sync**

- Git repository sync
- Google Drive integration
- Dropbox support
- Offline-first design

</td>
<td width="50%">

### 📥 **Easy Import**

- CSV bank statements
- Excel spreadsheets
- OFX financial files
- Auto-categorization

</td>
</tr>
</table>

---

## 🚀 Quick Start

```bash
# Clone and install
git clone https://github.com/YehiaGewily/dot-spend.git
cd dot-spend
pip install -r requirements.txt

# Add your first expense
python main.py add -a 25.00 -c "Food" -n "Lunch"

# View your expenses
python main.py list

# Launch interactive mode
python main.py tui
```

---

## 📖 Commands

| Command | Description |
|---------|-------------|
| `add` | Add new expense |
| `list` | View expenses with filters |
| `delete` | Remove expense by ID |
| `edit` | Modify existing expense |
| `graph` | Terminal visualizations |
| `budget` | Manage category budgets |
| `insights` | Spending analytics |
| `import` | Import bank statements |
| `export` | Export to CSV/Excel/PDF |
| `tui` | Interactive dashboard |
| `sync` | Cloud synchronization |
| `recurring` | Manage recurring expenses |
| `currency` | Multi-currency settings |

---

## 🎯 Usage Examples

```bash
# Add expenses
spend add -a 50 -c "Groceries" -n "Weekly shopping"
spend add -a 9.99 -c "Subscriptions" -n "Netflix" --currency EUR

# Set budgets
spend budget set Food 500
spend budget status

# Import bank statement
spend import statement.csv --interactive

# Get insights
spend insights --period month

# Sync to cloud
spend sync setup git
spend sync now
```

---

## 🗂️ Project Structure

```
dot-spend/
├── main.py          # CLI entry point
├── config.py        # Configuration management
├── datastore.py     # Data storage (JSON/SQLite)
├── insights.py      # Analytics engine
├── recurring.py     # Recurring expenses
├── currency.py      # Multi-currency support
├── sync/            # Cloud sync providers
├── importers/       # Bank statement importers
├── docs/            # Documentation
└── tests/           # Test suite
```

---

## 📦 Installation Options

### From Source

```bash
pip install -r requirements.txt
python main.py --help
```

### Build Executable

```bash
pyinstaller --onefile --name spend main.py
```

### Docker

```bash
docker build -t dot-spend .
docker run -v ~/.dot-spend:/data dot-spend list
```

---

## 🧪 Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v --cov

# Format code
black .

# Lint
flake8 .
```

---

## 📚 Documentation

- [User Guide](docs/user-guide.md) - Getting started
- [Advanced Features](docs/advanced.md) - Budgets, sync, import
- [Configuration](docs/configuration.md) - Settings reference
- [Changelog](CHANGELOG.md) - Version history

---

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and submit a PR.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/YehiaGewily">Yehia Gewily</a>
</p>
