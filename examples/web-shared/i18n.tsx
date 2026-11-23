// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

"use client";

import { createContext, useContext, type ReactNode } from "react";
import { setFormatLocale } from "./format";
import { setToolCopyLanguage } from "./tool-copy";

export type Lang = "en" | "zh" | "ja" | "ko";

export const LANGUAGES: { id: Lang; label: string; short: string }[] = [
  { id: "en", label: "English", short: "EN" },
  { id: "zh", label: "中文", short: "中" },
  { id: "ja", label: "日本語", short: "日" },
  { id: "ko", label: "한국어", short: "한" },
];

export const LOCALES: Record<Lang, string> = {
  en: "en-US",
  zh: "zh-CN",
  ja: "ja-JP",
  ko: "ko-KR",
};

export function asLang(value: string | undefined): Lang {
  return value === "zh" || value === "ja" || value === "ko" ? value : "en";
}

// UI strings. Keyed by the English source; unknown keys render the key itself, so an
// untranslated string degrades to the original English rather than disappearing.
type Row = Partial<Record<Lang, string>>;
const DICT: Record<string, Row> = {
  // storefront shell
  Assistant: { zh: "助手", ja: "アシスタント", ko: "어시스턴트" },
  Orders: { zh: "订单", ja: "注文", ko: "주문" },
  Cart: { zh: "购物车", ja: "カート", ko: "장바구니" },
  item: { zh: "件", ja: "点", ko: "개" },
  Guest: { zh: "访客", ja: "ゲスト", ko: "손님" },
  "Ask about an order, a return, a delivery…": { zh: "询问订单、退货或配送…", ja: "注文・返品・配送について質問…", ko: "주문, 반품, 배송에 대해 질문…" },
  "Ask about a product, a project, an order…": { zh: "询问商品、方案或订单…", ja: "商品・プラン・注文について質問…", ko: "상품, 계획, 주문에 대해 질문…" },
  "All orders": { zh: "全部订单", ja: "すべての注文", ko: "모든 주문" },
  "running late": { zh: "即将延迟", ja: "遅延気味", ko: "지연 예정" },
  "on the way": { zh: "配送中", ja: "配送中", ko: "배송 중" },
  // portal shell
  Home: { zh: "首页", ja: "ホーム", ko: "홈" },
  Catalog: { zh: "商品目录", ja: "カタログ", ko: "카탈로그" },
  Inventory: { zh: "库存", ja: "在庫", ko: "재고" },
  "Merchant workspace": { zh: "商家工作台", ja: "加盟店ワークスペース", ko: "판매자 작업 공간" },
  "Store manager": { zh: "店长", ja: "店長", ko: "매장 관리자" },
  Operator: { zh: "操作员", ja: "オペレーター", ko: "운영자" },
  "Business memory": { zh: "业务记忆", ja: "ビジネスメモリ", ko: "비즈니스 메모리" },
  "Merchant assistant": { zh: "商家助手", ja: "加盟店アシスタント", ko: "판매자 어시스턴트" },
  // home view
  "Hello": { zh: "您好", ja: "こんにちは", ko: "안녕하세요" },
  "order": { zh: "笔订单", ja: "件の注文", ko: "건의 주문" },
  "the next arrives": { zh: "下一笔预计到达", ja: "次の到着は", ko: "다음 도착 예정은" },
  "Ask about a product, a project, an order, or a return.": { zh: "可以询问商品、方案、订单或退货。", ja: "商品・プラン・注文・返品について質問できます。", ko: "상품, 계획, 주문, 반품에 대해 질문할 수 있습니다." },
  "Nothing is on the way right now. Ask about a product, a project, or a return.": { zh: "目前没有在途订单。可以询问商品、方案或退货。", ja: "現在配送中の注文はありません。商品・プラン・返品について質問できます。", ko: "현재 배송 중인 주문이 없습니다. 상품, 계획, 반품에 대해 질문할 수 있습니다." },
  "Popular right now": { zh: "热门商品", ja: "人気の商品", ko: "인기 상품" },
  "Bestsellers and new arrivals; open one to ask about it": { zh: "畅销与新品；点开即可咨询", ja: "ベストセラーと新着；開いて詳細を確認", ko: "베스트셀러와 신상품; 열어서 자세히 보기" },
  "Tell me about the": { zh: "介绍一下", ja: "について教えて", ko: "에 대해 알려줘" },
  "Ask why, or ask about a return on anything delivered.": { zh: "可以询问原因，或对已送达商品申请退货。", ja: "理由を確認するか、配達済みの返品について質問できます。", ko: "이유를 묻거나 배송 완료된 상품의 반품에 대해 질문할 수 있습니다." },
  "Ask about any of them, or about a return on anything delivered.": { zh: "可以询问其中任意一笔，或对已送达商品申请退货。", ja: "いずれかについて質問するか、配達済みの返品について質問できます。", ko: "그중 하나에 대해 묻거나 배송 완료된 상품의 반품에 대해 질문할 수 있습니다." },
};

export function translate(language: string, key: string): string {
  const lang = asLang(language);
  if (lang === "en") return key;
  return DICT[key]?.[lang] ?? key;
}

interface I18nValue {
  language: Lang;
  t: (key: string) => string;
  locale: string;
  setLanguage: (language: Lang) => Promise<void>;
}

const I18nContext = createContext<I18nValue>({
  language: "en",
  t: (key) => key,
  locale: "en-US",
  setLanguage: async () => {},
});

export function useI18n(): I18nValue {
  return useContext(I18nContext);
}

/** Wraps a retail app. `api` drives the in-place session PATCH; `onChange` re-renders
 * data that came from the server (catalog, cart) so it follows the new language. */
export function I18nProvider({
  api,
  language,
  onChange,
  children,
}: {
  api: { setLanguage: (language: string) => Promise<boolean> };
  language: string;
  onChange: (language: Lang) => void;
  children: ReactNode;
}) {
  const lang = asLang(language);
  setToolCopyLanguage(lang);
  setFormatLocale(LOCALES[lang]);
  const value: I18nValue = {
    language: lang,
    locale: LOCALES[lang],
    t: (key: string) => translate(lang, key),
    setLanguage: async (next: Lang) => {
      const ok = await api.setLanguage(next);
      if (ok) onChange(next);
    },
  };
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

/** Four-way toggle for the session language. */
export function LanguageSwitcher() {
  const { language, setLanguage } = useI18n();
  return (
    <div className="flex items-center gap-1" role="group" aria-label="Language">
      {LANGUAGES.map((option) => (
        <button
          key={option.id}
          type="button"
          onClick={() => void setLanguage(option.id)}
          aria-pressed={language === option.id}
          title={option.label}
          className={`rounded-md px-2 py-1 text-[12px] font-medium transition-colors ${
            language === option.id
              ? "bg-(--ink) text-(--surface)"
              : "text-(--ink-soft) hover:bg-(--ink)/8"
          }`}
        >
          {option.short}
        </button>
      ))}
    </div>
  );
}
