// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

"use client";

import { useCallback, useEffect, useState } from "react";
import {
  ArrivingPanel,
  estimateOf,
  Greeting,
  greeting,
  HomeSection,
  type Order,
  plural,
  type Starter,
  Starters,
  upcoming,
  useCatalogIndex,
  useI18n,
  useStoreFrame,
} from "web-shared";
import { fetchProducts } from "@/lib/api";
import { NOUNS, OrderThumb } from "@/lib/orders";
import type { Product } from "@/lib/types";
import ProductTile from "../ProductTile";

const STARTERS_EN = [
  "A dental curing light for a general practice, under ¥5000",
  "Compare two high-speed handpieces for posterior access",
  "Set up an endodontics station for a two-chair clinic",
  "Remember: general practice, restorative and endodontics focus",
];
const STARTERS: Record<string, string[]> = {
  zh: [
    "为普通诊所推荐一款牙科光固化机，预算 5000 元以内",
    "比较两款适合后牙操作的高速手机",
    "为双椅位诊所配置一套根管治疗设备",
    "记住：普通诊所，重点是修复和根管治疗",
  ],
  ja: [
    "一般開業用の歯科光硬化機、5000 元以内で",
    "奥歯へのアクセスに適した高速ハンドピースを2機種比較",
    "2チェアの診療所向けに根管治療ステーションを構成",
    "記憶して: 一般診療、修復と根管治療が中心",
  ],
  ko: [
    "일반 진료소용 광중합기, 5000위안 이하로 추천",
    "구치부 접근에 적합한 고속 핸드피스 두 가지 비교",
    "2체어 진료소를 위한 근관 치료 스테이션 구성",
    "기억해줘: 일반 진료, 보철과 근관 치료 중심",
  ],
};
const STARTER_ICONS: Starter["icon"][] = ["search", "home", "tag", "edit"];

/** What the store is featuring: labelled bestseller or new, photographed ones first. */
function featured(catalog: Record<string, Product>): Product[] {
  return Object.values(catalog)
    .filter((product) => product.labels?.some((label) => label === "bestseller" || label === "new") && product.in_stock !== false)
    .sort((a, b) => Number(Boolean(b.image_url)) - Number(Boolean(a.image_url)))
    .slice(0, 4);
}

function Brief({ orders }: { orders: Order[] | null }) {
  const { t } = useI18n();
  if (!orders) return <>{t("Ask about a product, a project, an order, or a return.")}</>;
  const open = upcoming(orders);
  if (!open.length) return <>{t("Nothing is on the way right now. Ask about a product, a project, or a return.")}</>;
  const late = open.filter((order) => order.status === "delayed");
  const next = estimateOf(open.find((order) => order.status !== "delayed") ?? open[0])?.date;
  return (
    <>
      {plural(open.length, t("order"))} {t("on the way")}{next ? `; ${t("the next arrives")} ${next}` : ""}.{" "}
      {late.length ? <span className="font-semibold text-(--warn)">{t("running late")}.</span> : null}
    </>
  );
}

/** The clock is read after mount, so the prerendered page never disagrees with the browser's day. */
function useNow(): Date | null {
  const [now, setNow] = useState<Date | null>(null);
  useEffect(() => setNow(new Date()), []);
  return now;
}

export default function HomeView({
  shopperName,
  orders,
  ordersFailed,
  onSeeOrders,
}: {
  shopperName: string;
  orders: Order[] | null;
  ordersFailed: boolean;
  onSeeOrders: () => void;
}) {
  const { ask } = useStoreFrame();
  const { language, locale, t } = useI18n();
  const load = useCallback(() => fetchProducts(language), [language]);
  const catalog = useCatalogIndex(load);
  const picks = featured(catalog);
  const now = useNow();
  const starters: Starter[] = (STARTERS[language] ?? STARTERS_EN).map((prompt, i) => ({ icon: STARTER_ICONS[i], prompt }));
  return (
    <div className="flex flex-col gap-4">
      <Greeting
        eyebrow={now ? now.toLocaleDateString(locale, { weekday: "long", month: "long", day: "numeric" }) : "\u00a0"}
        title={<h1 className="text-[28px] font-semibold leading-tight tracking-[-0.02em] text-(--ink)">{`${now ? greeting(now) : t("Hello")}, ${shopperName}`}</h1>}
      >
        <Brief orders={orders} />
      </Greeting>
      <Starters items={starters} />
      <ArrivingPanel orders={orders} failed={ordersFailed} nouns={NOUNS} thumb={(order) => <OrderThumb order={order} />} onSeeAll={onSeeOrders} />
      {picks.length ? (
        <HomeSection title={t("Popular right now")} subtitle={t("Bestsellers and new arrivals; open one to ask about it")}>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {picks.map((product) => (
              <ProductTile key={product.product_id} product={product} fluid onOpen={(item) => ask(t("Tell me about the").concat(" ", item.title, "."))} />
            ))}
          </div>
        </HomeSection>
      ) : null}
    </div>
  );
}
