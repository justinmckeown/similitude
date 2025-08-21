# 🌀 Similitude

[![CI](https://github.com/justinmckeown/similitude/actions/workflows/ci.yml/badge.svg)](https://github.com/justinmckeown/similitude/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
![Types: mypy](https://img.shields.io/badge/types-mypy-informational)
[![License](https://img.shields.io/badge/license-Apache--2.0-green)](LICENSE)

**Similitude** is a Python tool for 📂 file intelligence and 🔍 duplicate detection with similarity awareness. The devleopment goal is to provide Intelligence for managing data you no longer control.

---

## ✨ Features

- 🚀 Fast file system scanning  
- 🧩 Duplicate detection using strong hashes (SHA256)  
- 🔎 Pluggable architecture (filesystem, index, hashers)  
- 💾 SQLite-backed metadata store  
- 📊 JSON reports of duplicate clusters  

---

## 📦 Installation

```bash
git clone https://github.com/justinmckeown/similitude.git
cd similitude
pip install -e .
```

For development (with linting & tests):

```bash
pip install -e ".[dev]"
```

---

## 🛠️ Usage

Run the CLI:

```bash
similitude scan /path/to/dir

# writes to ./duplicates.json by default
similitude report --fmt json

# write to a directory (auto-named file)
similitude report --fmt json --out .

# or specify a full file path
similitude report --fmt json --out .\reports\my-duplicates.json

```

Example:  

```bash
similitude scan ~/Documents
similitude report --fmt json --out duplicates.json
```

---

## 🧪 Running Tests

```bash
pytest -vv
```

---

## 📂 Project Structure

```
similitude/
│
├── src/similitude/          # Core source code
│   ├── adapters/            # Adapters for DB and FS
│   ├── services/            # Application services
│   ├── ports/               # Hexagonal architecture ports
│   └── cli/                 # Typer CLI
│
├── tests/                   # Unit and integration tests
├── pyproject.toml           # Build system + dependencies
├── CONTRIBUTING.md          # Contribution guidelines
└── README.md                # This file
```

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!  
Feel free to check the [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 📜 License

This project is licensed under the **Apache 2.0 License**.  
See the [LICENSE](LICENSE) file for details.

---

### 🙌 Acknowledgements
Inspired by classic duplicate finders, rebuilt with modern Python tooling and privacy engineering goals.  