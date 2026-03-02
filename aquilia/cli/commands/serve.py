"""Production server command.

Starts the production server using frozen artifacts (if available)
or the standard workspace app loader.  Multi-worker support is enabled
by default for production workloads.

Supports two backends:
- **gunicorn** (recommended) — multi-worker process manager with
  UvicornWorker class for ASGI.  Best for production deploys.
- **uvicorn** (fallback) — single-process or multi-worker via
  uvicorn's built-in forking.

The production pipeline:
1. Run the build pipeline (compile, check, bundle to Crous binary)
2. Verify pre-built artifacts (or rebuild if missing/stale)
3. Boot the server from compiled state
"""

import os
import sys
from pathlib import Path

from ..utils.workspace import get_workspace_file


def serve_production(
    workers: int = 1,
    bind: str = '0.0.0.0:8000',
    verbose: bool = False,
    use_gunicorn: bool = False,
    timeout: int = 120,
    graceful_timeout: int = 30,
) -> None:
    """
    Start production server.

    Args:
        workers: Number of workers
        bind: Bind address (host:port)
        verbose: Enable verbose output
        use_gunicorn: Use gunicorn with UvicornWorker (recommended for production)
        timeout: Worker timeout in seconds (gunicorn only)
        graceful_timeout: Graceful shutdown timeout (gunicorn only)
    """
    workspace_root = Path.cwd()
    ws_file = get_workspace_file(workspace_root)

    if not ws_file:
        raise ValueError("Not in an Aquilia workspace (workspace.py not found)")

    # Parse host:port from bind
    if ':' in bind:
        host, port_str = bind.rsplit(':', 1)
        port = int(port_str)
    else:
        host = bind
        port = 8000

    # Add workspace to path
    if str(workspace_root) not in sys.path:
        sys.path.insert(0, str(workspace_root))

    # Set env variables for production mode
    os.environ['AQUILIA_ENV'] = 'prod'
    os.environ['AQUILIA_WORKSPACE'] = str(workspace_root)

    # ===== BUILD PIPELINE — Compile, check, and bundle (prod mode) =====
    print("  Running production build pipeline...")
    try:
        from aquilia.build import AquiliaBuildPipeline
        build_result = AquiliaBuildPipeline.build(
            workspace_root=str(workspace_root),
            mode="prod",
            verbose=verbose,
            compression="lz4",
        )

        if not build_result.success:
            print("\n  ✗ Production build FAILED — server will not start.\n")
            for err in build_result.errors:
                print(f"  {err}")
            if build_result.warnings:
                print()
                for warn in build_result.warnings:
                    print(f"  {warn}")
            print(f"\n  Build failed in {build_result.total_ms:.0f}ms")
            print("  Fix the errors above and try again.\n")
            return

        print(f"  ✓ {build_result.summary()}")

        if build_result.warnings and verbose:
            for warn in build_result.warnings:
                print(f"  {warn}")

    except ImportError:
        if verbose:
            print("  ⚠ Build pipeline not available, proceeding without pre-compilation")
    except Exception as e:
        if verbose:
            print(f"  ⚠ Build pipeline error: {e}, proceeding without pre-compilation")

    # ===== ARTIFACT VERIFICATION =====
    build_dir = workspace_root / "build"
    build_verified = False

    if build_dir.exists():
        try:
            from aquilia.build.resolver import BuildResolver
            resolver = BuildResolver(build_dir, verbose=verbose)
            resolved = resolver.resolve()

            if resolved:
                build_verified = True
                if verbose:
                    print(f"  ✓ Verified {len(resolved.artifacts)} pre-built artifact(s)")
                    print(f"    fingerprint: {resolved.fingerprint[:16]}…")
        except Exception as e:
            if verbose:
                print(f"  ⚠ Artifact verification failed: {e}")

    # Use the same app loader as `aq run` (runtime/app.py)
    from .run import _create_workspace_app
    app_module = _create_workspace_app(workspace_root, mode='prod', verbose=verbose)

    backend = "gunicorn" if use_gunicorn else "uvicorn"

    if verbose:
        print(f"  Starting Aquilia production server")
        print(f"  Backend: {backend}")
        print(f"  Bind:    {host}:{port}")
        print(f"  Workers: {workers}")
        print(f"  App:     {app_module}")
        print(f"  Build:   {'verified' if build_verified else 'dynamic'}")
        print()

    if use_gunicorn:
        _serve_with_gunicorn(
            app_module=app_module,
            bind=f"{host}:{port}",
            workers=workers,
            timeout=timeout,
            graceful_timeout=graceful_timeout,
            verbose=verbose,
        )
    else:
        _serve_with_uvicorn(
            app_module=app_module,
            host=host,
            port=port,
            workers=workers,
            verbose=verbose,
        )


def _serve_with_gunicorn(
    app_module: str,
    bind: str,
    workers: int,
    timeout: int,
    graceful_timeout: int,
    verbose: bool,
) -> None:
    """Start production server using gunicorn with UvicornWorker."""
    try:
        from gunicorn.app.wsgiapp import WSGIApplication
    except ImportError:
        raise ImportError(
            "gunicorn is required for --use-gunicorn mode.\n"
            "Install it with: pip install gunicorn\n"
            "Or with extras: pip install 'aquilia[server]'"
        )

    class AquiliaGunicornApp(WSGIApplication):
        """Custom gunicorn application for Aquilia ASGI servers."""

        def init(self, parser, opts, args):
            return {
                "bind": bind,
                "workers": workers,
                "worker_class": "uvicorn.workers.UvicornWorker",
                "timeout": timeout,
                "graceful_timeout": graceful_timeout,
                "accesslog": "-" if verbose else None,
                "errorlog": "-",
                "loglevel": "info" if verbose else "warning",
                "preload_app": False,
                "proxy_protocol": True,
                "forwarded_allow_ips": "*",
            }

        def load(self):
            # gunicorn loads the app string itself via UvicornWorker
            return None

    # gunicorn expects the app module on sys.argv
    sys.argv = ["gunicorn", app_module]
    AquiliaGunicornApp("%(prog)s [OPTIONS]").run()


def _serve_with_uvicorn(
    app_module: str,
    host: str,
    port: int,
    workers: int,
    verbose: bool,
) -> None:
    """Start production server using uvicorn directly."""
    try:
        import uvicorn
    except ImportError:
        raise ImportError(
            "uvicorn is required to run the production server.\n"
            "Install it with: pip install uvicorn\n"
            "Or with extras: pip install 'aquilia[server]'"
        )

    uvicorn.run(
        app=app_module,
        host=host,
        port=port,
        workers=workers,
        reload=False,
        log_level="warning" if not verbose else "info",
        access_log=False,
    )
