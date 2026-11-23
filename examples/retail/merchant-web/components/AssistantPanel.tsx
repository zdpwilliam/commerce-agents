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
    "今天有哪些需要我关注的事项？",
    "本周销售和上周相比怎么样？",
    "哪些商品库存不足了？",
    "哪些滞销商品应该降价？",
  ],
  label: "向商家助手提问",
  placeholder: "咨询销售、库存、定价…",
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
