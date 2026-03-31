from __future__ import annotations

from jinja2 import TemplateSyntaxError

from aquilia.templates import TemplateEngine, TemplateLoader


def _write_template(tmp_path, name: str, content: str) -> None:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


async def test_static_tag_renders_with_default_prefix(tmp_path):
    _write_template(
        tmp_path,
        "index.html",
        "<link rel='stylesheet' href=\"{% static 'css/styles.css' %}\">",
    )

    engine = TemplateEngine(TemplateLoader(search_paths=[str(tmp_path)]))
    html = await engine.render("index.html")

    assert "/static/css/styles.css" in html


async def test_static_tag_supports_assignment_form(tmp_path):
    _write_template(
        tmp_path,
        "index.html",
        "{% static 'js/app.js' as app_js %}<script src=\"{{ app_js }}\"></script>",
    )

    engine = TemplateEngine(TemplateLoader(search_paths=[str(tmp_path)]))
    html = await engine.render("index.html")

    assert "/static/js/app.js" in html


async def test_static_tag_uses_context_static_function(tmp_path):
    _write_template(
        tmp_path,
        "index.html",
        "<script src=\"{% static 'js/app.js' %}\"></script>",
    )

    engine = TemplateEngine(TemplateLoader(search_paths=[str(tmp_path)]))
    html = await engine.render("index.html", {"static": lambda path: f"/assets/{path}"})

    assert "/assets/js/app.js" in html


async def test_asset_tag_renders_with_static_prefix(tmp_path):
    _write_template(
        tmp_path,
        "index.html",
        "<script src=\"{% asset 'js/app.js' %}\"></script>",
    )

    engine = TemplateEngine(TemplateLoader(search_paths=[str(tmp_path)]))
    html = await engine.render("index.html")

    assert "/static/js/app.js" in html


async def test_media_tag_renders_with_media_prefix(tmp_path):
    _write_template(
        tmp_path,
        "index.html",
        "<img src=\"{% media 'avatars/me.png' %}\">",
    )

    engine = TemplateEngine(TemplateLoader(search_paths=[str(tmp_path)]))
    html = await engine.render("index.html")

    assert "/media/avatars/me.png" in html


async def test_media_tag_supports_assignment_form(tmp_path):
    _write_template(
        tmp_path,
        "index.html",
        "{% media 'avatars/me.png' as avatar_url %}<img src=\"{{ avatar_url }}\">",
    )

    engine = TemplateEngine(TemplateLoader(search_paths=[str(tmp_path)]))
    html = await engine.render("index.html")

    assert "/media/avatars/me.png" in html


async def test_static_tag_normalizes_unsafe_segments(tmp_path):
    _write_template(
        tmp_path,
        "index.html",
        "<link href=\"{% static '../css/./app.css' %}\">",
    )

    engine = TemplateEngine(TemplateLoader(search_paths=[str(tmp_path)]))
    html = await engine.render("index.html")

    assert "/static/css/app.css" in html


def test_static_tag_requires_argument(tmp_path):
    _write_template(tmp_path, "broken.html", "{% static %}")

    engine = TemplateEngine(TemplateLoader(search_paths=[str(tmp_path)]))

    try:
        engine.get_template("broken.html")
    except TemplateSyntaxError:
        pass
    else:
        raise AssertionError("Expected TemplateSyntaxError for malformed static tag")
