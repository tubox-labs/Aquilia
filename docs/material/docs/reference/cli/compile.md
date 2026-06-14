# aq compile

Compile workspace and module manifests into the native artifact store. Uses the Aquilia workspace compiler to generate `.surp` binary artifact files.

## Usage

```bash
aq compile [OPTIONS]
```

## Options

| Option     | Description                         | Default       |
| ---------- | ----------------------------------- | ------------- |
| `--watch`  | Watch for changes and recompile     | `False`       |
| `--output` | Output directory for artifacts      | `artifacts/`  |

## Process

The `WorkspaceCompiler` reads `workspace.py`, discovers all registered modules, parses each module's `manifest.py`, and compiles the following into `.surp` artifacts:

- Route definitions
- DI/service graph
- Module metadata
- Fault domain registrations
- Middleware declarations

## Output

Compiled artifacts are placed in the output directory (default: `artifacts/`):

```
artifacts/
├── routes.surp
├── di_graph.surp
├── modules.surp
├── faults.surp
├── middleware.surp
├── manifest.surp
└── ...
```

## Watch Mode

```bash
aq compile --watch
```

In watch mode, the compiler monitors `workspace.py` and all module `manifest.py` files for changes and recompiles automatically. Useful during development to keep artifacts synchronized with manifest declarations.

!!! note "Watch Mode Dependencies"
    Watch mode requires the `watchfiles` package: `pip install watchfiles`

## Examples

```bash
# Compile to default artifacts/ directory
aq compile

# Compile to custom directory
aq compile --output=dist/

# Watch for changes and recompile
aq compile --watch

# Compile with verbose output
aq compile -v --output=build/
```

## Exit Codes

| Code | Meaning              |
| ---- | -------------------- |
| `0`  | Compilation success  |
| `1`  | Compilation failed   |

## See Also

- [`aq freeze`](freeze.md) — Freeze compiled artifacts for production
- [`aq validate`](validate.md) — Validate manifests before compiling
- [`aq artifacts`](artifacts.md) — Artifact management commands