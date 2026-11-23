// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

"use client";

import { useEffect, useState } from "react";
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
  useStoreFrame,
} from "web-shared";
import { fetchProducts } from "@/lib/api";
import { NOUNS, OrderThumb } from "@/lib/orders";
import type { Product } from "@/lib/types";
import ProductTile from "../ProductTile";

const STARTERS: Starter[] = [
  { icon: "search", prompt: "为普通诊所推荐一款牙科光固化机，预算 5000 元以内" },
  { icon: "home", prompt: "比较两款适合后牙操作的高速手机" },
  { icon: "tag", prompt: "为双椅位诊所配置一套根管治疗设备" },
  { icon: "edit", prompt: "记住：普通诊所，重点是修复和根管治疗" },
];

/** What the store is featuring: labelled bestseller or new, photographed ones first. */
function featured(catalog: Record<string, Product>): Product[] {
  return Object.values(catalog)
    .filter((product) => product.labels?.some((label) => label === "热销" || label === "新品") && product.in_stock !== false)
    .sort((a, b) => Number(Boolean(b.image_url)) - Number(Boolean(a.image_url)))
    .slice(0, 4);
}

function Brief({ orders }: { orders: Order[] | null }) {
  if (!orders) return <>可以询问商品、方案、订单或退货。</>;
  const open = upcoming(orders);
  if (!open.length) return <>目前没有在途订单。可以咨询商品、方案或退货。</>;
  const late = open.filter((order) => order.status === "delayed");
  const next = estimateOf(open.find((order) => order.status !== "delayed") ?? open[0])?.date;
  return (
    <>
      {plural(open.length, "笔订单", "笔订单")}配送中{next ? `；下一笔预计 ${next} 送达` : ""}。{" "}
      {late.length ? <span className="font-semibold text-(--warn)">{late.length === 1 ? "有 1 笔" : `有 ${late.length} 笔`}延误。</span> : null}
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
  const catalog = useCatalogIndex(fetchProducts);
  const picks = featured(catalog);
  const now = useNow();
  return (
    <div className="flex flex-col gap-4">
      <Greeting
        eyebrow={now ? now.toLocaleDateString("zh-CN", { weekday: "long", month: "long", day: "numeric" }) : "\u00a0"}
        title={<h1 className="text-[28px] font-semibold leading-tight tracking-[-0.02em] text-(--ink)">{`${now ? greeting(now) : "您好"}, ${shopperName}`}</h1>}
      >
        <Brief orders={orders} />
      </Greeting>
      <Starters items={STARTERS} />
      <ArrivingPanel orders={orders} failed={ordersFailed} nouns={NOUNS} thumb={(order) => <OrderThumb order={order} />} onSeeAll={onSeeOrders} />
      {picks.length ? (
        <HomeSection title="热门商品" subtitle="畅销与新品；点开即可咨询">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {picks.map((product) => (
              <ProductTile key={product.product_id} product={product} fluid onOpen={(item) => ask(`介绍一下${item.title}。`)} />
            ))}
          </div>
        </HomeSection>
      ) : null}
    </div>
  );
}
