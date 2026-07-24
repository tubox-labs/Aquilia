# Aquilia 1.3.4 Migration Guide

Aquilia 1.3.4 is a minor release focused on bug fixes and performance. **There are no breaking changes.** All manifests and configurations from 1.3.3 will continue to work without modification.

However, several APIs have been improved, and we recommend migrating to the new patterns to future-proof your applications.

## Upgrading

Upgrade your environment using pip:

```bash
pip install aquilia==1.3.4
```

## Secret API Changes

The `Secret` class now enforces strict separation between literal values and environment variable lookups.

**1.3.3 Behavior:** 
`Secret("API_KEY")` ambiguously tried to look up the `API_KEY` environment variable because the string was all caps.

**1.3.4 Behavior:**
Positional arguments are strictly treated as literal values. If you want to pull a secret from the environment, you must use the `env` keyword argument.

**Migration Steps:**
If you see a `DeprecationWarning: ALL_CAPS positional argument treated as literal`, update your code:

```python
# Change this:
my_key = Secret("STRIPE_KEY")

# To this:
my_key = Secret(env="STRIPE_KEY")
```

## `imports` vs `depends_on`

The `depends_on` field in `AppManifest` is officially deprecated in favor of `imports`. 

**Migration Steps:**
Both fields will work identically in 1.3.4 due to internal bidirectional synchronization. However, you should update your manifests:

```python
# Change this:
manifest = AppManifest(name="app", depends_on=["other"])

# To this:
manifest = AppManifest(name="app", imports=["other"])
```
Use `aq validate --deprecated` to find all instances of `depends_on` in your codebase.

## AQUILIA_FAIL_FAST Environment Variable

By default, Aquilia catches startup exceptions to allow local development servers to boot and serve 500-error stubs. If you prefer your server to immediately crash and exit on a bad boot (highly recommended for CI/CD and Production), opt-in using the new environment variable.

**Migration Steps:**
No action is required to maintain 1.3.3 behavior. To enable fail-fast, add the following to your environment:

```bash
export AQUILIA_FAIL_FAST=1
```
