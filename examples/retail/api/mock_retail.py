# Copyright 2026 Anthropic PBC
# SPDX-License-Identifier: Apache-2.0

"""The retail example's ``StorefrontBackend`` over the fixtures in ``data/``: keyword
search, per-session carts, fixture orders and policies. An adopter replaces this class
with calls to their own catalog, cart, and order systems."""

from __future__ import annotations

import hashlib
import json
import math

# CJK ranges: Han, Hiragana, Katakana, Hangul. Used only to decide when to take the
# substring-match search path, since the shared ASCII tokenizer drops these characters.
import re as _re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from demo_common.storefront_fixtures import (
    SessionCarts,
    example_data_dir,
    find_order,
    find_product,
    load_catalog,
    load_orders,
    load_policies,
    load_users,
    newest_orders,
    option_text,
    orders_for,
    preferences_of,
    search_help,
    summary_of,
    unavailable_detail,
    within_price_and_rating,
)
from shopping_agent import (
    Cart,
    FulfillmentOption,
    Order,
    Policy,
    Product,
    ProductDetails,
    SearchFilters,
    ShoppingSessionContext,
    StorefrontBackend,
    Unavailable,
    UserPreferences,
)

_CJK = _re.compile(r"[\u4e00-\u9fff]")
_WORD = _re.compile(r"[a-z0-9]+")


def _text_tokens(text: str) -> set[str]:
    """ASCII words plus CJK unigrams/bigrams, so Chinese queries match Chinese catalog text."""
    lowered = text.lower()
    tokens = set(_WORD.findall(lowered))
    cjk = "".join(_CJK.findall(lowered))
    tokens.update(cjk)
    tokens.update(cjk[i : i + 2] for i in range(len(cjk) - 1))
    return tokens


def _query_tokens(query: str) -> list[str]:
    return sorted(_text_tokens(query))


DATA_DIR = example_data_dir(__file__)

# Attributes stamped onto products at boot rather than authored in the catalog. The
# merchant side re-stamps LOW_STOCK_ATTRIBUTE when an applied change moves the number.
DELIVERY_ATTRIBUTE = "delivery"
LOW_STOCK_ATTRIBUTE = "low_stock"
_STAMPED_ATTRIBUTES = {DELIVERY_ATTRIBUTE, LOW_STOCK_ATTRIBUTE}

_SEARCH_WEIGHTS = {
    "title": 3.0,
    "brand": 2.0,
    "category": 2.0,
    "attributes": 1.5,
    "description": 1.0,
}
# Review-aspect vocabularies per category (invented, like the reviews themselves).
_ASPECTS_BY_CATEGORY: dict[str, list[str]] = {
    "牙科手机": ["做工", "转速稳定", "可高温灭菌", "性价比"],
    "根管治疗": ["定位精准", "操作顺畅", "耐用性", "性价比"],
    "修复固化": ["固化效果", "光强稳定", "操作便捷", "性价比"],
    "牙周洁治": ["清洁效果", "舒适度", "耐用性", "性价比"],
    "影像设备": ["成像清晰", "扫描精度", "操作便捷", "稳定性"],
    "综合治疗台": ["做工", "舒适度", "调节顺滑", "耐用性"],
    "消毒灭菌": ["灭菌可靠", "容量", "操作便捷", "稳定性"],
    "耗材配件": ["品质", "与描述一致", "规格合适", "性价比"],
}
_ASPECTS_FALLBACK = ["品质", "与描述一致", "性价比"]
_FREIGHT_CATEGORIES = {"影像设备", "综合治疗台"}
_FREIGHT_PRICE_FLOOR = 3000
# The terms of the shipping entry in policies.json, which is what the agent quotes;
# test_mock_retail checks that the entry still states each of them. CNY amounts.
FREE_SHIPPING_OVER = 500
STANDARD_SHIPPING = FulfillmentOption(method="delivery", eta="3-5 个工作日（标准）", fee=60.0)
EXPRESS_SHIPPING = FulfillmentOption(method="delivery", eta="2 个工作日（加急）", fee=120.0)
FREIGHT_SHIPPING = FulfillmentOption(
    method="shipping", eta="5-7 个工作日（货运）", fee=290.0
)
_STORE_OPENS, _STORE_CLOSES = 9, 21


