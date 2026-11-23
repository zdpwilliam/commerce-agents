# Copyright 2026 Anthropic PBC
# SPDX-License-Identifier: Apache-2.0

"""Localization of retail catalog records from the translation table.

English stays in catalog.json as the single source. This module overlays the zh/ja/ko
values from ``translations.json`` onto the localizable fields of a ``Product`` when the
session asks for a different language. It returns copies: the English catalog objects
that search, provenance and the merchant side hold are never mutated, so ids, prices,
ratings and availability stay byte-for-byte identical on every path.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import TypeVar

from shopping_agent import Product

LANGUAGES = ("en", "zh", "ja", "ko")
DEFAULT_LANGUAGE = "en"

# UI-facing names for each language, injected into the fenced context for the agent.
LANGUAGE_LABELS = {
    "en": "English",
    "zh": "中文 (Simplified Chinese)",
    "ja": "日本語 (Japanese)",
    "ko": "한국어 (Korean)",
}

# Fields the translation table owns. Everything else (id, brand, model, price, rating,
# currency, in_stock, labels, image_url, options, variants) stays from the catalog.
_LOCALIZED_FIELDS = ("title", "short_description", "long_description", "attributes")

T = TypeVar("T", bound=Product)


def language_label(language: str) -> str:
    return LANGUAGE_LABELS.get(language, LANGUAGE_LABELS[DEFAULT_LANGUAGE])


def load_translations(data_dir: Path) -> dict[str, dict[str, dict]]:
    path = data_dir / "translations.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _overlay(product: T, entry: dict | None, language: str) -> T:
    if language == DEFAULT_LANGUAGE or not entry or language not in entry:
        return product
    translated = entry[language]
    update = {field: translated[field] for field in _LOCALIZED_FIELDS if field in translated}
    if update:
        return product.model_copy(update=update)
    return product


def localize(product: T, language: str, table: dict[str, dict[str, dict]]) -> T:
    """Return a copy of ``product`` with localizable fields overlaid for ``language``."""
    return _overlay(product, table.get(product.product_id), language)


def localize_products(
    products: Iterable[T], language: str, table: dict[str, dict[str, dict]]
) -> list[T]:
    """Return localized copies of a sequence of products, in the same order."""
    return [localize(product, language, table) for product in products]


def localize_cart(cart, language: str, table: dict[str, dict[str, dict]]):
    """Return a copy of a cart whose item titles follow ``language``, so the fenced
    context and the bag UI never show a stale-language title after a switch. The stored
    cart (and its prices and quantities) is untouched."""
    if language == DEFAULT_LANGUAGE:
        return cart
    items = []
    for item in cart.items:
        entry = table.get(item.product_id)
        title = item.title
        if entry and language in entry and "title" in entry[language]:
            title = entry[language]["title"]
        items.append(item.model_copy(update={"title": title}))
    return cart.model_copy(update={"items": items})


def localized_search_text(product: Product, table: dict[str, dict[str, dict]]) -> str:
    """All-language title/description/attribute text for a product, so a query in any
    supported language can match the English catalog's search index."""
    entry = table.get(product.product_id)
    if not entry:
        return ""
    parts: list[str] = []
    for translated in entry.values():
        for field in ("title", "short_description", "long_description"):
            if translated.get(field):
                parts.append(str(translated[field]))
        attrs = translated.get("attributes") or {}
        parts.extend(f"{k} {v}" for k, v in attrs.items())
    return " ".join(parts)
