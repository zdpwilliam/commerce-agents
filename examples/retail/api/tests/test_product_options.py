# Copyright 2026 Anthropic PBC
# SPDX-License-Identifier: Apache-2.0

"""Products with options over HTTP: listings, the detail route, and the add button."""

import pytest

from demo_common.tests.fixtures import session_record
from retail.api import main


@pytest.fixture
def add(client, shopper):
    """Returns ``add(product_id, *seen) -> (response, session record)``."""

    def _add(product_id: str, *seen: str):
        headers = shopper(*seen)
        body = {"product_id": product_id, "quantity": 1}
        return client.post("/api/cart/add", json=body, headers=headers), session_record(
            main, headers
        )

    return _add


def test_listings_carry_the_family_and_none_of_its_variants(client):
    products = client.get("/api/products", params={"category": "耗材配件"}).json()["products"]
    ids = {product["product_id"] for product in products}
    assert "DEN-1050" in ids and not {pid for pid in ids if pid.startswith("DEN-1050-")}
    family = next(product for product in products if product["product_id"] == "DEN-1050")
    assert family["options"] == {"configuration": ["基础配置", "含骨粉", "全套"]}
    assert "variants" not in family


def test_the_detail_route_resolves_a_family_and_a_variant(client):
    family = client.get("/api/products/DEN-1050").json()
    assert [v["product_id"] for v in family["variants"]] == [
        "DEN-1050-BASIC",
        "DEN-1050-GRAFT",
        "DEN-1050-FULL",
    ]
    assert family["variants"][1]["in_stock"] is False
    variant = client.get("/api/products/DEN-1050-FULL").json()
    assert variant["variant_of"] == "DEN-1050" and variant["price"] == 29800.0
    assert variant["price_intelligence"] and variant["review_aspects"]


def test_the_add_button_on_a_family_is_held_with_the_route_to_a_variant(add):
    response, record = add("DEN-1050", "DEN-1050")
    assert response.status_code == 400
    assert "规格" in response.json()["detail"]
    assert record.pending_app_events == []


def test_the_add_button_on_a_seen_variant_writes_a_line_with_its_choice(add):
    response, record = add("DEN-1050-FULL", "DEN-1050", "DEN-1050-FULL")
    assert response.status_code == 200
    [line] = response.json()["cart"]["items"]
    assert line["product_id"] == "DEN-1050-FULL"
    assert line["option_values"] == {"configuration": "全套"} and line["variant_of"] == "DEN-1050"
    assert "DEN-1050-FULL" in record.pending_app_events[0]


def test_a_sold_out_variant_is_refused_with_its_in_stock_siblings_named(add):
    response, record = add("DEN-1050-GRAFT", "DEN-1050", "DEN-1050-GRAFT")
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "DEN-1050-GRAFT 已售罄" in detail and "DEN-1050-FULL" in detail
    assert record.pending_app_events == []
