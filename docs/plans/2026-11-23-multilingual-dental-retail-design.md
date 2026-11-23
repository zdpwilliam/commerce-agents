# Multilingual dental retail design

This design turns the retail vertical into a four-language dental instrument storefront.
Languages are Simplified Chinese (`zh`), English (`en`), Japanese (`ja`), and Korean
(`ko`). The catalog becomes 50 dental instruments with real brands and list prices from
public procurement records. Only the retail vertical changes; travel, telecom, and
entertainment stay as they are.

## Decisions

| Dimension | Decision |
|---|---|
| Scope | Retail storefront and merchant portal only |
| Languages | `zh`, `en`, `ja`, `ko`, across conversation, catalog data, and web UI |
| Language state | A field on the session; switching updates it in place and keeps the cart and transcript |
| Agent language | Injected into the fenced dynamic context; the static prompt gains one rule |
| Catalog | 50 real dental instruments; real brand, model, and price; other fields constructed per category |
| Currency | CNY |
| Translation | A separate translation table, applied by a wrapper at read time; `Product` and the three runtimes stay unchanged |

## Language data flow

The language switcher writes `language` to the session through `PATCH /api/session`.
Three consumers read it from the same record and need no direct coupling to each other:

```
language switcher
      |
      v
PATCH /api/session { language }  ->  SessionRecord.language (persisted)
      |
      +--> web UI: i18n dictionary, locale-formatted dates, CNY money
      |
      +--> backend: translation layer localizes the localized catalog fields
      |
      +--> agent: build_dynamic_context emits response_language in the fence
```

The static prompt and `tools[]` do not change per request. Only the fenced block gains a
`response_language` field, so the cache breakpoint holds and `scripts/check.py` stays
stable after `system.md` is re-derived once. The Messages API, Agent SDK, and Managed
Agents paths share the backend and `build_dynamic_context`, so they inherit the behavior.

## Language state and switching

`SessionRecord` gains `language: str = "en"`. `state_document()` persists it, so a switch
is a write to the live session, not a new one.

`PATCH /api/session` accepts `{ language }`, loads the record through `CurrentSession`,
sets `record.language`, and relies on the dependency to write it back at request end.
`StartSessionRequest` gains an optional `language` taken from the browser's stored choice
on first load.

`StorefrontHost.context()` passes `record.language` into `ShoppingSessionContext`, which
gains the same field. `build_dynamic_context` adds a `response_language` label such as
`中文` or `日本語` to the fenced payload. The static prompt gains one rule: answer in the
language named by `response_language`, and keep product identifiers, model numbers, and
prices verbatim.

The merchant portal has its own session in `demo_common/merchant.py` and needs the
parallel field, route, and context wiring. Its prompt gains the same language rule.

When the language changes, the fence's `cart.items[].title` and `seen_products` titles are
re-localized through the same translation function, so the agent's next turn does not read
a stale-language title. Past transcript text is not rewritten; earlier messages keep the
language they were written in.

## Catalog data

`examples/retail/data/catalog.json` holds 50 dental instruments in eight categories:

| Category | Examples |
|---|---|
| Handpieces | NSK Pana-Max2 M4, Foshan Jingmei J1Plus-004, implant handpiece CX235C6 |
| Endodontics | Woodpecker Endo Radar Pro, Ai-Pex apex locator, Fi-E/Fi-P gutta-percha filler |
| Restorative curing | Woodpecker i Led, Weirun VAFU, Dentsply Demiplus |
| Periodontics | Weirun DA-20 ultrasonic scaler, PT-A air polisher |
| Imaging | Shining Aoralscan3 intraoral scanner, APSARAS 3D CBCT, DOM4000D endo microscope |
| Treatment units | Xino S2313, A-J15 A15 dental chair |
| Sterilization | Xinhua MOST-T autoclave, TQX-200BH ultrasonic cleaner |
| Consumables | burs, gutta-percha points, impression material, handpiece oiler |

`product_id` uses a `DEN-1001` sequence. `brand`, `model`, and `price` come from the
procurement records; `price` is CNY. `rating` and `review_count` are constructed per
category. `attributes` carry instrument specifications such as speed and power.
`short_description` and `long_description` are authored in English as the single source.
`image_url` points to a local placeholder; procurement records carry no usable image and
real product photos carry licensing risk.

`merchant_inventory.json`, `merchant_metrics.json`, `merchant_campaigns.json`, and
`merchant_messages.json` are updated to reference dental SKUs. Localizable listing fields
use the same translation table.

## Translation layer

A new `data/translations.json` maps each `product_id` to `zh`, `ja`, and `ko` values for
`title`, `short_description`, `long_description`, and `attributes` (both keys and values).
English stays in the catalog and is not duplicated in the table.

A new `examples/retail/api/i18n.py` exposes
`localize_products(products, language) -> list[Product]`. It reads the table and returns
each product with its localizable fields replaced through `model_copy(update=...)`;
`product_id`, `price`, `rating`, and other identifiers are untouched. The backend wraps
`search_products` and `get_product_details` with this function. The `Product` model and
all three runtimes need no change.

## Web UI

A new `web-shared/i18n.ts` exports the `Lang` type, a `useI18n()` hook, and the four
dictionaries. The dictionaries cover tool-copy strings, shell labels, and order nouns.
Date formatting follows the locale; `formatMoney` renders CNY with `¥`.

`useSession` starts one session and stores the language choice in `localStorage`.
`AgentApi.setLanguage(lang)` calls `PATCH /api/session` and keeps the same `sessionId`.
A `LanguageSwitcher` on the storefront and portal calls it, updates the i18n state, and
re-fetches catalog data. It does not restart the session, clear the cart, or clear the
transcript.

## Files to change

- Data: `examples/retail/data/catalog.json`; new `translations.json`; the `merchant_*.json` files.
- Translation: new `examples/retail/api/i18n.py`; `mock_retail.py` read wrappers.
- Session and context: `demo_common/sessions.py`, `storefront.py`, `merchant.py`;
  `shopping_agent/types.py`, `prompt.py`; `retail/api/agent_config.py`.
- Web: new `web-shared/i18n.ts`; `api.ts`, `session.ts`, `tool-copy.ts`, `format.ts`;
  the retail storefront and portal `page.tsx` files.

## Verification

1. Re-derive `system.md` after the prompt change, then run `python scripts/check.py`.
2. Run `ruff check . && ruff format --check . && pytest`. The gate, grounding, and
   serialization suites are the regression focus: localization must not change
   `product_id` or provenance behavior.
3. Add tests for the four-language table coverage, the session PATCH updating language
   without dropping state, and the `response_language` field in the dynamic context.
4. Run `python scripts/run_demo.py retail` and check that switching language updates the
   UI, the agent's replies, and the catalog descriptions while the cart and conversation
   remain.

## Out of scope

Travel, telecom, and entertainment. Runtime-specific configuration for SDK and Managed
Agents, which inherit the behavior through the shared backend. A persistent crawler; the
50 records are authored into the catalog once.
