"""Development server command."""

import sys
import os
import re
import importlib
from pathlib import Path
from typing import Optional, Dict, List, Set


def _validate_workspace_config(workspace_root: Path, verbose: bool = False) -> List[str]:
    """
    Validate that all modules registered in workspace.py/manifest.py actually exist.
    
    Checks:
    1. All registered module directories exist
    2. All manifest.py files can be found
    3. All controller/service imports are valid file paths
    4. No circular or missing dependencies
    
    Args:
        workspace_root: Path to workspace root
        verbose: Enable verbose output
        
    Returns:
        List of error messages (empty if validation passes)
    """
    errors = []
    
    try:
        # Check if workspace.py exists and is valid
        workspace_py = workspace_root / "workspace.py"
        if not workspace_py.exists():
            errors.append("workspace.py not found in workspace root")
            return errors
        
        # Read workspace.py to find registered modules
        try:
            workspace_content = workspace_py.read_text()
        except Exception as e:
            errors.append(f"Cannot read workspace.py: {str(e)[:60]}")
            return errors
        
        # Remove comment lines to avoid matching commented-out modules
        # This fixes the issue where default templates have commented-out 'auth' and 'users' modules
        clean_content = "\n".join(
            line for line in workspace_content.splitlines() 
            if not line.strip().startswith("#")
        )
        
        # Extract module names from workspace.py
        import re
        module_matches = re.findall(r'Module\("([^"]+)"', clean_content)
        module_names = list(set(module_matches))  # Deduplicate

        # The "starter" pseudo-module lives in workspace root (starter.py),
        # not under modules/.  Skip it during validation -- the server
        # auto-loads it via _load_starter_controller().
        module_names = [m for m in module_names if m != "starter"]
        
        if not module_names:
            # No modules registered - that's OK
            return errors
        
        modules_dir = workspace_root / "modules"
        if not modules_dir.exists():
            errors.append(f"modules directory not found at {modules_dir}")
            return errors
        
        # Validate each registered module
        for module_name in module_names:
            module_dir = modules_dir / module_name
            
            # Check if module directory exists
            if not module_dir.exists():
                errors.append(f"Module directory not found: modules/{module_name}")
                continue
            
            # Check if manifest.py exists
            manifest_path = module_dir / "manifest.py"
            if not manifest_path.exists():
                errors.append(f"Module manifest not found: modules/{module_name}/manifest.py")
                continue
            
            # Read manifest and validate imports
            try:
                manifest_content = manifest_path.read_text()
            except Exception as e:
                errors.append(f"Cannot read manifest for {module_name}: {str(e)[:50]}")
                continue
            
            # Extract controller and service imports (skip commented lines)
            # Format: "modules.mymodule.services:MymoduleService"
            imports = []
            for line in manifest_content.split('\n'):
                # Skip lines that are comments
                stripped = line.strip()
                if stripped.startswith('#'):
                    continue
                # Extract quoted strings with ':' pattern from this line
                line_imports = re.findall(r'"([^"]*:[\w]+)"', line)
                imports.extend(line_imports)
            
            # Validate each import can be resolved
            for import_path in imports:
                if ':' not in import_path:
                    continue
                
                module_path, class_name = import_path.split(':')
                
                # Convert module path to file path
                # Example: "modules.mymodule.services" -> "modules/mymodule/services.py"
                parts = module_path.split('.')
                
                # Skip 'modules' prefix and rebuild path starting from module_dir
                if parts[0] == 'modules' and len(parts) > 1:
                    parts = parts[1:]  # Remove 'modules' prefix
                
                # Skip module name itself (parts[0] is module_name)
                if parts and parts[0] == module_name:
                    parts = parts[1:]
                
                # Build file path
                try:
                    file_path = module_dir
                    for part in parts:
                        file_path = file_path / part
                    
                    file_path = file_path.with_suffix('.py')
                    
                    if not file_path.exists():
                        errors.append(
                            f"Import error in {module_name}: {import_path} "
                            f"(file not found: {file_path.relative_to(workspace_root)})"
                        )
                except Exception as e:
                    errors.append(
                        f"Cannot validate import {import_path} in {module_name}: {str(e)[:40]}"
                    )
    
    except Exception as e:
        errors.append(f"Unexpected error during validation: {str(e)[:60]}")
    
    return errors


