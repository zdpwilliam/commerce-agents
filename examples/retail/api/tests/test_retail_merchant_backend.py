# Copyright 2026 Anthropic PBC
# SPDX-License-Identifier: Apache-2.0

import pytest

from merchant_agent import (
    InventoryActionItem,
    ListingFilters,
    MerchantAgentConfig,
    PriceUpdateItem,
)
from retail.api.mock_merchant import MockRetailMerchant


async def test_snapshot_counts_the_fixture_alerts(merchant, operator_session):
    snapshot = await merchant.get_business_snapshot(operator_session)
    assert snapshot.alerts.low_stock >= 2
    assert snapshot.alerts.order_issues >= 3


async def test_query_metrics_supports_the_kids_room_segment(merchant, operator_session):
    overall = await merchant.query_metrics(operator_session, "sales", "last_7_days")
    kids = await merchant.query_metrics(
        operator_session, "sales", "last_7_days", segment="kids-room"
    )
    assert len(overall.points) == 7
    assert len(kids.points) == 7
    assert sum(p.value for p in kids.points) < sum(p.value for p in overall.points)
    assert kids.segment == "kids-room"


async def test_weekly_granularity_recomputes_ratio_metrics(merchant, operator_session):
    daily = await merchant.query_metrics(operator_session, "conversion_rate", "last_30_days")
    weekly = await merchant.query_metrics(
        operator_session, "conversion_rate", "last_30_days", granularity="week"
    )
    daily_avg = sum(p.value for p in daily.points) / len(daily.points)
    # Seven daily rates summed would be about seven times the daily average.
    assert all(p.value < daily_avg * 2 for p in weekly.points)
    weekly_aov = await merchant.query_metrics(
        operator_session, "average_order_value", "last_30_days", granularity="week"
    )
    assert all(p.value > 0 for p in weekly_aov.points)


async def test_alerts_cover_the_demo_listings(merchant, operator_session):
    alerts = await merchant.get_inventory_alerts(operator_session)
    by_id = {alert.listing_id: alert for alert in alerts}
    assert by_id["DEN-1048"].kind == "low_stock"
    assert by_id["DEN-1010"].kind == "low_stock"
    assert by_id["DEN-1048"].days_of_cover > 0


async def test_storefront_oos_products_are_not_active_in_the_portal(merchant, operator_session):
    # DEN-1025 is paused; DEN-1002 and DEN-1019 are out of stock in the overlay.
    paused = await merchant.get_listing(operator_session, "DEN-1025")
    assert paused.status == "paused"
    for product_id in ("DEN-1002", "DEN-1019"):
        listing = await merchant.get_listing(operator_session, product_id)
        assert listing.status == "out_of_stock"
        assert listing.stock == 0


def test_boot_rejects_a_catalog_vs_overlay_stock_contradiction(backend):
    with pytest.raises(ValueError, match="DEN-1025"):
        broken = MockRetailMerchant(backend, MerchantAgentConfig(brand_name="ACME Dental"))
        broken._inventory["DEN-1025"].pop("status")
        broken._assert_storefront_consistency()


async def test_listing_details_carry_quality_and_review_data(merchant, operator_session):
    listing = await merchant.get_listing(operator_session, "DEN-1048")
    assert listing is not None
    assert listing.content_quality == "needs_work"
    assert listing.stock == 3
    assert listing.missing_attributes
    assert listing.sales_last_30d


async def test_order_issues_load_from_the_messages_fixture(merchant, operator_session):
    issues = await merchant.get_order_issues(operator_session)
    kinds = {issue.kind for issue in issues}
    assert "return_spike" in kinds
    assert any(issue.listing_id == "DEN-1031" for issue in issues)


