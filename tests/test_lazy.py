"""Self-check for aquilia.lazy. Run: python tests/test_lazy.py"""

import sys
import threading

sys.path.insert(0, __file__.rsplit("/tests/", 1)[0])

from aquilia.lazy import LazyModule, LazyObject, install_lazy_exports, lazy_attr, lazy_import, require


def test_lazy_module_defers():
    sys.modules.pop("uuid", None)
    proxy = lazy_import("uuid")
    assert "uuid" not in sys.modules, "import happened too early"
    assert "pending" in repr(proxy)
    assert proxy.uuid4() is not None
    assert "uuid" in sys.modules
    assert "resolved" in repr(proxy)
    assert proxy.__wrapped__ is sys.modules["uuid"]


def test_lazy_object_call_and_attr():
    counter = lazy_attr("collections", "Counter")
    assert "pending" in repr(counter)
    c = counter("aab")
    assert c["a"] == 2
    assert counter.__wrapped__ is __import__("collections").Counter
    assert bool(counter) is True
    assert "most_common" in dir(counter)


def test_lazy_object_missing_attr():
    bad = lazy_attr("collections", "NoSuchThing")
    try:
        bad()
    except AttributeError as e:
        assert "NoSuchThing" in str(e)
    else:
        raise AssertionError("expected AttributeError")


def test_lazy_module_missing():
    try:
        lazy_import("aquilia_does_not_exist_zzz").anything
    except ImportError as e:
        assert "aquilia_does_not_exist_zzz" in str(e)
    else:
        raise AssertionError("expected ImportError")


def test_install_lazy_exports_caches_in_namespace():
    ns = {"__all__": ["Counter"]}
    install_lazy_exports("collections", ns, {"Counter": ("collections", "Counter")})
    assert "Counter" not in ns
    got = ns["__getattr__"]("Counter")
    assert got is __import__("collections").Counter
    assert ns["Counter"] is got, "value must be cached into the namespace"
    assert "Counter" in ns["__dir__"]()


def test_install_lazy_exports_submodule_fallback():
    ns = {}
    install_lazy_exports("email", ns, {})
    mod = ns["__getattr__"]("utils")
    assert mod is sys.modules["email.utils"]


def test_install_lazy_exports_unknown_name():
    ns = {}
    install_lazy_exports("collections", ns, {})
    try:
        ns["__getattr__"]("definitely_not_here_zz")
    except AttributeError as e:
        assert "definitely_not_here_zz" in str(e)
    else:
        raise AssertionError("expected AttributeError")


def test_install_lazy_exports_bad_spec():
    try:
        install_lazy_exports("collections", {}, {"X": "not-a-tuple"})
    except TypeError as e:
        assert "tuple" in str(e)
    else:
        raise AssertionError("expected TypeError")


def test_install_lazy_exports_wrong_attr_message():
    ns = {}
    install_lazy_exports("collections", ns, {"X": ("collections", "NopeNope")})
    try:
        ns["__getattr__"]("X")
    except AttributeError as e:
        assert "NopeNope" in str(e) and "collections" in str(e)
    else:
        raise AssertionError("expected AttributeError")


def test_require_missing_gives_hint():
    try:
        require("zzz_not_installed", feature="Widget backend", extra="aquilia[widget]")
    except ImportError as e:
        assert "pip install aquilia[widget]" in str(e)
        assert "Widget backend" in str(e)
    else:
        raise AssertionError("expected ImportError")


def test_require_present():
    assert require("json", feature="x").dumps({"a": 1}) == '{"a": 1}'


def test_thread_safe_single_resolution():
    # All threads must observe the same object; a torn resolve would differ.
    proxy = LazyObject("collections", "OrderedDict")
    seen = []
    barrier = threading.Barrier(8)

    def worker():
        barrier.wait()
        seen.append(proxy.__wrapped__)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(seen) == 8 and len(set(map(id, seen))) == 1


def test_lazy_module_type():
    assert isinstance(lazy_import("json"), LazyModule)
    assert isinstance(lazy_attr("json", "dumps"), LazyObject)


def test_aquilia_exports_and_type_checking_sync():
    """Verify that aquilia.__init__ has 100% sync between _EXPORTS, _OPTIONAL_TARGETS, __all__, and TYPE_CHECKING."""
    import ast
    from pathlib import Path

    init_path = Path(__file__).resolve().parent.parent / "aquilia" / "__init__.py"
    tree = ast.parse(init_path.read_text(encoding="utf-8"))

    exports_names = set()
    optional_names = set()
    all_names = set()
    type_checking_names = set()

    for stmt in tree.body:
        if isinstance(stmt, (ast.Assign, ast.AnnAssign)):
            target = stmt.targets[0] if isinstance(stmt, ast.Assign) else stmt.target
            if isinstance(target, ast.Name):
                if target.id == "_EXPORTS":
                    for k in stmt.value.keys:
                        if isinstance(k, ast.Constant):
                            exports_names.add(k.value)
                elif target.id == "_OPTIONAL_TARGETS":
                    for k in stmt.value.keys:
                        if isinstance(k, ast.Constant):
                            optional_names.add(k.value)
                elif target.id == "__all__":
                    for elt in stmt.value.elts:
                        if isinstance(elt, ast.Constant):
                            all_names.add(elt.value)
        elif isinstance(stmt, ast.If):
            # Check for if TYPE_CHECKING:
            test = stmt.test
            is_type_checking = (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or (
                isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
            )
            if is_type_checking:
                for sub in stmt.body:
                    if isinstance(sub, ast.ImportFrom):
                        for alias in sub.names:
                            type_checking_names.add(alias.asname or alias.name)

    total_exports = exports_names | optional_names
    assert total_exports, "Expected _EXPORTS and _OPTIONAL_TARGETS to be non-empty"
    assert all_names == total_exports, f"Mismatch between exports and __all__: {all_names ^ total_exports}"
    assert type_checking_names == total_exports, f"Mismatch between exports and TYPE_CHECKING: {type_checking_names ^ total_exports}"


def test_aquilia_top_level_deferred_import():
    """Verify that 'import aquilia' remains lazy and does not drag heavy subsystems into sys.modules."""
    import subprocess

    cmd = [
        sys.executable,
        "-c",
        (
            "import sys\n"
            "import aquilia\n"
            "heavy = ['aquilia.admin', 'aquilia.models', 'aquilia.storage', 'aquilia.mail', 'aquilia.tasks', 'aquilia.sockets']\n"
            "loaded = [mod for mod in heavy if mod in sys.modules]\n"
            "assert not loaded, f'Heavy subsystems eagerly loaded: {loaded}'\n"
            "assert aquilia.Controller.__name__ == 'Controller'\n"
            "assert 'aquilia.controller' in sys.modules\n"
        ),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Lazy import failed:\n{res.stderr}"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("all lazy self-checks passed")