def _discover_and_update_manifests(workspace_root: Path, verbose: bool = False) -> None:
    """
    Discover controllers, services, models, guards, pipes, interceptors
    in all modules and auto-update manifest.py files.
    
    Discovery pipeline (v2.1):
    1. ``AutoDiscoveryEngine`` (AST-based) -- primary scanner for all
       component kinds including models, guards, pipes, interceptors.
    2. ``EnhancedDiscovery`` -- fallback for controllers/services/sockets.
    3. Compares with manifest.py declarations.
    4. Automatically updates manifest.py with missing declarations.
    5. Updates workspace.py with module registrations.
    
    Args:
        workspace_root: Path to workspace root
        verbose: Enable verbose output
    """
    from aquilia.cli.discovery_utils import EnhancedDiscovery
    from pathlib import Path
    import sys
    
    workspace_root = Path(workspace_root)
    
    # Add workspace root to Python path for imports
    workspace_abs = workspace_root.resolve()
    if str(workspace_abs) not in sys.path:
        sys.path.insert(0, str(workspace_abs))
    
    modules_dir = workspace_root / "modules"
    if not modules_dir.exists():
        return
    
    # --- v2.1: Try AST-based auto-discovery engine first ---
    ast_results = {}
    try:
        from aquilia.discovery.engine import AutoDiscoveryEngine
        engine = AutoDiscoveryEngine(modules_dir)
        ast_results = engine.discover_all()
    except Exception:
        pass
    
    discovery = EnhancedDiscovery(verbose=verbose)
    
    # Track discovery results
    total_controllers = 0
    total_services = 0
    total_models = 0
    total_guards = 0
    total_pipes = 0
    total_interceptors = 0
    modules_updated = 0
    
    # Discover all modules with manifest.py
    for module_dir in modules_dir.iterdir():
        if not module_dir.is_dir() or module_dir.name.startswith('_'):
            continue
        
        manifest_path = module_dir / "manifest.py"
        if not manifest_path.exists():
            continue
        
        module_name = module_dir.name
        base_package = f"modules.{module_name}"
        
        if verbose:
            print(f"\n  Discovering module: {module_name}")
        
        try:
            # ── Discover via AST engine (models, guards, pipes, interceptors) ──
            ast_models = []
            ast_guards = []
            ast_pipes = []
            ast_interceptors = []
            
            if module_name in ast_results:
                result = ast_results[module_name]
                ast_models = [c.name for c in result.models]
                ast_guards = [c.name for c in result.guards]
                ast_pipes = [c.name for c in result.pipes]
                ast_interceptors = [c.name for c in result.interceptors]
                
                if verbose:
                    if ast_models:
                        print(f"    + Found {len(ast_models)} model(s): {', '.join(ast_models)}")
                    if ast_guards:
                        print(f"    + Found {len(ast_guards)} guard(s): {', '.join(ast_guards)}")
                    if ast_pipes:
                        print(f"    + Found {len(ast_pipes)} pipe(s): {', '.join(ast_pipes)}")
                    if ast_interceptors:
                        print(f"    + Found {len(ast_interceptors)} interceptor(s): {', '.join(ast_interceptors)}")
            
            total_models += len(ast_models)
            total_guards += len(ast_guards)
            total_pipes += len(ast_pipes)
            total_interceptors += len(ast_interceptors)
            
            # ── Discover controllers / services / sockets via EnhancedDiscovery ──
            result = discovery.discover_module_controllers_and_services(
                base_package, module_name
            )
            # Handle both 2-tuple (legacy) and 3-tuple (new) return values
            if len(result) == 3:
                discovered_controllers, discovered_services, discovered_sockets = result
            else:
                discovered_controllers, discovered_services = result
                discovered_sockets = []
            
            if verbose:
                if discovered_controllers:
                    print(f"    + Found {len(discovered_controllers)} controller(s)")
                if discovered_services:
                    print(f"    + Found {len(discovered_services)} service(s)")
                if discovered_sockets:
                    print(f"    + Found {len(discovered_sockets)} socket controller(s)")
            
            total_controllers += len(discovered_controllers)
            total_services += len(discovered_services)
            
            # Read manifest content
            try:
                manifest_content = manifest_path.read_text()
            except (OSError, IOError) as e:
                if verbose:
                    print(f"    !  Cannot read manifest: {str(e)[:60]}")
                continue
            
            # Clean and update manifest with properly classified items
            try:
                updated_content, services_added, controllers_added = discovery.clean_manifest_lists(
                    manifest_content,
                    discovered_controllers,
                    discovered_services,
                    module_dir=module_dir,  # Pass module path for validation
                    discovered_sockets=discovered_sockets,
                )
            except Exception as e:
                if verbose:
                    print(f"    !  Error cleaning manifest: {str(e)[:60]}")
                continue
            
            # ── v2.1: Inject models/guards/pipes/interceptors into manifest ──
            updated_content = _inject_component_list(
                updated_content, "models", ast_models
            )
            updated_content = _inject_component_list(
                updated_content, "guards", ast_guards
            )
            updated_content = _inject_component_list(
                updated_content, "pipes", ast_pipes
            )
            updated_content = _inject_component_list(
                updated_content, "interceptors", ast_interceptors
            )
            
            # Write updated manifest if there were changes
            if updated_content != manifest_content:
                try:
                    manifest_path.write_text(updated_content)
                    modules_updated += 1
                    if verbose:
                        total_changes = services_added + controllers_added
                        print(f"    + Updated manifest: {services_added} service(s), {controllers_added} controller(s) added")
                except (OSError, IOError) as e:
                    if verbose:
                        print(f"    !  Cannot write manifest: {str(e)[:60]}")
            elif verbose:
                print(f"    . Manifest already up-to-date")
                
        except Exception as e:
            if verbose:
                print(f"    !  Unexpected error processing {module_name}: {str(e)[:80]}")
    
    # Summary (v2.1)
    if verbose:
        print(f"\n  Discovery summary:")
        print(f"    Controllers: {total_controllers}  Services: {total_services}")
        print(f"    Models: {total_models}  Guards: {total_guards}")
        print(f"    Pipes: {total_pipes}  Interceptors: {total_interceptors}")
        print(f"    Modules updated: {modules_updated}")
    
    # After updating all manifests, update workspace.py with discovered configs
    try:
        from ..generators.workspace import WorkspaceGenerator
        
        generator = WorkspaceGenerator(
            name=workspace_root.name,
            path=workspace_root
        )
        
        # Re-discover with updated manifests to get all controllers/services
        discovered = generator._discover_modules()
        
        if discovered:
            workspace_py_path = workspace_root / "workspace.py"
            if workspace_py_path.exists():
                generator.update_workspace_config(workspace_py_path, discovered)
    
    except Exception as e:
        if verbose:
            print(f"  !  Failed to update workspace.py: {str(e)[:80]}")