async def test_applied_restock_is_visible_to_the_storefront(merchant, backend, operator_session):
    before = (await merchant.get_listing(operator_session, "DEN-1048")).stock
    change = await merchant.stage_inventory_action(
        operator_session,
        [InventoryActionItem(listing_id="DEN-1048", action="restock", quantity=24)],
    )
    assert (await merchant.get_listing(operator_session, "DEN-1048")).stock == before  # staged only

    await merchant.apply_change(operator_session, change.change_id)
    after = await merchant.get_listing(operator_session, "DEN-1048")
    assert after.stock == before + 24
    assert backend.products["DEN-1048"].in_stock is True
    assert (await merchant.get_business_snapshot(operator_session)).alerts.low_stock >= 1


async def test_applied_price_change_updates_the_shared_catalog(merchant, backend, operator_session):
    pricing = await merchant.get_pricing_context(operator_session, "DEN-1002")
    new_price = round(pricing.current_price * 0.9, 2)
    change = await merchant.stage_price_update(
        operator_session, [PriceUpdateItem(listing_id="DEN-1002", new_price=new_price)]
    )
    assert change.margin_impact is not None
    assert backend.products["DEN-1002"].price == pricing.current_price

    await merchant.apply_change(operator_session, change.change_id)
    assert backend.products["DEN-1002"].price == new_price


async def test_listing_update_apply_fixes_content_quality(merchant, backend, operator_session):
    change = await merchant.stage_listing_update(
        operator_session,
        "DEN-1048",
        {"short_description": "36 peel-and-stick ocean decals that remove cleanly."},
        note="Refresh the decals listing copy",
    )
    await merchant.apply_change(operator_session, change.change_id)
    listing = await merchant.get_listing(operator_session, "DEN-1048")
    assert listing.short_description.startswith("36 peel-and-stick")
    assert listing.content_quality == "good"
    assert backend.products["DEN-1048"].short_description.startswith("36 peel-and-stick")


async def test_merchant_context_reports_alert_counts(merchant, operator_session):
    context = await merchant.get_merchant_context(operator_session)
    assert context["store"] == "ACME Dental"
    assert context["alerts"]["low_stock"] >= 2


async def test_browse_filters_narrow_the_whole_catalog(merchant, operator_session):
    flagged = await merchant.search_listings(
        operator_session, "", ListingFilters(content_quality="needs_work"), limit=25
    )
    assert {listing.listing_id for listing in flagged} == {"DEN-1048", "DEN-1031"}
    low_stock = await merchant.search_listings(
        operator_session, "all", ListingFilters(max_stock=3), limit=25
    )
    assert any(listing.listing_id == "DEN-1048" for listing in low_stock)


async def test_staged_price_cut_carries_fixture_true_margins(merchant, operator_session):
    # DEN-1048 has a true cost in the overlay; any move within the guardrail carries margins.
    before = (await merchant.get_pricing_context(operator_session, "DEN-1048")).current_price
    new = round(before * 0.95, 2)
    change = await merchant.stage_price_update(
        operator_session, [PriceUpdateItem(listing_id="DEN-1048", new_price=new)]
    )
    assert change.currency == "CNY"
    assert change.margin_before_pct is not None
    assert change.margin_after_pct is not None


async def test_multi_item_price_update_carries_per_item_margin_notes(merchant, operator_session):
    change = await merchant.stage_price_update(
        operator_session,
        [
            PriceUpdateItem(listing_id="DEN-1048", new_price=210.0),
            PriceUpdateItem(listing_id="DEN-1002", new_price=1450.0),
        ],
    )
    # Change-level margins are set for single-listing moves only; multi-item changes get a note per listing.
    assert change.margin_before_pct is None and change.margin_after_pct is None
    assert len([note for note in change.guardrail_notes if "margin" in note]) == 2


def test_kpi_trends_match_the_snapshot_window(merchant):
    """Seven daily points per KPI, ratios recomputed per day."""
    trends = merchant.kpi_trends()
    assert set(trends) == {"sales", "orders", "conversion", "average_order_value"}
    for points in trends.values():
        assert len(points) == 7
    day = trends["sales"][0]
    matching = next(p for p in trends["orders"] if p["date"] == day["date"])
    aov = next(p for p in trends["average_order_value"] if p["date"] == day["date"])
    assert aov["value"] == round(day["value"] / matching["value"], 2)


