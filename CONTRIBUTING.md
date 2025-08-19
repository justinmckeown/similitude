# Contributing to Similitude

Thank you for considering contributing to **Similitude**! 🚀  
This project is an experiment in file intelligence and duplicate detection with similarity awareness.

---

## 📦 Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/justinmckeown/similitude.git
   cd similitude
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux / macOS
   .venv\Scripts\activate    # Windows PowerShell
   ```

3. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Run tests**
   ```bash
   pytest -vv
   ```

---

## 🧹 Code Style

We use:
- **Black** for formatting  
- **Ruff** for linting  
- **Mypy** for type checking  

Run checks before committing:
```bash
black src tests
ruff check src tests
mypy src
```

---

## 🧪 Testing

- Tests live in the `tests/` folder, structured into **unit** and **integration**.
- Use `pytest -s -vv` for detailed test output.
- To run a specific test:
  ```bash
  pytest -s -vv tests/integration/test_scan_and_report.py::test_scan_and_report_duplicates
  ```

---

## 📝 Git Commit Guidelines

- Use clear, descriptive commit messages.
- Prefix optional keywords like:
  - `feat:` new feature
  - `fix:` bug fix
  - `docs:` documentation changes
  - `test:` test-related changes
  - `refactor:` code restructuring without behavior change

Example:
```
feat(scan): add logging for processed file count
```

---

## 🤝 Pull Requests

- Fork the repo and create your feature branch:
  ```bash
  git checkout -b feat/amazing-feature
  ```
- Commit changes and push to your fork.
- Open a PR with a clear description of your changes.

---

## 💡 Suggestions

Issues, questions, and ideas are welcome!  
Please use [GitHub Issues](https://github.com/justinmckeown/similitude/issues) to start a discussion.

---

Thanks for helping improve **Similitude**!