def _inject_component_list(
    content: str,
    field_name: str,
    discovered_items: list,
) -> str:
    """
    Inject or update a component list (models, guards, pipes, interceptors)
    in a manifest.py content string.
    
    If the field already exists, merges new items into the existing list.
    If not present, does nothing (the user can add it when ready).
    
    Args:
        content: manifest.py text
        field_name: e.g. "models", "guards", "pipes", "interceptors"
        discovered_items: list of class names discovered by AST engine
    
    Returns:
        Updated content string
    """
    import re
    
    if not discovered_items:
        return content
    
    # Find existing field declaration: e.g. models=["Foo", "Bar"]
    pattern = rf'({field_name}\s*=\s*\[)(.*?)(\])'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        return content  # Field not declared -- user hasn't opted in
    
    # Parse existing items
    existing_items = re.findall(r'"([^"]+)"', match.group(2))
    
    # Merge (preserve order, add new at end)
    merged = list(existing_items)
    for item in discovered_items:
        if item not in merged:
            merged.append(item)
    
    if set(merged) == set(existing_items):
        return content  # No changes
    
    # Rebuild the list
    items_str = ", ".join(f'"{item}"' for item in merged)
    new_field = f'{field_name}=[{items_str}]'
    
    return content[:match.start()] + new_field + content[match.end():]


