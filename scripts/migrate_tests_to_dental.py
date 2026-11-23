"""One-off: remap reference tests from the old retail fixtures to the dental catalog.

Run from the repo root:
    python scripts/migrate_tests_to_dental.py

The dental catalog keeps the same *roles* the tests need (a plain in-stock product, an
out-of-stock product, a low-stock product, a family with variants), so the tests still
guard the same behavior with dental data.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ID remap: preserve roles.
# - family / variants -> the implant-kit family
# - generic in-stock product -> curing light / handpiece
# - out-of-stock -> an out-of-stock handpiece
# - low-stock overlay row -> the low-stock burs
IDS = {
    "AR-1902": "DEN-1050",
    "AR-1902-KING": "DEN-1050-FULL",
    "AR-1902-QUEEN": "DEN-1050-GRAFT",
    "AR-1902-TWIN": "DEN-1050-BASIC",
    "AR-1902-FULL": "DEN-1050-FULL",
    "AR-1606": "DEN-1050",
    "AR-1606-KING-BLUSH": "DEN-1050-FULL",
    "AR-1105": "DEN-1001",
    "AR-1301": "DEN-1017",
    "AR-1201": "DEN-1003",
    "AR-1202": "DEN-1004",
    "AR-1203": "DEN-1005",
    "AR-1207": "DEN-1002",
    "AR-1307": "DEN-1032",
    "AR-1401": "DEN-1029",
    "AR-1507": "DEN-1026",
    "AR-1508": "DEN-1019",
    "AR-1601": "DEN-1020",
    "AR-1602": "DEN-1021",
    "AR-1801": "DEN-1030",
    "AR-1804": "DEN-1031",
    "AR-2003": "DEN-1048",
    "AR-2102": "DEN-1048",
    "AR-2106": "DEN-1010",
    "AR-0000": "DEN-0000",
    "AR-00000": "DEN-00000",
    "AR-9999": "DEN-9999",
    "AR-1": "DEN-1",
    "AR-2": "DEN-2",
    "AR-3": "DEN-3",
}

# Search queries with a known lead product, remapped to dental terms that lead to the
# dental product now occupying that ID's role.
QUERIES = {
    '"headphones"': '"handpiece"',
    '"tent for two people"': '"high-speed handpiece"',
    '"wooden block set for a 9 year old"': '"curing light"',
    '"carry-on luggage"': '"intraoral scanner"',
    '"hiking backpack for overnight trips"': '"implant handpiece"',
    '"camping tent"': '"dental handpiece"',
    '"sleeping bag camping"': '"dental handpiece"',
    '"tent stove cooler"': '"dental"',
    '"fitness"': '"restorative"',
    '"coffee"': '"handpiece"',
    '"yoga mat"': '"curing light"',
    '"coffee maker"': '"curing light"',
    '"king mattress"': '"implant kit"',
    '"hybrid mattress"': '"implant kit"',
    '"tent"': '"handpiece"',
    '"tents"': '"handpieces"',
}

# Brand / store / category tokens remapped to dental.
TOKENS = {
    '"ACME Basecamp"': '"NSK"',
    '"ACME"': '"ACME Dental"',
    "'ACME'": "'ACME Dental'",
    '"outdoor-camping"': '"handpieces"',
    '"office-electronics"': '"handpieces"',
    '"furniture-bedroom"': '"units"',
    '"home-kitchen"': '"restorative"',
    '"fitness"': '"restorative"',
    '"beauty-personal-care"': '"restorative"',
    '"pet-supplies"': '"consumables"',
    '"toys-games"': '"consumables"',
    '"gift"': '"consumables"',
}

FILES = [
    *ROOT.glob("conftest.py"),
    *ROOT.glob("tests/**/*.py"),
    *ROOT.glob("examples/demo_common/tests/**/*.py"),
    *ROOT.glob("examples/retail/api/tests/**/*.py"),
    *ROOT.glob("shopping-agent/**/tests/**/*.py"),
    *ROOT.glob("merchant-agent/**/tests/**/*.py"),
]


def main() -> None:
    changed = []
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        orig = text
        # Replace the longest ids first so variant ids are not clobbered by their family.
        for old in sorted(IDS, key=len, reverse=True):
            text = text.replace(old, IDS[old])
        for old, new in QUERIES.items():
            text = text.replace(old, new)
        for old, new in TOKENS.items():
            text = text.replace(old, new)
        if text != orig:
            path.write_text(text, encoding="utf-8")
            changed.append(str(path.relative_to(ROOT)))
    print(f"migrated {len(changed)} files")
    for name in changed:
        print("  ", name)


if __name__ == "__main__":
    main()