def test_home_insights_are_deterministic_and_fixture_grounded(merchant):
    first = merchant.home_insights()
    assert first == merchant.home_insights()
    assert 1 <= len(first) <= 3
    for insight in first:
        assert insight["headline"]
        assert insight["prompt"]
    # The fixtures give DEN-1031 an 11% return rate and kids-room a week-over-week move.
    ids = {insight["insight_id"] for insight in first}
    assert "return-rate-DEN-1031" in ids
    assert "segment-trend-kids-room" in ids


# -- listings with options ------------------------------------------------------------


async def test_a_family_listing_reads_as_from_price_summed_stock_and_variant_rows(
    merchant, operator_session
):
    families = [
        x
        for x in await merchant.search_listings(operator_session, "implant kit")
        if x.listing_id == "DEN-1050"
    ]
    assert len(families) == 1
    family = families[0]
    assert family.options == {"configuration": ["basic", "with graft", "full kit"]}
    details = await merchant.get_listing(operator_session, "DEN-1050")
    by_id = {v.listing_id: v for v in details.variants}
    assert set(by_id) == {"DEN-1050-BASIC", "DEN-1050-GRAFT", "DEN-1050-FULL"}
    assert family.price == min(v.price for v in details.variants if v.status == "active")
    assert family.stock == sum(v.stock for v in details.variants)
    assert by_id["DEN-1050-GRAFT"].status == "out_of_stock" and by_id["DEN-1050-GRAFT"].stock == 0
    assert by_id["DEN-1050-GRAFT"].option_values == {"configuration": "with graft"}
    assert all(v.variant_of == "DEN-1050" for v in details.variants)
    variant = await merchant.get_listing(operator_session, "den-1050-full")
    assert (
        variant.listing_id == "DEN-1050-FULL"
        and variant.price == 29800.0
        and variant.variants == []
    )


async def test_pricing_context_prices_a_family_per_variant(merchant, operator_session):
    family = await merchant.get_pricing_context(operator_session, "DEN-1050")
    assert family.unit_cost is None and family.margin_pct is None  # a family has no cost
    assert family.current_price == 19700.0
    assert {v.listing_id for v in family.variants} == {
        "DEN-1050-BASIC",
        "DEN-1050-GRAFT",
        "DEN-1050-FULL",
    }
    full = next(v for v in family.variants if v.listing_id == "DEN-1050-FULL")
    assert full.current_price == 29800.0 and full.unit_cost == 16390.0 and full.margin_pct
    alone = await merchant.get_pricing_context(operator_session, "DEN-1050-FULL")
    assert alone.option_values == {"configuration": "full kit"} and alone.variants == []


async def test_price_and_restock_writes_name_a_variant_and_refresh_the_family(
    merchant, backend, operator_session
):
    with pytest.raises(ValueError, match="per variant"):
        await merchant.stage_price_update(
            operator_session, [PriceUpdateItem(listing_id="DEN-1050", new_price=599)]
        )
    with pytest.raises(ValueError, match="per variant"):
        await merchant.stage_inventory_action(
            operator_session,
            [InventoryActionItem(listing_id="DEN-1050", action="restock", quantity=5)],
        )

    change = await merchant.stage_price_update(
        operator_session, [PriceUpdateItem(listing_id="DEN-1050-BASIC", new_price=19000.0)]
    )
    assert [(i.target, i.before, i.after) for i in change.items] == [
        ("DEN-1050-BASIC", 19700.0, 19000.0)
    ]
    assert change.margin_before_pct is not None  # a single variant carries its margins
    await merchant.apply_change(operator_session, change.change_id)
    assert backend.variants["DEN-1050-BASIC"].price == 19000.0
    # The family's own price follows its lowest in-stock variant.
    assert backend.products["DEN-1050"].price == 19000.0
    assert (await merchant.get_listing(operator_session, "DEN-1050")).price == 19000.0

    restock = await merchant.stage_inventory_action(
        operator_session,
        [InventoryActionItem(listing_id="DEN-1050-FULL", action="restock", quantity=8)],
    )
    await merchant.apply_change(operator_session, restock.change_id)
    assert backend.variants["DEN-1050-FULL"].in_stock is True
    full = await merchant.get_listing(operator_session, "DEN-1050-FULL")
    assert full.stock >= 8 and full.status == "active"


