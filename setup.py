#!/usr/bin/env python3
"""
Setup script for Aquilia framework.

NOTE: This file exists for backwards compatibility with older tooling.
All canonical configuration lives in ``pyproject.toml``.
"""

from setuptools import setup, find_packages
from pathlib import Path

# ---------------------------------------------------------------------------
# Version — single source of truth is aquilia/_version.py
# ---------------------------------------------------------------------------
_version: dict = {}
exec(Path("aquilia/_version.py").read_text(encoding="utf-8"), _version)
_FRAMEWORK_VERSION: str = _version["__version__"]

# ---------------------------------------------------------------------------
# Long description from README
# ---------------------------------------------------------------------------
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# ---------------------------------------------------------------------------
# Core dependencies — mirrors [project.dependencies] in pyproject.toml
# ---------------------------------------------------------------------------
CORE_DEPS = [
    "click>=8.1.0",
    "PyYAML>=6.0.0",
    "uvicorn>=0.30.0",
    # Template engine — used by admin panel and user templates (always loaded)
    "jinja2>=3.1.0",
    "markupsafe>=2.1.0",
    # Async SQLite — default database backend
    "aiosqlite>=0.20.0",
    # Crous compiler — used for manifest compilation and runtime evaluation
    "crousr",
    "crous-native",
]

# ---------------------------------------------------------------------------
# Optional dependency groups — mirrors [project.optional-dependencies]
# ---------------------------------------------------------------------------
EXTRAS = {
    # -- Framework extras --
    # NOTE: jinja2/markupsafe and aiosqlite are now core dependencies.
    # Keep these keys as empty lists so existing installs that request
    # aquilia[templates] or aquilia[db] don't get a "no such extra" error.
    "templates": [],
    "db": [],
    "auth": ["cryptography>=42.0.0", "argon2-cffi>=23.1.0"],
    "files": ["aiofiles>=23.0.0"],
    "multipart": ["python-multipart>=0.0.9"],
    "redis": ["redis[asyncio]>=5.0.0"],
    "mail": ["aiosmtplib>=3.0.0"],
    "mail-ses": ["aiobotocore>=2.9.0"],
    "mail-sendgrid": ["httpx>=0.27.0"],
    "server": ["gunicorn>=22.0.0", "uvicorn[standard]>=0.30.0"],
    # -- MLOps extras --
    "mlops": ["numpy>=1.24.0"],
    "mlops-onnx": ["onnxruntime>=1.16.0", "onnx>=1.14.0"],
    "mlops-torch": ["torch>=2.0.0"],
    "mlops-s3": ["boto3>=1.28.0"],
    "mlops-bento": ["bentoml>=1.2.0"],
    "mlops-explain": ["shap>=0.42.0", "lime>=1.0.0"],
    # -- Testing & development --
    "testing": [
        "pytest>=8.0.0",
        "pytest-asyncio>=0.23.0",
        "pytest-cov>=4.1.0",
        "httpx>=0.27.0",
    ],
    "dev": [
        "pytest>=8.0.0",
        "pytest-asyncio>=0.23.0",
        "pytest-cov>=4.1.0",
        "httpx>=0.27.0",
        "ruff>=0.4.0",
        "mypy>=1.10.0",
        "pre-commit>=3.7.0",
    ],
}

# Build compound groups
EXTRAS["mlops-all"] = (
    EXTRAS["mlops"]
    + EXTRAS["mlops-onnx"]
    + EXTRAS["mlops-torch"]
    + EXTRAS["mlops-s3"]
    + EXTRAS["mlops-bento"]
    + EXTRAS["mlops-explain"]
)
EXTRAS["full"] = (
    EXTRAS["auth"]
    + EXTRAS["files"]
    + EXTRAS["multipart"]
    + EXTRAS["redis"]
    + EXTRAS["mail"]
    + EXTRAS["mail-ses"]
    + EXTRAS["mail-sendgrid"]
    + EXTRAS["server"]
)
EXTRAS["all"] = EXTRAS["full"] + EXTRAS["mlops-all"]

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
setup(
    name="aquilia",
    version=_FRAMEWORK_VERSION,
    description="Async-native Python web framework with flow-first routing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Pawan Kumar",
    author_email="aegis.invincible@gmail.com",
    url="https://github.com/axiomchronicles/Aquilia",
    packages=find_packages(
        where=".",
        include=["aquilia", "aquilia.*"],
        exclude=["tests", "tests.*", "benchmark", "benchmark.*", "docs", "myapp", "myapp.*"],
    ),
    include_package_data=True,
    package_data={
        "aquilia": ["py.typed"],
        "aquilia.admin": ["templates/**/*.html"],
        "aquilia.mlops.deploy": ["grafana/*.json", "k8s/*.yaml"],
        "aquilia.patterns": ["README.md"],
        "aquilia.templates": ["README.md"],
    },
    python_requires=">=3.10",
    install_requires=CORE_DEPS,
    extras_require=EXTRAS,
    entry_points={
        "console_scripts": [
            "aq=aquilia.cli.__main__:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Framework :: AsyncIO",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Typing :: Typed",
    ],
    keywords="web framework async asgi http api routing middleware dependency-injection",
    project_urls={
        "Homepage": "https://github.com/axiomchronicles/Aquilia",
        "Documentation": "https://github.com/axiomchronicles/Aquilia#readme",
        "Repository": "https://github.com/axiomchronicles/Aquilia",
        "Issues": "https://github.com/axiomchronicles/Aquilia/issues",
        "Changelog": "https://github.com/axiomchronicles/Aquilia/blob/main/CHANGELOG.md",
    },
    license="MIT",
    zip_safe=False,
)
