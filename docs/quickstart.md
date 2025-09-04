# 🚀 Similitude — Quick Start

Similitude scans a folder, indexes files into a SQLite DB, and reports duplicates.
It does **not** delete files.

## 📦 Install

```bash
python -m venv .venv && . .venv/Scripts/activate  # Windows (PowerShell)
pip install -U pip
pip install ".[dev,phash]"  # include image pHash extra
```

## 🔍 Minimal scan

```bash
similitude scan --path D:\photos --db D:\similitude.db
```

### Scan with progress every 100 files

```bash
similitude scan --path D:\data --db D:\sim.db --progress 100

```

### Quiet final line (useful in scripts)

```bash
similitude scan --path D:\data --db D:\sim.db --progress 250 --quiet
```





## 🖼️ Enable perceptual/fuzzy hashing
```bash
similitude scan --path D:\photos --db D:\similitude.db --enable phash,ssdeep
```

> On Windows, `ssdeep` is optional and may be unavailable; the scan still works.

## 📊 Report duplicates
```bash
# show exact duplicates (default)
similitude report --db D:\similitude.db --fmt json --out D:\reports\

# output will be D:\reports\duplicates.json
```

## 🙈 Typical ignore patterns

Create a `.similitudeignore` in your project root:
```
# folders
**/.git/**
**/node_modules/**
**/__pycache__/**

# temporary & logs
*.tmp
*.log
```

## 🛠️ Troubleshooting

- ⚠️ **Long paths on Windows** — use a short root (e.g., `D:\data`) to avoid MAX_PATH issues.
- 🔑 **Permissions** — run PowerShell/CMD as Administrator if some folders are unreadable.
- ⏱️ **Speed** — first run is the slowest. Re-runs only update changed files.

## 🛡️ Safety

MVP **never deletes** files. It only writes to the SQLite DB and produces reports.