async def test_pausing_a_family_takes_every_variant_off_sale_and_back(
    merchant, backend, operator_session
):
    pause = await merchant.stage_inventory_action(
        operator_session, [InventoryActionItem(listing_id="DEN-1050", action="pause")]
    )
    await merchant.apply_change(operator_session, pause.change_id)
    assert backend.products["DEN-1050"].in_stock is False
    assert not any(v.in_stock for v in backend.products["DEN-1050"].variants)
    assert (await merchant.get_listing(operator_session, "DEN-1050")).status == "paused"

    resume = await merchant.stage_inventory_action(
        operator_session, [InventoryActionItem(listing_id="DEN-1050", action="activate")]
    )
    await merchant.apply_change(operator_session, resume.change_id)
    assert backend.products["DEN-1050"].in_stock is True
    # The variant with no stock stays off sale.
    assert backend.variants["DEN-1050-GRAFT"].in_stock is False


async def test_a_promotion_on_a_family_is_a_promotion_on_each_variant(merchant, operator_session):
    from merchant_agent import PromotionDraft

    change = await merchant.stage_promotion(
        operator_session,
        PromotionDraft(
            name="Sleep week",
            listing_ids=["DEN-1050"],
            discount_pct=10,
            starts="2026-09-01",
            ends="2026-09-07",
        ),
    )
    assert [i.target for i in change.items] == ["DEN-1050-BASIC", "DEN-1050-GRAFT", "DEN-1050-FULL"]
    assert change.items[-1].after == round(29800.0 * 0.9, 2)


async def test_variant_alerts_say_which_variant(merchant, operator_session):
    alerts = await merchant.get_inventory_alerts(operator_session)
    graft = next(a for a in alerts if a.listing_id == "DEN-1050-GRAFT")
    assert graft.option_values == {"configuration": "with graft"}
    assert not any(a.listing_id == "DEN-1050" for a in alerts)  # the family itself never alerts


async def test_a_content_edit_on_a_variant_names_the_family_in_this_catalog(
    merchant, operator_session
):
    from merchant_agent import ChangeNotApplicable

    with pytest.raises(ChangeNotApplicable, match="DEN-1050"):
        await merchant.stage_listing_update(
            operator_session, "DEN-1050-FULL", {"short_description": "Firmer feel."}
        )
    # An attribute the family does not own passes through to the variant.
    change = await merchant.stage_listing_update(
        operator_session, "DEN-1050-FULL", {"sku": "MAT-K"}
    )
    assert [(i.target, i.field, i.after) for i in change.items] == [
        ("DEN-1050-FULL", "sku", "MAT-K")
    ]


async def test_the_store_says_what_it_cannot_supply(merchant, operator_session):
    context = await merchant.get_merchant_context(operator_session)
    assert {entry["source"] for entry in context["limitations"]} == {"campaigns", "orders"}
    campaigns = await merchant.get_campaign_performance(operator_session)
    email = next(c for c in campaigns if c.campaign_id == "C-203")
    # The email channel reports spend and no revenue: None, never a stand-in zero.
    assert email.spend > 0 and email.revenue is None


async def test_a_price_below_the_reported_floor_is_refused(merchant, operator_session):
    from merchant_agent import ChangeNotApplicable, PriceUpdateItem

    context = await merchant.get_pricing_context(operator_session, "DEN-1050-FULL")
    assert context.min_price is not None
    with pytest.raises(ChangeNotApplicable, match="below the floor"):
        await merchant.stage_price_update(
            operator_session,
            [PriceUpdateItem(listing_id="DEN-1050-FULL", new_price=context.min_price - 1)],
        )
