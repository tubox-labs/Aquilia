"""
Provider CLI commands — ``aq provider``.

Manages cloud provider authentication and configuration:

    aq provider login render       Login to Render (stores token securely)
    aq provider logout render      Remove stored credentials
    aq provider status render      Show credential/connection status
    aq provider render env set     Manage Render env vars

Credentials are stored using the Crous binary format with HMAC-SHA256
integrity protection and machine-derived encryption keys.  Tokens are
never stored in plain text or logged.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click

from ..utils.colors import (
    success, error, info, warning, dim, bold,
    section, kv, rule, panel, next_steps,
    banner, _CHECK, _CROSS, _ARROW,
    status_line, detail_card, phase_header,
    _ROCKET, _LOCK, _GLOBE, _PKG, _GEAR, _BOLT,
    _SHIELD, _CLOUD, _CLOCK, _SPARK, _WARN, _KEY, _EYE, _LINK,
)
from ..utils.prompts import (
    flow_header, flow_done, ask, ask_password, select, confirm,
)


# ═══════════════════════════════════════════════════════════════════════════
# Click groups
# ═══════════════════════════════════════════════════════════════════════════

@click.group("provider")
def provider_group():
    """Manage cloud provider authentication & configuration.

    Currently supported providers:
      render   — Render PaaS (Docker-based cloud hosting)

    Examples:
      aq provider login render
      aq provider status render
      aq provider logout render
      aq provider render env set MY_VAR "value"
    """
    pass


@provider_group.group("render")
def render_group():
    """Render provider management.

    Authenticate, manage env vars, and check connection status
    for the Render cloud platform.
    """
    pass


# ═══════════════════════════════════════════════════════════════════════════
# aq provider login render
# ═══════════════════════════════════════════════════════════════════════════

@provider_group.command("login")
@click.argument("provider_name", type=click.Choice(["render"]))
@click.option("--token", "-t", type=str, default=None,
              help="API token (reads from stdin if omitted)")
@click.option("--region", "-r", type=str, default="oregon",
              help="Default deployment region")
def provider_login(provider_name: str, token: Optional[str], region: str):
    """Login to a cloud provider.

    Securely stores your API token using Crous-encrypted storage.
    The token is encrypted with a machine-derived key and signed
    with HMAC-SHA256 for tamper detection.

    Get your Render API key from:
      https://dashboard.render.com/account/settings#api-keys

    Examples:
      aq provider login render
      aq provider login render --token rnd_xxxxx
      echo $RENDER_TOKEN | aq provider login render --token -
    """
    if provider_name != "render":
        error(f"  {_CROSS} Unknown provider: {provider_name}")
        sys.exit(1)

    from aquilia.providers.render.store import RenderCredentialStore
    from aquilia.providers.render.client import RenderClient
    from aquilia.faults.domains import ProviderAuthFault, ProviderAPIFault

    store = RenderCredentialStore()

    click.echo()
    banner("Render · Login", subtitle="Securely authenticate with the Render platform", icon=_CLOUD, fg="magenta")
    click.echo()

    # ── Get token ────────────────────────────────────────────────────
    if token == "-":
        # Read from stdin (pipe)
        token = sys.stdin.readline().strip()
    elif not token:
        # Check existing
        if store.is_configured():
            existing = store.load()
            if existing:
                detail_card(
                    "Existing credentials",
                    [
                        ("Status", "Configured"),
                        ("Action", "Login again to replace"),
                    ],
                    icon=_LOCK,
                    fg="yellow",
                )
                click.echo()
                if not confirm("Replace existing credentials?", default=True):
                    info(f"  {_ARROW} Cancelled.")
                    return

        status_line(_KEY, "API key source", "https://dashboard.render.com/account/settings#api-keys")
        click.echo()
        token = ask_password(
            "Render API key",
            confirm=False,
            min_length=8,
        )

    if not token:
        error(f"  {_CROSS} No token provided.")
        sys.exit(1)

    # ── Validate token ───────────────────────────────────────────────
    phase_header(1, "Validating token", icon=_SHIELD)

    try:
        client = RenderClient(token=token)
        if not client.validate_token():
            error(f"  {_CROSS} Invalid or expired API key.")
            status_line(_KEY, "Get a new key", "https://dashboard.render.com/account/settings#api-keys")
            sys.exit(1)

        # Get owner info for display
        owners = client.list_owners()
        owner_name = owners[0].name if owners else "unknown"
        owner_email = owners[0].email if owners else "unknown"

        success(f"  {_CHECK} Token validated successfully")
        click.echo()

        detail_card(
            "Account",
            [
                ("Email", owner_email or "—"),
                ("Workspace", owner_name),
                ("Region", region),
            ],
            icon=_GLOBE,
        )

    except ProviderAuthFault:
        error(f"  {_CROSS} Authentication failed — invalid token.")
        sys.exit(1)
    except ProviderAPIFault as e:
        error(f"  {_CROSS} API error: {e}")
        sys.exit(1)

    # ── Store credentials ────────────────────────────────────────────
    phase_header(2, "Storing credentials", icon=_LOCK)

    store.save(
        token=token,
        owner_name=owner_name,
        default_region=region,
        metadata={"email": owner_email},
    )

    success(f"  {_CHECK} Credentials encrypted & stored")
    status_line(_SHIELD, "Encryption", "AES-256-GCM + HMAC-SHA256")
    status_line(_PKG, "Location", str(store.credentials_path))
    click.echo()

    flow_done(f"{_SPARK} Render login complete.")
    click.echo()
    next_steps([
        "aq deploy render               # Deploy your workspace",
        "aq provider status render      # Check connection status",
        "aq provider render env set     # Manage Render env vars",
    ])


# ═══════════════════════════════════════════════════════════════════════════
# aq provider logout render
# ═══════════════════════════════════════════════════════════════════════════

@provider_group.command("logout")
@click.argument("provider_name", type=click.Choice(["render"]))
def provider_logout(provider_name: str):
    """Logout from a cloud provider.

    Securely deletes stored credentials by overwriting with
    random data before unlinking.

    Example:
      aq provider logout render
    """
    from aquilia.providers.render.store import RenderCredentialStore

    store = RenderCredentialStore()

    if not store.is_configured():
        click.echo()
        info(f"  {_ARROW} No Render credentials found — nothing to do.")
        return

    click.echo()
    banner("Render · Logout", subtitle="Remove stored credentials", icon=_LOCK, fg="yellow")
    click.echo()

    detail_card(
        "Warning",
        [
            ("Action", "Securely erase credentials"),
            ("Method", "Overwrite with random data"),
            ("Reversible", "No"),
        ],
        icon=_WARN,
        fg="yellow",
    )
    click.echo()

    if not confirm("Remove Render credentials?", default=False):
        info(f"  {_ARROW} Cancelled.")
        return

    store.clear()
    click.echo()
    success(f"  {_CHECK} Render credentials securely removed.")


# ═══════════════════════════════════════════════════════════════════════════
# aq provider status render
# ═══════════════════════════════════════════════════════════════════════════

@provider_group.command("status")
@click.argument("provider_name", type=click.Choice(["render"]))
def provider_status(provider_name: str):
    """Show cloud provider authentication status.

    Displays credential status, workspace, and connectivity.

    Example:
      aq provider status render
    """
    from aquilia.providers.render.store import RenderCredentialStore
    from aquilia.providers.render.client import RenderClient
    from aquilia.faults.domains import ProviderAPIFault, ProviderCredentialFault

    store = RenderCredentialStore()
    status = store.status()

    click.echo()
    banner("Render · Status", subtitle="Provider authentication & connectivity", icon=_EYE, fg="cyan")
    click.echo()

    # ── Credentials card ─────────────────────────────────────────────
    cred_items = [
        ("Configured", click.style("yes", fg="green") if status["configured"] else click.style("no", fg="red")),
        ("Path", str(status["credentials_path"])),
        ("Workspace", status.get("owner_name") or "—"),
        ("Region", status.get("default_region", "oregon")),
    ]
    if status.get("stored_at"):
        import datetime
        stored = datetime.datetime.fromtimestamp(status["stored_at"])
        cred_items.append(("Stored at", stored.strftime("%Y-%m-%d %H:%M:%S")))

    detail_card("Credentials", cred_items, icon=_LOCK, fg="cyan")
    click.echo()

    if not status["configured"]:
        warning(f"  {_WARN}  Not authenticated.")
        click.echo()
        next_steps(["aq provider login render"])
        return

    # ── Connectivity ─────────────────────────────────────────────────
    phase_header(1, "Connectivity check", icon=_GLOBE)

    token = store.load()
    if not token:
        error(f"  {_CROSS} Could not decrypt stored credentials")
        click.echo()
        next_steps(["aq provider login render  # Re-authenticate"])
        return

    try:
        client = RenderClient(token=token)
        owners = client.list_owners()
        success(f"  {_CHECK} Connected to Render API")
        click.echo()

        if owners:
            detail_card(
                "Workspace",
                [
                    ("Name", owners[0].name),
                    ("Email", owners[0].email or "—"),
                ],
                icon=_CLOUD,
            )
            click.echo()

        # List services
        services = client.list_services()
        section(f"Services ({len(services)})")
        if services:
            for svc in services[:8]:
                svc_status = svc.status or "unknown"
                if svc_status in ("live", "deployed"):
                    st = click.style(f"● {svc_status}", fg="green")
                elif svc_status in ("deploying", "building"):
                    st = click.style(f"● {svc_status}", fg="cyan")
                elif svc_status in ("failed", "error"):
                    st = click.style(f"● {svc_status}", fg="red")
                else:
                    st = click.style(f"○ {svc_status}", fg="yellow")
                name = click.style(svc.name, fg="white", bold=True)
                click.echo(f"    {st}  {name}")
            if len(services) > 8:
                dim(f"    ... and {len(services) - 8} more")
        else:
            dim(f"    No services found.")
        click.echo()

    except ProviderAPIFault as e:
        error(f"  {_CROSS} API connection failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# aq provider render env — Env var management
# ═══════════════════════════════════════════════════════════════════════════

@render_group.group("env")
def render_env_group():
    """Manage Render service environment variables.

    Render env vars are set directly on services.  You need
    a service name (--service) to manage env vars.

    Examples:
      aq provider render env list --service my-api
      aq provider render env set DATABASE_URL "postgres://..." --service my-api
      aq provider render env delete DATABASE_URL --service my-api
    """
    pass


def _get_render_client():
    """Get an authenticated RenderClient or exit with error."""
    from aquilia.providers.render.store import RenderCredentialStore
    from aquilia.providers.render.client import RenderClient
    from aquilia.faults.domains import ProviderCredentialFault

    store = RenderCredentialStore()
    if not store.is_configured():
        error(f"  {_CROSS} Not authenticated. Run: aq provider login render")
        sys.exit(1)

    token = store.load()
    if not token:
        error(f"  {_CROSS} Could not decrypt credentials. Re-authenticate: aq provider login render")
        sys.exit(1)

    return RenderClient(token=token)


def _resolve_service_id(client, service_name: str) -> str:
    """Resolve a service name to its ID, or exit."""
    from aquilia.faults.domains import ProviderAPIFault

    try:
        svc = client.get_service_by_name(service_name)
        if not svc or not svc.id:
            error(f"  {_CROSS} Service '{service_name}' not found on Render.")
            sys.exit(1)
        return svc.id
    except ProviderAPIFault as e:
        error(f"  {_CROSS} Failed to find service: {e}")
        sys.exit(1)


@render_env_group.command("list")
@click.option("--service", "-s", required=True, help="Render service name")
def render_env_list(service: str):
    """List all environment variables for a Render service."""
    from aquilia.faults.domains import ProviderAPIFault

    client = _get_render_client()
    service_id = _resolve_service_id(client, service)

    try:
        env_vars = client.list_env_vars(service_id)
        if not env_vars:
            click.echo()
            info(f"  {_ARROW} No environment variables found for '{service}'.")
            return

        click.echo()
        banner(f"Env Vars · {service}", subtitle=f"{len(env_vars)} variable(s)", icon=_GEAR, fg="cyan")
        click.echo()

        for ev in env_vars:
            key = ev.get("key", "?")
            value = ev.get("value", "")
            # Redact long values
            if len(value) > 30:
                display = value[:12] + "···" + value[-4:]
            elif not value:
                display = click.style("(generated)", fg="yellow")
            else:
                display = value
            status_line(_KEY, key, display, label_fg="cyan")
        click.echo()
    except ProviderAPIFault as e:
        error(f"  {_CROSS} Failed to list env vars: {e}")
        sys.exit(1)


@render_env_group.command("set")
@click.argument("name")
@click.argument("value", required=False)
@click.option("--service", "-s", required=True, help="Render service name")
def render_env_set(name: str, value: Optional[str], service: str):
    """Create or update an environment variable on a Render service.

    If VALUE is omitted, you'll be prompted to enter it securely.

    Examples:
      aq provider render env set DATABASE_URL "postgres://..." --service my-api
      aq provider render env set API_KEY --service my-api
    """
    from aquilia.faults.domains import ProviderAPIFault

    client = _get_render_client()
    service_id = _resolve_service_id(client, service)

    if not value:
        value = ask_password(f"Value for '{name}'", confirm=False, min_length=1)
        if not value:
            error(f"  {_CROSS} No value provided.")
            sys.exit(1)

    try:
        # Get existing env vars, update/add, then PUT them all
        existing = client.list_env_vars(service_id)
        updated = False
        env_list = []
        for ev in existing:
            if ev.get("key") == name:
                env_list.append({"key": name, "value": value})
                updated = True
            else:
                env_list.append({"key": ev.get("key", ""), "value": ev.get("value", "")})
        if not updated:
            env_list.append({"key": name, "value": value})

        client.update_env_vars(service_id, env_list)
        success(f"  {_CHECK} Env var '{name}' saved on service '{service}'.")
    except ProviderAPIFault as e:
        error(f"  {_CROSS} Failed to set env var: {e}")
        sys.exit(1)


@render_env_group.command("delete")
@click.argument("name")
@click.option("--service", "-s", required=True, help="Render service name")
def render_env_delete(name: str, service: str):
    """Delete an environment variable from a Render service.

    Example:
      aq provider render env delete MY_VAR --service my-api
    """
    from aquilia.faults.domains import ProviderAPIFault

    client = _get_render_client()
    service_id = _resolve_service_id(client, service)

    if not confirm(f"Delete env var '{name}' from service '{service}'?", default=False):
        info("  Cancelled.")
        return

    try:
        client.delete_env_var(service_id, name)
        success(f"  {_CHECK} Env var '{name}' deleted from service '{service}'.")
    except ProviderAPIFault as e:
        error(f"  {_CROSS} Failed to delete env var: {e}")
        sys.exit(1)