def _discover_and_display_routes(workspace_root: Path, verbose: bool = False) -> None:
    """
    Discover all modules and their routes before starting server.
    
    Args:
        workspace_root: Path to workspace root
        verbose: Enable verbose output
    """
    from aquilia.cli.discovery_utils import EnhancedDiscovery
    from pathlib import Path
    import sys
    
    workspace_root = Path(workspace_root)
    
    # Add workspace root to path
    workspace_abs = workspace_root.resolve()
    if str(workspace_abs) not in sys.path:
        sys.path.insert(0, str(workspace_abs))
    
    modules_dir = workspace_root / "modules"
    if not modules_dir.exists():
        return
    
    discovery = EnhancedDiscovery(verbose=False)
    
    # Collect all discovered modules with their controllers and services
    discovered_modules = {}
    
    # Discover all modules with manifest.py
    for module_dir in modules_dir.iterdir():
        if not module_dir.is_dir() or module_dir.name.startswith('_'):
            continue
            
        manifest_path = module_dir / 'manifest.py'
        if not manifest_path.exists():
            continue
            
        module_name = module_dir.name
        base_package = f"modules.{module_name}"
        
        try:
            # Use enhanced discovery
            result = discovery.discover_module_controllers_and_services(
                base_package, module_name
            )
            # Handle both 2-tuple (legacy) and 3-tuple (new) return values
            if len(result) == 3:
                discovered_controllers, discovered_services, discovered_sockets = result
            else:
                discovered_controllers, discovered_services = result
                discovered_sockets = []
            
            # Extract metadata from manifest
            manifest_content = manifest_path.read_text()
            import re
            version = re.search(r'version="([^"]+)"', manifest_content)
            description = re.search(r'description="([^"]+)"', manifest_content)
            route_prefix = re.search(r'route_prefix="([^"]+)"', manifest_content)
            tags = re.findall(r'"([^"]+)"', re.search(r'tags=\[(.*?)\]', manifest_content).group(1) if re.search(r'tags=\[(.*?)\]', manifest_content) else '')
            
            discovered_modules[module_name] = {
                'name': module_name,
                'version': version.group(1) if version else '0.1.0',
                'description': description.group(1) if description else f'{module_name.capitalize()} module',
                'route_prefix': route_prefix.group(1) if route_prefix else f'/{module_name}',
                'tags': tags or [module_name, 'core'],
                'controllers_list': [c["path"] if isinstance(c, dict) else c for c in discovered_controllers],
                'services_list': [s["path"] if isinstance(s, dict) else s for s in discovered_services],
                'sockets_list': [
                    {'path': s['path'] if isinstance(s, dict) else s,
                     'namespace': s.get('metadata', {}).get('namespace', '') if isinstance(s, dict) else ''}
                    for s in discovered_sockets
                ],
                'controllers_count': len(discovered_controllers),
                'services_count': len(discovered_services),
                'sockets_count': len(discovered_sockets),
                'has_controllers': len(discovered_controllers) > 0,
                'has_services': len(discovered_services) > 0,
                'has_sockets': len(discovered_sockets) > 0,
            }
            
            if verbose:
                print(f"\n  Discovering module: {module_name}")
                if discovered_controllers:
                    print(f"  + Found {len(discovered_controllers)} controller(s)")
                if discovered_services:
                    print(f"  + Found {len(discovered_services)} service(s)")
            
        except Exception as e:
            if verbose:
                print(f"  !  Error discovering {module_name}: {str(e)[:80]}")
    
    if not discovered_modules:
        return
    
    # Now display the results
    from ..generators.workspace import WorkspaceGenerator
    
    try:
        generator = WorkspaceGenerator(
            name=workspace_root.name,
            path=workspace_root
        )
        
        sorted_names = generator._resolve_dependencies(discovered_modules)
        validation = generator._validate_modules(discovered_modules)
    except Exception:
        sorted_names = sorted(discovered_modules.keys())
        validation = {'valid': True, 'warnings': [], 'errors': []}
    
    print("\n  Discovered Routes & Modules")
    print("=" * 70)
    
    # Display module table with controller details
    print(f"\n{'Module':<20} {'Route Prefix':<25} {'Controllers':<12} {'Services':<10} {'Sockets':<10}")
    print(f"{'-'*20} {'-'*25} {'-'*12} {'-'*10} {'-'*10}")
    
    for mod_name in sorted_names:
        if mod_name not in discovered_modules:
            continue
        mod = discovered_modules[mod_name]
        route = mod['route_prefix']
        controllers_count = mod.get('controllers_count', 0)
        services_count = mod.get('services_count', 0)
        sockets_count = mod.get('sockets_count', 0)
        print(f"{mod_name:<20} {route:<25} {controllers_count:<12} {services_count:<10} {sockets_count:<10}")
    
    # Show detailed controller information
    total_controllers = sum(mod.get('controllers_count', 0) for mod in discovered_modules.values())
    if total_controllers > 0:
        print(f"\n  Controller Details:")
        for mod_name in sorted_names:
            if mod_name not in discovered_modules:
                continue
            mod = discovered_modules[mod_name]
            controllers_list = mod.get('controllers_list', [])
            if controllers_list:
                print(f"  {mod_name}:")
                for controller in controllers_list:
                    # Extract controller class name
                    if ':' in controller:
                        controller_class = controller.split(':')[1]
                    else:
                        controller_class = controller.split('.')[-1]
                    print(f"    • {controller_class}")
    
    # Show WebSocket controller details
    total_sockets = sum(mod.get('sockets_count', 0) for mod in discovered_modules.values())
    if total_sockets > 0:
        print(f"\n  WebSocket Controllers:")
        for mod_name in sorted_names:
            if mod_name not in discovered_modules:
                continue
            mod = discovered_modules[mod_name]
            sockets_list = mod.get('sockets_list', [])
            if sockets_list:
                print(f"  {mod_name}:")
                for sock in sockets_list:
                    sock_path = sock['path'] if isinstance(sock, dict) else sock
                    namespace = sock.get('namespace', '') if isinstance(sock, dict) else ''
                    if ':' in sock_path:
                        sock_class = sock_path.split(':')[1]
                    else:
                        sock_class = sock_path.split('.')[-1]
                    if namespace:
                        print(f"    -> {sock_class} -> {namespace}")
                    else:
                        print(f"    -> {sock_class}")
    
    print()
    
    # Summary
    print(f"\n  Summary:")
    with_services = sum(1 for m in discovered_modules.values() if m['has_services'])
    with_controllers = sum(1 for m in discovered_modules.values() if m['has_controllers'])
    with_sockets = sum(1 for m in discovered_modules.values() if m.get('has_sockets', False))
    
    total_services = sum(m.get('services_count', 0) for m in discovered_modules.values())
    total_controllers = sum(m.get('controllers_count', 0) for m in discovered_modules.values())
    total_sockets = sum(m.get('sockets_count', 0) for m in discovered_modules.values())
    
    print(f"  Total Modules: {len(discovered_modules)}")
    print(f"  With Services: {with_services} ({total_services} total)")
    print(f"  With Controllers: {with_controllers} ({total_controllers} total)")
    if total_sockets > 0:
        print(f"  With Sockets: {with_sockets} ({total_sockets} total)")
    
    # Validation status
    if validation['errors']:
        print(f"\n  Validation Errors: {len(validation['errors'])}")
        for error in validation['errors']:
            print(f"    - {error}")
    elif validation['warnings']:
        print(f"\n  Validation Warnings: {len(validation['warnings'])}")
        for warning in validation['warnings'][:3]:
            print(f"    - {warning}")
    else:
        print(f"\n  All modules validated!")
    
    print(f"{'='*70}\n")


