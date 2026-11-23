# Copyright 2026 Anthropic PBC
# SPDX-License-Identifier: Apache-2.0

"""The retail four-language layer: translation coverage, localized reads, and the
in-place session language switch."""

from __future__ import annotations

import pytest

from demo_common.sessions import SessionStore
from retail.api.i18n import (
    LANGUAGES,
    language_label,
    load_translations,
    localize,
    localize_cart,
)
from retail.api.mock_retail import DATA_DIR
from shopping_agent import Cart, CartItem, ShoppingSessionState
from shopping_agent.prompt import build_dynamic_context


@pytest.fixture(scope="module")
def translations():
    return load_translations(DATA_DIR)


def test_all_languages_and_products_are_covered(translations):
    assert LANGUAGES == ("en", "zh", "ja", "ko")
    assert len(translations) == 50
    for entry in translations.values():
        assert set(entry) == {"zh", "ja", "ko"}
        for translated in entry.values():
            assert translated["title"]
            assert translated["short_description"]
            assert translated["long_description"]
            assert translated["attributes"]


def test_language_label():
    assert language_label("zh") == "中文 (Simplified Chinese)"
    assert language_label("nope") == "English"


def test_localize_changes_text_but_not_identifiers(translations):
    from retail.api.mock_retail import MockRetail

    product = MockRetail().products["DEN-1001"]
    zh = localize(product, "zh", translations)
    assert zh.product_id == product.product_id
    assert zh.price == product.price and zh.currency == product.currency
    assert zh.title != product.title and "高速" in zh.title
    assert product.title == "NSK Pana-Max2 M4 High-Speed Turbine Handpiece"  # not mutated


def test_localize_cart_retranslates_titles(translations):
    item = CartItem(
        product_id="DEN-1001",
        title="NSK Pana-Max2 M4 High-Speed Turbine Handpiece",
        price=860.0,
        quantity=1,
    )
    cart = Cart(items=[item], currency="CNY")
    zh = localize_cart(cart, "zh", translations)
    assert zh.items[0].title != item.title
    assert cart.items[0].title == item.title  # stored cart untouched


def test_session_language_switch_keeps_state():
    store = SessionStore(ShoppingSessionState)
    record = store.start("demo-user")
    assert record.language == "en"
    from retail.api.mock_retail import MockRetail

    product = MockRetail().products["DEN-1001"]
    record.state.seen_products["DEN-1001"] = product
    record.language = "ja"
    store.save(record)
    reloaded = store.require(record.session_id)
    assert reloaded.language == "ja"
    assert "DEN-1001" in reloaded.state.seen_products  # cart/provenance survived


def test_dynamic_context_names_the_response_language():
    for language in LANGUAGES:
        block = build_dynamic_context(
            preferences=None, memory_facts=[], cart=None, page=None, language=language
        )
        assert "response_language" in block
    zh = build_dynamic_context(
        preferences=None, memory_facts=[], cart=None, page=None, language="zh"
    )
    assert "Chinese" in zh
