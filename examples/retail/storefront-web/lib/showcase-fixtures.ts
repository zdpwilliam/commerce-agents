// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

/** 商品来自 examples/retail/data/catalog.json 的记录。 */

import type {
  CartPayload, CheckoutPayload, ComparisonPayload, GuidePayload, OrderStatusPayload,
  PlanPayload, Product, ProductsPayload,
} from "./types";

const BUR_KIT: Product = {
  product_id: "DEN-1048",
  title: "啄木鸟 FG 车针混合装",
  brand: "Woodpecker",
  price: 220.0,
  currency: "CNY",
  image_url: "/products/pexels-6627456.jpg",
  rating: 4.2,
  review_count: 436,
  category: "耗材配件",
  labels: [],
  attributes: {"类型": "车针", "柄型": "FG 柄", "粒度": "混合装", "无菌": "一次性"},
  in_stock: true,
  short_description: "FG 柄车针混合装，用于备牙与修整，单次使用保持锋利。",
};;

const CURING_LIGHT: Product = {
  product_id: "DEN-1017",
  title: "啄木鸟 i Led 光固化机",
  brand: "Woodpecker",
  price: 1500.0,
  currency: "CNY",
  image_url: "/products/pexels-31188650.jpg",
  rating: 4.3,
  review_count: 1689,
  category: "修复固化",
  labels: ["热销"],
  attributes: {"类型": "光固化机", "波长": "420-480 nm", "功率": "1200 mW/cm2", "照明": "LED 照明"},
  in_stock: true,
  short_description: "LED 光固化机，光谱宽、固化快，各色树脂均匀固化。",
};;

const SCANNER: Product = {
  product_id: "DEN-1029",
  title: "先临 Aoralscan3 口内扫描仪",
  brand: "Shining3D",
  price: 40000.0,
  currency: "CNY",
  image_url: "/products/pexels-6501852.jpg",
  rating: 4.7,
  review_count: 2133,
  category: "影像设备",
  labels: ["热销"],
  attributes: {"类型": "口内扫描仪", "精度": "高", "色彩": "全彩", "工作尖": "自动加热"},
  in_stock: true,
  short_description: "口内扫描仪，全彩捕捉，全口扫描快速精准。",
};;

const HANDPIECE: Product = {
  product_id: "DEN-1001",
  title: "NSK Pana-Max2 M4 高速涡轮手机",
  brand: "NSK",
  price: 860.0,
  currency: "CNY",
  image_url: "/products/pexels-6502661.jpg",
  rating: 4.3,
  review_count: 1097,
  category: "牙科手机",
  labels: [],
  attributes: {"转速": "400,000 rpm", "接口": "4 孔", "机头": "标准", "灭菌方式": "可高温高压灭菌"},
  in_stock: true,
  short_description: "紧凑机头，转速平稳安静，适合常规备牙；陶瓷轴承与气路清洁系统。",
};;

const LOW_SPEED: Product = {
  product_id: "DEN-1005",
  title: "佛山精美 L 低速手机",
  brand: "Foshan Jingmei",
  price: 350.0,
  currency: "CNY",
  image_url: "/products/pexels-6502549.jpg",
  rating: 4.7,
  review_count: 1245,
  category: "牙科手机",
  labels: ["新品"],
  attributes: {"转速": "20,000 rpm", "接口": "4 孔", "类型": "低速", "灭菌方式": "可高温高压灭菌"},
  in_stock: true,
  short_description: "用于抛光、修整和低速备牙的低速手机。",
};;

const APEX_LOCATOR: Product = {
  product_id: "DEN-1011",
  title: "啄木鸟 Ai-Pex 根尖定位仪",
  brand: "Woodpecker",
  price: 2590.0,
  currency: "CNY",
  image_url: "/products/pexels-6529107.jpg",
  rating: 4.5,
  review_count: 1467,
  category: "根管治疗",
  labels: ["热销"],
  attributes: {"类型": "根尖定位仪", "显示屏": "LCD 屏", "精度": "±0.1 mm", "功率": "电池供电"},
  in_stock: true,
  short_description: "亮屏根尖定位仪，湿性根管内读数依然稳定。",
};;

