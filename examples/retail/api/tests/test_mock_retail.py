# Copyright 2026 Anthropic PBC
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime

from commerce_common.types import MemoryCategory, MemoryFact
from demo_common.storefront_fixtures import load_json
from retail.api.mock_retail import (
    DATA_DIR,
    FREE_SHIPPING_OVER,
    FREIGHT_SHIPPING,
    STANDARD_SHIPPING,
    MockRetail,
)
from shopping_agent import SearchFilters


def test_catalog_loads_and_validates(backend):
    assert len(backend.products) >= 50
    assert backend.store_name == "ACME 牙科"
    sample = backend.products["DEN-1003"]
    assert sample.brand == "Foshan Jingmei"
    assert sample.long_description  # hero products carry a long description


async def test_search_relevance(backend, session):
    tents = await backend.search_products(session, "高速手机")
    assert tents and tents[0].product_id in {"DEN-1003", "DEN-1004"}

    gift_toys = await backend.search_products(session, "光固化")
    assert gift_toys and gift_toys[0].product_id == "DEN-1022"

    luggage = await backend.search_products(session, "扫描仪")
    assert any(p.product_id == "DEN-1030" for p in luggage[:3])

    nothing = await backend.search_products(session, "zzzqqq")
    assert nothing == []


async def test_out_of_stock_items_are_searchable(backend, session):
    packs = await backend.search_products(session, "高速手机")
    assert any(p.product_id == "DEN-1002" and p.in_stock is False for p in packs)


async def test_delivery_promises_stamped(backend):
    for product in backend.products.values():
        promise = product.attributes.get("delivery")
        if product.in_stock:
            assert promise is not None and promise.startswith("预计")
        else:
            assert promise is None

    # The promise is kept out of search scoring.
    sample = next(p for p in backend.products.values() if p.in_stock)
    assert "Get it by" not in backend._searchable_text(sample)["attributes"]


def test_memory_seed_is_schema_valid():
    seed = load_json(DATA_DIR, "memory-seed.json")
    assert "demo-user" in seed
    for facts in seed.values():
        for raw in facts:
            fact = MemoryFact(
                key=raw["key"], value=raw["value"], category=MemoryCategory(raw["category"])
            )
            assert fact.key and fact.value


async def test_search_filters_and_sort(backend, session):
    cheap_coffee = await backend.search_products(session, "高速手机", SearchFilters(max_price=100))
    assert all(p.price <= 100 for p in cheap_coffee)
    assert all(p.product_id != "DEN-1002" for p in cheap_coffee)

    outdoor_only = await backend.search_products(
        session, "高速手机", SearchFilters(category="牙科手机"), limit=20
    )
    assert outdoor_only and all(p.category == "牙科手机" for p in outdoor_only)

    by_price = await backend.search_products(
        session, "restorative", SearchFilters(sort="price_asc"), limit=20
    )
    prices = [p.price for p in by_price]
    assert prices == sorted(prices)


async def test_policy_search(backend, session):
    returns = await backend.search_policies(session, "how do refunds and returns work")
    assert returns and returns[0].policy_id == "returns"

    membership = await backend.search_policies(session, "how much does membership cost per year")
    assert any(p.policy_id == "membership" for p in membership)


async def test_fulfillment_options_follow_the_shipping_policy(backend, session):
    options = await backend.get_fulfillment_options(session, ["DEN-1001"])
    assert [o.method for o in options] == ["delivery", "delivery", "pickup"]
    standard, express, _pickup = options
    assert backend.products["DEN-1001"].price > FREE_SHIPPING_OVER and standard.fee == 0.0
    cheapest = min(backend.products.values(), key=lambda p: p.price)
    (paid, *_rest) = await backend.get_fulfillment_options(session, [cheapest.product_id])
    assert paid.fee == STANDARD_SHIPPING.fee

    freight = await backend.get_fulfillment_options(session, ["DEN-1032"])
    assert freight[-1] == FREIGHT_SHIPPING

    shipping = next(p for p in backend._policies if p.policy_id == "shipping").content
    for term in (
        f"¥{STANDARD_SHIPPING.fee:.0f}",
        f"满 ¥{FREE_SHIPPING_OVER} 免运费",
        "3-5 个工作日",
        "2 个工作日",
        f"¥{express.fee:.0f}",
        "货运",
    ):
        assert term in shipping, term


def test_pickup_eta_stays_inside_store_hours():
    eta = MockRetail._pickup_eta
    # Two hours of prep, rounded up to the hour.
    assert eta(datetime(2026, 7, 14, 13, 0)) == "今天 下午 3 点前"
    assert eta(datetime(2026, 7, 14, 13, 20)) == "今天 下午 4 点前"
    # Before opening, the two hours count from the 9 AM open.
    assert eta(datetime(2026, 7, 14, 6, 30)) == "今天 上午 11 点前"
    # 19:00 plus two hours lands on the 9 PM close.
    assert eta(datetime(2026, 7, 14, 19, 0)) == "今天 下午 9 点前"
    assert eta(datetime(2026, 7, 14, 19, 30)) == "明早"
    assert eta(datetime(2026, 7, 14, 23, 0)) == "明早"


async def test_a_family_is_found_by_its_option_values_and_its_variants_stay_out_of_listings(
    backend, session
):
    assert "DEN-1050" in backend.products and "DEN-1050-FULL" not in backend.products
    assert backend.variants["DEN-1050-FULL"].variant_of == "DEN-1050"
    hits = await backend.search_products(session, "种植套件")
    assert hits and hits[0].product_id == "DEN-1050"
    assert hits[0].options == {"configuration": ["基础配置", "含骨粉", "全套"]}
    assert all(hit.variant_of is None for hit in hits)


async def test_details_resolve_a_family_and_a_variant(backend, session):
    family = await backend.get_product_details(session, "DEN-1050")
    assert family is not None and set(family.options) == {"configuration"}
    assert len(family.variants) == 3
    assert all(set(v.option_values) == {"configuration"} for v in family.variants)
    variant = await backend.get_product_details(session, "DEN-1050-FULL")
    assert variant is not None and variant.variant_of == "DEN-1050"
    assert variant.in_stock is True and variant.price == 29800.0
    assert backend.listing_of("DEN-1050-FULL") is family


async def test_an_order_line_for_a_variant_names_its_choice(backend, session):
    orders = await backend.get_orders(session)
    lines = [item for order in orders for item in order.items if item.variant_of]
    assert [(i.product_id, i.option_values, i.variant_of) for i in lines] == [
        ("DEN-1050-GRAFT", {"configuration": "含骨粉"}, "DEN-1050")
    ]
