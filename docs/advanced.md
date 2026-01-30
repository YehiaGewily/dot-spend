# Advanced Features

## Budget Management

### Setting Budgets

```bash
spend budget set Food 500
spend budget set Transport 200
```

### Checking Status

```bash
spend budget status
```

Shows remaining budget, usage percentage, and warnings.

## Data Analysis & Insights

```bash
spend insights                    # Full analysis
spend insights --period month     # Monthly trends
spend insights --category Food    # Category focus
```

**Includes:**

- Top spending categories
- Weekly/monthly trends
- Budget vs actual comparison
- Spending predictions

## Import System

### Supported Formats

- CSV (most banks)
- Excel (.xlsx)
- OFX (Open Financial Exchange)

### Basic Import

```bash
spend import statement.csv
```

### Preview Mode

```bash
spend import statement.csv --preview
```

### Interactive Review

```bash
spend import statement.csv --interactive
```

### Auto-Categorization

Built-in rules categorize common merchants (grocery stores, restaurants, etc.).

## Export Options

```bash
spend export                     # CSV to current dir
spend export --format excel      # Excel format
spend export --format pdf        # PDF report
spend export --output report.csv # Custom path
```

## Cloud Sync

### Git Sync

```bash
spend sync setup git
# Configure remote manually in data directory
spend sync enable
spend sync now
```

### Google Drive

```bash
spend sync setup google_drive
# Complete OAuth flow in browser
```

### Dropbox

```bash
spend sync setup dropbox --token YOUR_TOKEN
```

## Storage Backends

### Switch to SQLite

```bash
spend migrate to-sqlite
spend config set storage_backend sqlite
```

### Switch to JSON

```bash
spend migrate to-json
spend config set storage_backend json
```
