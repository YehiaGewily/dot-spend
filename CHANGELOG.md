# Changelog

All notable changes to dot-spend will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-01-30

### 🎉 Major Features

- **Interactive TUI**: Full-screen terminal dashboard with `spend tui`
- **Cloud Sync**: Sync data via Git, Google Drive, or Dropbox
- **Bank Import**: Import CSV, Excel, OFX statements
- **SQLite Backend**: Optional SQLite storage for larger datasets
- **Budget Management**: Set and track category budgets
- **Analytics & Insights**: Spending trends, predictions, anomaly detection

### ✨ Enhancements

- Enhanced date range filtering (`--from`, `--to`)
- Edit and undo functionality
- Improved category management
- Multi-format export (CSV, Excel, PDF)
- Better terminal visualizations

### 📚 Documentation

- Comprehensive user guide
- Advanced features documentation
- Configuration reference
- CI/CD pipeline with GitHub Actions

### 🧪 Testing

- Added pytest test suite
- Test coverage reporting
- Pre-commit hooks for code quality

## [1.0.0] - 2025-11-30

### Added

- Initial release
- Basic expense tracking (add, list, delete)
- Terminal graphs
- CSV export
- Widget integration (Polybar, Waybar, Rainmeter)
