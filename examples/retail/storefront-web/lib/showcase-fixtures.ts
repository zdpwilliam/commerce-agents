// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

/** Products are records from examples/retail/data/catalog.json. */

import type {
  CartPayload,
  CheckoutPayload,
  ComparisonPayload,
  GuidePayload,
  OrderStatusPayload,
  PlanPayload,
  Product,
  ProductsPayload,
} from "./types";

const BLOCK_SET: Product = {
  product_id: "DEN-1048",
  title: "Woodpecker Dental Burs FG Assorted Kit",
  brand: "Woodpecker",
  price: 220.0,
  currency: "CNY",
  rating: 4.2,
  review_count: 436,
  category: "consumables",
  labels: [],
  attributes: {type: "burs", shank: "FG", grit: "assorted", sterile: "single-use"},
  in_stock: true,
  short_description: "Assorted friction-grip burs for cavity preparation and finishing; single-use for a sharp cut.",
  long_description: "Assorted friction-grip burs for cavity preparation and finishing; single-use for a sharp cut. Supplied sterile and backed by clinical support for dental professionals.",
};

const PUZZLE: Product = {
  product_id: "DEN-1017",
  title: "Woodpecker i Led Curing Light",
  brand: "Woodpecker",
  price: 1500.0,
  currency: "CNY",
  rating: 4.3,
  review_count: 1689,
  category: "restorative",
  labels: ["bestseller"],
  attributes: {type: "curing light", wavelength: "420-480 nm", power: "1200 mW/cm2", light: "LED"},
  in_stock: true,
  short_description: "LED curing light with a broad spectrum and a quick, even cure across composite shades.",
  long_description: "LED curing light with a broad spectrum and a quick, even cure across composite shades. Supplied sterile and backed by clinical support for dental professionals.",
};

const POSTER_SET: Product = {
  product_id: "DEN-1029",
  title: "Shining Aoralscan3 Intraoral Scanner",
  brand: "Shining3D",
  price: 40000.0,
  currency: "CNY",
  rating: 4.7,
  review_count: 2133,
  category: "imaging",
  labels: ["bestseller"],
  attributes: {type: "intraoral scanner", accuracy: "high", color: "full-color", tip: "auto-heating"},
  in_stock: true,
  short_description: "Intraoral scanner with full-color capture and fast, accurate full-arch scanning.",
  long_description: "Intraoral scanner with full-color capture and fast, accurate full-arch scanning. Supplied sterile and backed by clinical support for dental professionals.",
};

const WALL_DECALS: Product = {
  product_id: "DEN-1001",
  title: "NSK Pana-Max2 M4 High-Speed Turbine Handpiece",
  brand: "NSK",
  price: 860.0,
  currency: "CNY",
  rating: 4.3,
  review_count: 1097,
  category: "handpieces",
  labels: [],
  attributes: {speed: "400,000 rpm", connection: "4-hole", head: "standard", sterilization: "autoclavable"},
  in_stock: true,
  short_description: "Fast, quiet turbine with a compact head for routine cavity prep; ceramic bearings and a clean-air system.",
  long_description: "Fast, quiet turbine with a compact head for routine cavity prep; ceramic bearings and a clean-air system. Supplied sterile and backed by clinical support for dental professionals.",
};

const STORYBOOK_BEAR: Product = {
  product_id: "DEN-1005",
  title: "Foshan Jingmei L Low-Speed Handpiece",
  brand: "Foshan Jingmei",
  price: 350.0,
  currency: "CNY",
  rating: 4.7,
  review_count: 1245,
  category: "handpieces",
  labels: ["new"],
  attributes: {speed: "20,000 rpm", connection: "4-hole", type: "low-speed", sterilization: "autoclavable"},
  in_stock: true,
  short_description: "Low-speed handpiece for polishing, finishing and slow-speed preparation.",
  long_description: "Low-speed handpiece for polishing, finishing and slow-speed preparation. Supplied sterile and backed by clinical support for dental professionals.",
};

const STORAGE_BINS: Product = {
  product_id: "DEN-1011",
  title: "Woodpecker Ai-Pex Apex Locator",
  brand: "Woodpecker",
  price: 2590.0,
  currency: "CNY",
  rating: 4.5,
  review_count: 1467,
  category: "endodontics",
  labels: ["bestseller"],
  attributes: {type: "apex locator", display: "LCD", accuracy: "±0.1 mm", power: "battery"},
  in_stock: true,
  short_description: "Apex locator with a bright display and stable readings even in a wet canal.",
  long_description: "Apex locator with a bright display and stable readings even in a wet canal. Supplied sterile and backed by clinical support for dental professionals.",
};

const products: ProductsPayload = {
  title: "Gifts for a 9-Year-Old Builder (~$45)",
  layout: "carousel",
  items: [
    {
      product: BLOCK_SET,
      reason: "Bestseller with idea cards that turn a pile into bridges and towns.",
    },
    {
      product: PUZZLE,
      reason: "An afternoon at the table with a frame-worthy finish.",
    },
    {
      product: POSTER_SET,
      reason: "Reference-wall decor that answers her questions.",
    },
    {
      product: STORYBOOK_BEAR,
      reason: "The soft option — the bear that ends up in every photo.",
    },
  ],
};