const products: ProductsPayload = {
  title: "诊所常用器械精选",
  layout: "carousel",
  items: [
    { product: BUR_KIT, reason: "备牙与修整的常备耗材，单次使用始终锋利。" },
    { product: CURING_LIGHT, reason: "光谱宽、固化快，各色树脂均匀固化。" },
    { product: SCANNER, reason: "全彩捕捉，全口扫描快速精准。" },
    { product: APEX_LOCATOR, reason: "亮屏显示，湿性根管内读数依然稳定。" },
  ],
};

const comparison: ComparisonPayload = {
  title: "高速手机 vs. 低速手机：如何选",
  entries: [
    {
      product_id: "DEN-1001",
      product: HANDPIECE,
      best_for: "常规备牙、牙冠预备，追求转速与效率",
      pros: ["40 万转/分钟，切削有力", "紧凑机头，后牙区易操作", "可高温高压灭菌，陶瓷轴承更耐用"],
      cons: ["需匹配 4 孔接口", "价格高于低速手机"],
    },
    {
      product_id: "DEN-1005",
      product: LOW_SPEED,
      best_for: "抛光、修整及低速备牙",
      pros: ["低速平稳，适合精细修整", "价格亲民", "同样可高温高压灭菌"],
      cons: ["不适合快速切削", "功能相对单一"],
    },
  ],
  dimensions: ["适用场景", "转速", "灭菌方式", "价格"],
  recommended_product_id: "DEN-1001",
};

const plan: PlanPayload = {
  title: "根管治疗工作站配置",
  intro: "三步配齐根管治疗的核心设备，覆盖定位、成形与充填。",
  steps: [
    { label: "精准定位", detail: "根尖定位仪，湿性根管读数稳定", products: [APEX_LOCATOR] },
    { label: "高效成形", detail: "根管马达配合机头，成形精准", products: [HANDPIECE] },
    { label: "严密充填", detail: "热牙胶充填，三维致密充填", products: [BUR_KIT] },
    { label: "已配备：光固化", detail: "您的光固化机可继续使用，无需重复采购。", products: [] },
  ],
};

const guide: GuidePayload = {
  title: "光固化机的日常维护",
  sections: [
    { heading: "导光棒清洁", body: "每次使用后以酒精棉擦拭导光棒端面，避免树脂残留影响光强输出。" },
    { heading: "电池与存放", body: "避免长时间空置耗尽电量；存放于干燥处，定期做光强检测以确保固化效果。" },
  ],
  related_products: [CURING_LIGHT],
};

const order_status: OrderStatusPayload = {
  order_id: "DN-77903",
  summary: "低速手机订单于 6 月 10 日下单，目前标记为延误——原定 6 月 21 日送达未达成，预计改为 6 月 27 日。",
  next_step: "查看物流获取承运商最新进展，或向我询问可选方案。",
  order: {
    order_id: "DN-77903",
    status: "delayed",
    placed_at: "2026-06-10",
    items: [{ product_id: "DEN-1005", title: "佛山精美 L 低速手机", quantity: 1, price: 350.0 }],
    total: 350.0,
    currency: "CNY",
    estimated_delivery: "2026-06-27（因承运商延误更新；原定 2026-06-21 未达成）",
    tracking_url: "https://track.example.com/DN-77903",
  },
};

const checkout: CheckoutPayload = {
  note: "两件商品均有货，将一同发出。",
  fulfillment_method: "delivery",
  cart: {
    items: [
      { product_id: "DEN-1048", title: "啄木鸟 FG 车针混合装", price: 220.0, quantity: 1, image_url: "/products/pexels-6627456.jpg", line_total: 220.0 },
      { product_id: "DEN-1017", title: "啄木鸟 i Led 光固化机", price: 1500.0, quantity: 1, image_url: "/products/pexels-31188650.jpg", line_total: 1500.0 },
    ],
    item_count: 2,
    subtotal: 1720.0,
    currency: "CNY",
  },
};

export const SHOWCASE = { products, comparison, plan, guide, order_status, checkout };

/** 略低于免运费门槛。 */
export const SHOWCASE_CART: CartPayload = {
  items: [
    { product_id: "DEN-1048", title: "啄木鸟 FG 车针混合装", price: 220.0, quantity: 1, image_url: "/products/pexels-6627456.jpg", line_total: 220.0 },
    { product_id: "DEN-1049", title: "八颗牙 0.06 锥度牙胶尖", price: 125.0, quantity: 1, line_total: 125.0 },
  ],
  item_count: 2,
  subtotal: 345.0,
  currency: "CNY",
  image_url: "/products/pexels-7789653.jpg",
};