def _write_discovery_report(workspace_root: Path, discovered: Dict, sorted_names: List[str], validation: Dict) -> None:
    """
    Write discovery report to routes.md file.
    
    Args:
        workspace_root: Path to workspace root
        discovered: Dictionary of discovered modules
        sorted_names: Module names in load order
        validation: Validation results
    """
    try:
        report_lines = [
            "# Auto-Discovered Routes & Modules\n",
            f"*Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n",
            "\n## Module Routes\n",
        ]
        
        # Module table
        report_lines.append("| Module | Route Prefix | Version | Tags | Components |\n")
        report_lines.append("|--------|--------------|---------|------|------------|\n")
        
        for mod_name in sorted_names:
            mod = discovered[mod_name]
            tags = ", ".join(mod.get('tags', [])[:3]) if mod.get('tags') else "-"
            components = []
            if mod['has_services']:
                components.append("Services")
            if mod['has_controllers']:
                components.append("Controllers")
            if mod['has_middleware']:
                components.append("Middleware")
            comp_str = ", ".join(components) if components else "-"
            
            report_lines.append(
                f"| {mod_name} | `{mod['route_prefix']}` | {mod['version']} | {tags} | {comp_str} |\n"
            )
        
        # Dependencies section
        has_deps = any(mod.get('depends_on') for mod in discovered.values())
        if has_deps:
            report_lines.append("\n## Dependencies\n\n")
            for mod_name in sorted_names:
                mod = discovered[mod_name]
                deps = mod.get('depends_on', [])
                if deps:
                    deps_str = " → ".join(deps)
                    report_lines.append(f"- **{mod_name}** depends on: {deps_str}\n")
                else:
                    report_lines.append(f"- **{mod_name}** (no dependencies)\n")
        
        # Statistics
        with_services = sum(1 for m in discovered.values() if m['has_services'])
        with_controllers = sum(1 for m in discovered.values() if m['has_controllers'])
        with_middleware = sum(1 for m in discovered.values() if m['has_middleware'])
        
        report_lines.append("\n## Statistics\n\n")
        report_lines.append(f"- **Total Modules**: {len(discovered)}\n")
        report_lines.append(f"- **With Services**: {with_services}\n")
        report_lines.append(f"- **With Controllers**: {with_controllers}\n")
        report_lines.append(f"- **With Middleware**: {with_middleware}\n")
        report_lines.append(f"- **Load Order**: {' → '.join(sorted_names)}\n")
        
        # Validation section
        report_lines.append("\n## Validation\n\n")
        if validation['errors']:
            report_lines.append(f"**Errors**: {len(validation['errors'])}\n\n")
            for error in validation['errors']:
                report_lines.append(f"- {error}\n")
        elif validation['warnings']:
            report_lines.append(f"**Warnings**: {len(validation['warnings'])}\n\n")
            for warning in validation['warnings']:
                report_lines.append(f"- {warning}\n")
        else:
            report_lines.append("**Status**: All modules validated!\n")
        
        # Write report
        report_file = workspace_root / "ROUTES.md"
        report_file.write_text("".join(report_lines))
    
    except Exception:
        # Silently fail - don't interrupt server startup
        pass