const comparison: ComparisonPayload = {
  title: "Block Set vs. Puzzle for a 9-Year-Old",
  entries: [
    {
      product_id: "DEN-1048",
      product: BLOCK_SET,
      best_for: "Active, hands-on building and a kid who rebuilds bigger every time",
      pros: [
        "Solid beechwood — no small parts to snap, survives being stepped on",
        "Water-based paint holds up through a year of rough play (per reviews)",
        "Idea cards add structure without turning play into homework",
      ],
      cons: ["54 pieces to keep track of", "Carry sack fills fast during cleanup races"],
    },
    {
      product_id: "DEN-1017",
      product: PUZZLE,
      best_for: "Quiet-table focus and a kid who loves finishing things",
      pros: [
        "300 pieces sits right at the 8+ sweet spot",
        "Original meadow art — frame-worthy once finished",
        "The calm-afternoon gift parents thank you for",
      ],
      cons: [
        "Cardboard — less durable than solid wood if bent",
        "Mostly a one-builder activity at the table",
      ],
    },
  ],
  dimensions: ["Sturdiness", "Age appropriateness (9)", "Play engagement", "Price"],
  recommended_product_id: "DEN-1048",
};

const plan: PlanPayload = {
  title: "Kids' Room Refresh",
  intro: "Three coordinated steps that turn the spare wall into the fun wall.",
  steps: [
    { label: "The centerpiece", detail: "One hero piece the room hangs off", products: [WALL_DECALS] },
    { label: "The soft layer", detail: "Something to hug during story time", products: [STORYBOOK_BEAR] },
    { label: "The cleanup game", detail: "Bins that make sorting part of play", products: [STORAGE_BINS] },
    {
      label: "Already covered: the reading nook",
      detail: "Your beanbag fits the corner as-is — nothing to buy.",
      products: [],
    },
  ],
};

const guide: GuidePayload = {
  title: "Keeping plush toys clean",
  sections: [
    {
      heading: "Machine washing",
      body: "Plush with embroidered eyes and sewn seams can go through a gentle cold cycle in a pillowcase. Air-dry fully before it goes back to bed duty.",
    },
    {
      heading: "Between washes",
      body: "A lint roller and ten minutes in the sun handle most weeks. Spot-clean spills right away so they don't set into the pile.",
    },
  ],
  related_products: [STORYBOOK_BEAR],
};

const order_status: OrderStatusPayload = {
  order_id: "DN-77903",
  summary:
    "The ACME Paws Orthopedic Dog Bed was placed June 10 and is marked delayed — the delivery estimate was revised to June 27 after the original June 21 date was missed.",
  next_step: "Track the package for the latest carrier update, or ask me about your options.",
  order: {
    order_id: "DN-77903",
    status: "delayed",
    placed_at: "2026-06-10",
    items: [
      {
        product_id: "DEN-1005",
        title: "ACME Paws Orthopedic Memory Foam Dog Bed, Large",
        quantity: 1,
        price: 79.0,
      },
    ],
    total: 79.0,
    currency: "USD",
    // Same shape as the orders fixture: current estimate first, missed original in the note.
    estimated_delivery:
      "2026-06-27 (updated after a carrier delay; the original 2026-06-21 estimate was missed)",
    tracking_url: "https://track.example.com/DN-77903",
  },
};

const checkout: CheckoutPayload = {
  note: "Both gifts are in stock and ship together.",
  fulfillment_method: "delivery",
  cart: {
    items: [
      {
        product_id: "DEN-1048",
        title: "ACME Playroom Stacking Wooden Block Set (54 pc)",
        price: 34.0,
        quantity: 1,
        image_url: "/products/DEN-1048.webp",
        line_total: 34.0,
      },
      {
        product_id: "DEN-1017",
        title: "ACME Makers 300-Piece Meadow Puzzle",
        price: 27.0,
        quantity: 1,
        image_url: "/products/DEN-1017.webp",
        line_total: 27.0,
      },
    ],
    item_count: 2,
    subtotal: 61.0,
    currency: "USD",
  },
};

export const SHOWCASE = { products, comparison, plan, guide, order_status, checkout };

/** Just under the free-shipping threshold. */
export const SHOWCASE_CART: CartPayload = {
  items: [
    {
      product_id: "DEN-1048",
      title: "ACME Playroom Stacking Wooden Block Set (54 pc)",
      price: 34.0,
      quantity: 1,
      image_url: "/products/DEN-1048.webp",
      line_total: 34.0,
    },
    {
      product_id: "DEN-1011",
      title: "ACME Pantry Weeknight Stir-Fry Dinner Kit",
      price: 12.0,
      quantity: 1,
      line_total: 12.0,
    },
  ],
  item_count: 2,
  subtotal: 46.0,
  currency: "USD",
};
