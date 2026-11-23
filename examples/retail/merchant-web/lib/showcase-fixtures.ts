// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

/** 复制自 data/ 下的商家 fixture。 */

import type { ChangePreviewPayload, DigestPayload } from "./types";

const digest: DigestPayload = {
  title: "早间摘要",
  items: [
    {
      kind: "low_stock",
      ref_id: "DEN-1048",
      headline: "啄木鸟车针套装（DEN-1048）仅剩 3 件 — 库存不足两天",
      why_it_matters: "每月约售出 52 件；照此速度本周将售罄。",
      listing: {
        listing_id: "DEN-1048",
        title: "啄木鸟 FG 车针混合装",
        status: "active",
        price: 220.0,
        stock: 3,
      },
    },
    {
      kind: "order_issue",
      ref_id: "DN-80417",
      headline: "本周种植套件出现六笔退货，均提到骨粉数量不足",
      why_it_matters: "热销商品退货激增通常意味着商品描述存在信息缺口。",
    },
    {
      kind: "metric",
      headline: "根管治疗品类销售额环比增长 21%",
      why_it_matters: "大部分提升来自根管治疗产品线的增长。",
    },
  ],
};

const change_preview: ChangePreviewPayload = {
  change_id: "chg-3021",
  headline: "在售罄前补货啄木鸟车针套装",
  note: "按近期销售速度，补货后可恢复约一个月的库存覆盖。",
  change: {
    change_id: "chg-3021",
    kind: "inventory_action",
    status: "staged",
    summary: "为啄木鸟 FG 车针混合装（DEN-1048）增加 52 件",
    items: [{ target: "DEN-1048", field: "stock", before: 3, after: 55 }],
    created_at: "2026-07-09",
    created_by: "助手",
    created_by_kind: "agent",
  },
};

export const SHOWCASE = { digest, change_preview };
