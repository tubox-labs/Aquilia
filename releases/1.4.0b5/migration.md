# Migration and Upgrade Guide — v1.4.0b4 → v1.4.0b5

## Upgrade

```bash
python -m pip install --upgrade --no-cache-dir "aquilia==1.4.0b5"
```

Use `--no-cache-dir` on Windows if an earlier beta wheel produced a DLL load error.

## Application Migration

No application API migration is required. Controller decorators, handler signatures, Contracts, workspace configuration, CLI commands, and runtime accelerator settings remain source-compatible.

## Before and After

### Windows installation

```text
Before: pip install succeeds; importing _dataengine can fail with a missing DLL.
After:  the published VS 2022 wheel imports on a clean supported Windows system.
```

### Compiler-free source installation

```text
Before: CMake fails at project(... LANGUAGES C CXX).
After:  pip installs the package with pure-Python fallbacks.
```

### Controller handlers

```python
# Both forms remain valid; no workaround is needed.
def health(self):
    return {"ok": True}

async def details(self):
    return await load_details()
```

### Invalid deferred Contract annotations

Invalid facet definitions now reliably raise `CastFault` on Python 3.14. Fix the constraint rather than suppressing the fault.

## CI/CD Migration

If your pipeline requires native artifacts, use:

```bash
CMAKE_ARGS="-DAQUILIA_ENGINE_OPTIONAL=OFF" python -m build
```

Then install the wheel into a clean environment and run the native assertions from outside the source directory.

If your pipeline verifies compiler-free compatibility, set invalid `CC`/`CXX` paths, install the sdist, and assert that the fallbacks load. Do not expect native flags in that job.

## Compatibility Considerations

- Python 3.10 through 3.14 are supported.
- Existing Python 3.10–3.13 applications require no code changes.
- Python 3.14 is newly included in classifiers, CI, and binary wheels.
- Runtime environment variables keep their previous precedence and meaning.
- Private access to `ControllerEngine._is_coro_cache` is unsupported and must be removed.

## Performance Considerations

- Users moving from a broken Windows wheel fallback to the corrected wheel regain native acceleration.
- Compiler-free installs are intentionally slower but behaviorally compatible.
- Sync/async dispatch adds one result awaitability check and removes an unsafe cache lookup.

## Upgrade Checklist

- [ ] Upgrade to v1.4.0b5 without using an older cached Windows wheel.
- [ ] Confirm `aquilia.__version__ == "1.4.0b5"`.
- [ ] If native performance is required, verify all three native flags.
- [ ] Run mixed sync/async controller tests.
- [ ] Run Contract tests under Python 3.14 if adopting it.
- [ ] Update strict packaging CI to pass a CMake definition.
- [ ] Review [Known Issues](README.md#known-issues).

## Related Pages

- [Native packaging](native_packaging.md)
- [Controller dispatch](controller_dispatch.md)
- [Contract safety](contract_safety.md)
- [CI release pipeline](ci_release_pipeline.md)
