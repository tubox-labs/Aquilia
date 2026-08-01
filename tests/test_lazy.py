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


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("all lazy self-checks passed")
