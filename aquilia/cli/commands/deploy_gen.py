"""
Deploy CLI commands -- ``aq deploy`` group.

**Build-first deployment**: Like React/Vite/Next.js, Aquilia requires a
production build (``aq build --mode=prod``) before deploying.  The deploy
system reads the compiled build manifest (``build/manifest.json``) to
generate deployment files — this ensures deploy artifacts are consistent
with what was built.

If no production build is found when you run ``aq deploy``, the wizard
offers to build automatically.  If the build is stale (source files changed
since the last build), it warns and offers to rebuild.

Production-ready deployment file generators **and executor** for Aquilia
workspaces.  Each sub-command generates a specific deployment artefact:

    aq deploy                -- Interactive wizard (build gate + generate + execute)
    aq deploy dockerfile     -- Dockerfile (production / dev / mlops)
    aq deploy compose        -- docker-compose.yml
    aq deploy kubernetes     -- Full Kubernetes manifest suite
    aq deploy nginx          -- Nginx reverse-proxy configuration
    aq deploy ci             -- CI/CD pipeline (GitHub Actions / GitLab CI)
    aq deploy monitoring     -- Prometheus + Grafana provisioning
    aq deploy env            -- .env.example template
    aq deploy makefile       -- Makefile with dev/build/deploy targets
    aq deploy all            -- Generate everything at once

Running ``aq deploy`` with **no** sub-command launches an interactive
wizard (like ``aq init``) that lets you pick which artefacts to generate,
configure options, and optionally **execute** the deployment (docker build,
docker compose up, kubectl apply, monitoring stack, etc.).

All generators consume the build manifest (preferred) or introspect the
workspace directly (with ``--skip-build-check``) to detect enabled
components and tailor the output accordingly.

Flags:
    --force              Overwrite existing files (default: skip existing)
    --dry-run            Preview what would be generated without writing
    --skip-build-check   Bypass the build requirement (use live introspection)
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, List

import click

from ..utils.colors import (
    success, error, info, warning, dim, bold,
    section, kv, rule, panel, next_steps, table,
    file_written, file_skipped, file_dry,
    banner, _CHECK, _CROSS, _ARROW,
)
from ..utils.prompts import (
    flow_header, flow_done, ask, select, multi_select, confirm, recap,
)


# ═══════════════════════════════════════════════════════════════════════════
# Build-first deploy gate
# ═══════════════════════════════════════════════════════════════════════════
#
# Just like React/Vite/Next.js require `npm run build` before deploying,
# Aquilia requires `aq build --mode=prod` before `aq deploy`.  The deploy
# system reads the compiled build manifest to generate deployment files —
# this ensures the deploy artifacts are consistent with what was built.
#
# Flow:
#   1. Check if build/manifest.json + build/bundle.crous exist
#   2. If missing → prompt user to build (or auto-build with -y)
#   3. If stale (source files newer than build) → warn and offer rebuild
#   4. Load BuildManifest → to_deploy_context()
#   5. Generators receive exact, verified workspace metadata
# ═══════════════════════════════════════════════════════════════════════════


def _has_production_build(workspace_root: Path) -> bool:
    """Return True if a valid production build exists."""
    build_dir = workspace_root / "build"
    return (
        (build_dir / "manifest.json").exists()
        and (build_dir / "bundle.crous").exists()
    )


def _is_build_stale(workspace_root: Path) -> bool:
    """Return True if source files are newer than the last build.

    Compares the mtime of ``build/manifest.json`` against all
    ``workspace.py``, ``modules/*/manifest.py``, and ``modules/**/*.py``
    files.  If any source file is newer, the build is stale.
    """
    manifest_path = workspace_root / "build" / "manifest.json"
    if not manifest_path.exists():
        return True

    build_mtime = manifest_path.stat().st_mtime

    # Check workspace.py
    ws_file = workspace_root / "workspace.py"
    if ws_file.exists() and ws_file.stat().st_mtime > build_mtime:
        return True

    # Check all module source files
    modules_dir = workspace_root / "modules"
    if modules_dir.exists():
        for py_file in modules_dir.rglob("*.py"):
            if py_file.stat().st_mtime > build_mtime:
                return True

    # Check config files
    config_dir = workspace_root / "config"
    if config_dir.exists():
        for cfg_file in config_dir.rglob("*"):
            if cfg_file.is_file() and cfg_file.stat().st_mtime > build_mtime:
                return True

    return False


def _auto_build(workspace_root: Path) -> bool:
    """Run ``aq build --mode=prod`` and return True on success."""
    from aquilia.build import AquiliaBuildPipeline

    click.echo()
    banner("Build", subtitle="Building for production before deploy")
    click.echo()

    result = AquiliaBuildPipeline.build(
        workspace_root=str(workspace_root),
        mode="prod",
        verbose=False,
    )

    if result.success:
        success(f"  {_CHECK} Production build complete")
        if result.fingerprint:
            kv("  Fingerprint", result.fingerprint[:16] + "...")
        click.echo()
        return True
    else:
        error(f"  {_CROSS} Build failed with {len(result.errors)} error(s):")
        for err in result.errors[:10]:
            error(f"    {err}")
        if len(result.errors) > 10:
            dim(f"    ... and {len(result.errors) - 10} more")
        click.echo()
        return False


def _ensure_production_build(
    workspace_root: Path,
    *,
    interactive: bool = True,
    skip_build_check: bool = False,
) -> bool:
    """Ensure a production build exists before deploying.

    Like ``npm run build`` in React/Vite/Next.js, Aquilia requires
    a production build before deployment files can be generated.
    This function checks for build artifacts and offers to build
    automatically if they're missing or stale.

    Args:
        workspace_root: Path to the Aquilia workspace root.
        interactive: If True, prompt the user. If False (``-y``), auto-build.
        skip_build_check: If True, bypass the build check entirely.

    Returns:
        True if a valid build exists (or was just created).
        False if the user declined to build or the build failed.
    """
    if skip_build_check:
        return True

    has_build = _has_production_build(workspace_root)
    is_stale = has_build and _is_build_stale(workspace_root)

    if has_build and not is_stale:
        # Build exists and is fresh — proceed
        return True

    # ── No build or stale build ──────────────────────────────────
    click.echo()
    if not has_build:
        panel(
            "No production build found",
            body=(
                "Aquilia requires a production build before deploying.\n"
                "Run `aq build --mode=prod` to compile your workspace,\n"
                "or let the deploy wizard build it for you now.\n\n"
                "  build/manifest.json  → workspace metadata for generators\n"
                "  build/bundle.crous   → compiled binary artifacts"
            ),
        )
    else:
        panel(
            "Stale production build detected",
            body=(
                "Source files have been modified since the last build.\n"
                "Deployment files may not reflect the latest changes.\n\n"
                "Rebuild to ensure deploy artifacts match your code."
            ),
        )

    if interactive:
        label = "Build now?" if not has_build else "Rebuild now?"
        should_build = confirm(label, default=True)
        if not should_build:
            if not has_build:
                error(f"  {_CROSS} Cannot deploy without a production build.")
                info(f"  Run: aq build --mode=prod")
                return False
            else:
                warning("  Continuing with stale build -- deploy files may be outdated.")
                return True
    else:
        # Non-interactive: auto-build
        info("  Auto-building for production...")

    # Execute the build
    if not _auto_build(workspace_root):
        error(f"  {_CROSS} Build failed. Fix errors above, then retry: aq deploy")
        return False

    return True


def _get_ctx(workspace_root: Path, *, skip_build_check: bool = False) -> dict:
    """Introspect the workspace and return a context dict.

    **Build-first**: Prefers ``build/manifest.json`` (the build → deploy
    contract).  Falls back to ``WorkspaceIntrospector`` only when
    ``--skip-build-check`` is set or no workspace.py exists.
    """
    build_dir = workspace_root / "build"
    try:
        from aquilia.build.pipeline import BuildManifest
        manifest = BuildManifest.load(build_dir)
        return manifest.to_deploy_context(workspace_root)
    except (FileNotFoundError, ValueError, Exception):
        pass

    from ..generators.deployment import WorkspaceIntrospector
    return WorkspaceIntrospector(workspace_root).introspect()


def _subcommand_build_gate(ctx: click.Context, workspace_root: Path) -> None:
    """Build gate for individual subcommands (not the interactive wizard).

    Checks if a production build exists; if not, prompts or auto-builds
    before the subcommand introspects the workspace.  This is the same
    gate used by the interactive wizard, applied to each subcommand.
    """
    skip = ctx.obj.get("skip_build_check", False)
    interactive = sys.stdin.isatty()

    if not _ensure_production_build(
        workspace_root,
        interactive=interactive,
        skip_build_check=skip,
    ):
        sys.exit(1)


def _write_file(
    path: Path,
    content: str,
    *,
    label: str,
    verbose: bool,
    force: bool = False,
    dry_run: bool = False,
) -> bool:
    """Write content to a file, creating parent directories.

    Returns True if the file was written, False if skipped.
    """
    if path.exists() and not force:
        file_skipped(label, reason="exists, use --force")
        return False

    if dry_run:
        file_dry(label)
        return True

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    file_written(label, verbose=verbose, path=str(path))
    return True


def deploy_options(f):
    """Decorator to add shared --force and --dry-run options to subcommands."""
    import functools
    @click.option("--force", "-f", is_flag=True, help="Overwrite existing files")
    @click.option("--dry-run", is_flag=True, help="Preview without writing files")
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    return wrapper


# ═══════════════════════════════════════════════════════════════════════════
# Execution helpers -- run containers, compose, k8s, monitoring
# ═══════════════════════════════════════════════════════════════════════════

def _has_command(name: str) -> bool:
    """Check whether a CLI tool is available on PATH."""
    return shutil.which(name) is not None


def _run(cmd: List[str], *, label: str, cwd: Path, dry_run: bool = False) -> bool:
    """Run a shell command with styled output.

    Returns True on success, False on failure.
    """
    display = " ".join(cmd)
    if dry_run:
        dim(f"  [dry-run] {display}")
        return True

    info(f"  $ {display}")
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=False,
            text=True,
        )
        if result.returncode == 0:
            success(f"  {_CHECK} {label}")
            return True
        else:
            error(f"  {_CROSS} {label} failed (exit {result.returncode})")
            return False
    except FileNotFoundError:
        error(f"  {_CROSS} Command not found: {cmd[0]}")
        return False
    except Exception as e:
        error(f"  {_CROSS} {label} error: {e}")
        return False


def _exec_docker_build(workspace_root: Path, wctx: dict, *, dry_run: bool = False) -> bool:
    """Build the Docker image."""
    name = wctx["name"]
    tag = f"{name}:latest"
    dockerfile = workspace_root / "Dockerfile"
    if not dockerfile.exists() and not dry_run:
        warning(f"  Dockerfile not found -- skipping build")
        return False
    return _run(
        ["docker", "build", "-t", tag, "."],
        label=f"Docker image built: {tag}",
        cwd=workspace_root,
        dry_run=dry_run,
    )


def _exec_compose_up(workspace_root: Path, *, detach: bool = True,
                      monitoring: bool = False, dry_run: bool = False) -> bool:
    """Bring up docker compose stack."""
    compose_file = workspace_root / "docker-compose.yml"
    if not compose_file.exists() and not dry_run:
        warning(f"  docker-compose.yml not found -- skipping")
        return False
    cmd = ["docker", "compose"]
    if monitoring:
        cmd.extend(["--profile", "monitoring"])
    cmd.append("up")
    if detach:
        cmd.append("-d")
    return _run(
        cmd,
        label="Docker Compose stack started",
        cwd=workspace_root,
        dry_run=dry_run,
    )


def _k8s_cluster_reachable() -> bool:
    """Return True if the current kubectl context has a reachable API server.

    Runs ``kubectl cluster-info --request-timeout=3s`` and checks the exit
    code.  Suppresses all output so the check is silent.
    """
    try:
        result = subprocess.run(
            ["kubectl", "cluster-info", "--request-timeout=3s"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def _exec_k8s_apply(workspace_root: Path, *, namespace: str = "",
                     dry_run: bool = False):
    """Apply Kubernetes manifests via kustomize.

    Returns:
        True  -- manifests applied successfully
        False -- kubectl exited non-zero (real failure)
        None  -- skipped (no cluster reachable / missing k8s dir / no kubectl)
    """
    if dry_run:
        dim("  [dry-run] kubectl apply -k k8s/")
        return True

    k8s_dir = workspace_root / "k8s"
    if not k8s_dir.exists():
        warning("  k8s/ directory not found -- skipping")
        return None

    if not _has_command("kubectl"):
        warning("  kubectl not found on PATH -- skipping k8s apply")
        return None

    info("  Checking cluster connectivity...")
    if not _k8s_cluster_reachable():
        warning("  No Kubernetes cluster reachable (kubectl cluster-info failed).")
        dim("  Manifests are ready in k8s/ -- apply when a cluster is available:")
        dim("    kubectl apply -k k8s/")
        if namespace:
            dim(f"    kubectl apply -k k8s/ -n {namespace}")
        return None          # not a hard error -- manifests were generated fine

    cmd = ["kubectl", "apply", "-k", "k8s/", "--validate=false"]
    if namespace:
        cmd.extend(["-n", namespace])
    return _run(
        cmd,
        label="Kubernetes manifests applied",
        cwd=workspace_root,
        dry_run=False,
    )


def _exec_compose_audit(workspace_root: Path, *, dry_run: bool = False) -> bool:
    """Audit running compose services (ps + health)."""
    compose_file = workspace_root / "docker-compose.yml"
    if not compose_file.exists() and not dry_run:
        return False
    return _run(
        ["docker", "compose", "ps", "--format", "table"],
        label="Compose service audit",
        cwd=workspace_root,
        dry_run=dry_run,
    )


def _exec_monitoring_up(workspace_root: Path, *, dry_run: bool = False) -> bool:
    """Start monitoring stack via compose profile."""
    compose_file = workspace_root / "docker-compose.yml"
    if not compose_file.exists() and not dry_run:
        warning("  docker-compose.yml not found -- cannot start monitoring")
        return False
    return _run(
        ["docker", "compose", "--profile", "monitoring", "up", "-d"],
        label="Monitoring stack started (Prometheus + Grafana)",
        cwd=workspace_root,
        dry_run=dry_run,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Click group
# ═══════════════════════════════════════════════════════════════════════════

@click.group("deploy", invoke_without_command=True)
@click.option("--force", "-f", is_flag=True, help="Overwrite existing files")
@click.option("--dry-run", is_flag=True, help="Preview without writing files")
@click.option("--yes", "-y", is_flag=True, help="Skip interactive prompts, use defaults")
@click.option("--skip-build-check", is_flag=True, help="Skip production build check (use live introspection)")
@click.pass_context
def deploy_gen_group(ctx, force: bool, dry_run: bool, yes: bool, skip_build_check: bool):
    """Generate & execute production deployment files.

    Requires a production build (``aq build --mode=prod``) before
    deploying.  If no build is found, offers to build automatically —
    just like React/Vite/Next.js require ``npm run build`` before deploy.

    Interactive wizard:
      aq deploy              # Full interactive setup + execute
      aq deploy -y           # Non-interactive, auto-build + deploy
      aq deploy --dry-run    # Preview what would happen

    Sub-commands:
      aq deploy dockerfile
      aq deploy compose --monitoring
      aq deploy kubernetes
      aq deploy all
      aq deploy all --force
      aq deploy all --dry-run

    Flags:
      --skip-build-check     Use live workspace introspection (skip build gate)
    """
    ctx.ensure_object(dict)
    ctx.obj["force"] = force
    ctx.obj["dry_run"] = dry_run
    ctx.obj["skip_build_check"] = skip_build_check

    # If a sub-command was given, delegate to it
    if ctx.invoked_subcommand is not None:
        return

    # ── Interactive deploy wizard ────────────────────────────────────
    _interactive_deploy(ctx, force=force, dry_run=dry_run, yes=yes,
                        skip_build_check=skip_build_check)


# ═══════════════════════════════════════════════════════════════════════════
# Interactive deploy wizard
# ═══════════════════════════════════════════════════════════════════════════

def _interactive_deploy(
    ctx: click.Context,
    *,
    force: bool,
    dry_run: bool,
    yes: bool,
    skip_build_check: bool = False,
) -> None:
    """Full interactive deployment wizard.

    Steps:
      0. Ensure production build (build-first gate)
      1. Introspect workspace (from build manifest)
      2. Select artefacts to generate
      3. Configure options (CI provider, monitoring, dev mode, …)
      4. Review & confirm
      5. Generate files
      6. Optionally execute deployment
    """
    from ..generators.deployment import (
        DockerfileGenerator,
        ComposeGenerator,
        KubernetesGenerator,
        NginxGenerator,
        CIGenerator,
        PrometheusGenerator,
        GrafanaGenerator,
        EnvGenerator,
        MakefileGenerator,
    )

    workspace_root = Path.cwd()
    verbose = ctx.obj.get("verbose", False)
    interactive = not yes and sys.stdin.isatty()
    written = 0

    # ── 0. Build gate ────────────────────────────────────────────────
    # Like React/Vite/Next.js: you must build before you deploy.
    if not _ensure_production_build(
        workspace_root,
        interactive=interactive,
        skip_build_check=skip_build_check,
    ):
        sys.exit(1)

    # ── 1. Introspect workspace (from build manifest) ────────────────
    try:
        wctx = _get_ctx(workspace_root, skip_build_check=skip_build_check)
    except Exception as e:
        error(f"  {_CROSS} Workspace introspection failed: {e}")
        sys.exit(1)

    name = wctx["name"]

    if interactive:
        flow_header(
            "aquilia deploy",
            "Generate & execute production deployment for your workspace.",
        )

        # Show detected workspace info
        from_build = wctx.get("_from_build_manifest", False)
        section("Workspace detected")
        kv("Name", name)
        kv("Source", "build manifest" if from_build else "live introspection")
        if from_build and wctx.get("build_fingerprint"):
            kv("Build", wctx["build_fingerprint"][:16] + "...")
        kv("Modules", str(wctx.get("module_count", 0)))
        kv("DB driver", wctx.get("db_driver", "none"))
        kv("Python", wctx.get("python_version", "3.12"))
        kv("Cache", "yes" if wctx.get("has_cache") else "no")
        kv("WebSockets", "yes" if wctx.get("has_websockets") else "no")
        kv("MLOps", "yes" if wctx.get("has_mlops") else "no")
        click.echo()

        # ── 2. Select artefacts ──────────────────────────────────────
        artefacts = multi_select("Artefacts to generate", [
            ("dockerfile",  "Dockerfile (prod + dev + mlops)",     True),
            ("compose",     "docker-compose.yml (full stack)",     True),
            ("kubernetes",  "Kubernetes manifests (k8s/)",         False),
            ("nginx",       "Nginx reverse-proxy config",          False),
            ("ci",          "CI/CD pipeline (GitHub/GitLab)",      True),
            ("monitoring",  "Prometheus + Grafana provisioning",   True),
            ("env",         ".env.example template",               True),
            ("makefile",    "Makefile (dev/build/deploy targets)", True),
        ])

        if not artefacts:
            info("  No artefacts selected -- nothing to do.")
            return

        # ── 3. Configure options ─────────────────────────────────────

        # CI provider (only if ci selected)
        ci_provider = "github"
        if "ci" in artefacts:
            ci_provider = select("CI/CD provider", [
                ("github", "GitHub Actions"),
                ("gitlab", "GitLab CI/CD"),
                ("both",   "Both providers"),
            ], default=0)

        # Dev mode dockerfiles
        include_dev = False
        if "dockerfile" in artefacts:
            include_dev = confirm("Generate dev Dockerfile? (hot-reload)", default=True)

        # Monitoring in compose
        include_monitoring = "monitoring" in artefacts
        if "compose" in artefacts and not include_monitoring:
            include_monitoring = confirm(
                "Include monitoring services in Compose?", default=False
            )

        # Output directory
        output_dir = ask(
            "Output directory",
            default=".",
            hint="relative to workspace root",
        )

        # ── 4. Execution options ─────────────────────────────────────
        section("Execution")

        exec_actions = multi_select("After generating, execute", [
            ("docker-build",   "Build Docker image",                     "dockerfile" in artefacts),
            ("compose-up",     "Start Docker Compose stack",             "compose" in artefacts),
            ("k8s-apply",      "Apply Kubernetes manifests (kubectl)",   "kubernetes" in artefacts),
            ("monitoring-up",  "Start monitoring (Prometheus+Grafana)",  include_monitoring),
            ("compose-audit",  "Audit running services (docker ps)",     "compose" in artefacts),
        ])

        # ── 5. Review & confirm ─────────────────────────────────────
        recap([
            ("Workspace",    name),
            ("Artefacts",    ", ".join(artefacts)),
            ("CI provider",  ci_provider if "ci" in artefacts else "—"),
            ("Dev Dockerfile", "yes" if include_dev else "no"),
            ("Monitoring",   "yes" if include_monitoring else "no"),
            ("Output",       output_dir),
            ("Execute",      ", ".join(exec_actions) if exec_actions else "none"),
            ("Force",        "yes" if force else "no"),
            ("Dry run",      "yes" if dry_run else "no"),
        ], title="Deploy configuration")

        if not confirm("Proceed with deployment?", default=True):
            click.echo()
            info("  Cancelled.")
            return

    else:
        # ── Non-interactive defaults ─────────────────────────────────
        artefacts = [
            "dockerfile", "compose", "kubernetes", "nginx",
            "ci", "monitoring", "env", "makefile",
        ]
        ci_provider = "github"
        include_dev = True
        include_monitoring = True
        output_dir = "."
        exec_actions = ["docker-build", "compose-up", "compose-audit"]

    # ── 6. Generate files ────────────────────────────────────────────
    out = Path(output_dir)

    click.echo()
    banner(f"Deploy: {name}", subtitle="DRY RUN" if dry_run else "Generating deployment suite")
    click.echo()

    # -- Dockerfiles --
    if "dockerfile" in artefacts:
        section("Docker")
        docker_gen = DockerfileGenerator(wctx)
        if _write_file(out / "Dockerfile", docker_gen.generate_dockerfile(),
                       label="Dockerfile (production)", verbose=verbose,
                       force=force, dry_run=dry_run):
            written += 1
        if _write_file(out / ".dockerignore", docker_gen.generate_dockerignore(),
                       label=".dockerignore", verbose=verbose,
                       force=force, dry_run=dry_run):
            written += 1
        if include_dev:
            if _write_file(out / "Dockerfile.dev", docker_gen.generate_dockerfile_dev(),
                           label="Dockerfile.dev (development)", verbose=verbose,
                           force=force, dry_run=dry_run):
                written += 1
        if wctx.get("has_mlops"):
            if _write_file(out / "Dockerfile.mlops", docker_gen.generate_dockerfile_mlops(),
                           label="Dockerfile.mlops (model-serving)", verbose=verbose,
                           force=force, dry_run=dry_run):
                written += 1
        click.echo()

    # -- Compose --
    if "compose" in artefacts:
        section("Docker Compose")
        compose_gen = ComposeGenerator(wctx)
        if _write_file(out / "docker-compose.yml",
                       compose_gen.generate_compose(include_monitoring=include_monitoring),
                       label="docker-compose.yml", verbose=verbose,
                       force=force, dry_run=dry_run):
            written += 1
        if include_dev:
            if _write_file(out / "docker-compose.dev.yml",
                           compose_gen.generate_compose_dev(),
                           label="docker-compose.dev.yml (dev override)", verbose=verbose,
                           force=force, dry_run=dry_run):
                written += 1
        click.echo()

    # -- Kubernetes --
    if "kubernetes" in artefacts:
        section("Kubernetes")
        k8s_gen = KubernetesGenerator(wctx)
        manifests = k8s_gen.generate_all()
        for filename, content in manifests.items():
            if _write_file(out / "k8s" / filename, content,
                           label=f"k8s/{filename}", verbose=verbose,
                           force=force, dry_run=dry_run):
                written += 1

        kustomize_resources = "\n".join(f"  - {f}" for f in sorted(manifests.keys()))
        kustomize_content = (
            f"apiVersion: kustomize.config.k8s.io/v1beta1\n"
            f"kind: Kustomization\n"
            f"namespace: {name}\n\n"
            f"labels:\n"
            f"  - pairs:\n"
            f"      app.kubernetes.io/name: {name}\n"
            f"      app.kubernetes.io/managed-by: aquilia-cli\n\n"
            f"resources:\n{kustomize_resources}\n"
        )
        if _write_file(out / "k8s" / "kustomization.yaml",
                       kustomize_content,
                       label="k8s/kustomization.yaml", verbose=verbose,
                       force=force, dry_run=dry_run):
            written += 1
        click.echo()

    # -- Nginx --
    if "nginx" in artefacts:
        section("Nginx")
        nginx_gen = NginxGenerator(wctx)
        if _write_file(out / "deploy" / "nginx" / "nginx.conf",
                       nginx_gen.generate_nginx_conf(),
                       label="deploy/nginx/nginx.conf", verbose=verbose,
                       force=force, dry_run=dry_run):
            written += 1
        if not dry_run:
            (out / "deploy" / "nginx" / "ssl").mkdir(parents=True, exist_ok=True)
        if _write_file(out / "deploy" / "nginx" / "ssl" / ".gitkeep", "",
                       label="deploy/nginx/ssl/.gitkeep", verbose=verbose,
                       force=force, dry_run=dry_run):
            written += 1
        click.echo()

    # -- CI/CD --
    if "ci" in artefacts:
        section("CI/CD")
        ci_gen = CIGenerator(wctx)
        if ci_provider in ("github", "both"):
            if _write_file(out / ".github" / "workflows" / "ci.yml",
                           ci_gen.generate_github_actions(),
                           label=".github/workflows/ci.yml", verbose=verbose,
                           force=force, dry_run=dry_run):
                written += 1
        if ci_provider in ("gitlab", "both"):
            if _write_file(out / ".gitlab-ci.yml",
                           ci_gen.generate_gitlab_ci(),
                           label=".gitlab-ci.yml", verbose=verbose,
                           force=force, dry_run=dry_run):
                written += 1
        click.echo()

    # -- Monitoring --
    if "monitoring" in artefacts:
        section("Monitoring")
        prom_gen = PrometheusGenerator(wctx)
        if _write_file(out / "deploy" / "prometheus" / "prometheus.yml",
                       prom_gen.generate_prometheus_yml(),
                       label="deploy/prometheus/prometheus.yml", verbose=verbose,
                       force=force, dry_run=dry_run):
            written += 1
        graf_gen = GrafanaGenerator(wctx)
        if _write_file(out / "deploy" / "grafana" / "provisioning" / "datasources" / "datasource.yml",
                       graf_gen.generate_datasource(),
                       label="deploy/grafana/.../datasource.yml", verbose=verbose,
                       force=force, dry_run=dry_run):
            written += 1
        if _write_file(out / "deploy" / "grafana" / "provisioning" / "dashboards" / "dashboards.yml",
                       graf_gen.generate_dashboard_provisioning(),
                       label="deploy/grafana/.../dashboards.yml", verbose=verbose,
                       force=force, dry_run=dry_run):
            written += 1
        click.echo()

    # -- Env --
    if "env" in artefacts:
        section("Environment")
        env_gen = EnvGenerator(wctx)
        if _write_file(out / ".env.example", env_gen.generate_env_example(),
                       label=".env.example", verbose=verbose,
                       force=force, dry_run=dry_run):
            written += 1
        click.echo()

    # -- Makefile --
    if "makefile" in artefacts:
        section("Makefile")
        mk_gen = MakefileGenerator(wctx)
        if _write_file(out / "Makefile", mk_gen.generate_makefile(),
                       label="Makefile", verbose=verbose,
                       force=force, dry_run=dry_run):
            written += 1
        click.echo()

    # -- Generation summary --
    rule()
    click.echo()
    if dry_run:
        info(f"  {written} file(s) would be generated")
    else:
        success(f"  {_CHECK} {written} file(s) generated for '{name}'")
    click.echo()

    # ── 7. Execute deployment ────────────────────────────────────────
    if exec_actions and not dry_run:
        rule()
        banner(f"Execute: {name}", subtitle="Running deployment actions")
        click.echo()

        exec_ok = 0
        exec_fail = 0
        exec_skip = 0

        if "docker-build" in exec_actions:
            section("Docker Build")
            if not _has_command("docker"):
                warning("  Docker not found on PATH -- skipping build")
                exec_fail += 1
            elif _exec_docker_build(workspace_root, wctx, dry_run=dry_run):
                exec_ok += 1
            else:
                exec_fail += 1
            click.echo()

        if "compose-up" in exec_actions:
            section("Docker Compose Up")
            if not _has_command("docker"):
                warning("  Docker not found on PATH -- skipping compose")
                exec_fail += 1
            elif _exec_compose_up(
                workspace_root,
                monitoring=include_monitoring and "monitoring-up" in exec_actions,
                dry_run=dry_run,
            ):
                exec_ok += 1
            else:
                exec_fail += 1
            click.echo()

        if "k8s-apply" in exec_actions:
            section("Kubernetes Apply")
            k8s_result = _exec_k8s_apply(workspace_root, namespace=name, dry_run=dry_run)
            if k8s_result is True:
                exec_ok += 1
            elif k8s_result is None:
                exec_skip += 1   # no cluster -- not a failure
            else:
                exec_fail += 1
            click.echo()

        if "monitoring-up" in exec_actions and "compose-up" not in exec_actions:
            # Only start monitoring separately if compose-up didn't already
            section("Monitoring Stack")
            if not _has_command("docker"):
                warning("  Docker not found on PATH -- skipping monitoring")
                exec_fail += 1
            elif _exec_monitoring_up(workspace_root, dry_run=dry_run):
                exec_ok += 1
            else:
                exec_fail += 1
            click.echo()

        if "compose-audit" in exec_actions:
            section("Service Audit")
            if _has_command("docker"):
                _exec_compose_audit(workspace_root, dry_run=dry_run)
                exec_ok += 1
            else:
                warning("  Docker not found on PATH -- skipping audit")
                exec_fail += 1
            click.echo()

        # Execution summary
        rule()
        click.echo()
        if exec_fail == 0:
            success(f"  {_CHECK} All {exec_ok} action(s) completed successfully")
        elif exec_ok == 0 and exec_fail == 0:
            info(f"  {exec_skip} action(s) skipped (no cluster / tool unavailable)")
        else:
            parts = [f"{exec_ok} succeeded"]
            if exec_skip:
                parts.append(f"{exec_skip} skipped")
            if exec_fail:
                parts.append(f"{exec_fail} failed")
            warning(f"  {', '.join(parts)}")
        click.echo()

    elif exec_actions and dry_run:
        rule()
        click.echo()
        info(f"  [dry-run] {len(exec_actions)} action(s) would be executed:")
        for action in exec_actions:
            dim(f"    {_ARROW} {action}")
        click.echo()

    # ── 8. Next steps ────────────────────────────────────────────────
    tips: list[str] = []
    if "env" in artefacts:
        tips.append("cp .env.example .env && edit .env")
    if "compose" in artefacts and "compose-up" not in exec_actions:
        tips.append("docker compose up -d")
    if "kubernetes" in artefacts and "k8s-apply" not in exec_actions:
        tips.append("kubectl apply -k k8s/")
    if "makefile" in artefacts:
        tips.append("make help")
    if "monitoring" in artefacts:
        tips.append("Open Grafana at http://localhost:3000 (admin/admin)")
    if tips:
        next_steps(tips)
        click.echo()

    flow_done("Deployment complete.")


# ═══════════════════════════════════════════════════════════════════════════
# aq deploy dockerfile
# ═══════════════════════════════════════════════════════════════════════════

@deploy_gen_group.command("dockerfile")
@click.option("--dev", "dev_mode", is_flag=True, help="Generate development Dockerfile (with hot-reload)")
@click.option("--mlops", "mlops_mode", is_flag=True, help="Generate MLOps model-serving Dockerfile")
@click.option("--output", "-o", type=click.Path(), default=".", help="Output directory")
@deploy_options
@click.pass_context
def deploy_dockerfile(ctx, dev_mode: bool, mlops_mode: bool, output: str, force: bool, dry_run: bool):
    """
    Generate production-ready Dockerfiles.

    Creates a multi-stage Dockerfile optimised for Aquilia with
    non-root user, health-checks, tini init, BuildKit cache mounts,
    and artifact compilation.

    Examples:
      aq deploy dockerfile
      aq deploy dockerfile --dev
      aq deploy dockerfile --mlops
      aq deploy dockerfile --dev --mlops   # Generate all variants
      aq deploy -f dockerfile              # Force overwrite
    """
    from ..generators.deployment import DockerfileGenerator

    workspace_root = Path.cwd()
    out = Path(output)
    verbose = ctx.obj.get("verbose", False)
    force = force or ctx.obj.get("force", False)
    dry_run = dry_run or ctx.obj.get("dry_run", False)

    _subcommand_build_gate(ctx, workspace_root)

    try:
        wctx = _get_ctx(workspace_root)
        gen = DockerfileGenerator(wctx)

        action = "DRY RUN" if dry_run else "Generating"
        section(f"{action}: Dockerfiles for '{wctx['name']}'")

        kv("Modules", str(wctx.get('module_count', 0)))
        kv("DB driver", wctx.get('db_driver', 'none'))
        kv("Python", wctx.get('python_version', '3.12'))
        click.echo()

        # Always generate production Dockerfile + .dockerignore
        if not dev_mode or mlops_mode:
            _write_file(out / "Dockerfile", gen.generate_dockerfile(),
                        label="Dockerfile (production)", verbose=verbose,
                        force=force, dry_run=dry_run)
            _write_file(out / ".dockerignore", gen.generate_dockerignore(),
                        label=".dockerignore", verbose=verbose,
                        force=force, dry_run=dry_run)

        if dev_mode:
            _write_file(out / "Dockerfile.dev", gen.generate_dockerfile_dev(),
                        label="Dockerfile.dev (development)", verbose=verbose,
                        force=force, dry_run=dry_run)
            if not mlops_mode:
                _write_file(out / ".dockerignore", gen.generate_dockerignore(),
                            label=".dockerignore", verbose=verbose,
                            force=force, dry_run=dry_run)

        if mlops_mode or wctx.get("has_mlops"):
            _write_file(out / "Dockerfile.mlops", gen.generate_dockerfile_mlops(),
                        label="Dockerfile.mlops (model-serving)", verbose=verbose,
                        force=force, dry_run=dry_run)

        click.echo()
        next_steps([
            "docker build -t myapp .",
            "docker run -p 8000:8000 myapp",
        ])

    except Exception as e:
        error(f"  {_CROSS} Dockerfile generation failed: {e}")
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════
# aq deploy compose
# ═══════════════════════════════════════════════════════════════════════════

@deploy_gen_group.command("compose")
@click.option("--dev", "dev_mode", is_flag=True, help="Also generate docker-compose.dev.yml")
@click.option("--monitoring", is_flag=True, help="Include Prometheus + Grafana services")
@click.option("--output", "-o", type=click.Path(), default=".", help="Output directory")
@deploy_options
@click.pass_context
def deploy_compose(ctx, dev_mode: bool, monitoring: bool, output: str, force: bool, dry_run: bool):
    """
    Generate docker-compose.yml for the workspace.

    Auto-detects services: PostgreSQL, MySQL, Redis, MLOps model server,
    Nginx, monitoring, and mail based on your workspace configuration.
    Uses compose profiles for optional services (mlops, monitoring, dev).

    Examples:
      aq deploy compose
      aq deploy compose --monitoring
      aq deploy compose --dev
      aq deploy -f compose   # Force overwrite
    """
    from ..generators.deployment import ComposeGenerator

    workspace_root = Path.cwd()
    out = Path(output)
    verbose = ctx.obj.get("verbose", False)
    force = force or ctx.obj.get("force", False)
    dry_run = dry_run or ctx.obj.get("dry_run", False)

    _subcommand_build_gate(ctx, workspace_root)

    try:
        wctx = _get_ctx(workspace_root)
        gen = ComposeGenerator(wctx)

        action = "DRY RUN" if dry_run else "Generating"
        section(f"{action}: Docker Compose for '{wctx['name']}'")

        _write_file(out / "docker-compose.yml",
                     gen.generate_compose(include_monitoring=monitoring),
                     label="docker-compose.yml", verbose=verbose,
                     force=force, dry_run=dry_run)

        if dev_mode:
            _write_file(out / "docker-compose.dev.yml",
                         gen.generate_compose_dev(),
                         label="docker-compose.dev.yml", verbose=verbose,
                         force=force, dry_run=dry_run)

        click.echo()
        next_steps([
            "docker compose up -d",
            "docker compose --profile proxy up -d        # Include Nginx",
            "docker compose --profile monitoring up -d   # Include Prometheus + Grafana",
            "docker compose logs -f app",
        ])

    except Exception as e:
        error(f"  {_CROSS} Compose generation failed: {e}")
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════
# aq deploy kubernetes
# ═══════════════════════════════════════════════════════════════════════════

@deploy_gen_group.command("kubernetes")
@click.option("--output", "-o", type=click.Path(), default="k8s", help="Output directory")
@click.option("--mlops", is_flag=True, help="Force include MLOps manifests")
@deploy_options
@click.pass_context
def deploy_kubernetes(ctx, output: str, mlops: bool, force: bool, dry_run: bool):
    """
    Generate production Kubernetes manifests.

    Generates namespace, deployment, service, ingress, HPA, PDB,
    network policy, configmap, secret, service account, PVC,
    CronJob for maintenance, and init containers for DB readiness.
    Includes MLOps manifests if mlops components are detected.

    Examples:
      aq deploy kubernetes
      aq deploy kubernetes -o deploy/k8s
      aq deploy kubernetes --mlops
    """
    from ..generators.deployment import KubernetesGenerator

    workspace_root = Path.cwd()
    out = Path(output)
    verbose = ctx.obj.get("verbose", False)
    force = force or ctx.obj.get("force", False)
    dry_run = dry_run or ctx.obj.get("dry_run", False)

    _subcommand_build_gate(ctx, workspace_root)

    try:
        wctx = _get_ctx(workspace_root)
        if mlops:
            wctx["has_mlops"] = True

        gen = KubernetesGenerator(wctx)

        action = "DRY RUN" if dry_run else "Generating"
        section(f"{action}: Kubernetes manifests for '{wctx['name']}'")

        manifests = gen.generate_all()
        for filename, content in manifests.items():
            _write_file(out / filename, content,
                         label=filename, verbose=verbose,
                         force=force, dry_run=dry_run)

        # Generate kustomization.yaml
        kustomize_resources = "\n".join(f"  - {f}" for f in sorted(manifests.keys()))
        kustomize_content = (
            f"# Kustomize configuration for {wctx['name']}\n"
            f"# Generated by: aq deploy kubernetes\n\n"
            f"apiVersion: kustomize.config.k8s.io/v1beta1\n"
            f"kind: Kustomization\n\n"
            f"namespace: {wctx['name']}\n\n"
            f"labels:\n"
            f"  - pairs:\n"
            f"      app.kubernetes.io/name: {wctx['name']}\n"
            f"      app.kubernetes.io/managed-by: aquilia-cli\n\n"
            f"resources:\n{kustomize_resources}\n"
        )
        _write_file(out / "kustomization.yaml", kustomize_content,
                     label="kustomization.yaml", verbose=verbose,
                     force=force, dry_run=dry_run)

        click.echo()
        kv("Manifests", str(len(manifests)))
        click.echo()
        next_steps([
            f"kubectl apply -k {output}/",
            f"kustomize build {output}/ | kubectl apply -f -",
        ])

    except Exception as e:
        error(f"  {_CROSS} Kubernetes generation failed: {e}")
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════
# aq deploy nginx
# ═══════════════════════════════════════════════════════════════════════════

@deploy_gen_group.command("nginx")
@click.option("--output", "-o", type=click.Path(), default="deploy/nginx", help="Output directory")
@deploy_options
@click.pass_context
def deploy_nginx(ctx, output: str, force: bool, dry_run: bool):
    """
    Generate Nginx reverse-proxy configuration.

    Includes rate-limiting, security headers (HSTS, CSP, XSS), gzip,
    WebSocket upgrade support, upstream keepalive, and MLOps proxy
    if detected. HTTPS block included (commented) with modern TLS config.

    Examples:
      aq deploy nginx
      aq deploy nginx -o config/nginx
    """
    from ..generators.deployment import NginxGenerator

    workspace_root = Path.cwd()
    out = Path(output)
    verbose = ctx.obj.get("verbose", False)
    force = force or ctx.obj.get("force", False)
    dry_run = dry_run or ctx.obj.get("dry_run", False)

    _subcommand_build_gate(ctx, workspace_root)

    try:
        wctx = _get_ctx(workspace_root)
        gen = NginxGenerator(wctx)

        action = "DRY RUN" if dry_run else "Generating"
        section(f"{action}: Nginx config for '{wctx['name']}'")

        _write_file(out / "nginx.conf", gen.generate_nginx_conf(),
                     label="nginx.conf", verbose=verbose,
                     force=force, dry_run=dry_run)

        # Create ssl directory placeholder
        if not dry_run:
            ssl_dir = out / "ssl"
            ssl_dir.mkdir(parents=True, exist_ok=True)
            _write_file(ssl_dir / ".gitkeep", "",
                         label="ssl/.gitkeep (placeholder)", verbose=verbose,
                         force=force, dry_run=dry_run)

        click.echo()
        next_steps([
            "Place TLS certificates in deploy/nginx/ssl/",
            "Uncomment HTTPS block in nginx.conf",
        ])

    except Exception as e:
        error(f"  {_CROSS} Nginx generation failed: {e}")
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════
# aq deploy ci
# ═══════════════════════════════════════════════════════════════════════════

@deploy_gen_group.command("ci")
@click.option("--provider", type=click.Choice(["github", "gitlab"]), default="github",
              help="CI provider")
@click.option("--output", "-o", type=click.Path(), default=None, help="Output directory")
@deploy_options
@click.pass_context
def deploy_ci(ctx, provider: str, output: Optional[str], force: bool, dry_run: bool):
    """
    Generate CI/CD pipeline configuration.

    Creates a CI/CD workflow with lint, test, security scan, build,
    and deploy stages. Includes Trivy container scanning, dependency
    auditing, and Aquilia-specific validation steps.

    Supported providers:
      --provider=github   GitHub Actions (default)
      --provider=gitlab   GitLab CI/CD

    Examples:
      aq deploy ci
      aq deploy ci --provider=github
      aq deploy ci --provider=gitlab
    """
    from ..generators.deployment import CIGenerator

    workspace_root = Path.cwd()
    verbose = ctx.obj.get("verbose", False)
    force = force or ctx.obj.get("force", False)
    dry_run = dry_run or ctx.obj.get("dry_run", False)

    _subcommand_build_gate(ctx, workspace_root)

    try:
        wctx = _get_ctx(workspace_root)
        gen = CIGenerator(wctx)

        action = "DRY RUN" if dry_run else "Generating"
        section(f"{action}: CI/CD pipeline for '{wctx['name']}' ({provider})")

        if provider == "github":
            out_dir = Path(output) if output else workspace_root / ".github" / "workflows"
            _write_file(out_dir / "ci.yml", gen.generate_github_actions(),
                         label=".github/workflows/ci.yml", verbose=verbose,
                         force=force, dry_run=dry_run)
        elif provider == "gitlab":
            out_dir = Path(output) if output else workspace_root
            _write_file(out_dir / ".gitlab-ci.yml", gen.generate_gitlab_ci(),
                         label=".gitlab-ci.yml", verbose=verbose,
                         force=force, dry_run=dry_run)

        click.echo()
        next_steps([
            "Review the generated workflow",
            "Configure secrets in repository settings",
            "Push to trigger CI",
        ])

    except Exception as e:
        error(f"  {_CROSS} CI generation failed: {e}")
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════
# aq deploy monitoring
# ═══════════════════════════════════════════════════════════════════════════

@deploy_gen_group.command("monitoring")
@click.option("--output", "-o", type=click.Path(), default="deploy", help="Output base directory")
@deploy_options
@click.pass_context
def deploy_monitoring(ctx, output: str, force: bool, dry_run: bool):
    """
    Generate monitoring configuration (Prometheus + Grafana).

    Creates Prometheus scrape config and Grafana provisioning files
    for Aquilia app and MLOps model server metrics.

    Prometheus scrape targets are auto-configured based on detected
    modules (app metrics, model-server, Redis, Postgres exporters).

    Examples:
      aq deploy monitoring
      aq deploy monitoring -o infra/
      aq deploy monitoring --force
    """
    from ..generators.deployment import PrometheusGenerator, GrafanaGenerator

    workspace_root = Path.cwd()
    out = Path(output)
    verbose = ctx.obj.get("verbose", False)
    force = force or ctx.obj.get("force", False)
    dry_run = dry_run or ctx.obj.get("dry_run", False)

    _subcommand_build_gate(ctx, workspace_root)

    try:
        wctx = _get_ctx(workspace_root)

        action = "DRY RUN" if dry_run else "Generating"
        section(f"{action}: Monitoring for '{wctx['name']}'")

        prom_gen = PrometheusGenerator(wctx)
        _write_file(out / "prometheus" / "prometheus.yml",
                     prom_gen.generate_prometheus_yml(),
                     label="prometheus/prometheus.yml", verbose=verbose,
                     force=force, dry_run=dry_run)

        graf_gen = GrafanaGenerator(wctx)
        _write_file(out / "grafana" / "provisioning" / "datasources" / "datasource.yml",
                     graf_gen.generate_datasource(),
                     label="grafana/provisioning/datasources/datasource.yml", verbose=verbose,
                     force=force, dry_run=dry_run)
        _write_file(out / "grafana" / "provisioning" / "dashboards" / "dashboards.yml",
                     graf_gen.generate_dashboard_provisioning(),
                     label="grafana/provisioning/dashboards/dashboards.yml", verbose=verbose,
                     force=force, dry_run=dry_run)

        click.echo()
        next_steps([
            "aq deploy compose --monitoring",
            "docker compose up -d prometheus grafana",
            "Open Grafana at http://localhost:3000 (admin/admin)",
        ])

    except Exception as e:
        error(f"  {_CROSS} Monitoring generation failed: {e}")
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════
# aq deploy env
# ═══════════════════════════════════════════════════════════════════════════

@deploy_gen_group.command("env")
@click.option("--output", "-o", type=click.Path(), default=".", help="Output directory")
@deploy_options
@click.pass_context
def deploy_env(ctx, output: str, force: bool, dry_run: bool):
    """
    Generate .env.example template with all Aquilia settings.

    Scans the workspace for enabled components and generates
    a comprehensive environment variable template. Includes
    db-driver-aware DATABASE_URL defaults, telemetry, CORS,
    and monitoring sections when relevant.

    Examples:
      aq deploy env
      aq deploy env --force
    """
    from ..generators.deployment import EnvGenerator

    workspace_root = Path.cwd()
    out = Path(output)
    verbose = ctx.obj.get("verbose", False)
    force = force or ctx.obj.get("force", False)
    dry_run = dry_run or ctx.obj.get("dry_run", False)

    _subcommand_build_gate(ctx, workspace_root)

    try:
        wctx = _get_ctx(workspace_root)
        gen = EnvGenerator(wctx)

        action = "DRY RUN" if dry_run else "Generating"
        section(f"{action}: .env.example for '{wctx['name']}'")

        _write_file(out / ".env.example", gen.generate_env_example(),
                     label=".env.example", verbose=verbose,
                     force=force, dry_run=dry_run)

        click.echo()
        kv("DB driver", wctx.get('db_driver', 'sqlite'))
        click.echo()
        next_steps([
            "cp .env.example .env",
            "Fill in real secrets -- never commit .env",
        ])

    except Exception as e:
        error(f"  {_CROSS} Env generation failed: {e}")
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════
# aq deploy all
# ═══════════════════════════════════════════════════════════════════════════

@deploy_gen_group.command("all")
@click.option("--output", "-o", type=click.Path(), default=".", help="Output base directory")
@click.option("--monitoring", is_flag=True, default=True, help="Include monitoring (default: yes)")
@click.option("--ci-provider", type=click.Choice(["github", "gitlab", "both"]),
              default="github", help="CI/CD provider")
@deploy_options
@click.pass_context
def deploy_all(ctx, output: str, monitoring: bool, ci_provider: str, force: bool, dry_run: bool):
    """
    Generate ALL deployment files at once.

    Creates Dockerfile, docker-compose.yml, Kubernetes manifests,
    Nginx config, CI/CD pipeline(s), Makefile, monitoring, and
    .env template.  Respects --force and --dry-run flags.

    Examples:
      aq deploy all
      aq deploy all -o deploy/
      aq deploy all --ci-provider=both --force
    """
    from ..generators.deployment import (
        DockerfileGenerator,
        ComposeGenerator,
        KubernetesGenerator,
        NginxGenerator,
        CIGenerator,
        PrometheusGenerator,
        GrafanaGenerator,
        EnvGenerator,
        MakefileGenerator,
    )

    workspace_root = Path.cwd()
    out = Path(output)
    verbose = ctx.obj.get("verbose", False)
    force = force or ctx.obj.get("force", False)
    dry_run = dry_run or ctx.obj.get("dry_run", False)
    written = 0  # track files written

    _subcommand_build_gate(ctx, workspace_root)

    try:
        wctx = _get_ctx(workspace_root)
        name = wctx["name"]

        action = "DRY RUN" if dry_run else "Generating"
        banner(f"Deploy: {name}", subtitle=f"{action} full deployment suite")
        click.echo()

        # -- Dockerfiles --
        section("Docker")
        docker_gen = DockerfileGenerator(wctx)
        if _write_file(out / "Dockerfile", docker_gen.generate_dockerfile(),
                       label="Dockerfile", verbose=verbose,
                       force=force, dry_run=dry_run):
            written += 1
        if _write_file(out / "Dockerfile.dev", docker_gen.generate_dockerfile_dev(),
                       label="Dockerfile.dev", verbose=verbose,
                       force=force, dry_run=dry_run):
            written += 1
        if _write_file(out / ".dockerignore", docker_gen.generate_dockerignore(),
                       label=".dockerignore", verbose=verbose,
                       force=force, dry_run=dry_run):
            written += 1
        if wctx.get("has_mlops"):
            if _write_file(out / "Dockerfile.mlops", docker_gen.generate_dockerfile_mlops(),
                           label="Dockerfile.mlops", verbose=verbose,
                           force=force, dry_run=dry_run):
                written += 1

        # -- Compose --
        click.echo()
        section("Docker Compose")
        compose_gen = ComposeGenerator(wctx)
        if _write_file(out / "docker-compose.yml",
                       compose_gen.generate_compose(include_monitoring=monitoring),
                       label="docker-compose.yml", verbose=verbose,
                       force=force, dry_run=dry_run):
            written += 1
        if _write_file(out / "docker-compose.dev.yml",
                       compose_gen.generate_compose_dev(),
                       label="docker-compose.dev.yml", verbose=verbose,
                       force=force, dry_run=dry_run):
            written += 1

        # -- Kubernetes --
        click.echo()
        section("Kubernetes")
        k8s_gen = KubernetesGenerator(wctx)
        manifests = k8s_gen.generate_all()
        for filename, content in manifests.items():
            if _write_file(out / "k8s" / filename, content,
                           label=f"k8s/{filename}", verbose=verbose,
                           force=force, dry_run=dry_run):
                written += 1

        kustomize_resources = "\n".join(f"  - {f}" for f in sorted(manifests.keys()))
        kustomize_content = (
            f"apiVersion: kustomize.config.k8s.io/v1beta1\n"
            f"kind: Kustomization\n"
            f"namespace: {name}\n\n"
            f"labels:\n"
            f"  - pairs:\n"
            f"      app.kubernetes.io/name: {name}\n"
            f"      app.kubernetes.io/managed-by: aquilia-cli\n\n"
            f"resources:\n{kustomize_resources}\n"
        )
        if _write_file(out / "k8s" / "kustomization.yaml",
                       kustomize_content,
                       label="k8s/kustomization.yaml", verbose=verbose,
                       force=force, dry_run=dry_run):
            written += 1

        # -- Nginx --
        click.echo()
        section("Nginx")
        nginx_gen = NginxGenerator(wctx)
        if _write_file(out / "deploy" / "nginx" / "nginx.conf",
                       nginx_gen.generate_nginx_conf(),
                       label="deploy/nginx/nginx.conf", verbose=verbose,
                       force=force, dry_run=dry_run):
            written += 1
        if not dry_run:
            (out / "deploy" / "nginx" / "ssl").mkdir(parents=True, exist_ok=True)
        if _write_file(out / "deploy" / "nginx" / "ssl" / ".gitkeep", "",
                       label="deploy/nginx/ssl/.gitkeep", verbose=verbose,
                       force=force, dry_run=dry_run):
            written += 1

        # -- CI/CD --
        click.echo()
        section("CI/CD")
        ci_gen = CIGenerator(wctx)
        if ci_provider in ("github", "both"):
            if _write_file(out / ".github" / "workflows" / "ci.yml",
                           ci_gen.generate_github_actions(),
                           label=".github/workflows/ci.yml", verbose=verbose,
                           force=force, dry_run=dry_run):
                written += 1
        if ci_provider in ("gitlab", "both"):
            if _write_file(out / ".gitlab-ci.yml",
                           ci_gen.generate_gitlab_ci(),
                           label=".gitlab-ci.yml", verbose=verbose,
                           force=force, dry_run=dry_run):
                written += 1

        # -- Monitoring --
        if monitoring:
            click.echo()
            section("Monitoring")
            prom_gen = PrometheusGenerator(wctx)
            if _write_file(out / "deploy" / "prometheus" / "prometheus.yml",
                           prom_gen.generate_prometheus_yml(),
                           label="deploy/prometheus/prometheus.yml", verbose=verbose,
                           force=force, dry_run=dry_run):
                written += 1
            graf_gen = GrafanaGenerator(wctx)
            if _write_file(out / "deploy" / "grafana" / "provisioning" / "datasources" / "datasource.yml",
                           graf_gen.generate_datasource(),
                           label="deploy/grafana/provisioning/datasources/datasource.yml",
                           verbose=verbose, force=force, dry_run=dry_run):
                written += 1
            if _write_file(out / "deploy" / "grafana" / "provisioning" / "dashboards" / "dashboards.yml",
                           graf_gen.generate_dashboard_provisioning(),
                           label="deploy/grafana/provisioning/dashboards/dashboards.yml",
                           verbose=verbose, force=force, dry_run=dry_run):
                written += 1

        # -- Env --
        click.echo()
        section("Environment")
        env_gen = EnvGenerator(wctx)
        if _write_file(out / ".env.example", env_gen.generate_env_example(),
                       label=".env.example", verbose=verbose,
                       force=force, dry_run=dry_run):
            written += 1

        # -- Makefile --
        click.echo()
        section("Makefile")
        mk_gen = MakefileGenerator(wctx)
        if _write_file(out / "Makefile", mk_gen.generate_makefile(),
                       label="Makefile", verbose=verbose,
                       force=force, dry_run=dry_run):
            written += 1

        # -- Summary --
        click.echo()
        rule()
        click.echo()
        if dry_run:
            info(f"  {written} file(s) would be generated")
        else:
            success(f"  {_CHECK} {written} file(s) generated for '{name}'")
        click.echo()

        next_steps([
            "cp .env.example .env && edit .env",
            "make docker-up                (Docker Compose)",
            "make k8s-apply                (Kubernetes)",
            "make help                     (see all targets)",
        ])

        click.echo()
        section("Generated structure")

        # Build structure listing
        structure = [
            ("Dockerfile",             "Production (multi-stage, BuildKit)"),
            ("Dockerfile.dev",         "Development (hot-reload)"),
            (".dockerignore",          "Build context exclusions"),
        ]
        if wctx.get("has_mlops"):
            structure.append(("Dockerfile.mlops", "MLOps model server"))
        structure += [
            ("docker-compose.yml",     "Full service stack (profiles)"),
            ("docker-compose.dev.yml", "Dev override"),
            (f"k8s/",                  f"Kubernetes manifests ({len(manifests)} files)"),
            ("deploy/nginx/",          "Nginx reverse-proxy (TLS-ready)"),
        ]
        if monitoring:
            structure.append(("deploy/prometheus/", "Prometheus config"))
            structure.append(("deploy/grafana/",    "Grafana provisioning"))
        if ci_provider in ("github", "both"):
            structure.append((".github/workflows/", "GitHub Actions pipeline"))
        if ci_provider in ("gitlab", "both"):
            structure.append((".gitlab-ci.yml",     "GitLab CI/CD pipeline"))
        structure += [
            (".env.example",           "Environment template"),
            ("Makefile",               "Dev/deploy task runner"),
        ]

        table(
            headers=["File", "Description"],
            rows=[(f, d) for f, d in structure],
            col_widths=[28, 40],
        )

    except Exception as e:
        error(f"  {_CROSS} Full deployment generation failed: {e}")
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════
# aq deploy makefile
# ═══════════════════════════════════════════════════════════════════════════

@deploy_gen_group.command("makefile")
@click.option("--output", "-o", type=click.Path(), default=".", help="Output directory")
@deploy_options
@click.pass_context
def deploy_makefile(ctx, output: str, force: bool, dry_run: bool):
    """
    Generate a self-documenting Makefile for dev & ops tasks.

    Includes targets for running, testing, linting, Docker build/up/down,
    Kubernetes apply/delete, database migrations, and deployment file
    generation.  Run `make help` to see all targets.

    Examples:
      aq deploy makefile
      aq deploy makefile --force
    """
    from ..generators.deployment import MakefileGenerator

    workspace_root = Path.cwd()
    out = Path(output)
    verbose = ctx.obj.get("verbose", False)
    force = force or ctx.obj.get("force", False)
    dry_run = dry_run or ctx.obj.get("dry_run", False)

    _subcommand_build_gate(ctx, workspace_root)

    try:
        wctx = _get_ctx(workspace_root)
        action = "DRY RUN" if dry_run else "Generating"
        section(f"{action}: Makefile for '{wctx['name']}'")

        gen = MakefileGenerator(wctx)
        _write_file(out / "Makefile", gen.generate_makefile(),
                     label="Makefile", verbose=verbose,
                     force=force, dry_run=dry_run)

        click.echo()
        next_steps([
            "make help          # see all available targets",
            "make dev           # start dev server",
            "make docker-up     # bring up compose stack",
        ])

    except Exception as e:
        error(f"  {_CROSS} Makefile generation failed: {e}")
        sys.exit(1)
