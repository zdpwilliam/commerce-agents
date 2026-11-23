"""One-off generator for the retail dental-instrument catalog.

Brands, models, categories and CNY list prices come from public Chinese dental-equipment
procurement awards collected in November 2026. Ratings, review counts, attributes and
descriptions are authored per category for the demo. Run from the repo root:

    python scripts/build_dental_catalog.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "examples" / "retail" / "data" / "catalog.json"

# (title_en, brand, model, price_cny, category, attributes, short_description_en)
ROWS: list[tuple[str, str, str, float, str, dict[str, str], str]] = [
    # --- handpieces (8) ---
    (
        "NSK Pana-Max2 M4 High-Speed Turbine Handpiece",
        "NSK",
        "Pana-Max2 M4",
        860.0,
        "handpieces",
        {
            "speed": "400,000 rpm",
            "connection": "4-hole",
            "head": "standard",
            "sterilization": "autoclavable",
        },
        "Fast, quiet turbine with a compact head for routine cavity prep; ceramic bearings and a clean-air system.",
    ),
    (
        "NSK Ti-Max X95L High-Speed Handpiece",
        "NSK",
        "Ti-Max X95L",
        1480.0,
        "handpieces",
        {"speed": "400,000 rpm", "connection": "6-hole", "head": "miniature", "light": "LED"},
        "Titanium miniature head with LED for posterior access; ceramic bearings and a strong, steady cut.",
    ),
    (
        "Foshan Jingmei J1Plus-004 High-Speed Handpiece",
        "Foshan Jingmei",
        "J1Plus-004",
        450.0,
        "handpieces",
        {
            "speed": "350,000 rpm",
            "connection": "4-hole",
            "head": "standard",
            "sterilization": "autoclavable",
        },
        "Durable turbine handpiece built for daily clinic use; dependable speed at a value price.",
    ),
    (
        "Foshan Jingmei J45-204 Angle High-Speed Handpiece",
        "Foshan Jingmei",
        "J45-204",
        950.0,
        "handpieces",
        {"speed": "350,000 rpm", "connection": "4-hole", "head": "angle", "angle": "45 degrees"},
        "45-degree angled head reaches the back teeth comfortably without sacrificing cutting power.",
    ),
    (
        "Foshan Jingmei L Low-Speed Handpiece",
        "Foshan Jingmei",
        "L",
        350.0,
        "handpieces",
        {
            "speed": "20,000 rpm",
            "connection": "4-hole",
            "type": "low-speed",
            "sterilization": "autoclavable",
        },
        "Low-speed handpiece for polishing, finishing and slow-speed preparation.",
    ),
    (
        "Woodpecker CX235C7 Extraction Angle",
        "Woodpecker",
        "CX235C7",
        2150.0,
        "handpieces",
        {
            "type": "surgical angle",
            "connection": "ISO",
            "use": "extraction",
            "sterilization": "autoclavable",
        },
        "Surgical angle for atraumatic extraction; strong, steady torque in a slim profile.",
    ),
    (
        "Woodpecker CX235C6 Implant Handpiece",
        "Woodpecker",
        "CX235C6",
        2100.0,
        "handpieces",
        {
            "type": "implant handpiece",
            "connection": "ISO",
            "use": "implant",
            "sterilization": "autoclavable",
        },
        "Implant handpiece with controlled torque for a steadyosteotomy and precise placement.",
    ),
    (
        "NSK WP-1L Implant Handpiece",
        "NSK",
        "WP-1L",
        5000.0,
        "handpieces",
        {"type": "implant handpiece", "connection": "ISO", "light": "LED", "use": "implant"},
        "LED implant handpiece for guided surgery; smooth low-speed control and reliable illumination.",
    ),
    # --- endodontics (8) ---
    (
        "Woodpecker Endo Radar Pro Root Canal Motor",
        "Woodpecker",
        "Endo Radar Pro",
        5000.0,
        "endodontics",
        {
            "type": "endodontic motor",
            "torque": "0.5-4 Ncm",
            "speed": "100-1000 rpm",
            "light": "LED",
        },
        "Cordless endodontic motor with a built-in apex locator for accurate, adaptive shaping.",
    ),
    (
        "Dentsply X-SMART Plus Root Canal Motor",
        "Dentsply Sirona",
        "X-SMART Plus",
        24000.0,
        "endodontics",
        {"type": "endodontic motor", "torque": "adjustable", "recall": "yes", "light": "LED"},
        "Endodontic motor with a programmable program memory and a bright operating light.",
    ),
    (
        "Woodpecker Ai-Pex Apex Locator",
        "Woodpecker",
        "Ai-Pex",
        2590.0,
        "endodontics",
        {"type": "apex locator", "display": "LCD", "accuracy": "±0.1 mm", "power": "battery"},
        "Apex locator with a bright display and stable readings even in a wet canal.",
    ),
    (
        "Dentsply PROPEX PIXI Apex Locator",
        "Dentsply Sirona",
        "PROPEX PIXI",
        9800.0,
        "endodontics",
        {"type": "apex locator", "display": "LCD touch", "accuracy": "±0.1 mm", "power": "battery"},
        "Compact apex locator with crisp visual guidance and automatic calibration.",
    ),
    (
        "Woodpecker Fi-E / Fi-P Gutta-Percha Filler",
        "Woodpecker",
        "Fi-E / Fi-P",
        8050.0,
        "endodontics",
        {
            "type": "gutta-percha filler",
            "temperature": "200 C",
            "tips": "multiple",
            "power": "battery",
        },
        "Warm gutta-percha filling system with interchangeable tips for a dense, three-dimensional fill.",
    ),
    (
        "Woodpecker Fi-P Heat Carrier",
        "Woodpecker",
        "Fi-P",
        8000.0,
        "endodontics",
        {"type": "heat carrier", "temperature": "200 C", "use": "downpack", "power": "battery"},
        "Downpack heat carrier that softens and condenses gutta-percha to the apical seal.",
    ),
    (
        "Yusen C-FILL X Gutta-Percha Filler",
        "Yusen",
        "C-FILL X",
        13000.0,
        "endodontics",
        {
            "type": "gutta-percha filler",
            "temperature": "adjustable",
            "tips": "multiple",
            "power": "battery",
        },
        "Cordless obturation system with precise temperature control for consistent fills.",
    ),
    (
        "Woodpecker D600 LED Ultrasonic Endo Unit",
        "Woodpecker",
        "D600 LED",
        5800.0,
        "endodontics",
        {
            "type": "ultrasonic endo unit",
            "light": "LED",
            "power": "ultrasonic",
            "use": "irrigation",
        },
        "Ultrasonic endodontic unit for irrigation and activation with an integrated LED.",
    ),
    # --- restorative / curing (7) ---
    (
        "Woodpecker i Led Curing Light",
        "Woodpecker",
        "i Led",
        1500.0,
        "restorative",
        {
            "type": "curing light",
            "wavelength": "420-480 nm",
            "power": "1200 mW/cm2",
            "light": "LED",
        },
        "LED curing light with a broad spectrum and a quick, even cure across composite shades.",
    ),
    (
        "Woodpecker LED.G Curing Light",
        "Woodpecker",
        "LED.G",
        3000.0,
        "restorative",
        {"type": "curing light", "wavelength": "420-480 nm", "modes": "3", "light": "LED"},
        "Curing light with multiple modes and a slim light guide for tight contact areas.",
    ),
    (
        "Woodpecker O-Star Curing Light",
        "Woodpecker",
        "O-Star",
        2400.0,
        "restorative",
        {
            "type": "curing light",
            "wavelength": "385-515 nm",
            "power": "1500 mW/cm2",
            "light": "LED",
        },
        "Wide-spectrum curing light that cures bulk-fill and conventional composites quickly.",
    ),
    (
        "Eighteeth CuringPen Curing Light",
        "Eighteeth",
        "CuringPen",
        1680.0,
        "restorative",
        {"type": "curing light", "wavelength": "420-480 nm", "modes": "5", "light": "LED"},
        "Pen-style curing light with several programs and a comfortable, balanced grip.",
    ),
    (
        "Dentsply Demiplus Curing Light",
        "Dentsply Sirona",
        "Demiplus",
        6150.0,
        "restorative",
        {
            "type": "curing light",
            "wavelength": "450-470 nm",
            "power": "1100 mW/cm2",
            "light": "LED",
        },
        "Curing light with a broad, even beam and an long-life battery for a full clinic day.",
    ),
    (
        "Weirun VAFU Curing Light",
        "Weirun",
        "VAFU",
        13500.0,
        "restorative",
        {"type": "curing light", "wavelength": "380-515 nm", "power": "high", "light": "LED"},
        "High-output curing light covering a wide spectrum for fast, reliable polymerization.",
    ),
    # --- periodontics (6) ---
    (
        "Woodpecker PT-A Air Polisher",
        "Woodpecker",
        "PT-A",
        19500.0,
        "periodontics",
        {"type": "air polisher", "powder": "supragingival", "water": "yes", "light": "LED"},
        "Air polishing unit for comfortable, effective supragingival biofilm and stain removal.",
    ),
    (
        "Woodpecker PT-B Air Polisher",
        "Woodpecker",
        "PT-B",
        19000.0,
        "periodontics",
        {"type": "air polisher", "powder": "subgingival", "water": "yes", "light": "LED"},
        "Subgingival air polisher with a slim nozzle for periodontal and peri-implant maintenance.",
    ),
    (
        "Woodpecker DA-20 Ultrasonic Scaler",
        "Woodpecker",
        "DA-20",
        1500.0,
        "periodontics",
        {"type": "ultrasonic scaler", "frequency": "30 kHz", "tips": "compatible", "water": "yes"},
        "Ultrasonic scaler with a steady water spray and broad tip compatibility for daily scaling.",
    ),
    (
        "Woodpecker UDS-N2 Ultrasonic Scaler",
        "Woodpecker",
        "UDS-N2",
        8800.0,
        "periodontics",
        {"type": "ultrasonic scaler", "frequency": "30 kHz", "modes": "3", "light": "LED"},
        "Ultrasonic scaler with multiple modes and an LED handpiece for precise calculus removal.",
    ),
    (
        "Woodpecker S6 LED Ultrasonic Scaler",
        "Woodpecker",
        "S6 LED",
        3000.0,
        "periodontics",
        {"type": "ultrasonic scaler", "frequency": "30 kHz", "light": "LED", "water": "yes"},
        "LED ultrasonic scaler with a comfortable grip and efficient scaling action.",
    ),
    (
        "EMS AIRFLOW Prophylaxis Master",
        "EMS",
        "AIRFLOW Prophylaxis Master",
        175000.0,
        "periodontics",
        {"type": "prophylaxis unit", "powder": "subgingival", "water": "yes", "light": "LED"},
        "Guided biofilm therapy unit combining scaling and air polishing for minimally invasive cleaning.",
    ),
    # --- imaging (7) ---
    (
        "Shining Aoralscan3 Intraoral Scanner",
        "Shining3D",
        "Aoralscan3",
        40000.0,
        "imaging",
        {
            "type": "intraoral scanner",
            "accuracy": "high",
            "color": "full-color",
            "tip": "auto-heating",
        },
        "Intraoral scanner with full-color capture and fast, accurate full-arch scanning.",
    ),
    (
        "3Shape TRIOS 5 Intraoral Scanner",
        "3Shape",
        "TRIOS 5",
        190000.0,
        "imaging",
        {"type": "intraoral scanner", "accuracy": "high", "color": "full-color", "wireless": "yes"},
        "Wireless intraoral scanner with real-time color and shade detection for precise restorations.",
    ),
    (
        "3Shape S1P-2 Intraoral Scanner",
        "3Shape",
        "S1P-2",
        190000.0,
        "imaging",
        {"type": "intraoral scanner", "accuracy": "high", "color": "full-color", "tip": "heated"},
        "Intraoral scanner with a heated tip and reliable capture for full-arch impressions.",
    ),
    (
        "Vatech APSARAS 3D CBCT",
        "Vatech",
        "APSARAS 3D",
        264000.0,
        "imaging",
        {"type": "CBCT", "field": "large", "detector": "flat panel", "mode": "3D/2D"},
        "Cone-beam CT with a large field of view for implant planning and 3D diagnosis.",
    ),
    (
        "BlueX RAY98(M) Dental X-Ray Unit",
        "BlueX",
        "RAY98(M)",
        40000.0,
        "imaging",
        {"type": "intraoral X-ray", "power": "high-frequency", "timer": "digital", "arm": "wall"},
        "High-frequency dental X-ray unit with a digital timer for sharp, low-dose radiographs.",
    ),
    (
        "Hainan JYF-10D Digital Dental X-Ray",
        "Hainan",
        "JYF-10D",
        22800.0,
        "imaging",
        {"type": "intraoral X-ray", "power": "high-frequency", "timer": "digital", "arm": "mobile"},
        "Digital dental X-ray unit with a mobile stand for flexible chairside imaging.",
    ),
    (
        "Carestream 3600P Dental X-Ray",
        "Carestream",
        "3600P",
        32000.0,
        "imaging",
        {"type": "intraoral X-ray", "power": "high-frequency", "timer": "digital", "arm": "wall"},
        "Digital panoramic and cephalometric X-ray system for clear, detailed diagnostics.",
    ),
    # --- treatment units (6) ---
    (
        "Xino S2313 Dental Treatment Chair",
        "Xino",
        "S2313",
        25000.0,
        "units",
        {
            "type": "treatment chair",
            "dental_light": "LED",
            "delivery": "cart",
            "upholstery": "leather",
        },
        "Dental treatment chair with an LED light and a smooth, quiet chair adjustment.",
    ),
    (
        "Xino S2313 Implant Treatment Chair",
        "Xino",
        "S2313 (Implant)",
        40000.0,
        "units",
        {
            "type": "implant chair",
            "dental_light": "LED",
            "delivery": "cart",
            "upholstery": "leather",
        },
        "Implant-configured treatment chair with reinforced delivery and a wide recline range.",
    ),
    (
        "A-dec AJ21 Dental Treatment Chair",
        "A-dec",
        "AJ21",
        74500.0,
        "units",
        {
            "type": "treatment chair",
            "dental_light": "LED",
            "delivery": "unit",
            "upholstery": "premium",
        },
        "Treatment chair with an integrated delivery unit and an ergonomic, durable build.",
    ),
    (
        "Belmont CLESTA II Dental Unit",
        "Belmont",
        "CLESTA II",
        129500.0,
        "units",
        {
            "type": "treatment chair",
            "dental_light": "LED",
            "delivery": "unit",
            "upholstery": "premium",
        },
        "Dental unit with a self-returning arm and a cushion-contoured chair for long procedures.",
    ),
    (
        "Zehnder ZA-208B Implant Treatment Chair",
        "Zehnder",
        "ZA-208B",
        89600.0,
        "units",
        {
            "type": "implant chair",
            "dental_light": "LED",
            "delivery": "cart",
            "upholstery": "leather",
        },
        "Implant treatment chair with a wide backrest and an adjustable headrest for oral surgery.",
    ),
    (
        "Hongke H1 Dental Treatment Chair",
        "Hongke",
        "H1",
        51800.0,
        "units",
        {
            "type": "treatment chair",
            "dental_light": "LED",
            "delivery": "cart",
            "upholstery": "leather",
        },
        "Treatment chair with an ergonomic seat and a reliable delivery system for general dentistry.",
    ),
    # --- sterilization (6) ---
    (
        "Xinhua MOST-T Pressure Steam Sterilizer",
        "Xinhua",
        "MOST-T",
        13900.0,
        "sterilization",
        {"type": "autoclave", "capacity": "23 L", "cycle": "standard", "display": "LCD"},
        "Benchtop steam sterilizer with a clear cycle display and dependable spore-safe cycles.",
    ),
    (
        "Xinhua TQX-200BH Ultrasonic Cleaner",
        "Xinhua",
        "TQX-200BH",
        8100.0,
        "sterilization",
        {
            "type": "ultrasonic cleaner",
            "capacity": "large",
            "frequency": "40 kHz",
            "timer": "digital",
        },
        "Ultrasonic cleaner that removes debris from instruments before sterilization.",
    ),
    (
        "Xinhua XZY-02 Handpiece Oiler",
        "Xinhua",
        "XZY-02",
        1600.0,
        "sterilization",
        {
            "type": "handpiece oiler",
            "connection": "ISO",
            "cycles": "automatic",
            "power": "electric",
        },
        "Automatic handpiece oiler that lubricates and purges turbines after each cycle.",
    ),
    (
        "Xinhua FK-100 Pouch Sealer",
        "Xinhua",
        "FK-100",
        2000.0,
        "sterilization",
        {"type": "pouch sealer", "width": "seal", "temperature": "adjustable", "power": "electric"},
        "Pouch sealing machine for secure, traceable sterile packaging.",
    ),
    (
        "Hongrun HYT-500 Positive Pressure Unit",
        "Hongrun",
        "HYT-500",
        20000.0,
        "sterilization",
        {
            "type": "positive pressure unit",
            "output": "clean air",
            "use": "clinic",
            "power": "electric",
        },
        "Positive-pressure unit that keeps the clinic air clean and protected.",
    ),
    (
        "Aojie AJ/DL-B-1000 Air Disinfector",
        "Aojie",
        "AJ/DL-B-1000",
        3450.0,
        "sterilization",
        {"type": "air disinfector", "coverage": "clinic", "mode": "plasma", "power": "electric"},
        "Air disinfector with a plasma mode for steady, quiet clinic sanitation.",
    ),
    # --- consumables (2 base + one family with variants) ---
    (
        "Woodpecker Dental Burs FG Assorted Kit",
        "Woodpecker",
        "FG Assorted",
        220.0,
        "consumables",
        {"type": "burs", "shank": "FG", "grit": "assorted", "sterile": "single-use"},
        "Assorted friction-grip burs for cavity preparation and finishing; single-use for a sharp cut.",
    ),
    (
        "Eighteeth Gutta-Percha Points 0.06 Taper",
        "Eighteeth",
        "GP 0.06",
        125.0,
        "consumables",
        {"type": "gutta-percha points", "taper": "0.06", "sizes": "assorted", "sterile": "yes"},
        "Gutta-percha points with a 0.06 taper for a dense, predictable root canal fill.",
    ),
]

# One family demonstrating the option/variant flow: an implant kit sold in three configurations.
FAMILY = {
    "product_id": "DEN-1050",
    "title": "Woodpecker Implant Kit with Bone Graft Material",
    "brand": "Woodpecker",
    "price": 19700.0,
    "category": "consumables",
    "labels": ["bestseller"],
    "attributes": {"type": "implant kit", "contents": "drills + graft", "sterile": "yes"},
    "in_stock": True,
    "short_description": "Implant kit with drills, graft material and membranes; choose a configuration to match the case.",
    "variants": [
        {
            "product_id": "DEN-1050-BASIC",
            "option_values": {"configuration": "basic"},
            "price": 19700.0,
        },
        {
            "product_id": "DEN-1050-GRAFT",
            "option_values": {"configuration": "with graft"},
            "price": 24500.0,
        },
        {
            "product_id": "DEN-1050-FULL",
            "option_values": {"configuration": "full kit"},
            "price": 29800.0,
        },
    ],
}


def build() -> None:
    products: list[dict] = []
    seq = 1001
    for title, brand, model, price, category, attributes, short in ROWS:
        # Deterministic, category-tinted rating/count for a believable demo.
        rating = round(4.2 + (seq % 8) * 0.1, 1)
        review_count = 60 + (seq * 37) % 2400
        products.append(
            {
                "product_id": f"DEN-{seq}",
                "title": title,
                "brand": brand,
                "model": model,
                "price": price,
                "currency": "CNY",
                "rating": rating,
                "review_count": review_count,
                "category": category,
                "labels": ["new" if seq % 5 == 0 else "bestseller"] if seq % 3 == 0 else [],
                "attributes": attributes,
                "in_stock": seq % 11 != 0,
                "short_description": short,
                "long_description": short
                + " Supplied sterile and backed by clinical support for dental professionals.",
            }
        )
        seq += 1
    products.append(FAMILY)
    assert len([p for p in products if "variants" not in p]) == len(ROWS), "base count mismatch"
    assert len(products) == 50, f"expected 50 products, got {len(products)}"
    OUT.write_text(
        json.dumps(
            {"store_name": "ACME Dental", "products": products}, ensure_ascii=False, indent=1
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(products)} products to {OUT}")


if __name__ == "__main__":
    build()
