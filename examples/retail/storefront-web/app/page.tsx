// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

"use client";

import { useCallback, useEffect, useState } from "react";
import {
  type AgentEvent,
  asLang,
  formatMoney,
  I18nProvider,
  LanguageSwitcher,
  type Lang,
  OrdersView,
  plural,
  storeLanguage,
  StoreShell,
  type StoreView,
  translate,
  upcoming,
  useAgentTurn,
  useResource,
  useSession,
} from "web-shared";
import CartPanel from "@/components/CartPanel";
import Chat from "@/components/Chat";
import HomeView from "@/components/views/HomeView";
import { api, UNREACHABLE } from "@/lib/api";
import { NOUNS, OrderThumb } from "@/lib/orders";
import type { CartPayload } from "@/lib/types";

type View = "assistant" | "orders";

const ASSISTANT = "ACME Assistant";

function Wordmark() {
  return (
    <span className="flex items-center gap-2.5 pr-1">
      <span aria-hidden className="grid h-[30px] w-[30px] place-items-center rounded-lg bg-(--ink) text-[15px] font-bold text-(--surface)">
        A
      </span>
      <span className="text-[17px] font-bold tracking-[-0.02em] text-(--ink)">ACME Dental</span>
    </span>
  );
}

function Storefront() {
  const session = useSession(api);
  const [view, setView] = useState<View>("assistant");
  const [cart, setCart] = useState<CartPayload | null>(null);
  const [checkoutStaged, setCheckoutStaged] = useState(false);
  const [panelOpen, setPanelOpen] = useState(false);
  const [language, setLanguage] = useState<Lang>(asLang(session.language));
  const t = useCallback((key: string) => translate(language, key), [language]);

  const handleCartUpdate = useCallback((next: CartPayload) => {
    setCart(next);
    setCheckoutStaged(false);
  }, []);

  const onEvent = useCallback(
    (event: AgentEvent) => {
      if (event.type === "cart_update") handleCartUpdate(event.data.cart as CartPayload);
      else if (event.type === "ui" && event.data.component === "checkout") setCheckoutStaged(true);
    },
    [handleCartUpdate],
  );

  const chat = useAgentTurn(api, { ...session, unreachable: UNREACHABLE, onEvent });
  const { data: orders, failed: ordersFailed } = useResource(session.sessionId ? () => api.fetchOrders() : null, [session.sessionId, chat.completed, language]);

  useEffect(() => {
    if (session.sessionId) void api.fetchCart<CartPayload>().then((next) => next && setCart(next));
  }, [session.sessionId, language]);

  const onLanguageChange = useCallback((next: Lang) => {
    storeLanguage(next);
    setLanguage(next);
  }, []);

  const late = orders?.filter((order) => order.status === "delayed").length ?? 0;
  const views: StoreView<View>[] = [
    { id: "assistant", label: t("Assistant"), icon: "spark" },
    { id: "orders", label: t("Orders"), icon: "box", attention: late ? { count: late, label: `${late} ${t("running late")}` } : null },
  ];
  const shopper = session.shopper ?? { name: t("Guest") };
  const count = cart?.item_count ?? 0;

  return (
    <I18nProvider api={api} language={language} onChange={onLanguageChange}>
      <StoreShell
        brand={<Wordmark />}
        views={views}
        view={view}
        onViewChange={setView}
        chat={chat}
        api={api}
        assistantName={ASSISTANT}
        shopper={shopper}
        bag={{ label: t("Cart"), count, noun: t("item"), figure: count ? formatMoney(cart?.subtotal ?? 0, cart?.currency) : null }}
        panel={<CartPanel cart={cart} checkoutStaged={checkoutStaged} />}
        panelOpen={panelOpen}
        onPanelOpenChange={setPanelOpen}
        placeholder={view === "orders" ? t("Ask about an order, a return, a delivery…") : t("Ask about a product, a project, an order…")}
        headerExtra={<LanguageSwitcher />}
      >
        <div className={view === "assistant" ? "h-full" : "hidden"}>
          <Chat chat={chat} onCartUpdate={handleCartUpdate} home={<HomeView shopperName={shopper.name} orders={orders} ordersFailed={ordersFailed} onSeeOrders={() => setView("orders")} />} />
        </div>
        {view === "orders" ? (
          <OrdersView
            orders={orders}
            failed={ordersFailed}
            nouns={NOUNS}
            subtitle={
              orders
                ? late
                  ? `${plural(late, t("order"))} ${t("running late")}. ${t("Ask why, or ask about a return on anything delivered.")}`
                  : `${plural(upcoming(orders).length, t("order"))} ${t("on the way")}. ${t("Ask about any of them, or about a return on anything delivered.")}`
                : undefined
            }
            thumb={(order) => <OrderThumb order={order} />}
          />
        ) : null}
      </StoreShell>
    </I18nProvider>
  );
}

export default function StorefrontPage() {
  return <Storefront />;
}
