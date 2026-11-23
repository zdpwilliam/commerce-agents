// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

/** 与 ../data/policies.json 保持一致；修改时请同步更新该文件。 */
export const STORE_POLICY = {
  returnsShort: "30 天退货",
  returnsLine: "未开封、无菌密封的器械可在送达后 30 天内退货，全额退还至原支付方式。已安装或使用过的设备、定制商品及已开封的耗材，除质量问题外不可退货。",
  freeShippingThreshold: 500,
  standardShippingEta: "3-5 个工作日",
} as const;
