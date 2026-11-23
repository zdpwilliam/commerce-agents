// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

const TOOL_COPY: Record<string, string> = {
  search_products: "正在搜索商品目录…",
  get_product_details: "正在读取商品详情…",
  search_policies: "正在查询门店政策…",
  get_orders: "正在查询订单…",
  get_order_status: "正在查询订单状态…",
  get_fulfillment_options: "正在查询配送与自提选项…",
  get_cart: "正在查看购物车…",
  add_to_cart: "正在更新购物车…",
  update_cart_item: "正在更新购物车…",
  remove_from_cart: "正在更新购物车…",
  checkout: "正在准备订单摘要…",
  get_preferences: "正在读取您的资料…",
  recall_memories: "正在回忆您告诉我的内容…",
  save_memory: "正在为您记住…",
  load_skill: "正在加载…",
  web_search: "正在搜索网络…",
  get_business_snapshot: "正在读取业务概览…",
  query_metrics: "正在查询经营指标…",
  search_listings: "正在搜索商品…",
  get_listing: "正在读取商品信息…",
  get_inventory_alerts: "正在检查库存预警…",
  get_order_issues: "正在检查订单问题…",
  get_pricing_context: "正在读取定价信息…",
  get_campaign_performance: "正在读取活动表现…",
  get_pending_changes: "正在检查待审变更…",
  run_analysis: "正在运行分析…",
  apply_change: "正在应用变更…",
  discard_change: "正在放弃变更…",
};

const QUERY_TOOLS = new Set([
  "search_products",
  "search_policies",
  "search_listings",
  "web_search",
]);

export function describeToolCall(tool: string, input: Record<string, unknown> = {}): string {
  const copy = TOOL_COPY[tool];
  const query = typeof input.query === "string" ? input.query.trim() : "";
  if (copy && query && QUERY_TOOLS.has(tool)) {
    return `${copy.replace(/…$/, "")}：“${query}”`;
  }
  if (copy) return copy;
  if (tool.startsWith("present_")) return "正在组织回答…";
  if (tool.startsWith("stage_")) return "正在暂存变更以供审核…";
  return `${tool.replaceAll("_", " ")}…`;
}
