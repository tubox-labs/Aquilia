# aq analytics

Run discovery analytics and generate a health report for your workspace. Analyzes module relationships, health metrics, and provides optimization recommendations.

## Usage

```bash
aq analytics [OPTIONS]
```

## Options

| Option   | Description       | Default |
| -------- | ----------------- | ------- |
| `--path` | Workspace path    | `.`     |

## Report Sections

### Summary

```
Summary
Total Modules: 5
With Services: 3
With Controllers: 5
With Middleware: 0
With Dependencies: 2
```

### Health Metrics

```
Health Metrics
Health Score: 85.0/100
Validation Errors: 0
Validation Warnings: 2
```

The health score (0-100) is calculated from:

- **Deductions**: -10 per validation error, -5 per validation warning
- **Bonuses**: up to +20 for modules with metadata (author, tags, non-default version), +10 for modules with documented dependencies

### Dependencies

```
Dependencies
Max Depth: 3
Cyclic Dependencies: None
```

Dependency analysis includes:

- Dependency graph depth calculation
- Cyclic dependency detection
- Load order resolution

### Recommendations

```
Recommendations
  1. Module 'users': Add author field to manifest
  2. Module 'products': Add tags for better discoverability
  3. Module 'admin': Consider versioning (current: 0.1.0)
  4. Resolve 2 dependency errors
```

Recommendations cover:

- Missing metadata (author, tags)
- Version maturity (alpha/beta/stable/production)
- Dependency issues
- Modularity suggestions
- Route prefix conflicts

## Module Analysis

Per-module analysis includes:

| Metric           | Description                                           |
| ---------------- | ----------------------------------------------------- |
| **Version**      | Current version string                                |
| **Maturity**     | Assessed from version: alpha, beta, stable, production|
| **Components**   | services, controllers, middleware                     |
| **Complexity**   | simple, moderate, or complex                          |
| **Dependencies** | Count of declared dependencies                        |
| **Metadata**     | Presence of author, tags                              |

## Caching

Analysis results are cached in `build/.cache/analysis.surp` (or `.json` fallback) for up to 1 hour. Subsequent runs within the cache window return cached results.

## Examples

```bash
# Run analytics on current workspace
aq analytics

# Run on a specific workspace
aq analytics --path=/path/to/workspace
```

## See Also

- [`aq discover`](discover.md) — Auto-discover components
- [`aq doctor`](index.md) — Comprehensive workspace diagnostics