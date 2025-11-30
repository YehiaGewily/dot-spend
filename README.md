# dot-spend

A cross-platform CLI expense tracker for users who prefer managing their finances directly from the terminal.

## Overview

dot-spend is a minimalist, keyboard‑driven tool designed for speed, clarity, and compatibility. It runs seamlessly on Windows (PowerShell/CMD) and Linux systems, providing an efficient way to record, review, and export expenses without ever leaving the command line.

## Features

* **Zero Friction Entry:** Add expenses quickly through simple command flags.
* **Terminal Graphs:** View spending patterns using ASCII bar charts displayed directly in the console.
* **Delete by ID:** Remove entries easily by referencing their list ID.
* **Excel‑Ready Exports:** Output your data to CSV for analysis in Excel or Google Sheets.
* **Widget Integration:** Output formatted data for Polybar, Waybar, Rainmeter, or custom JSON‑based widgets.
* **Smart Storage:** Automatically follows XDG standards on Linux and uses AppData on Windows.

## Installation

dot-spend can be used either as a standalone application or run directly from source.

### Option A: Standalone Executable (Recommended)

This produces a single executable file that runs without requiring Python.

1. Clone the repository:

```
git clone https://github.com/yourusername/dot-spend.git
cd dot-spend
```

2. Install dependencies:

```
pip install -r requirements.txt
```

3. Build the executable using PyInstaller:

```
pyinstaller --onefile --name spend --hidden-import=jaraco.text main.py
```

4. Add the resulting binary to your system PATH.

**Windows:**

* Create a folder such as `C:\Tools`.
* Move `dist\spend.exe` into it.
* Add that folder to the System PATH.

**Linux:**

```
sudo mv dist/spend /usr/local/bin/spend
```

5. Verify installation:

```
spend list
```

### Option B: Run from Source

For development or modification:

1. Clone and install dependencies as shown above.
2. Execute commands using Python:

```
python main.py list
```

## Usage

### Command Overview

```
Usage: spend [OPTIONS] COMMAND [ARGS]...

Options:
  --help     Show this message and exit.

Commands:
  add        Add a new expense.
  delete     Delete an expense by its ID.
  export     Export data to CSV.
  graph      Visualize spending.
  list       Display recorded expenses.
  nuke       Remove all stored data.
  status     Show daily totals.
```

### 1. Add an Expense

```
spend add --amount 12.50 --category "Food" --note "Lunch"
```

Short format:

```
spend add -a 12.50 -c "Food" -n "Lunch"
```

### 2. View History

```
spend list
spend list --last 20
```

### 3. Visualize Data

```
spend graph
```

### 4. Delete an Entry

```
spend delete 2
```

### 5. Export to CSV

```
spend export
spend export C:\Users\You\Desktop\budget.csv
```

### 6. Desktop Widget Integration

```
spend status
spend status --style polybar
spend status --style json
```

## Data Storage

**Windows:** `C:\Users\You\AppData\Local\Personal\dot-spend\expenses.json`

**Linux:** `~/.local/share/dot-spend/expenses.json`

To reset all data:

```
spend nuke
```