class MockRetail(StorefrontBackend):
    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        catalog, self.products, self.variants = load_catalog(data_dir)
        self.store_name: str = catalog.get("store_name", "本店")
        self._users = load_users(data_dir)
        self._orders = load_orders(data_dir)
        self._policies = load_policies(data_dir)
        self._carts = SessionCarts()
        self._stamp_delivery_promises()
        self._stamp_low_stock(data_dir)

    def _stamp_delivery_promises(self) -> None:
        """A "Get it by <day>" attribute on every in-stock product: boot date plus a
        stable 2-4 day offset per product, never a Sunday, so promises stay current and
        a product's promise is the same for the whole run."""
        boot = datetime.now()
        for product in self.products.values():
            if not product.in_stock:
                continue
            promised = boot + timedelta(days=2 + sum(ord(ch) for ch in product.product_id) % 3)
            if promised.weekday() == 6:
                promised += timedelta(days=1)
            label = f"预计 {promised.strftime('%m 月 %d 日')} 送达"
            product.attributes[DELIVERY_ATTRIBUTE] = label
            # A family's in-stock variants ship on the family's promise.
            for variant in product.variants:
                if (record := self.variants.get(variant.product_id)) and record.in_stock:
                    record.attributes[DELIVERY_ATTRIBUTE] = label

    def _stamp_low_stock(self, data_dir: Path) -> None:
        """The "only N left" attribute, taken from the same inventory rows the merchant
        portal shows, so the storefront's scarcity chip and the portal agree."""
        overlay_path = data_dir / "merchant_inventory.json"
        if not overlay_path.exists():
            return
        overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
        default_threshold = int(overlay.get("default_threshold", 8))
        for row in overlay.get("inventory", []):
            product = self.product(row.get("product_id", ""))
            if product is None or not product.in_stock:
                continue
            stock = int(row.get("stock", 0))
            if 0 < stock <= int(row.get("threshold", default_threshold)):
                product.attributes[LOW_STOCK_ATTRIBUTE] = str(stock)

    # ------------------------------------------------------------------
    # Catalog
    # ------------------------------------------------------------------

    def listing_of(self, product_id: str) -> ProductDetails | None:
        """The listing an id belongs to: itself, or its family when it is a variant."""
        record = self.product(product_id)
        if record is not None and record.variant_of:
            return self.products.get(record.variant_of)
        return record

    def _searchable_text(self, product: ProductDetails) -> dict[str, str]:
        return {
            "title": product.title,
            "brand": product.brand or "",
            "category": product.category or "",
            "attributes": " ".join(
                f"{k} {v}" for k, v in product.attributes.items() if k not in _STAMPED_ATTRIBUTES
            )
            + " "
            + option_text(product),
            "description": f"{product.short_description or ''} {product.long_description or ''}",
        }

    def _score(self, product: ProductDetails, query_tokens: list[str]) -> float:
        # The catalog and queries are Chinese: the shared ASCII tokenizer drops CJK, so
        # score on character bigrams (plus ASCII words) with the usual field weights.
        fields = {name: _text_tokens(text) for name, text in self._searchable_text(product).items()}
        score = 0.0
        for token in query_tokens:
            score += max(
                (weight for name, weight in _SEARCH_WEIGHTS.items() if token in fields[name]),
                default=0.0,
            )
        return score

    @staticmethod
    def _soft_filter(product: ProductDetails, filters: SearchFilters) -> bool:
        if filters.category and filters.category.lower() not in (product.category or "").lower():
            return False
        if not filters.attributes:
            return True
        haystack = " ".join(
            f"{k}={v}".lower()
            for k, v in product.attributes.items()
            if k not in _STAMPED_ATTRIBUTES
        )
        haystack += f" {product.title.lower()} {option_text(product).lower()}"
        return all(str(value).lower() in haystack for value in filters.attributes.values())

    def _rank(self, query: str, filters: SearchFilters | None, limit: int) -> list[ProductDetails]:
        """Rank the Chinese catalog for a query. Mirrors ``rank_products``: hard filters,
        a relevance cutoff at half the best score, soft filters, and the requested sort."""
        query_tokens = _query_tokens(query)
        if not query_tokens:
            return []
        scored = [
            (self._score(product, query_tokens), product)
            for product in self.products.values()
            if filters is None or within_price_and_rating(product, filters)
        ]
        scored = [(points, product) for points, product in scored if points > 0]
        if scored:
            best = max(points for points, _ in scored)
            scored = [(points, product) for points, product in scored if points >= best / 2]
        if filters is not None:
            narrowed = [
                (p, product) for p, product in scored if self._soft_filter(product, filters)
            ]
            scored = narrowed or scored
        sort = filters.sort if filters else "relevance"
        if sort == "price_asc":
            scored.sort(key=lambda pair: pair[1].price)
        elif sort == "price_desc":
            scored.sort(key=lambda pair: -pair[1].price)
        elif sort == "rating":
            scored.sort(key=lambda pair: -(pair[1].rating or 0))
        else:
            scored.sort(key=lambda pair: (-pair[0], -(pair[1].rating or 0)))
        return [product for _, product in scored[:limit]]

    async def search_products(
        self,
        session: ShoppingSessionContext,
        query: str,
        filters: SearchFilters | None = None,
        limit: int = 8,
    ) -> list[Product]:
        del session
        return [summary_of(product) for product in self._rank(query, filters, limit)]

    def product(self, product_id: str) -> ProductDetails | None:
        return find_product(self.products, self.variants, product_id)

    async def get_product_details(
        self, session: ShoppingSessionContext, product_id: str
    ) -> ProductDetails | None:
        del session
        return self.product(product_id)

    def price_intelligence(self, product_id: str) -> dict[str, Any] | None:
        """A 90-day price series derived from the product id, ending at today's price,
        with a verdict computed from where that price sits in the series' range. Read
        by the storefront's detail panel; the agent never sees it."""
        product = self.product(product_id)
        if product is None or product.price <= 0:
            return None
        digest = hashlib.sha256(product_id.encode("utf-8")).digest()
        amplitude = product.price * (0.06 + (digest[0] / 255) * 0.08)
        phase = (digest[1] / 255) * 2 * math.pi
        drift = ((digest[2] / 255) - 0.5) * 0.5
        points = 13
        series = []
        for i in range(points):
            wobble = math.sin(phase + i * 1.1) + 0.4 * math.sin(phase * 2 + i * 2.3)
            trend = drift * (i - points + 1) / points
            series.append(round(max(product.price + amplitude * (wobble / 1.4 + trend), 0.5), 2))
        series[-1] = product.price
        low, high = min(series), max(series)
        if high - low < 0.01:
            position = "typical"
        else:
            ratio = (product.price - low) / (high - low)
            position = "low" if ratio <= 0.25 else "high" if ratio >= 0.75 else "typical"
        verdict = {
            "low": f"¥{product.price:.2f} 接近该商品 90 天最低价",
            "typical": f"¥{product.price:.2f} 处于该商品的常见价位",
            "high": f"¥{product.price:.2f} 高于该商品的常见价位",
        }[position]
        return {
            "days": 90,
            "series": series,
            "low": low,
            "high": high,
            "position": position,
            "verdict": f"{verdict}（90 天区间 ¥{low:.0f}–¥{high:.0f}）",
        }

    def review_aspects(self, product_id: str) -> dict[str, Any] | None:
        """Review-aspect chips derived from the product id, with sentiment anchored to
        its rating and mention counts bounded by its review count. Detail panel only."""
        product = self.listing_of(product_id)
        if product is None or not product.review_count or product.review_count < 25:
            return None
        digest = hashlib.sha256(f"aspects:{product.product_id}".encode()).digest()
        names = _ASPECTS_BY_CATEGORY.get(product.category or "", _ASPECTS_FALLBACK)
        count = 3 if len(names) < 4 or digest[0] % 2 == 0 else 4
        rating = product.rating or 4.2
        mention_share = 0.32 + (digest[1] / 255) * 0.2
        aspects = []
        for i, name in enumerate(names[:count]):
            jitter = (digest[2 + i] / 255 - 0.5) * 14
            positive_pct = round(min(97.0, max(45.0, rating * 20 - 4 + jitter - i * 3)))
            share = mention_share * (0.45 if i == 0 else 0.55 / max(count - 1, 1))
            floor = min(12, product.review_count // (count + 1))
            mentions = max(int(product.review_count * share), floor, 1)
            aspects.append({"name": name, "positive_pct": int(positive_pct), "mentions": mentions})
        return {"review_count": product.review_count, "aspects": aspects}

    # ------------------------------------------------------------------
    # Cart
    # ------------------------------------------------------------------

    def _with_catalog_currency(self, cart: Cart) -> Cart:
        # The catalog is priced in CNY; the shared SessionCarts type defaults to USD.
        # Every cart read/write must carry the catalog's currency, not just get_cart —
        # otherwise the cart_update event from an add stages US$ prices in the UI.
        catalog_currency = next((p.currency for p in self.products.values() if p.currency), "CNY")
        return cart.model_copy(update={"currency": catalog_currency})

    async def get_cart(self, session: ShoppingSessionContext) -> Cart:
        return self._with_catalog_currency(self._carts.cart(session.session_id))

    async def add_to_cart(
        self, session: ShoppingSessionContext, product_id: str, quantity: int
    ) -> Cart:
        product = self.product(product_id)
        if product is None or product.has_options:
            # The executor's gates hold both cases before they reach a backend; a real
            # cart service refuses them on its own terms too.
            raise KeyError(product_id)
        if not product.in_stock:
            raise Unavailable(unavailable_detail(product, self.listing_of(product_id)))
        existing = self._carts.lines(session.session_id).get(product_id)
        quantity += existing.quantity if existing else 0
        return self._with_catalog_currency(self._carts.put(session.session_id, product, quantity))

    async def update_cart_item(
        self, session: ShoppingSessionContext, product_id: str, quantity: int
    ) -> Cart:
        return self._with_catalog_currency(self._carts.set_quantity(session.session_id, product_id, quantity))

    async def remove_from_cart(self, session: ShoppingSessionContext, product_id: str) -> Cart:
        return self._with_catalog_currency(self._carts.remove(session.session_id, product_id))

    def reset_session(self, session_id: str) -> None:
        self._carts.reset(session_id)

    # ------------------------------------------------------------------
    # Customer, orders, help content, fulfillment
    # ------------------------------------------------------------------

    async def get_preferences(self, session: ShoppingSessionContext) -> UserPreferences:
        return preferences_of(self._users, session.user_id)

    async def get_orders(self, session: ShoppingSessionContext, limit: int = 5) -> list[Order]:
        return orders_for(self._orders, session.user_id, limit)

    async def get_order(self, session: ShoppingSessionContext, order_id: str) -> Order | None:
        return find_order(self._orders, session.user_id, order_id)

    def recent_orders(self, limit: int = 6) -> list[Order]:
        return newest_orders(self._orders, limit)

    async def search_policies(self, session: ShoppingSessionContext, query: str) -> list[Policy]:
        del session
        return search_help(self._policies, query)

    @staticmethod
    def _pickup_eta(now: datetime) -> str:
        """Two hours of preparation from now (or from opening), promised as the top of
        an hour inside store hours, otherwise tomorrow morning."""
        opens = now.replace(hour=_STORE_OPENS, minute=0, second=0, microsecond=0)
        ready = max(now, opens) + timedelta(hours=2)
        if ready.minute or ready.second or ready.microsecond:
            ready = ready.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        if ready.date() != now.date() or ready.hour > _STORE_CLOSES:
            return "明早"
        period = "上午" if ready.hour < 12 else "下午"
        hour12 = ready.hour % 12 or 12
        return f"今天 {period} {hour12} 点前"

    async def get_fulfillment_options(
        self, session: ShoppingSessionContext, product_ids: list[str]
    ) -> list[FulfillmentOption]:
        prefs = await self.get_preferences(session)
        location = prefs.default_location or "您所在地区"
        quoted = [product for pid in product_ids if (product := self.product(pid))]
        standard = STANDARD_SHIPPING
        if sum(product.price for product in quoted) > FREE_SHIPPING_OVER:
            standard = standard.model_copy(update={"fee": 0.0})
        options = [
            standard,
            EXPRESS_SHIPPING,
            FulfillmentOption(
                method="pickup",
                eta=self._pickup_eta(datetime.now()),
                fee=0.0,
                location=f"恒信 {location} 自提点",
            ),
        ]
        if any(
            product.category in _FREIGHT_CATEGORIES and product.price > _FREIGHT_PRICE_FLOOR
            for product in quoted
        ):
            options.append(FREIGHT_SHIPPING)
        return options
