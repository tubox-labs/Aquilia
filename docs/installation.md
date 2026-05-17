# Installation And Setup

## Requirements

Aquilia requires Python `>=3.10` according to `pyproject.toml`. The console script is `aq = aquilia.cli.__main__:main`.

## Core Install

```bash
pip install aquilia
```

Core dependencies from `pyproject.toml` are `click`, `uvicorn`, `jinja2`, `markupsafe`, `crousr`, and `crous-native`.

## Optional Extras

| Extra | Adds |
| --- | --- |
| `auth` | `cryptography`, `argon2-cffi` |
| `multipart` | `python-multipart` |
| `redis` | `redis[asyncio]` for cache/socket backends |
| `mail` | `aiosmtplib` |
| `mail-ses` | `aiobotocore` |
| `mail-sendgrid` | `httpx` |
| `server` | `gunicorn`, `uvicorn[standard]` |
| `mlops` | `numpy` |
| `mlops-onnx` | `onnxruntime`, `onnx` |
| `mlops-torch` | `torch` |
| `mlops-s3` | `boto3` |
| `mlops-bento` | `bentoml` |
| `mlops-explain` | `shap`, `lime` |
| `testing` | `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx` |
| `dev` | `aquilia[testing]`, `ruff`, `mypy`, `pre-commit` |

`templates`, `db`, and `files` are compatibility aliases in `pyproject.toml`; Jinja2 is core, database support is native, and native filesystem support lives in `aquilia.filesystem`.

## First Workspace

```bash
aq init workspace my-api
cd my-api
cp .env.example .env
pip install -r requirements.txt
aq add module users
aq validate
aq run
```

Operational `aq` commands require `workspace.py` in the current directory except for `init`, `version`, help, and `doctor`.

## Runtime Entrypoints

Development uses `aq run` or `AquiliaServer.run()`. Production containers can use:

```bash
uvicorn aquilia.entrypoint:app --host 0.0.0.0 --port 8000
```

Set `AQUILIA_WORKSPACE` to the workspace root and `AQUILIA_ENV` to `dev`, `test`, or `prod`.
