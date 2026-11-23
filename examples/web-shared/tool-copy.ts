// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

const TOOL_COPY_EN: Record<string, string> = {
  search_products: "Searching the catalog…",
  get_product_details: "Reading the details…",
  search_policies: "Checking the policies…",
  get_orders: "Looking up your orders…",
  get_order_status: "Looking up your orders…",
  get_fulfillment_options: "Checking delivery and pickup options…",
  get_cart: "Checking the cart…",
  add_to_cart: "Updating the cart…",
  update_cart_item: "Updating the cart…",
  remove_from_cart: "Updating the cart…",
  checkout: "Preparing your order summary…",
  get_preferences: "Reading your profile…",
  recall_memories: "Recalling what you've told me…",
  save_memory: "Saving that for next time…",
  load_skill: "Loading…",
  web_search: "Searching the web…",
  get_business_snapshot: "Reading the business snapshot…",
  query_metrics: "Querying metrics…",
  search_listings: "Searching the listings…",
  get_listing: "Reading the listing…",
  get_inventory_alerts: "Checking inventory alerts…",
  get_order_issues: "Checking order issues…",
  get_pricing_context: "Reading the pricing context…",
  get_campaign_performance: "Reading campaign performance…",
  get_pending_changes: "Checking pending changes…",
  run_analysis: "Running the analysis…",
  apply_change: "Applying the change…",
  discard_change: "Discarding the change…",
};

const COPY_ZH: Record<string, string> = {
  "Searching the catalog…": "正在搜索商品目录…", "Reading the details…": "正在读取详情…",
  "Checking the policies…": "正在查询政策…", "Looking up your orders…": "正在查询订单…",
  "Checking delivery and pickup options…": "正在查询配送与自提选项…", "Checking the cart…": "正在查看购物车…",
  "Updating the cart…": "正在更新购物车…", "Preparing your order summary…": "正在准备订单摘要…",
  "Reading your profile…": "正在读取您的资料…", "Recalling what you've told me…": "正在回忆您告诉我的内容…",
  "Saving that for next time…": "正在为下次保存…", "Loading…": "加载中…", "Searching the web…": "正在搜索网络…",
  "Reading the business snapshot…": "正在读取业务概览…", "Querying metrics…": "正在查询指标…",
  "Searching the listings…": "正在搜索商品…", "Reading the listing…": "正在读取商品…",
  "Checking inventory alerts…": "正在检查库存预警…", "Checking order issues…": "正在检查订单问题…",
  "Reading the pricing context…": "正在读取定价信息…", "Reading campaign performance…": "正在读取活动表现…",
  "Checking pending changes…": "正在检查待审变更…", "Running the analysis…": "正在运行分析…",
  "Applying the change…": "正在应用变更…", "Discarding the change…": "正在放弃变更…",
  "Composing the answer…": "正在组织回答…", "Staging a change for review…": "正在暂存变更以供审核…",
};
const COPY_JA: Record<string, string> = {
  "Searching the catalog…": "カタログを検索中…", "Reading the details…": "詳細を読み取り中…",
  "Checking the policies…": "規約を確認中…", "Looking up your orders…": "注文を検索中…",
  "Checking delivery and pickup options…": "配送・受取方法を確認中…", "Checking the cart…": "カートを確認中…",
  "Updating the cart…": "カートを更新中…", "Preparing your order summary…": "注文内容を準備中…",
  "Reading your profile…": "プロフィールを読み取り中…", "Recalling what you've told me…": "お話しいただいた内容を思い出し中…",
  "Saving that for next time…": "次回のために保存中…", "Loading…": "読み込み中…", "Searching the web…": "ウェブを検索中…",
  "Reading the business snapshot…": "事業概要を読み取り中…", "Querying metrics…": "指標を照会中…",
  "Searching the listings…": "商品を検索中…", "Reading the listing…": "商品を読み取り中…",
  "Checking inventory alerts…": "在庫アラートを確認中…", "Checking order issues…": "注文の問題を確認中…",
  "Reading the pricing context…": "価格情報を読み取り中…", "Reading campaign performance…": "キャンペーン実績を読み取り中…",
  "Checking pending changes…": "保留中の変更を確認中…", "Running the analysis…": "分析を実行中…",
  "Applying the change…": "変更を適用中…", "Discarding the change…": "変更を破棄中…",
  "Composing the answer…": "回答を作成中…", "Staging a change for review…": "レビュー用に変更を準備中…",
};
const COPY_KO: Record<string, string> = {
  "Searching the catalog…": "카탈로그 검색 중…", "Reading the details…": "상세 정보 확인 중…",
  "Checking the policies…": "정책 확인 중…", "Looking up your orders…": "주문 조회 중…",
  "Checking delivery and pickup options…": "배송 및 수령 옵션 확인 중…", "Checking the cart…": "장바구니 확인 중…",
  "Updating the cart…": "장바구니 업데이트 중…", "Preparing your order summary…": "주문 요약 준비 중…",
  "Reading your profile…": "프로필 확인 중…", "Recalling what you've told me…": "말씀하신 내용을 확인 중…",
  "Saving that for next time…": "다음에 사용하도록 저장 중…", "Loading…": "불러오는 중…", "Searching the web…": "웹 검색 중…",
  "Reading the business snapshot…": "비즈니스 개요 확인 중…", "Querying metrics…": "지표 조회 중…",
  "Searching the listings…": "상품 검색 중…", "Reading the listing…": "상품 확인 중…",
  "Checking inventory alerts…": "재고 알림 확인 중…", "Checking order issues…": "주문 문제 확인 중…",
  "Reading the pricing context…": "가격 정보 확인 중…", "Reading campaign performance…": "캠페인 실적 확인 중…",
  "Checking pending changes…": "대기 중인 변경 확인 중…", "Running the analysis…": "분석 실행 중…",
  "Applying the change…": "변경 적용 중…", "Discarding the change…": "변경 취소 중…",
  "Composing the answer…": "답변 작성 중…", "Staging a change for review…": "검토용 변경 준비 중…",
};

const TRANSLATIONS: Record<string, Record<string, string>> = { zh: COPY_ZH, ja: COPY_JA, ko: COPY_KO };

// The activity pipeline calls describeToolCall without a language argument. The provider
// sets this once per app; a browser tab is one session, so a module-level choice is safe.
let currentLanguage = "en";
export function setToolCopyLanguage(language: string): void {
  currentLanguage = language === "zh" || language === "ja" || language === "ko" ? language : "en";
}

const QUERY_TOOLS = new Set(["search_products", "search_policies", "search_listings", "web_search"]);

export function describeToolCall(tool: string, input: Record<string, unknown> = {}): string {
  const base = TOOL_COPY_EN[tool];
  const copy = base ? (TRANSLATIONS[currentLanguage]?.[base] ?? base) : undefined;
  const query = typeof input.query === "string" ? input.query.trim() : "";
  if (copy && query && QUERY_TOOLS.has(tool)) {
    return `${copy.replace(/…$/, "")} · “${query}”`;
  }
  if (copy) return copy;
  if (tool.startsWith("present_")) {
    return currentLanguage === "en" ? "Composing the answer…" : (TRANSLATIONS[currentLanguage]?.["Composing the answer…"] ?? "Composing the answer…");
  }
  if (tool.startsWith("stage_")) {
    return currentLanguage === "en" ? "Staging a change for review…" : (TRANSLATIONS[currentLanguage]?.["Staging a change for review…"] ?? "Staging a change for review…");
  }
  return `${tool.replaceAll("_", " ")}…`;
}
