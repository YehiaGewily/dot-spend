# dot-spend

A cross-platform, minimalist CLI expense tracker designed for users who enjoy customization. It follows XDG standards on Linux and stores data correctly in AppData on Windows.

## Features

* Fast startup time
* Cross-platform data storage (XDG paths on Linux, AppData on Windows)
* Clean, formatted terminal output using Rich
* Includes a `--style polybar` flag for integration with Linux status bars

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/dot-spend.git
cd dot-spend
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Add an expense:

```bash
python main.py add --amount 15.50 --category Food --note "Lunch"
```

List recent expenses:

```bash
python main.py list
```

Get status for widgets or bars:

```bash
python main.py status
```

## Building a Standalone Executable

To create a standalone file that runs without Python installed:

```bash
pyinstaller --onefile --name spend main.py
```

The executable will be generated inside the `dist/` folder.