def run_dev_server(
    mode: str = 'dev',
    host: str = '127.0.0.1',
    port: int = 8000,
    reload: bool = True,
    verbose: bool = False,
) -> None:
    """
    Start development server using uvicorn.
    
    Args:
        mode: Runtime mode (dev, test)
        host: Server host
        port: Server port
        reload: Enable hot-reload
        verbose: Enable verbose output
    """
    try:
        import uvicorn
    except ImportError:
        raise ImportError(
            "uvicorn is required to run the development server.\n"
            "Install it with: pip install uvicorn\n"
            "Or with extras: pip install 'aquilia[server]'"
        )
    
    workspace_root = Path.cwd()
    
    # Add workspace root to Python path for imports
    if str(workspace_root) not in sys.path:
        sys.path.insert(0, str(workspace_root))
    
    # Set environment variables
    os.environ['AQUILIA_ENV'] = mode
    os.environ['AQUILIA_WORKSPACE'] = str(workspace_root)
    
    # ===== AUTO-DISCOVER & UPDATE MANIFESTS FIRST =====
    # This must happen BEFORE creating the app so that workspace.py is up-to-date
    print("  Auto-discovering controllers and services...")
    _discover_and_update_manifests(workspace_root, verbose)
    
    # VALIDATE WORKSPACE CONFIGURATION BEFORE PROCEEDING
    print("  Validating workspace configuration...")
    validation_errors = _validate_workspace_config(workspace_root, verbose)
    if validation_errors:
        print("\n  Workspace validation failed! Fix these issues before starting the server:\n")
        for error in validation_errors:
            print(f"    - {error}")
        print()
        return
    
    # ===== BUILD PIPELINE -- Compile, check, and bundle before serving =====
    print("  Running build pipeline...")
    try:
        from aquilia.build import AquiliaBuildPipeline
        build_result = AquiliaBuildPipeline.build(
            workspace_root=str(workspace_root),
            mode=mode,
            verbose=verbose,
        )

        if not build_result.success:
            print("\n  Build FAILED -- server will not start.\n")
            for err in build_result.errors:
                print(f"  {err}")
            if build_result.warnings:
                print()
                for warn in build_result.warnings:
                    print(f"  {warn}")
            print(f"\n  Build failed in {build_result.total_ms:.0f}ms")
            print("  Fix the errors above and try again.\n")
            return

        # Report build success
        print(f"  {build_result.summary()}")

        if build_result.warnings and verbose:
            for warn in build_result.warnings:
                print(f"  {warn}")

    except ImportError:
        if verbose:
            print("  Build pipeline not available, proceeding without pre-compilation")
    except Exception as e:
        if verbose:
            print(f"  Build pipeline error: {e}, proceeding without pre-compilation")
    
    # Strategy 1: Check for workspace configuration (workspace.py) and auto-create app
    workspace_config = workspace_root / "workspace.py"
    if workspace_config.exists():
        if verbose:
            print("  Found workspace configuration: workspace.py")
        
        # Create a runtime app loader
        app_module = _create_workspace_app(workspace_root, mode, verbose)
        
        if verbose:
            print(f"  Using workspace-generated app")
    else:
        # Strategy 2: Look for existing app module
        app_module = _find_app_module(workspace_root, verbose)
        
        if not app_module:
            raise ValueError(
                "Could not find ASGI application.\n\n"
                "Expected one of:\n"
                "  1. Workspace configuration: workspace.py (recommended)\n"
                "  2. main.py with 'app' variable\n"
                "  3. app.py with 'app' variable\n"
                "  4. server.py with 'app' or 'server' variable\n\n"
                "For workspace-based projects:\n"
                "  Run: aq init workspace <name>\n"
                "  Then: aq add module <module_name>\n\n"
                "For standalone apps, create main.py:\n"
                "  from aquilia import AquiliaServer\n"
                "  from aquilia.manifest import AppManifest\n\n"
                "  class MyAppManifest(AppManifest):\n"
                "      name = 'myapp'\n"
                "      version = '1.0.0'\n"
                "      controllers = []\n\n"
                "  server = AquiliaServer(manifests=[MyAppManifest])\n"
                "  app = server.app\n"
            )
    
    if verbose:
        print(f"\n  Starting Aquilia development server...")
        print(f"  Mode: {mode}")
        print(f"  Host: {host}:{port}")
        print(f"  Reload: {reload}")
        print(f"  App: {app_module}")
        print()
    
    # Discover and display all routes before starting server
    _discover_and_display_routes(workspace_root, verbose)
    
    # Configure uvicorn
    uvicorn.run(
        app=app_module,
        host=host,
        port=port,
        reload=reload,
        reload_dirs=[str(workspace_root)] if reload else None,
        log_level="debug" if verbose else "info",
        access_log=True,
        use_colors=True,
    )
    
    # server = uvicorn.Server(config)
    # server.run()


