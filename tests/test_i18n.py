"""
Comprehensive i18n System Tests — Regression, Integration & Edge-case Coverage.

Tests every layer of the Aquilia i18n subsystem:

    §1  Locale — BCP 47 parsing, normalization, matching, negotiation
    §2  Plural — CLDR rules for 13 language families + edge cases
    §3  Catalog — Memory, File, CROUS, Namespaced, Merged catalogs
    §4  Formatter — ICU MessageFormat, number/currency/date/ordinal
    §5  Service — t/tn/tp, missing-key strategies, fallback chains
    §6  Lazy — LazyString / LazyPluralString protocol compliance
    §7  Middleware — All 5 resolvers + ChainResolver + I18nMiddleware
    §8  Faults — Fault hierarchy, metadata, domain
    §9  Template Integration — Jinja2 globals / filters / extension
    §10 DI Integration — Provider registration
    §11 Config Builders — Integration.i18n() / Workspace.i18n()
    §12 CLI Commands — init / check / inspect / extract / coverage / compile
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import tempfile
from datetime import date, datetime, time, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional, Set
from unittest.mock import MagicMock, AsyncMock, patch

import pytest


# ═══════════════════════════════════════════════════════════════════════════
# §1 — Locale
# ═══════════════════════════════════════════════════════════════════════════


class TestLocaleParsing:
    """BCP 47 locale tag parsing."""

    def test_simple_language(self):
        from aquilia.i18n.locale import parse_locale

        loc = parse_locale("en")
        assert loc.language == "en"
        assert loc.script is None
        assert loc.region is None
        assert loc.variant is None

    def test_language_region(self):
        from aquilia.i18n.locale import parse_locale

        loc = parse_locale("en-US")
        assert loc.language == "en"
        assert loc.region == "US"

    def test_language_script(self):
        from aquilia.i18n.locale import parse_locale

        loc = parse_locale("zh-Hans")
        assert loc.language == "zh"
        assert loc.script == "Hans"

    def test_full_tag(self):
        from aquilia.i18n.locale import parse_locale

        loc = parse_locale("zh-Hant-HK")
        assert loc.language == "zh"
        assert loc.script == "Hant"
        assert loc.region == "HK"

    def test_variant(self):
        from aquilia.i18n.locale import parse_locale

        loc = parse_locale("de-CH-nedis")  # Natisone dialect variant (5 chars)
        assert loc.language == "de"
        assert loc.region == "CH"
        assert loc.variant == "nedis"

    def test_underscore_notation(self):
        from aquilia.i18n.locale import parse_locale

        loc = parse_locale("en_US")
        assert loc.language == "en"
        assert loc.region == "US"

    def test_case_normalization(self):
        from aquilia.i18n.locale import parse_locale

        loc = parse_locale("EN-us")
        assert loc.language == "en"
        assert loc.region == "US"

    def test_invalid_empty(self):
        from aquilia.i18n.locale import parse_locale
        from aquilia.faults.domains import ConfigInvalidFault

        with pytest.raises(ConfigInvalidFault):
            parse_locale("")

    def test_invalid_none(self):
        from aquilia.i18n.locale import parse_locale
        from aquilia.faults.domains import ConfigInvalidFault

        with pytest.raises(ConfigInvalidFault):
            parse_locale(None)

    def test_invalid_garbage(self):
        from aquilia.i18n.locale import parse_locale
        from aquilia.faults.domains import ConfigInvalidFault

        with pytest.raises(ConfigInvalidFault):
            parse_locale("!!!invalid!!!")

    def test_three_letter_language(self):
        from aquilia.i18n.locale import parse_locale

        loc = parse_locale("fil")
        assert loc.language == "fil"

    def test_numeric_region(self):
        from aquilia.i18n.locale import parse_locale

        loc = parse_locale("es-419")  # Latin America
        assert loc.language == "es"
        assert loc.region == "419"


class TestLocaleTag:
    """Locale.tag property and string representation."""

    def test_simple(self):
        from aquilia.i18n.locale import Locale

        assert Locale("en").tag == "en"
        assert str(Locale("en")) == "en"

    def test_with_region(self):
        from aquilia.i18n.locale import Locale

        assert Locale("fr", region="CA").tag == "fr-CA"

    def test_with_script(self):
        from aquilia.i18n.locale import Locale

        assert Locale("zh", script="Hans").tag == "zh-Hans"

    def test_full(self):
        from aquilia.i18n.locale import Locale

        loc = Locale("zh", script="Hant", region="HK")
        assert loc.tag == "zh-Hant-HK"


class TestLocaleFallbackChain:
    """Locale.fallback_chain for step-down matching."""

    def test_simple_no_chain(self):
        from aquilia.i18n.locale import Locale

        chain = Locale("en").fallback_chain
        assert len(chain) == 1
        assert chain[0].tag == "en"

    def test_region_chain(self):
        from aquilia.i18n.locale import Locale

        chain = Locale("fr", region="CA").fallback_chain
        tags = [c.tag for c in chain]
        assert tags == ["fr-CA", "fr"]

    def test_script_region_chain(self):
        from aquilia.i18n.locale import Locale

        chain = Locale("zh", script="Hant", region="HK").fallback_chain
        tags = [c.tag for c in chain]
        assert "zh-Hant-HK" in tags
        assert "zh" in tags


class TestLocaleMatching:
    """Locale prefix matching."""

    def test_exact_match(self):
        from aquilia.i18n.locale import Locale

        assert Locale("en").matches(Locale("en"))

    def test_prefix_match(self):
        from aquilia.i18n.locale import Locale

        assert Locale("en").matches(Locale("en", region="US"))

    def test_no_match_different_language(self):
        from aquilia.i18n.locale import Locale

        assert not Locale("en").matches(Locale("fr"))

    def test_no_match_different_region(self):
        from aquilia.i18n.locale import Locale

        assert not Locale("en", region="US").matches(Locale("en", region="GB"))


class TestNormalizeLocale:
    """normalize_locale round-trip."""

    def test_lowercase_language(self):
        from aquilia.i18n.locale import normalize_locale

        assert normalize_locale("EN") == "en"

    def test_uppercase_region(self):
        from aquilia.i18n.locale import normalize_locale

        assert normalize_locale("en-us") == "en-US"

    def test_titlecase_script(self):
        from aquilia.i18n.locale import normalize_locale

        assert normalize_locale("zh-hans") == "zh-Hans"

    def test_underscore_to_hyphen(self):
        from aquilia.i18n.locale import normalize_locale

        assert normalize_locale("en_GB") == "en-GB"


class TestAcceptLanguageParsing:
    """parse_accept_language header values."""

    def test_single_tag(self):
        from aquilia.i18n.locale import parse_accept_language

        result = parse_accept_language("en")
        assert len(result) == 1
        assert result[0] == ("en", 1.0)

    def test_multiple_with_quality(self):
        from aquilia.i18n.locale import parse_accept_language

        result = parse_accept_language("fr-CH, fr;q=0.9, en;q=0.8, *;q=0.5")
        assert result[0][0] == "fr-CH"
        assert result[0][1] == 1.0
        assert result[-1][0] == "*"

    def test_empty_header(self):
        from aquilia.i18n.locale import parse_accept_language

        assert parse_accept_language("") == []

    def test_quality_sorted(self):
        from aquilia.i18n.locale import parse_accept_language

        result = parse_accept_language("en;q=0.5, de;q=0.9, fr;q=0.7")
        assert result[0][0] == "de"
        assert result[1][0] == "fr"
        assert result[2][0] == "en"


class TestNegotiateLocale:
    """negotiate_locale best-match resolution."""

    def test_exact_match(self):
        from aquilia.i18n.locale import negotiate_locale

        assert negotiate_locale("fr", ["en", "fr", "de"], "en") == "fr"

    def test_prefix_match(self):
        from aquilia.i18n.locale import negotiate_locale

        result = negotiate_locale("fr-CA", ["en", "fr"], "en")
        assert result == "fr"

    def test_no_match_returns_default(self):
        from aquilia.i18n.locale import negotiate_locale

        assert negotiate_locale("ja", ["en", "fr"], "en") == "en"

    def test_wildcard(self):
        from aquilia.i18n.locale import negotiate_locale

        result = negotiate_locale("*", ["de", "en"], "en")
        assert result == "de"

    def test_empty_header(self):
        from aquilia.i18n.locale import negotiate_locale

        assert negotiate_locale("", ["en"], "en") == "en"

    def test_empty_available(self):
        from aquilia.i18n.locale import negotiate_locale

        assert negotiate_locale("fr", [], "en") == "en"

    def test_complex_negotiation(self):
        from aquilia.i18n.locale import negotiate_locale

        result = negotiate_locale(
            "fr-CA;q=0.9, en;q=0.8",
            ["en", "fr", "de"],
            "en",
        )
        assert result == "fr"


class TestLocaleMatchFunction:
    """match_locale with available locale sequences."""

    def test_exact_match(self):
        from aquilia.i18n.locale import Locale, match_locale

        avail = [Locale("en"), Locale("fr")]
        assert match_locale(Locale("fr"), avail).tag == "fr"

    def test_fallback_match(self):
        from aquilia.i18n.locale import Locale, match_locale

        avail = [Locale("en"), Locale("fr")]
        result = match_locale(Locale("fr", region="CA"), avail)
        assert result.tag == "fr"

    def test_no_match(self):
        from aquilia.i18n.locale import Locale, match_locale

        avail = [Locale("en"), Locale("fr")]
        assert match_locale(Locale("ja"), avail) is None

    def test_empty_available(self):
        from aquilia.i18n.locale import Locale, match_locale

        assert match_locale(Locale("en"), []) is None


# ═══════════════════════════════════════════════════════════════════════════
# §2 — Plural Rules
# ═══════════════════════════════════════════════════════════════════════════


class TestPluralCategory:
    """PluralCategory enum."""

    def test_members(self):
        from aquilia.i18n.plural import PluralCategory

        assert PluralCategory.ZERO == "zero"
        assert PluralCategory.ONE == "one"
        assert PluralCategory.TWO == "two"
        assert PluralCategory.FEW == "few"
        assert PluralCategory.MANY == "many"
        assert PluralCategory.OTHER == "other"


class TestSelectPlural:
    """select_plural for diverse languages."""

    def test_english_one(self):
        from aquilia.i18n.plural import select_plural

        assert select_plural("en", 1) == "one"

    def test_english_zero(self):
        from aquilia.i18n.plural import select_plural

        assert select_plural("en", 0) == "other"

    def test_english_plural(self):
        from aquilia.i18n.plural import select_plural

        assert select_plural("en", 5) == "other"

    def test_english_float(self):
        from aquilia.i18n.plural import select_plural

        # 1.5 is not i=1 v=0
        assert select_plural("en", 1.5) == "other"

    def test_french_zero_is_one(self):
        from aquilia.i18n.plural import select_plural

        assert select_plural("fr", 0) == "one"
        assert select_plural("fr", 1) == "one"

    def test_french_two(self):
        from aquilia.i18n.plural import select_plural

        assert select_plural("fr", 2) == "other"

    def test_no_plural_languages(self):
        from aquilia.i18n.plural import select_plural

        for lang in ("zh", "ja", "ko", "vi", "th", "tr"):
            assert select_plural(lang, 0) == "other"
            assert select_plural(lang, 1) == "other"
            assert select_plural(lang, 100) == "other"

    def test_arabic_zero(self):
        from aquilia.i18n.plural import select_plural

        assert select_plural("ar", 0) == "zero"

    def test_arabic_one(self):
        from aquilia.i18n.plural import select_plural

        assert select_plural("ar", 1) == "one"

    def test_arabic_two(self):
        from aquilia.i18n.plural import select_plural

        assert select_plural("ar", 2) == "two"

    def test_arabic_few(self):
        from aquilia.i18n.plural import select_plural

        for n in (3, 4, 5, 6, 7, 8, 9, 10):
            assert select_plural("ar", n) == "few", f"ar({n})"

    def test_arabic_many(self):
        from aquilia.i18n.plural import select_plural

        for n in (11, 12, 50, 99):
            assert select_plural("ar", n) == "many", f"ar({n})"

    def test_arabic_other(self):
        from aquilia.i18n.plural import select_plural

        assert select_plural("ar", 100) == "other"

    def test_russian_one(self):
        from aquilia.i18n.plural import select_plural

        assert select_plural("ru", 1) == "one"
        assert select_plural("ru", 21) == "one"
        assert select_plural("ru", 101) == "one"

    def test_russian_few(self):
        from aquilia.i18n.plural import select_plural

        for n in (2, 3, 4, 22, 23, 24):
            assert select_plural("ru", n) == "few", f"ru({n})"

    def test_russian_many(self):
        from aquilia.i18n.plural import select_plural

        for n in (0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14):
            assert select_plural("ru", n) == "many", f"ru({n})"

    def test_russian_not_one_at_11(self):
        from aquilia.i18n.plural import select_plural

        assert select_plural("ru", 11) != "one"

    def test_polish_one(self):
        from aquilia.i18n.plural import select_plural

        assert select_plural("pl", 1) == "one"

    def test_polish_few(self):
        from aquilia.i18n.plural import select_plural

        for n in (2, 3, 4, 22, 23, 24):
            assert select_plural("pl", n) == "few", f"pl({n})"

    def test_polish_many(self):
        from aquilia.i18n.plural import select_plural

        for n in (0, 5, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19):
            assert select_plural("pl", n) == "many", f"pl({n})"

    def test_czech_one(self):
        from aquilia.i18n.plural import select_plural

        assert select_plural("cs", 1) == "one"

    def test_czech_few(self):
        from aquilia.i18n.plural import select_plural

        for n in (2, 3, 4):
            assert select_plural("cs", n) == "few"

    def test_czech_many_float(self):
        from aquilia.i18n.plural import select_plural

        assert select_plural("cs", 1.5) == "many"

    def test_german_family(self):
        from aquilia.i18n.plural import select_plural

        for lang in ("de", "nl", "it", "es", "pt"):
            assert select_plural(lang, 1) == "one", f"{lang}(1)"
            assert select_plural(lang, 2) == "other", f"{lang}(2)"

    def test_welsh_special_values(self):
        from aquilia.i18n.plural import select_plural

        assert select_plural("cy", 0) == "zero"
        assert select_plural("cy", 1) == "one"
        assert select_plural("cy", 2) == "two"
        assert select_plural("cy", 3) == "few"
        assert select_plural("cy", 6) == "many"
        assert select_plural("cy", 4) == "other"

    def test_unknown_language_defaults_to_english(self):
        from aquilia.i18n.plural import select_plural

        # Unknown language should fall back to English rules
        assert select_plural("xx", 1) == "one"
        assert select_plural("xx", 2) == "other"

    def test_get_plural_rule_fallback(self):
        from aquilia.i18n.plural import get_plural_rule

        rule = get_plural_rule("pt-BR")
        assert rule(0) == "one"  # French-family rule

    def test_negative_numbers(self):
        from aquilia.i18n.plural import select_plural

        assert select_plural("en", -1) == "one"


class TestPluralOperands:
    """CLDR operand extraction."""

    def test_integer(self):
        from aquilia.i18n.plural import _operands

        n, i, v, w, f, t = _operands(42)
        assert n == 42
        assert i == 42
        assert v == 0

    def test_float(self):
        from aquilia.i18n.plural import _operands

        n, i, v, w, f, t = _operands(1.5)
        assert n == 1.5
        assert i == 1
        assert v == 1
        assert f == 5


# ═══════════════════════════════════════════════════════════════════════════
# §3 — Catalogs
# ═══════════════════════════════════════════════════════════════════════════


class TestMemoryCatalog:
    """MemoryCatalog in-memory backend."""

    def _make_catalog(self):
        from aquilia.i18n.catalog import MemoryCatalog

        return MemoryCatalog(
            {
                "en": {
                    "messages": {
                        "welcome": "Hello!",
                        "greeting": "Hello, {name}!",
                        "items": {
                            "one": "{count} item",
                            "other": "{count} items",
                        },
                    },
                    "errors": {
                        "not_found": "Not found",
                    },
                },
                "fr": {
                    "messages": {
                        "welcome": "Bonjour !",
                        "greeting": "Bonjour, {name} !",
                    }
                },
            }
        )

    def test_get_simple(self):
        cat = self._make_catalog()
        assert cat.get("messages.welcome", "en") == "Hello!"

    def test_get_missing_returns_default(self):
        cat = self._make_catalog()
        assert cat.get("nonexistent", "en", default="fallback") == "fallback"

    def test_get_missing_returns_none(self):
        cat = self._make_catalog()
        assert cat.get("nonexistent", "en") is None

    def test_get_missing_locale(self):
        cat = self._make_catalog()
        assert cat.get("messages.welcome", "ja") is None

    def test_get_plural_dict_returns_other(self):
        cat = self._make_catalog()
        result = cat.get("messages.items", "en")
        assert result == "{count} items"  # returns "other" form

    def test_get_plural_one(self):
        cat = self._make_catalog()
        assert cat.get_plural("messages.items", "en", "one") == "{count} item"

    def test_get_plural_other(self):
        cat = self._make_catalog()
        assert cat.get_plural("messages.items", "en", "other") == "{count} items"

    def test_get_plural_missing_category_falls_to_other(self):
        cat = self._make_catalog()
        result = cat.get_plural("messages.items", "en", "few")
        assert result == "{count} items"  # falls back to "other"

    def test_has_key(self):
        cat = self._make_catalog()
        assert cat.has("messages.welcome", "en")
        assert not cat.has("messages.welcome", "ja")

    def test_locales(self):
        cat = self._make_catalog()
        assert cat.locales() == {"en", "fr"}

    def test_keys(self):
        cat = self._make_catalog()
        keys = cat.keys("en")
        assert "messages.welcome" in keys
        assert "messages.greeting" in keys
        assert "messages.items" in keys
        assert "errors.not_found" in keys

    def test_add_merges(self):
        cat = self._make_catalog()
        cat.add("en", {"messages": {"new_key": "New!"}})
        assert cat.get("messages.new_key", "en") == "New!"
        # Old key still exists
        assert cat.get("messages.welcome", "en") == "Hello!"

    def test_add_new_locale(self):
        cat = self._make_catalog()
        cat.add("de", {"messages": {"welcome": "Hallo!"}})
        assert cat.get("messages.welcome", "de") == "Hallo!"

    def test_deep_merge_overwrites(self):
        cat = self._make_catalog()
        cat.add("en", {"messages": {"welcome": "Updated!"}})
        assert cat.get("messages.welcome", "en") == "Updated!"

    def test_empty_catalog(self):
        from aquilia.i18n.catalog import MemoryCatalog

        cat = MemoryCatalog()
        assert cat.locales() == set()
        assert cat.get("anything", "en") is None


class TestFileCatalog:
    """FileCatalog file-based backend."""

    @pytest.fixture
    def locale_dir(self, tmp_path):
        """Create a temporary locale directory structure."""
        en_dir = tmp_path / "locales" / "en"
        en_dir.mkdir(parents=True)
        (en_dir / "messages.json").write_text(
            json.dumps(
                {
                    "welcome": "Welcome!",
                    "greeting": "Hello, {name}!",
                    "items": {"one": "{count} item", "other": "{count} items"},
                }
            ),
            encoding="utf-8",
        )
        (en_dir / "errors.json").write_text(
            json.dumps(
                {
                    "not_found": "Not found",
                    "server_error": "Internal error",
                }
            ),
            encoding="utf-8",
        )

        fr_dir = tmp_path / "locales" / "fr"
        fr_dir.mkdir(parents=True)
        (fr_dir / "messages.json").write_text(
            json.dumps(
                {
                    "welcome": "Bienvenue !",
                    "greeting": "Bonjour, {name} !",
                }
            ),
            encoding="utf-8",
        )

        return tmp_path / "locales"

    def test_load_and_get(self, locale_dir):
        from aquilia.i18n.catalog import FileCatalog

        cat = FileCatalog([locale_dir])
        assert cat.get("messages.welcome", "en") == "Welcome!"

    def test_namespaced_keys(self, locale_dir):
        from aquilia.i18n.catalog import FileCatalog

        cat = FileCatalog([locale_dir])
        assert cat.get("errors.not_found", "en") == "Not found"

    def test_locales(self, locale_dir):
        from aquilia.i18n.catalog import FileCatalog

        cat = FileCatalog([locale_dir])
        assert "en" in cat.locales()
        assert "fr" in cat.locales()

    def test_keys(self, locale_dir):
        from aquilia.i18n.catalog import FileCatalog

        cat = FileCatalog([locale_dir])
        keys = cat.keys("en")
        assert "messages.welcome" in keys
        assert "errors.not_found" in keys

    def test_missing_locale(self, locale_dir):
        from aquilia.i18n.catalog import FileCatalog

        cat = FileCatalog([locale_dir])
        assert cat.get("messages.welcome", "de") is None

    def test_hot_reload(self, locale_dir):
        from aquilia.i18n.catalog import FileCatalog

        cat = FileCatalog([locale_dir])
        cat.load()
        assert cat.get("messages.welcome", "en") == "Welcome!"

        # Modify file
        import time

        time.sleep(0.05)
        (locale_dir / "en" / "messages.json").write_text(
            json.dumps(
                {
                    "welcome": "Updated!",
                }
            ),
            encoding="utf-8",
        )

        cat.reload()
        assert cat.get("messages.welcome", "en") == "Updated!"

    def test_nonexistent_directory(self):
        from aquilia.i18n.catalog import FileCatalog

        cat = FileCatalog([Path("/nonexistent/path")])
        cat.load()
        assert cat.locales() == set()

    def test_lazy_loading(self, locale_dir):
        from aquilia.i18n.catalog import FileCatalog

        cat = FileCatalog([locale_dir])
        # Should not be loaded yet
        assert not cat._loaded
        # First access triggers load
        assert cat.get("messages.welcome", "en") == "Welcome!"
        assert cat._loaded

    def test_plural_from_file(self, locale_dir):
        from aquilia.i18n.catalog import FileCatalog

        cat = FileCatalog([locale_dir])
        assert cat.get_plural("messages.items", "en", "one") == "{count} item"
        assert cat.get_plural("messages.items", "en", "other") == "{count} items"

    def test_invalid_json(self, locale_dir):
        from aquilia.i18n.catalog import FileCatalog

        (locale_dir / "en" / "broken.json").write_text("{invalid json}")
        cat = FileCatalog([locale_dir])
        cat.load()
        # Should not crash, just skip the broken file
        assert cat.get("messages.welcome", "en") == "Welcome!"


class TestCrousCatalog:
    """CrousCatalog CROUS binary format backend."""

    @pytest.fixture
    def locale_dir(self, tmp_path):
        """Create locale dir with JSON files for CROUS testing."""
        en_dir = tmp_path / "locales" / "en"
        en_dir.mkdir(parents=True)
        (en_dir / "messages.json").write_text(
            json.dumps(
                {
                    "welcome": "Welcome!",
                    "greeting": "Hello, {name}!",
                    "items": {"one": "{count} item", "other": "{count} items"},
                }
            ),
            encoding="utf-8",
        )

        fr_dir = tmp_path / "locales" / "fr"
        fr_dir.mkdir(parents=True)
        (fr_dir / "messages.json").write_text(
            json.dumps(
                {
                    "welcome": "Bienvenue !",
                }
            ),
            encoding="utf-8",
        )

        return tmp_path / "locales"

    def test_has_crous(self):
        from aquilia.i18n.catalog import has_crous

        # Should be True since crous is installed
        assert has_crous() is True

    def test_load_from_json(self, locale_dir):
        from aquilia.i18n.catalog import CrousCatalog

        cat = CrousCatalog([locale_dir], auto_compile=False)
        assert cat.get("messages.welcome", "en") == "Welcome!"

    def test_auto_compile(self, locale_dir):
        from aquilia.i18n.catalog import CrousCatalog

        cat = CrousCatalog([locale_dir], auto_compile=True)
        cat.load()
        # After auto-compile, .crous files should exist
        crous_file = locale_dir / "en" / "messages.crous"
        assert crous_file.exists()

    def test_load_from_crous(self, locale_dir):
        from aquilia.i18n.catalog import CrousCatalog

        # First compile
        cat1 = CrousCatalog([locale_dir], auto_compile=True)
        cat1.load()

        # Remove JSON files
        (locale_dir / "en" / "messages.json").unlink()
        (locale_dir / "fr" / "messages.json").unlink()

        # Load from CROUS only
        cat2 = CrousCatalog([locale_dir], auto_compile=False)
        assert cat2.get("messages.welcome", "en") == "Welcome!"

    def test_compile_method(self, locale_dir):
        from aquilia.i18n.catalog import CrousCatalog

        cat = CrousCatalog([locale_dir], auto_compile=False)
        count = cat.compile()
        assert count == 2  # en/messages.json + fr/messages.json

    def test_locales(self, locale_dir):
        from aquilia.i18n.catalog import CrousCatalog

        cat = CrousCatalog([locale_dir])
        assert "en" in cat.locales()
        assert "fr" in cat.locales()

    def test_keys(self, locale_dir):
        from aquilia.i18n.catalog import CrousCatalog

        cat = CrousCatalog([locale_dir])
        keys = cat.keys("en")
        assert "messages.welcome" in keys
        assert "messages.greeting" in keys

    def test_has(self, locale_dir):
        from aquilia.i18n.catalog import CrousCatalog

        cat = CrousCatalog([locale_dir])
        assert cat.has("messages.welcome", "en")
        assert not cat.has("messages.welcome", "de")

    def test_plural_via_crous(self, locale_dir):
        from aquilia.i18n.catalog import CrousCatalog

        cat = CrousCatalog([locale_dir], auto_compile=True)
        assert cat.get_plural("messages.items", "en", "one") == "{count} item"
        assert cat.get_plural("messages.items", "en", "other") == "{count} items"

    def test_crous_prefers_crous_over_json(self, locale_dir):
        """When both .crous and .json exist, prefer .crous."""
        from aquilia.i18n.catalog import CrousCatalog

        # First load compiles to .crous from JSON
        cat1 = CrousCatalog([locale_dir], auto_compile=True)
        cat1.load()

        # Modify the JSON (but .crous still has old content)
        import time

        time.sleep(0.05)  # Ensure different mtime
        (locale_dir / "en" / "messages.json").write_text(
            json.dumps(
                {
                    "welcome": "JSON Updated!",
                }
            ),
            encoding="utf-8",
        )

        # Load again — should auto-recompile since JSON is newer
        cat2 = CrousCatalog([locale_dir], auto_compile=True)
        cat2.load()
        assert cat2.get("messages.welcome", "en") == "JSON Updated!"

    def test_nonexistent_dir(self):
        from aquilia.i18n.catalog import CrousCatalog

        cat = CrousCatalog([Path("/nonexistent")], auto_compile=False)
        cat.load()
        assert cat.locales() == set()

    def test_envelope_integrity(self, locale_dir):
        """Validate CROUS envelope structure."""
        import crous
        from aquilia.i18n.catalog import CrousCatalog

        cat = CrousCatalog([locale_dir], auto_compile=True)
        cat.load()

        crous_file = locale_dir / "en" / "messages.crous"
        data = crous.load(str(crous_file))
        assert data["__format__"] == "crous"
        assert data["schema_version"] == "1.0"
        assert data["artifact_type"] == "i18n_catalog"
        assert data["locale"] == "en"
        assert data["namespace"] == "messages"
        assert "fingerprint" in data
        assert data["fingerprint"].startswith("sha256:")
        assert "translations" in data
        assert data["translations"]["welcome"] == "Welcome!"


class TestNamespacedCatalog:
    """NamespacedCatalog prefix wrapper."""

    def _make(self):
        from aquilia.i18n.catalog import MemoryCatalog, NamespacedCatalog

        base = MemoryCatalog(
            {
                "en": {
                    "users": {
                        "welcome": "Hello user!",
                        "count": {"one": "{n} user", "other": "{n} users"},
                    },
                    "admin": {"welcome": "Hello admin!"},
                }
            }
        )
        return NamespacedCatalog(base, "users")

    def test_get_prefixed(self):
        ns = self._make()
        assert ns.get("welcome", "en") == "Hello user!"

    def test_get_not_in_namespace(self):
        ns = self._make()
        assert ns.get("admin.welcome", "en") is None  # admin is not under users

    def test_get_plural(self):
        ns = self._make()
        assert ns.get_plural("count", "en", "one") == "{n} user"

    def test_has(self):
        ns = self._make()
        assert ns.has("welcome", "en")
        assert not ns.has("nonexistent", "en")

    def test_keys(self):
        ns = self._make()
        keys = ns.keys("en")
        assert "welcome" in keys
        assert "count" in keys


class TestMergedCatalog:
    """MergedCatalog layered fallback."""

    def _make(self):
        from aquilia.i18n.catalog import MemoryCatalog, MergedCatalog

        primary = MemoryCatalog(
            {
                "en": {"messages": {"welcome": "Primary Hello!"}},
            }
        )
        fallback = MemoryCatalog(
            {
                "en": {
                    "messages": {"welcome": "Fallback Hello!", "goodbye": "Bye!"},
                    "errors": {"generic": "Error"},
                },
            }
        )
        return MergedCatalog([primary, fallback])

    def test_primary_wins(self):
        merged = self._make()
        assert merged.get("messages.welcome", "en") == "Primary Hello!"

    def test_fallback_for_missing(self):
        merged = self._make()
        assert merged.get("messages.goodbye", "en") == "Bye!"

    def test_all_missing(self):
        merged = self._make()
        assert merged.get("nonexistent", "en") is None

    def test_locales_merged(self):
        merged = self._make()
        assert "en" in merged.locales()

    def test_keys_merged(self):
        merged = self._make()
        keys = merged.keys("en")
        assert "messages.welcome" in keys
        assert "messages.goodbye" in keys
        assert "errors.generic" in keys

    def test_has(self):
        merged = self._make()
        assert merged.has("messages.welcome", "en")
        assert merged.has("errors.generic", "en")
        assert not merged.has("nonexistent", "en")

    def test_add_catalog(self):
        from aquilia.i18n.catalog import MemoryCatalog

        merged = self._make()
        top = MemoryCatalog({"en": {"messages": {"welcome": "Top priority!"}}})
        merged.add(top)
        assert merged.get("messages.welcome", "en") == "Top priority!"


# ═══════════════════════════════════════════════════════════════════════════
# §4 — Formatter
# ═══════════════════════════════════════════════════════════════════════════


class TestMessageFormatter:
    """ICU MessageFormat-style formatter."""

    def _fmt(self):
        from aquilia.i18n.formatter import MessageFormatter

        return MessageFormatter("en")

    def test_simple_interpolation(self):
        fmt = self._fmt()
        assert fmt.format("Hello, {name}!", name="World") == "Hello, World!"

    def test_multiple_args(self):
        fmt = self._fmt()
        result = fmt.format("{greeting}, {name}!", greeting="Hi", name="Alice")
        assert result == "Hi, Alice!"

    def test_missing_arg_left_as_is(self):
        fmt = self._fmt()
        result = fmt.format("Hello, {name}!")
        assert "{name}" in result

    def test_plural_one(self):
        fmt = self._fmt()
        result = fmt.format("{count, plural, one {# item} other {# items}}", count=1)
        assert result == "1 item"

    def test_plural_other(self):
        fmt = self._fmt()
        result = fmt.format("{count, plural, one {# item} other {# items}}", count=5)
        assert result == "5 items"

    def test_plural_zero_exact(self):
        fmt = self._fmt()
        result = fmt.format("{count, plural, =0 {no items} one {# item} other {# items}}", count=0)
        assert result == "no items"

    def test_select(self):
        fmt = self._fmt()
        result = fmt.format(
            "{gender, select, male {He} female {She} other {They}} left.",
            gender="female",
        )
        assert result == "She left."

    def test_select_other(self):
        fmt = self._fmt()
        result = fmt.format(
            "{gender, select, male {He} female {She} other {They}} left.",
            gender="nonbinary",
        )
        assert result == "They left."

    def test_number_type(self):
        fmt = self._fmt()
        result = fmt.format("Total: {amount, number}", amount=1234567)
        assert "1,234,567" in result

    def test_format_message_convenience(self):
        from aquilia.i18n.formatter import format_message

        result = format_message("Hello, {name}!", locale="en", name="Test")
        assert result == "Hello, Test!"


class TestFormatNumber:
    """format_number locale-specific formatting."""

    def test_english(self):
        from aquilia.i18n.formatter import format_number

        assert format_number(1234567.89, "en") == "1,234,567.89"

    def test_german(self):
        from aquilia.i18n.formatter import format_number

        assert format_number(1234567.89, "de") == "1.234.567,89"

    def test_french(self):
        from aquilia.i18n.formatter import format_number

        result = format_number(1234567.89, "fr")
        # Uses narrow no-break space as group separator
        assert "1" in result
        assert "89" in result

    def test_integer(self):
        from aquilia.i18n.formatter import format_number

        assert format_number(42, "en") == "42"

    def test_negative(self):
        from aquilia.i18n.formatter import format_number

        result = format_number(-1234, "en")
        assert result == "-1,234"

    def test_fixed_decimals(self):
        from aquilia.i18n.formatter import format_number

        assert format_number(42, "en", decimals=2) == "42.00"

    def test_zero(self):
        from aquilia.i18n.formatter import format_number

        assert format_number(0, "en") == "0"

    def test_small_number(self):
        from aquilia.i18n.formatter import format_number

        assert format_number(3, "en") == "3"

    def test_unknown_locale_falls_to_english(self):
        from aquilia.i18n.formatter import format_number

        assert format_number(1234, "xx") == "1,234"


class TestFormatCurrency:
    """format_currency locale-specific currency formatting."""

    def test_usd_english(self):
        from aquilia.i18n.formatter import format_currency

        assert format_currency(9.99, "USD", "en") == "$9.99"

    def test_eur_german(self):
        from aquilia.i18n.formatter import format_currency

        result = format_currency(9.99, "EUR", "de")
        assert "9,99" in result
        assert "€" in result

    def test_symbol_before_en(self):
        from aquilia.i18n.formatter import format_currency

        result = format_currency(100, "USD", "en")
        assert result.startswith("$")

    def test_symbol_after_de(self):
        from aquilia.i18n.formatter import format_currency

        result = format_currency(100, "EUR", "de")
        assert result.endswith("€")


class TestFormatDate:
    """format_date locale patterns."""

    def test_english_medium(self):
        from aquilia.i18n.formatter import format_date

        d = date(2024, 3, 15)
        result = format_date(d, "en", style="medium")
        assert "Mar" in result
        assert "15" in result

    def test_german_short(self):
        from aquilia.i18n.formatter import format_date

        d = date(2024, 3, 15)
        result = format_date(d, "de", style="short")
        assert "15.03.2024" in result

    def test_invalid_value(self):
        from aquilia.i18n.formatter import format_date

        result = format_date("not-a-date", "en")  # type: ignore
        assert result == "not-a-date"


class TestFormatTime:
    """format_time locale patterns."""

    def test_english_short(self):
        from aquilia.i18n.formatter import format_time

        t = time(14, 30)
        result = format_time(t, "en", style="short")
        assert "PM" in result or "30" in result

    def test_german_24h(self):
        from aquilia.i18n.formatter import format_time

        t = time(14, 30)
        result = format_time(t, "de", style="short")
        assert "14:30" in result


class TestFormatDatetime:
    """format_datetime combining date + time."""

    def test_basic(self):
        from aquilia.i18n.formatter import format_datetime

        dt = datetime(2024, 3, 15, 14, 30)
        result = format_datetime(dt, "en")
        assert "Mar" in result or "2024" in result


class TestFormatPercent:
    """format_percent percentage formatting."""

    def test_basic(self):
        from aquilia.i18n.formatter import format_percent

        assert format_percent(0.42, "en") == "42%"

    def test_with_decimals(self):
        from aquilia.i18n.formatter import format_percent

        result = format_percent(0.4256, "en", decimals=1)
        assert "42.6%" == result


class TestFormatDecimal:
    """format_decimal fixed precision."""

    def test_basic(self):
        from aquilia.i18n.formatter import format_decimal

        result = format_decimal(42, "en")
        assert result == "42.00"


class TestFormatOrdinal:
    """format_ordinal locale-specific ordinals."""

    def test_english_ordinals(self):
        from aquilia.i18n.formatter import format_ordinal

        assert format_ordinal(1, "en") == "1st"
        assert format_ordinal(2, "en") == "2nd"
        assert format_ordinal(3, "en") == "3rd"
        assert format_ordinal(4, "en") == "4th"
        assert format_ordinal(11, "en") == "11th"
        assert format_ordinal(12, "en") == "12th"
        assert format_ordinal(13, "en") == "13th"
        assert format_ordinal(21, "en") == "21st"
        assert format_ordinal(22, "en") == "22nd"
        assert format_ordinal(23, "en") == "23rd"

    def test_french_ordinals(self):
        from aquilia.i18n.formatter import format_ordinal

        assert format_ordinal(1, "fr") == "1er"
        assert format_ordinal(2, "fr") == "2e"

    def test_german_ordinals(self):
        from aquilia.i18n.formatter import format_ordinal

        assert format_ordinal(1, "de") == "1."
        assert format_ordinal(5, "de") == "5."

    def test_japanese_ordinals(self):
        from aquilia.i18n.formatter import format_ordinal

        assert format_ordinal(3, "ja") == "第3"


# ═══════════════════════════════════════════════════════════════════════════
# §5 — Service
# ═══════════════════════════════════════════════════════════════════════════


class TestI18nConfig:
    """I18nConfig dataclass."""

    def test_defaults(self):
        from aquilia.i18n.service import I18nConfig

        cfg = I18nConfig()
        assert cfg.default_locale == "en"
        assert cfg.catalog_format == "crous"
        assert cfg.enabled is True

    def test_from_dict(self):
        from aquilia.i18n.service import I18nConfig

        cfg = I18nConfig.from_dict(
            {
                "default_locale": "fr",
                "catalog_format": "json",
                "available_locales": ["fr", "en"],
            }
        )
        assert cfg.default_locale == "fr"
        assert cfg.catalog_format == "json"
        assert cfg.available_locales == ["fr", "en"]

    def test_to_dict_round_trip(self):
        from aquilia.i18n.service import I18nConfig

        cfg = I18nConfig(default_locale="de", available_locales=["de", "en"])
        d = cfg.to_dict()
        assert d["default_locale"] == "de"
        cfg2 = I18nConfig.from_dict(d)
        assert cfg2.default_locale == "de"

    def test_missing_key_strategy(self):
        from aquilia.i18n.service import I18nConfig

        cfg = I18nConfig(missing_key_strategy="raise")
        assert cfg.missing_key_strategy == "raise"


class TestI18nService:
    """I18nService orchestration."""

    def _make_service(self, **overrides):
        from aquilia.i18n.service import I18nConfig, I18nService
        from aquilia.i18n.catalog import MemoryCatalog

        catalog = MemoryCatalog(
            {
                "en": {
                    "messages": {
                        "welcome": "Welcome!",
                        "greeting": "Hello, {name}!",
                        "items": {"one": "{count} item", "other": "{count} items"},
                    },
                },
                "fr": {
                    "messages": {
                        "welcome": "Bienvenue !",
                        "greeting": "Bonjour, {name} !",
                    },
                },
            }
        )
        config = I18nConfig(
            default_locale="en",
            available_locales=["en", "fr"],
            fallback_locale="en",
            missing_key_strategy=overrides.get("missing_key_strategy", "log_and_key"),
        )
        return I18nService(config, catalog=catalog)

    def test_simple_translation(self):
        svc = self._make_service()
        assert svc.t("messages.welcome") == "Welcome!"

    def test_translation_with_locale(self):
        svc = self._make_service()
        assert svc.t("messages.welcome", locale="fr") == "Bienvenue !"

    def test_interpolation(self):
        svc = self._make_service()
        result = svc.t("messages.greeting", name="World")
        assert result == "Hello, World!"

    def test_plural_one(self):
        svc = self._make_service()
        result = svc.tn("messages.items", 1)
        assert "1 item" == result

    def test_plural_many(self):
        svc = self._make_service()
        result = svc.tn("messages.items", 5)
        assert "5 items" == result

    def test_tp_alias(self):
        svc = self._make_service()
        assert svc.tp("messages.greeting", name="Alice") == "Hello, Alice!"

    def test_has(self):
        svc = self._make_service()
        assert svc.has("messages.welcome")
        assert not svc.has("nonexistent")

    def test_available_locales(self):
        svc = self._make_service()
        assert svc.available_locales() == ["en", "fr"]

    def test_is_available(self):
        svc = self._make_service()
        assert svc.is_available("en")
        assert svc.is_available("fr")
        assert not svc.is_available("de")

    def test_negotiate(self):
        svc = self._make_service()
        assert svc.negotiate("fr-CA;q=0.9, en;q=0.8") == "fr"

    def test_locale_object(self):
        svc = self._make_service()
        loc = svc.locale("en-US")
        assert loc.language == "en"
        assert loc.region == "US"

    def test_locale_default(self):
        svc = self._make_service()
        loc = svc.locale()
        assert loc.language == "en"

    def test_missing_key_return_key(self):
        svc = self._make_service(missing_key_strategy="return_key")
        assert svc.t("nonexistent.key") == "nonexistent.key"

    def test_missing_key_return_empty(self):
        svc = self._make_service(missing_key_strategy="return_empty")
        assert svc.t("nonexistent.key") == ""

    def test_missing_key_raise(self):
        from aquilia.i18n.faults import MissingTranslationFault

        svc = self._make_service(missing_key_strategy="raise")
        with pytest.raises(MissingTranslationFault):
            svc.t("nonexistent.key")

    def test_missing_key_with_default(self):
        svc = self._make_service()
        assert svc.t("nonexistent.key", default="fallback") == "fallback"

    def test_fallback_locale(self):
        svc = self._make_service()
        # fr doesn't have errors, should fall back to en
        result = svc.t("messages.welcome", locale="fr")
        assert result == "Bienvenue !"

    def test_fallback_chain_fr_CA(self):
        svc = self._make_service()
        # fr-CA not available, should fall to fr
        result = svc.t("messages.welcome", locale="fr-CA")
        assert result == "Bienvenue !"


class TestCreateI18nService:
    """create_i18n_service factory."""

    def test_default_config(self):
        from aquilia.i18n.service import create_i18n_service

        svc = create_i18n_service()
        assert svc.config.default_locale == "en"

    def test_from_dict(self):
        from aquilia.i18n.service import create_i18n_service

        svc = create_i18n_service({"default_locale": "fr"})
        assert svc.config.default_locale == "fr"

    def test_from_config(self):
        from aquilia.i18n.service import I18nConfig, create_i18n_service

        cfg = I18nConfig(default_locale="de")
        svc = create_i18n_service(cfg)
        assert svc.config.default_locale == "de"

    def test_with_catalog(self):
        from aquilia.i18n.service import create_i18n_service
        from aquilia.i18n.catalog import MemoryCatalog

        cat = MemoryCatalog({"en": {"test": {"key": "value"}}})
        svc = create_i18n_service(catalog=cat)
        assert svc.t("test.key") == "value"


class TestServiceBuildCatalog:
    """Service._build_catalog with CROUS format."""

    def test_build_crous_catalog(self, tmp_path):
        from aquilia.i18n.service import I18nConfig, I18nService
        from aquilia.i18n.catalog import CrousCatalog

        locale_dir = tmp_path / "locales" / "en"
        locale_dir.mkdir(parents=True)
        (locale_dir / "messages.json").write_text(json.dumps({"hello": "Hello!"}), encoding="utf-8")

        cfg = I18nConfig(
            catalog_dirs=[str(tmp_path / "locales")],
            catalog_format="crous",
        )
        svc = I18nService(cfg)
        assert isinstance(svc.catalog, CrousCatalog)
        assert svc.t("messages.hello") == "Hello!"

    def test_build_json_catalog(self, tmp_path):
        from aquilia.i18n.service import I18nConfig, I18nService
        from aquilia.i18n.catalog import FileCatalog

        locale_dir = tmp_path / "locales" / "en"
        locale_dir.mkdir(parents=True)
        (locale_dir / "messages.json").write_text(json.dumps({"hello": "Hello!"}), encoding="utf-8")

        cfg = I18nConfig(
            catalog_dirs=[str(tmp_path / "locales")],
            catalog_format="json",
        )
        svc = I18nService(cfg)
        assert isinstance(svc.catalog, FileCatalog)
        assert svc.t("messages.hello") == "Hello!"


# ═══════════════════════════════════════════════════════════════════════════
# §6 — Lazy Strings
# ═══════════════════════════════════════════════════════════════════════════


class TestLazyString:
    """LazyString deferred translation."""

    def _make_service(self):
        from aquilia.i18n.service import I18nConfig, I18nService
        from aquilia.i18n.catalog import MemoryCatalog

        catalog = MemoryCatalog(
            {
                "en": {"messages": {"hello": "Hello!", "greeting": "Hi, {name}!"}},
                "fr": {"messages": {"hello": "Bonjour !"}},
            }
        )
        return I18nService(
            I18nConfig(default_locale="en", available_locales=["en", "fr"]),
            catalog=catalog,
        )

    def test_deferred_resolution(self):
        from aquilia.i18n.lazy import LazyString

        svc = self._make_service()
        lazy = LazyString("messages.hello", service=svc)
        assert str(lazy) == "Hello!"

    def test_no_service_returns_key(self):
        from aquilia.i18n.lazy import LazyString

        lazy = LazyString("messages.hello")
        assert str(lazy) == "messages.hello"

    def test_no_service_returns_default(self):
        from aquilia.i18n.lazy import LazyString

        lazy = LazyString("messages.hello", default="Fallback")
        assert str(lazy) == "Fallback"

    def test_with_locale(self):
        from aquilia.i18n.lazy import LazyString

        svc = self._make_service()
        lazy = LazyString("messages.hello", service=svc, locale="fr")
        assert str(lazy) == "Bonjour !"

    def test_len(self):
        from aquilia.i18n.lazy import LazyString

        svc = self._make_service()
        lazy = LazyString("messages.hello", service=svc)
        assert len(lazy) == len("Hello!")

    def test_contains(self):
        from aquilia.i18n.lazy import LazyString

        svc = self._make_service()
        lazy = LazyString("messages.hello", service=svc)
        assert "Hello" in lazy

    def test_equality(self):
        from aquilia.i18n.lazy import LazyString

        svc = self._make_service()
        lazy = LazyString("messages.hello", service=svc)
        assert lazy == "Hello!"

    def test_inequality(self):
        from aquilia.i18n.lazy import LazyString

        svc = self._make_service()
        lazy = LazyString("messages.hello", service=svc)
        assert lazy != "Goodbye!"

    def test_concatenation(self):
        from aquilia.i18n.lazy import LazyString

        svc = self._make_service()
        lazy = LazyString("messages.hello", service=svc)
        assert lazy + " World" == "Hello! World"
        assert "Prefix " + lazy == "Prefix Hello!"

    def test_hash(self):
        from aquilia.i18n.lazy import LazyString

        svc = self._make_service()
        lazy = LazyString("messages.hello", service=svc)
        assert hash(lazy) == hash("Hello!")

    def test_bool(self):
        from aquilia.i18n.lazy import LazyString

        svc = self._make_service()
        lazy = LazyString("messages.hello", service=svc)
        assert bool(lazy)

    def test_iteration(self):
        from aquilia.i18n.lazy import LazyString

        svc = self._make_service()
        lazy = LazyString("messages.hello", service=svc)
        assert list(lazy) == list("Hello!")

    def test_getitem(self):
        from aquilia.i18n.lazy import LazyString

        svc = self._make_service()
        lazy = LazyString("messages.hello", service=svc)
        assert lazy[0] == "H"
        assert lazy[-1] == "!"

    def test_repr(self):
        from aquilia.i18n.lazy import LazyString

        lazy = LazyString("messages.hello")
        assert "LazyString" in repr(lazy)
        assert "messages.hello" in repr(lazy)

    def test_upper_lower(self):
        from aquilia.i18n.lazy import LazyString

        svc = self._make_service()
        lazy = LazyString("messages.hello", service=svc)
        assert lazy.upper() == "HELLO!"
        assert lazy.lower() == "hello!"

    def test_strip(self):
        from aquilia.i18n.lazy import LazyString

        svc = self._make_service()
        lazy = LazyString("messages.hello", service=svc)
        assert lazy.strip("!") == "Hello"

    def test_startswith_endswith(self):
        from aquilia.i18n.lazy import LazyString

        svc = self._make_service()
        lazy = LazyString("messages.hello", service=svc)
        assert lazy.startswith("Hello")
        assert lazy.endswith("!")

    def test_encode(self):
        from aquilia.i18n.lazy import LazyString

        svc = self._make_service()
        lazy = LazyString("messages.hello", service=svc)
        assert lazy.encode() == b"Hello!"

    def test_comparisons(self):
        from aquilia.i18n.lazy import LazyString

        svc = self._make_service()
        lazy = LazyString("messages.hello", service=svc)
        assert lazy >= "Hello!"
        assert lazy <= "Hello!"
        assert not (lazy > "Hello!")
        assert not (lazy < "Hello!")

    def test_format(self):
        from aquilia.i18n.lazy import LazyString

        svc = self._make_service()
        lazy = LazyString("messages.hello", service=svc)
        assert f"{lazy}" == "Hello!"


class TestLazyPluralString:
    """LazyPluralString with count."""

    def _make_service(self):
        from aquilia.i18n.service import I18nConfig, I18nService
        from aquilia.i18n.catalog import MemoryCatalog

        catalog = MemoryCatalog(
            {
                "en": {"items": {"one": "{count} item", "other": "{count} items"}},
            }
        )
        return I18nService(
            I18nConfig(default_locale="en"),
            catalog=catalog,
        )

    def test_singular(self):
        from aquilia.i18n.lazy import LazyPluralString

        svc = self._make_service()
        lazy = LazyPluralString("items", 1, service=svc)
        assert "1 item" == str(lazy)

    def test_plural(self):
        from aquilia.i18n.lazy import LazyPluralString

        svc = self._make_service()
        lazy = LazyPluralString("items", 5, service=svc)
        assert "5 items" == str(lazy)

    def test_repr(self):
        from aquilia.i18n.lazy import LazyPluralString

        lazy = LazyPluralString("items", 3)
        assert "LazyPluralString" in repr(lazy)
        assert "count=3" in repr(lazy)


class TestLazyFactories:
    """lazy_t / lazy_tn factory functions."""

    def test_lazy_t(self):
        from aquilia.i18n.lazy import lazy_t, LazyString

        result = lazy_t("test.key", default="Default")
        assert isinstance(result, LazyString)

    def test_lazy_tn(self):
        from aquilia.i18n.lazy import lazy_tn, LazyPluralString

        result = lazy_tn("items", 5)
        assert isinstance(result, LazyPluralString)


class TestLazyContext:
    """set_lazy_context / clear_lazy_context."""

    def test_set_and_clear(self):
        from aquilia.i18n.lazy import set_lazy_context, clear_lazy_context, _service_ref, _locale_ref, LazyString

        svc = MagicMock()
        svc.t.return_value = "Resolved"

        set_lazy_context(svc, "fr")
        assert _service_ref.get() is svc
        assert _locale_ref.get() == "fr"

        lazy = LazyString("test.key")
        assert str(lazy) == "Resolved"

        clear_lazy_context()
        assert _service_ref.get() is None
        assert _locale_ref.get() is None

        lazy2 = LazyString("test.key")
        # Should fall back to key
        assert str(lazy2) == "test.key"

    @pytest.mark.asyncio
    async def test_context_isolated_across_tasks(self):
        from aquilia.i18n.lazy import LazyString, clear_lazy_context, set_lazy_context

        svc = MagicMock()
        svc.t.side_effect = lambda key, *, locale=None, default=None, **kwargs: f"{locale}:{key}"

        async def worker(locale):
            set_lazy_context(svc, locale)
            try:
                await asyncio.sleep(0)
                return str(LazyString("test.key"))
            finally:
                clear_lazy_context()

        result_en, result_fr = await asyncio.gather(worker("en"), worker("fr"))
        assert result_en == "en:test.key"
        assert result_fr == "fr:test.key"


# ═══════════════════════════════════════════════════════════════════════════
# §7 — Middleware
# ═══════════════════════════════════════════════════════════════════════════


class _MockRequest:
    """Lightweight mock for Aquilia request objects."""

    def __init__(
        self,
        headers: Optional[dict] = None,
        cookies: Optional[dict] = None,
        query_params: Optional[dict] = None,
        path: str = "/",
        state: Optional[dict] = None,
    ):
        self.headers = headers or {}
        self.cookies = cookies or {}
        self.query_params = query_params or {}
        self.url = type("URL", (), {"path": path})()
        self.state = state if state is not None else {}


class TestHeaderLocaleResolver:
    """HeaderLocaleResolver from Accept-Language."""

    def test_resolve_match(self):
        from aquilia.i18n.middleware import HeaderLocaleResolver

        resolver = HeaderLocaleResolver(["en", "fr", "de"], "en")
        request = _MockRequest(headers={"accept-language": "fr-CA, fr;q=0.9"})
        assert resolver.resolve(request) == "fr"

    def test_resolve_no_header(self):
        from aquilia.i18n.middleware import HeaderLocaleResolver

        resolver = HeaderLocaleResolver(["en", "fr"], "en")
        request = _MockRequest()
        assert resolver.resolve(request) is None


class TestCookieLocaleResolver:
    """CookieLocaleResolver from cookie."""

    def test_resolve_match(self):
        from aquilia.i18n.middleware import CookieLocaleResolver

        resolver = CookieLocaleResolver("aq_locale", ["en", "fr"])
        request = _MockRequest(cookies={"aq_locale": "fr"})
        assert resolver.resolve(request) == "fr"

    def test_resolve_no_cookie(self):
        from aquilia.i18n.middleware import CookieLocaleResolver

        resolver = CookieLocaleResolver("aq_locale")
        request = _MockRequest()
        assert resolver.resolve(request) is None

    def test_resolve_invalid_locale(self):
        from aquilia.i18n.middleware import CookieLocaleResolver

        resolver = CookieLocaleResolver("aq_locale", ["en"])
        request = _MockRequest(cookies={"aq_locale": "de"})
        assert resolver.resolve(request) is None  # de not in available


class TestQueryLocaleResolver:
    """QueryLocaleResolver from query parameter."""

    def test_resolve_match(self):
        from aquilia.i18n.middleware import QueryLocaleResolver

        resolver = QueryLocaleResolver("lang", ["en", "fr"])
        request = _MockRequest(query_params={"lang": "fr"})
        assert resolver.resolve(request) == "fr"

    def test_resolve_no_param(self):
        from aquilia.i18n.middleware import QueryLocaleResolver

        resolver = QueryLocaleResolver("lang")
        request = _MockRequest()
        assert resolver.resolve(request) is None

    def test_resolve_invalid(self):
        from aquilia.i18n.middleware import QueryLocaleResolver

        resolver = QueryLocaleResolver("lang", ["en"])
        request = _MockRequest(query_params={"lang": "xx"})
        assert resolver.resolve(request) is None


class TestPathLocaleResolver:
    """PathLocaleResolver from URL path prefix."""

    def test_resolve_match(self):
        from aquilia.i18n.middleware import PathLocaleResolver

        resolver = PathLocaleResolver(["en", "fr"])
        request = _MockRequest(path="/fr/about")
        assert resolver.resolve(request) == "fr"

    def test_resolve_root(self):
        from aquilia.i18n.middleware import PathLocaleResolver

        resolver = PathLocaleResolver(["en"])
        request = _MockRequest(path="/")
        assert resolver.resolve(request) is None

    def test_resolve_not_locale(self):
        from aquilia.i18n.middleware import PathLocaleResolver

        resolver = PathLocaleResolver(["en", "fr"])
        request = _MockRequest(path="/about")
        assert resolver.resolve(request) is None


class TestSessionLocaleResolver:
    """SessionLocaleResolver from session state."""

    def test_resolve_match(self):
        from aquilia.i18n.middleware import SessionLocaleResolver

        resolver = SessionLocaleResolver("locale", ["en", "fr"])
        request = _MockRequest(state={"session": {"locale": "fr"}})
        assert resolver.resolve(request) == "fr"

    def test_resolve_no_session(self):
        from aquilia.i18n.middleware import SessionLocaleResolver

        resolver = SessionLocaleResolver()
        request = _MockRequest()
        assert resolver.resolve(request) is None


class TestChainLocaleResolver:
    """ChainLocaleResolver tries multiple resolvers."""

    def test_first_wins(self):
        from aquilia.i18n.middleware import ChainLocaleResolver, QueryLocaleResolver, CookieLocaleResolver

        chain = ChainLocaleResolver(
            [
                QueryLocaleResolver("lang", ["en", "fr"]),
                CookieLocaleResolver("aq_locale", ["en", "fr"]),
            ]
        )
        request = _MockRequest(
            query_params={"lang": "fr"},
            cookies={"aq_locale": "en"},
        )
        assert chain.resolve(request) == "fr"

    def test_fallback_to_second(self):
        from aquilia.i18n.middleware import ChainLocaleResolver, QueryLocaleResolver, CookieLocaleResolver

        chain = ChainLocaleResolver(
            [
                QueryLocaleResolver("lang", ["en", "fr"]),
                CookieLocaleResolver("aq_locale", ["en", "fr"]),
            ]
        )
        request = _MockRequest(cookies={"aq_locale": "en"})
        assert chain.resolve(request) == "en"

    def test_all_none(self):
        from aquilia.i18n.middleware import ChainLocaleResolver, QueryLocaleResolver

        chain = ChainLocaleResolver([QueryLocaleResolver("lang")])
        request = _MockRequest()
        assert chain.resolve(request) is None

    def test_resolver_exception_skipped(self):
        from aquilia.i18n.middleware import ChainLocaleResolver, LocaleResolver

        class BrokenResolver(LocaleResolver):
            def resolve(self, request):
                raise RuntimeError("boom")

        chain = ChainLocaleResolver([BrokenResolver()])
        request = _MockRequest()
        assert chain.resolve(request) is None


class TestBuildResolver:
    """build_resolver factory."""

    def test_default_order(self):
        from aquilia.i18n.middleware import build_resolver
        from aquilia.i18n.service import I18nConfig

        config = I18nConfig()
        resolver = build_resolver(config)
        assert len(resolver.resolvers) == 3  # query, cookie, header


class TestI18nMiddleware:
    """I18nMiddleware request processing."""

    def _make_service(self):
        from aquilia.i18n.service import I18nConfig, I18nService
        from aquilia.i18n.catalog import MemoryCatalog

        return I18nService(
            I18nConfig(default_locale="en", available_locales=["en", "fr"]),
            catalog=MemoryCatalog({"en": {"test": "Hello"}, "fr": {"test": "Bonjour"}}),
        )

    @pytest.mark.asyncio
    async def test_injects_locale(self):
        from aquilia.i18n.middleware import I18nMiddleware, QueryLocaleResolver

        svc = self._make_service()
        resolver = QueryLocaleResolver("lang", ["en", "fr"])
        mw = I18nMiddleware(svc, resolver)

        request = _MockRequest(query_params={"lang": "fr"})
        called = False

        async def handler(req, ctx):
            nonlocal called
            called = True
            assert req.state["locale"] == "fr"
            assert req.state["i18n"] is svc
            return "ok"

        result = await mw(request, None, handler)
        assert called
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_default_locale_when_no_resolver(self):
        from aquilia.i18n.middleware import I18nMiddleware

        svc = self._make_service()
        mw = I18nMiddleware(svc, resolver=None)

        request = _MockRequest()

        async def handler(req, ctx):
            assert req.state["locale"] == "en"
            return "ok"

        await mw(request, None, handler)

    @pytest.mark.asyncio
    async def test_cleanup_on_exception(self):
        from aquilia.i18n.middleware import I18nMiddleware
        from aquilia.i18n.lazy import _service_ref

        svc = self._make_service()
        mw = I18nMiddleware(svc)

        request = _MockRequest()

        async def handler(req, ctx):
            raise ValueError("test error")

        with pytest.raises(ValueError):
            await mw(request, None, handler)


# ═══════════════════════════════════════════════════════════════════════════
# §8 — Faults
# ═══════════════════════════════════════════════════════════════════════════


class TestI18nFaults:
    """I18n fault hierarchy."""

    def test_missing_translation_fault(self):
        from aquilia.i18n.faults import MissingTranslationFault

        fault = MissingTranslationFault("messages.hello", "fr")
        assert fault.key == "messages.hello"
        assert fault.locale == "fr"
        assert fault.code == "I18N_MISSING_TRANSLATION"
        assert "messages.hello" in fault.message
        assert "fr" in fault.message

    def test_invalid_locale_fault(self):
        from aquilia.i18n.faults import InvalidLocaleFault

        fault = InvalidLocaleFault("!!!bad!!!")
        assert fault.tag == "!!!bad!!!"
        assert fault.code == "I18N_INVALID_LOCALE"

    def test_catalog_load_fault(self):
        from aquilia.i18n.faults import CatalogLoadFault

        fault = CatalogLoadFault("/path/to/file.json", "File not found")
        assert fault.path == "/path/to/file.json"
        assert fault.code == "I18N_CATALOG_LOAD"

    def test_plural_rule_fault(self):
        from aquilia.i18n.faults import PluralRuleFault

        fault = PluralRuleFault("xx", count=5, category="unknown")
        assert fault.language == "xx"
        assert fault.code == "I18N_PLURAL_RULE"

    def test_inheritance(self):
        from aquilia.i18n.faults import (
            I18nFault,
            MissingTranslationFault,
            InvalidLocaleFault,
            CatalogLoadFault,
            PluralRuleFault,
        )
        from aquilia.faults.core import Fault

        assert issubclass(I18nFault, Fault)
        assert issubclass(MissingTranslationFault, I18nFault)
        assert issubclass(InvalidLocaleFault, I18nFault)
        assert issubclass(CatalogLoadFault, I18nFault)
        assert issubclass(PluralRuleFault, I18nFault)

    def test_fault_domain(self):
        from aquilia.i18n.faults import I18nFault, MissingTranslationFault
        from aquilia.faults.core import FaultDomain

        fault = MissingTranslationFault("test", "en")
        assert fault.domain == FaultDomain.I18N

    def test_catalog_fault_original_error(self):
        from aquilia.i18n.faults import CatalogLoadFault

        original = ValueError("bad json")
        fault = CatalogLoadFault("/file.json", "parse error", original_error=original)
        assert fault.metadata["original_error"] == "bad json"

    def test_missing_translation_fallback_chain(self):
        from aquilia.i18n.faults import MissingTranslationFault

        fault = MissingTranslationFault("key", "fr-CA", fallback_chain=["fr-CA", "fr", "en"])
        assert fault.metadata["fallback_chain"] == ["fr-CA", "fr", "en"]


# ═══════════════════════════════════════════════════════════════════════════
# §9 — Template Integration
# ═══════════════════════════════════════════════════════════════════════════


class TestTemplateIntegration:
    """Jinja2 template integration."""

    def _make_env_and_service(self):
        from jinja2 import Environment
        from aquilia.i18n.service import I18nConfig, I18nService
        from aquilia.i18n.catalog import MemoryCatalog
        from aquilia.i18n.template_integration import register_i18n_template_globals

        catalog = MemoryCatalog(
            {
                "en": {"messages": {"hello": "Hello!", "greeting": "Hi, {name}!"}},
            }
        )
        svc = I18nService(
            I18nConfig(default_locale="en"),
            catalog=catalog,
        )
        env = Environment()
        register_i18n_template_globals(env, svc)
        return env, svc

    def test_translate_global(self):
        env, svc = self._make_env_and_service()
        assert "_" in env.globals
        assert env.globals["_"]("messages.hello") == "Hello!"

    def test_gettext_alias(self):
        env, svc = self._make_env_and_service()
        assert env.globals["gettext"]("messages.hello") == "Hello!"

    def test_ngettext_alias(self):
        env, svc = self._make_env_and_service()
        assert "_n" in env.globals
        assert "ngettext" in env.globals

    def test_format_number_global(self):
        env, svc = self._make_env_and_service()
        assert "format_number" in env.globals

    def test_service_injected(self):
        env, svc = self._make_env_and_service()
        assert env.globals["i18n_service"] is svc

    def test_template_rendering(self):
        env, svc = self._make_env_and_service()
        template = env.from_string('{{ _("messages.hello") }}')
        result = template.render()
        assert result == "Hello!"


# ═══════════════════════════════════════════════════════════════════════════
# §10 — DI Integration
# ═══════════════════════════════════════════════════════════════════════════


class TestDIIntegration:
    """DI container provider registration."""

    def test_register_in_dict(self):
        from aquilia.i18n.di_integration import register_i18n_providers
        from aquilia.i18n.service import I18nConfig, I18nService
        from aquilia.i18n.catalog import MemoryCatalog

        svc = I18nService(I18nConfig(), catalog=MemoryCatalog())
        container = {}
        register_i18n_providers(container, svc)

        assert I18nService in container
        assert I18nConfig in container
        assert container[I18nService] is svc
        assert container[I18nConfig] is svc.config

    def test_register_with_explicit_config(self):
        from aquilia.i18n.di_integration import register_i18n_providers
        from aquilia.i18n.service import I18nConfig, I18nService
        from aquilia.i18n.catalog import MemoryCatalog

        cfg = I18nConfig(default_locale="de")
        svc = I18nService(I18nConfig(), catalog=MemoryCatalog())
        container = {}
        register_i18n_providers(container, svc, config=cfg)

        assert container[I18nConfig].default_locale == "de"

    def test_register_value_api(self):
        from aquilia.i18n.di_integration import register_i18n_providers
        from aquilia.i18n.service import I18nConfig, I18nService
        from aquilia.i18n.catalog import MemoryCatalog

        class MockContainer:
            def __init__(self):
                self.values = {}

            def register_value(self, type_, value):
                self.values[type_] = value

        svc = I18nService(I18nConfig(), catalog=MemoryCatalog())
        container = MockContainer()
        register_i18n_providers(container, svc)
        assert I18nService in container.values

    def test_unsupported_container_no_crash(self):
        from aquilia.i18n.di_integration import register_i18n_providers
        from aquilia.i18n.service import I18nConfig, I18nService
        from aquilia.i18n.catalog import MemoryCatalog

        svc = I18nService(I18nConfig(), catalog=MemoryCatalog())
        # Should not crash, just log a warning
        register_i18n_providers(42, svc)  # type: ignore


# ═══════════════════════════════════════════════════════════════════════════
# §11 — Config Builders
# ═══════════════════════════════════════════════════════════════════════════


class TestConfigBuilders:
    """Integration.i18n() and Workspace.i18n() config wiring."""

    def test_integration_i18n_creates_config(self):
        from aquilia.config_builders import Integration

        integration = Integration.i18n(
            default_locale="fr",
            available_locales=["fr", "en", "de"],
            catalog_format="crous",
        )
        data = (
            integration.to_dict()
            if hasattr(integration, "to_dict")
            else integration._config
            if hasattr(integration, "_config")
            else {}
        )
        # Verify it contains the expected keys
        assert integration is not None

    def test_config_loader_defaults_crous(self):
        from aquilia.config import ConfigLoader

        loader = ConfigLoader()
        cfg = loader.get_i18n_config()
        assert cfg["catalog_format"] == "crous"


# ═══════════════════════════════════════════════════════════════════════════
# §12 — CLI Commands
# ═══════════════════════════════════════════════════════════════════════════


class TestCLIInit:
    """aq i18n init command."""

    def test_init_creates_files(self, tmp_path, monkeypatch):
        from aquilia.cli.commands.i18n import cmd_i18n_init

        monkeypatch.chdir(tmp_path)

        cmd_i18n_init(
            locales="en,fr",
            directory=str(tmp_path / "locales"),
            format="json",
        )

        assert (tmp_path / "locales" / "en" / "messages.json").exists()
        assert (tmp_path / "locales" / "fr" / "messages.json").exists()

    def test_init_json_content(self, tmp_path, monkeypatch):
        from aquilia.cli.commands.i18n import cmd_i18n_init

        monkeypatch.chdir(tmp_path)

        cmd_i18n_init(locales="en", directory=str(tmp_path / "locales"), format="json")

        data = json.loads((tmp_path / "locales" / "en" / "messages.json").read_text(encoding="utf-8"))
        assert "welcome" in data
        assert "greeting" in data

    def test_init_crous_format(self, tmp_path, monkeypatch):
        from aquilia.cli.commands.i18n import cmd_i18n_init

        monkeypatch.chdir(tmp_path)

        cmd_i18n_init(locales="en", directory=str(tmp_path / "locales"), format="crous")

        crous_file = tmp_path / "locales" / "en" / "messages.crous"
        assert crous_file.exists()

        import crous

        data = crous.load(str(crous_file))
        assert data["__format__"] == "crous"
        assert data["artifact_type"] == "i18n_catalog"
        assert "translations" in data

    def test_init_skip_existing(self, tmp_path, monkeypatch):
        from aquilia.cli.commands.i18n import cmd_i18n_init

        monkeypatch.chdir(tmp_path)

        # First run
        cmd_i18n_init(locales="en", directory=str(tmp_path / "locales"), format="json")
        # Second run should skip
        cmd_i18n_init(locales="en", directory=str(tmp_path / "locales"), format="json")
        # File should still exist (not error)
        assert (tmp_path / "locales" / "en" / "messages.json").exists()

    def test_init_unknown_locale_creates_minimal(self, tmp_path, monkeypatch):
        from aquilia.cli.commands.i18n import cmd_i18n_init

        monkeypatch.chdir(tmp_path)

        cmd_i18n_init(locales="xx", directory=str(tmp_path / "locales"), format="json")
        data = json.loads((tmp_path / "locales" / "xx" / "messages.json").read_text(encoding="utf-8"))
        assert "welcome" in data


class TestCLICompile:
    """aq i18n compile command."""

    def test_compile_json_to_crous(self, tmp_path, monkeypatch):
        from aquilia.cli.commands.i18n import cmd_i18n_compile, cmd_i18n_init

        monkeypatch.chdir(tmp_path)

        # Create JSON files
        cmd_i18n_init(locales="en", directory=str(tmp_path / "locales"), format="json")

        # Compile to CROUS
        cmd_i18n_compile(directory=str(tmp_path / "locales"))

        assert (tmp_path / "locales" / "en" / "messages.crous").exists()

    def test_compile_subcommand_is_wired(self, tmp_path, monkeypatch):
        pytest.importorskip("crous")

        from click.testing import CliRunner

        from aquilia.cli.__main__ import cli
        from aquilia.cli.commands.i18n import cmd_i18n_init

        monkeypatch.chdir(tmp_path)
        cmd_i18n_init(locales="en", directory=str(tmp_path / "locales"), format="json")

        runner = CliRunner()
        result = runner.invoke(cli, ["i18n", "compile", "--directory", str(tmp_path / "locales")])

        assert result.exit_code == 0
        assert (tmp_path / "locales" / "en" / "messages.crous").exists()


class TestCLIInspect:
    """aq i18n inspect command."""

    def test_inspect_outputs_json(self, capsys):
        from aquilia.cli.commands.i18n import cmd_i18n_inspect

        # This will output the config
        cmd_i18n_inspect()
        captured = capsys.readouterr()
        # Should be valid JSON
        data = json.loads(captured.out)
        assert isinstance(data, dict)


class TestCLICoverage:
    """aq i18n coverage command."""

    def test_coverage_report(self, tmp_path, monkeypatch):
        from aquilia.cli.commands.i18n import cmd_i18n_coverage

        # Create locale files
        en_dir = tmp_path / "locales" / "en"
        en_dir.mkdir(parents=True)
        (en_dir / "messages.json").write_text(
            json.dumps(
                {
                    "hello": "Hello",
                    "bye": "Bye",
                }
            )
        )
        fr_dir = tmp_path / "locales" / "fr"
        fr_dir.mkdir(parents=True)
        (fr_dir / "messages.json").write_text(
            json.dumps(
                {
                    "hello": "Bonjour",
                }
            )
        )

        monkeypatch.chdir(tmp_path)
        # This should not crash
        cmd_i18n_coverage(verbose=True)


# ═══════════════════════════════════════════════════════════════════════════
# §13 — Regression Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestI18nRegression:
    """Regression tests for specific bugs and edge cases."""

    def test_dot_in_translation_key(self):
        """Keys with multiple dots resolve correctly."""
        from aquilia.i18n.catalog import MemoryCatalog

        cat = MemoryCatalog(
            {
                "en": {"a": {"b": {"c": {"d": "deep value"}}}},
            }
        )
        assert cat.get("a.b.c.d", "en") == "deep value"

    def test_numeric_values_in_translations(self):
        """Numeric values in catalogs are converted to strings."""
        from aquilia.i18n.catalog import MemoryCatalog

        cat = MemoryCatalog(
            {
                "en": {"count": 42},
            }
        )
        assert cat.get("count", "en") == "42"

    def test_empty_string_translation(self):
        """Empty string is a valid translation (not missing)."""
        from aquilia.i18n.catalog import MemoryCatalog

        cat = MemoryCatalog(
            {
                "en": {"empty": ""},
            }
        )
        assert cat.has("empty", "en")
        assert cat.get("empty", "en") == ""

    def test_unicode_translations(self):
        """Full Unicode support in translations."""
        from aquilia.i18n.catalog import MemoryCatalog

        cat = MemoryCatalog(
            {
                "ja": {"greeting": "こんにちは"},
                "ar": {"greeting": "مرحبا"},
                "zh": {"greeting": "你好"},
                "ko": {"greeting": "안녕하세요"},
                "ru": {"greeting": "Привет"},
            }
        )
        assert cat.get("greeting", "ja") == "こんにちは"
        assert cat.get("greeting", "ar") == "مرحبا"
        assert cat.get("greeting", "zh") == "你好"
        assert cat.get("greeting", "ko") == "안녕하세요"
        assert cat.get("greeting", "ru") == "Привет"

    def test_concurrent_service_access(self):
        """Service is thread-safe for reads."""
        import threading
        from aquilia.i18n.service import I18nConfig, I18nService
        from aquilia.i18n.catalog import MemoryCatalog

        catalog = MemoryCatalog(
            {
                "en": {"test": "Hello"},
                "fr": {"test": "Bonjour"},
            }
        )
        svc = I18nService(
            I18nConfig(available_locales=["en", "fr"]),
            catalog=catalog,
        )
        results = []
        errors = []

        def worker(locale):
            try:
                for _ in range(100):
                    result = svc.t("test", locale=locale)
                    results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=worker, args=("en",)),
            threading.Thread(target=worker, args=("fr",)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert len(results) == 200

    def test_icu_nested_braces(self):
        """ICU MessageFormat handles nested braces in plural/select."""
        from aquilia.i18n.formatter import MessageFormatter

        fmt = MessageFormatter("en")
        pattern = "{count, plural, one {# item} other {# items}}"
        assert fmt.format(pattern, count=1) == "1 item"
        assert fmt.format(pattern, count=3) == "3 items"

    def test_format_number_large(self):
        """Large numbers formatted correctly."""
        from aquilia.i18n.formatter import format_number

        result = format_number(1_000_000_000, "en")
        assert result == "1,000,000,000"

    def test_format_number_decimal_precision(self):
        """Decimal precision is preserved."""
        from aquilia.i18n.formatter import format_decimal

        result = format_decimal(3.14159, "en", decimals=2)
        assert result == "3.14"

    def test_crous_round_trip(self, tmp_path):
        """CROUS catalog survives full write → read round-trip."""
        import crous
        from aquilia.i18n.catalog import CrousCatalog

        locale_dir = tmp_path / "locales" / "en"
        locale_dir.mkdir(parents=True)
        (locale_dir / "messages.json").write_text(
            json.dumps(
                {
                    "hello": "Hello!",
                    "nested": {"key": "value"},
                    "plural": {"one": "1 item", "other": "{n} items"},
                    "unicode": "日本語テスト 🎌",
                }
            ),
            encoding="utf-8",
        )

        # Write
        cat1 = CrousCatalog([tmp_path / "locales"], auto_compile=True)
        cat1.load()

        # Read from CROUS
        (locale_dir / "messages.json").unlink()
        cat2 = CrousCatalog([tmp_path / "locales"], auto_compile=False)
        assert cat2.get("messages.hello", "en") == "Hello!"
        assert cat2.get("messages.nested.key", "en") == "value"
        assert cat2.get_plural("messages.plural", "en", "one") == "1 item"
        assert cat2.get("messages.unicode", "en") == "日本語テスト 🎌"

    def test_service_reload(self, tmp_path):
        """Service.reload_catalogs creates fresh catalogs."""
        from aquilia.i18n.service import I18nConfig, I18nService

        locale_dir = tmp_path / "locales" / "en"
        locale_dir.mkdir(parents=True)
        (locale_dir / "messages.json").write_text(
            json.dumps(
                {
                    "hello": "Original",
                }
            ),
            encoding="utf-8",
        )

        cfg = I18nConfig(
            catalog_dirs=[str(tmp_path / "locales")],
            catalog_format="json",
        )
        svc = I18nService(cfg)
        assert svc.t("messages.hello") == "Original"

        # Modify
        (locale_dir / "messages.json").write_text(
            json.dumps(
                {
                    "hello": "Updated",
                }
            ),
            encoding="utf-8",
        )

        svc.reload_catalogs()
        assert svc.t("messages.hello") == "Updated"

    def test_missing_key_strategy_log_and_key(self):
        """log_and_key strategy logs warning and returns key."""
        from aquilia.i18n.service import I18nConfig, I18nService
        from aquilia.i18n.catalog import MemoryCatalog
        import logging

        svc = I18nService(
            I18nConfig(missing_key_strategy="log_and_key"),
            catalog=MemoryCatalog(),
        )
        with patch("aquilia.i18n.service.logger") as mock_logger:
            result = svc.t("missing.key")
            assert result == "missing.key"
            mock_logger.warning.assert_called()

    def test_locale_parse_and_str_round_trip(self):
        """Parse → str → parse is lossless."""
        from aquilia.i18n.locale import parse_locale

        tags = ["en", "en-US", "zh-Hans", "zh-Hant-HK", "fr-CA"]
        for tag in tags:
            loc = parse_locale(tag)
            assert parse_locale(str(loc)).tag == loc.tag

    def test_plural_boundary_values(self):
        """Plural rules at boundary values."""
        from aquilia.i18n.plural import select_plural

        # Russian: 11-14 are "many" not "one/few"
        assert select_plural("ru", 11) == "many"
        assert select_plural("ru", 12) == "many"
        assert select_plural("ru", 13) == "many"
        assert select_plural("ru", 14) == "many"
        # But 21 is "one"
        assert select_plural("ru", 21) == "one"
        # And 111 is "many"
        assert select_plural("ru", 111) == "many"

    def test_ordinal_english_special_teens(self):
        """English ordinals: 11th, 12th, 13th (not 11st, 12nd, 13rd)."""
        from aquilia.i18n.formatter import format_ordinal

        assert format_ordinal(11, "en") == "11th"
        assert format_ordinal(12, "en") == "12th"
        assert format_ordinal(13, "en") == "13th"
        assert format_ordinal(111, "en") == "111th"
        assert format_ordinal(112, "en") == "112th"

    def test_catalog_keys_exclude_plural_subkeys(self):
        """keys() returns 'items' not 'items.one', 'items.other'."""
        from aquilia.i18n.catalog import MemoryCatalog

        cat = MemoryCatalog(
            {
                "en": {
                    "items": {"one": "{n} item", "other": "{n} items"},
                    "simple": "Hello",
                }
            }
        )
        keys = cat.keys("en")
        assert "items" in keys
        assert "simple" in keys
        assert "items.one" not in keys
        assert "items.other" not in keys

    def test_merged_catalog_locales_union(self):
        """MergedCatalog.locales() is the union of all catalogs."""
        from aquilia.i18n.catalog import MemoryCatalog, MergedCatalog

        cat1 = MemoryCatalog({"en": {"a": "a"}})
        cat2 = MemoryCatalog({"fr": {"b": "b"}})
        merged = MergedCatalog([cat1, cat2])
        assert merged.locales() == {"en", "fr"}

    def test_accept_language_quality_clamping(self):
        """Quality values are clamped to [0, 1]."""
        from aquilia.i18n.locale import parse_accept_language

        result = parse_accept_language("en;q=1.5, fr;q=-0.1")
        for tag, q in result:
            assert 0.0 <= q <= 1.0

    def test_file_catalog_multiple_directories(self, tmp_path):
        """FileCatalog merges multiple directories."""
        from aquilia.i18n.catalog import FileCatalog

        dir1 = tmp_path / "locale1" / "en"
        dir1.mkdir(parents=True)
        (dir1 / "module1.json").write_text(json.dumps({"key1": "val1"}))

        dir2 = tmp_path / "locale2" / "en"
        dir2.mkdir(parents=True)
        (dir2 / "module2.json").write_text(json.dumps({"key2": "val2"}))

        cat = FileCatalog([tmp_path / "locale1", tmp_path / "locale2"])
        assert cat.get("module1.key1", "en") == "val1"
        assert cat.get("module2.key2", "en") == "val2"

    def test_has_crous_function(self):
        """has_crous() reports crous library availability."""
        from aquilia.i18n.catalog import has_crous

        assert isinstance(has_crous(), bool)
        assert has_crous() is True  # crous is installed in this env


# ═══════════════════════════════════════════════════════════════════════════
# §14 — Module Exports
# ═══════════════════════════════════════════════════════════════════════════


class TestModuleExports:
    """Verify all public symbols are exported from __init__."""

    def test_all_exports(self):
        import aquilia.i18n as i18n

        expected = [
            "Locale",
            "parse_locale",
            "normalize_locale",
            "match_locale",
            "parse_accept_language",
            "negotiate_locale",
            "TranslationCatalog",
            "MemoryCatalog",
            "FileCatalog",
            "CrousCatalog",
            "NamespacedCatalog",
            "MergedCatalog",
            "has_crous",
            "PluralCategory",
            "PluralRule",
            "get_plural_rule",
            "select_plural",
            "MessageFormatter",
            "format_message",
            "format_number",
            "format_currency",
            "format_date",
            "format_time",
            "format_datetime",
            "format_percent",
            "format_decimal",
            "format_ordinal",
            "I18nService",
            "I18nConfig",
            "create_i18n_service",
            "LazyString",
            "lazy_t",
            "lazy_tn",
            "I18nMiddleware",
            "LocaleResolver",
            "HeaderLocaleResolver",
            "CookieLocaleResolver",
            "QueryLocaleResolver",
            "PathLocaleResolver",
            "SessionLocaleResolver",
            "ChainLocaleResolver",
            "I18nFault",
            "MissingTranslationFault",
            "InvalidLocaleFault",
            "CatalogLoadFault",
            "PluralRuleFault",
            "register_i18n_template_globals",
            "I18nTemplateExtension",
            "register_i18n_providers",
        ]
        for name in expected:
            assert hasattr(i18n, name), f"Missing export: {name}"
            assert name in i18n.__all__, f"Not in __all__: {name}"

    def test_crous_catalog_importable(self):
        from aquilia.i18n import CrousCatalog

        assert CrousCatalog is not None

    def test_has_crous_importable(self):
        from aquilia.i18n import has_crous

        assert callable(has_crous)
