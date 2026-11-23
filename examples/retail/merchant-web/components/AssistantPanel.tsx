// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

"use client";

import { AssistantPanel as PanelShell, type MerchantChat, type Prefill } from "web-shared";
import type { StagedChange } from "@/lib/types";
import GenerativeBlock from "./generative";

const COPY = {
  title: "商家助手",
  intro: "咨询经营表现、库存、定价或活动。",
  starters: [
    "What needs my attention this morning?",
    "How did sales do this week compared to last?",
    "Which listings are running low on stock?",
    "Which slow movers should we mark down?",
  ],
  label: "向商家助手提问",
  placeholder: "Ask about sales, stock, pricing…",
};

export default function AssistantPanel({
  chat,
  prefill,
  onPrefill,
  ...shell
}: {
  chat: MerchantChat<StagedChange>;
  prefill: Prefill | null;
  onPrefill: (text: string) => void;
  newMemoryCount: number;
  onOpenActivity: () => void;
  onClose: () => void;
  fullscreen: boolean;
  onToggleFullscreen: () => void;
}) {
  return (
    <PanelShell
      chat={chat}
      copy={COPY}
      prefill={prefill}
      renderBlock={(segment) => (
        <GenerativeBlock
          block={segment.block}
          status={segment.status}
          onChangeAction={chat.actOnChange}
          onPrefill={onPrefill}
        />
      )}
      {...shell}
    />
  );
}
