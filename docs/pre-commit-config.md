# pre-commit-config
This is a quick guide on how to set up the `pre-commit-config.yaml` file located in the root dir. This file is used to automate some tests prior to installing making commits to git.

## One-time setup.
From within your virtual environment run do the following:

```bash
pip install pre-commit
pre-commit install
pre-commit install --hook-type pre-push
# optional: run on all files once
pre-commit run -a
```

## Day to day worflow
when working on project, do the following:

* `Commit`: pre-commit will auto-format & lint. If something fails, fix or let Black reformat and re-commit.
* `Push`: pre-commit runs mypy + pytest before the push goes out. If a test fails, the push is blocked (good!).

## SKipping (rarely needed)
Youy can bypass hooks with --no-verify. But try to avoid doing this:

```bash
git commit -m "hotfix" --no-verify
git push --no-verify

```

## Keep CI aligned
CI runs Ruff/Black/Mypy/Pytest too, so it mirrors local hoooks.