def _create_workspace_app(workspace_root: Path, mode: str, verbose: bool = False) -> str:
    """
    Create an ASGI app from workspace configuration.
    
    This generates a runtime app loader module that:
    1. Loads the workspace configuration (workspace.py)
    2. Discovers and loads module manifests (manifest.py)
    3. Creates AquiliaServer with all manifests
    4. Returns the ASGI app
    
    Args:
        workspace_root: Path to workspace root
        mode: Runtime mode (dev, test, prod)
        verbose: Enable verbose output
        
    Returns:
        Module path (e.g., "runtime.app:app")
    """
    runtime_dir = workspace_root / "runtime"
    runtime_dir.mkdir(exist_ok=True)
    
    # Create runtime app loader
    app_file = runtime_dir / "app.py"
    
    # Generate the app loader code
    app_code = _generate_workspace_app_code(workspace_root, mode, verbose)
    
    # Write the app file
    app_file.write_text(app_code)
    
    if verbose:
        print(f"  Generated runtime app: {app_file}")
    
    # Return the module path
    return "runtime.app:app"


def _generate_workspace_app_code(workspace_root: Path, mode: str, verbose: bool = False) -> str:
    """
    Generate the ASGI application entrypoint for the workspace.

    Architecture (v2):
    1. Set up sys.path and environment variables (AQUILIA_ENV, AQUILIA_WORKSPACE)
    2. Configure structured logging matching the requested mode
    3. Load workspace.py via ConfigLoader.load() -- the single source of truth
    4. Dynamically discover and import module manifests from modules/*/manifest.py
    5. Resolve RegistryMode from the workspace runtime config
    6. Construct AquiliaServer with the full manifest list and config
    7. Export ``app`` (ASGI callable) and ``server`` (AquiliaServer instance)

    The generated code is self-contained, reload-safe (no side-effects at
    import time that break ``uvicorn --reload``), and compatible with all
    ASGI servers (uvicorn, hypercorn, granian, daphne, gunicorn+uvicorn).

    Returns:
        Python source code as string
    """
    from datetime import datetime
    import re

    # ── Introspect workspace.py ──────────────────────────────────────
    workspace_file = workspace_root / "workspace.py"
    workspace_content = workspace_file.read_text()

    # Workspace name
    name_match = re.search(r'Workspace\(\s*(?:name\s*=\s*)?["\']([^"\']+)["\']', workspace_content)
    workspace_name = name_match.group(1) if name_match else "aquilia-app"

    # Strip comments before extracting modules to avoid commented-out matches
    clean_lines = [
        line for line in workspace_content.splitlines()
        if not line.strip().startswith("#")
    ]
    clean_content = "\n".join(clean_lines)

    # Extract module names from .module(Module("name" ...))
    modules = re.findall(
        r'\.module\(\s*Module\(\s*["\']([^"\']+)["\']', clean_content
    )
    # Deduplicate while preserving order
    seen: set = set()
    modules = [m for m in modules if m not in seen and not seen.add(m)]  # type: ignore[func-returns-value]

    # The starter pseudo-module lives at workspace root, not under modules/
    modules = [m for m in modules if m != "starter"]

    if verbose:
        print(f"  Discovered modules: {', '.join(modules) or '(none)'}")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── Build import block for known modules ─────────────────────────
    manifest_imports = ""
    manifest_vars: list = []
    for mod in modules:
        var = f"{mod}_manifest"
        manifest_imports += (
            f"from modules.{mod}.manifest import manifest as {var}\n"
        )
        manifest_vars.append(var)

    manifests_list = ", ".join(manifest_vars)

    # Also build a dynamic fallback that picks up any *new* modules the
    # user may have added since the last ``aq run`` without restarting.
    known_set_literal = ", ".join(f'"{m}"' for m in modules) if modules else ""

    code = f'''\
"""
Aquilia ASGI Runtime -- {workspace_name}
{"=" * (23 + len(workspace_name))}

Auto-generated by ``aq run``.  DO NOT EDIT -- regenerated on every launch.

Timestamp : {timestamp}
Workspace : {workspace_name}
Mode      : {mode}
Modules   : {len(modules)} ({", ".join(modules) or "none"})

Usage
-----
Development  : aq run
Production   : uvicorn runtime.app:app --host 0.0.0.0 --port 8000 --workers 4
Gunicorn     : gunicorn runtime.app:app -k uvicorn.workers.UvicornWorker -w 4
Hypercorn    : hypercorn runtime.app:app --bind 0.0.0.0:8000
Docker       : CMD ["uvicorn", "runtime.app:app", "--host", "0.0.0.0"]
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# ────────────────────────────────────────────────────────────────────────
# 1. Path & environment bootstrap
# ────────────────────────────────────────────────────────────────────────
_WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))

os.environ.setdefault("AQUILIA_ENV", "{mode}")
os.environ.setdefault("AQUILIA_WORKSPACE", str(_WORKSPACE_ROOT))

# ────────────────────────────────────────────────────────────────────────
# 2. Logging -- structured, mode-aware
# ────────────────────────────────────────────────────────────────────────
_LOG_LEVEL = logging.DEBUG if "{mode}" == "dev" else logging.INFO
_LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s -- %(message)s"
    if "{mode}" == "prod"
    else "%(levelname)-8s | %(name)s -- %(message)s"
)
logging.basicConfig(level=_LOG_LEVEL, format=_LOG_FORMAT, force=True)

# Silence noisy third-party loggers in dev mode
for _noisy in ("aiosqlite", "asyncio", "urllib3", "httpcore", "httpx",
               "watchfiles", "uvicorn.error"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

_logger = logging.getLogger("aquilia.runtime")

# ────────────────────────────────────────────────────────────────────────
# 3. Configuration -- single source of truth from workspace.py
# ────────────────────────────────────────────────────────────────────────
from aquilia.config import ConfigLoader

config = ConfigLoader.load(
    paths=["workspace.py"],
    overrides={{
        "mode": "{mode}",
        "debug": {"True" if mode == "dev" else "False"},
    }},
)

# Ensure ``apps`` namespace exists for every known module
if "apps" not in config.config_data:
    config.config_data["apps"] = {{}}
for _mod_name in [{known_set_literal}]:
    config.config_data["apps"].setdefault(_mod_name, {{}})

config._build_apps_namespace()

# ────────────────────────────────────────────────────────────────────────
# 4. Manifest discovery
#    Static imports for known modules (fast path) + dynamic fallback
#    for modules added after the last ``aq run``.
# ────────────────────────────────────────────────────────────────────────
{manifest_imports}
_manifests: list = [{manifests_list}]
_known_modules: set = {{{known_set_literal}}}

# Dynamic discovery -- pick up any *new* modules transparently
_modules_dir = _WORKSPACE_ROOT / "modules"
if _modules_dir.is_dir():
    for _pkg in sorted(_modules_dir.iterdir()):
        if (
            _pkg.is_dir()
            and _pkg.name not in _known_modules
            and (_pkg / "manifest.py").exists()
            and not _pkg.name.startswith(("_", "."))
        ):
            try:
                import importlib
                _mod = importlib.import_module(f"modules.{{_pkg.name}}.manifest")
                _m = getattr(_mod, "manifest", None)
                if _m is not None:
                    _manifests.append(_m)
                    config.config_data["apps"].setdefault(_pkg.name, {{}})
                    _logger.info("Auto-discovered module: %s", _pkg.name)
            except Exception as _exc:
                _logger.warning(
                    "Could not import manifest for module %s: %s",
                    _pkg.name, _exc,
                )

    # Rebuild apps namespace after potential new modules
    config._build_apps_namespace()

# ────────────────────────────────────────────────────────────────────────
# 5. Server construction
# ────────────────────────────────────────────────────────────────────────
from aquilia import AquiliaServer
from aquilia.aquilary.core import RegistryMode

_MODE_MAP = {{"dev": RegistryMode.DEV, "prod": RegistryMode.PROD, "test": RegistryMode.TEST}}
_registry_mode = _MODE_MAP.get("{mode}", RegistryMode.DEV)

server = AquiliaServer(
    manifests=_manifests,
    config=config,
    mode=_registry_mode,
)

# ────────────────────────────────────────────────────────────────────────
# 6. ASGI application export
# ────────────────────────────────────────────────────────────────────────
app = server.app

_logger.info(
    "Aquilia runtime ready  ·  workspace=%s  ·  mode=%s  ·  modules=%d",
    "{workspace_name}", "{mode}", len(_manifests),
)
'''

    return code


def _find_app_module(workspace_root: Path, verbose: bool = False) -> Optional[str]:
    """
    Find the ASGI app module.
    
    Looks for:
    1. main.py with 'app' or 'application'
    2. app.py with 'app' or 'application'  
    3. server.py with 'app' or 'server'
    
    Returns:
        Module path (e.g., "main:app") or None if not found
    """
    candidates = [
        ("main.py", ["app", "application", "server"]),
        ("app.py", ["app", "application", "server"]),
        ("server.py", ["app", "server", "application"]),
        ("asgi.py", ["app", "application"]),
    ]
    
    for filename, var_names in candidates:
        file_path = workspace_root / filename
        if file_path.exists():
            # Try to detect which variable is defined
            content = file_path.read_text()
            
            for var_name in var_names:
                # Look for variable assignments
                if f"{var_name} =" in content or f"{var_name}=" in content:
                    module_name = filename.replace(".py", "")
                    app_ref = f"{module_name}:{var_name}"
                    
                    if verbose:
                        print(f"Found app: {app_ref}")
                    
                    return app_ref
    
    return None
