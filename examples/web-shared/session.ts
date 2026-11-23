// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

"use client";

import { useEffect, useState } from "react";
import type { AgentApi } from "./api";

export interface Session {
  /** Null while login is in flight or after it failed. */
  sessionId: string | null;
  /** The signed-in operator's name, on merchant sessions. */
  operator?: string;
  /** The signed-in shopper, on storefront sessions. */
  shopper?: { name: string; tier?: string };
  /** The chosen response language ("en" | "zh" | "ja" | "ko"). */
  language?: string;
}

const LANGUAGE_KEY = "acme-language";

/** The language persisted across reloads, defaulting to English. */
export function storedLanguage(): string {
  try {
    return localStorage.getItem(LANGUAGE_KEY) ?? "en";
  } catch {
    return "en";
  }
}

export function storeLanguage(language: string): void {
  try {
    localStorage.setItem(LANGUAGE_KEY, language);
  } catch {
    // Storage may be unavailable; the session still carries the choice.
  }
}

const generations = new WeakMap<AgentApi, number>();

/**
 * Only the newest start installs its token. Key the caller on the profile so per-session
 * state resets with it.
 */
export function useSession(
  api: AgentApi,
  options: { profile?: string } = {},
): Session {
  const { profile } = options;
  const [session, setSession] = useState<Session>({ sessionId: null });

  useEffect(() => {
    const generation = (generations.get(api) ?? 0) + 1;
    generations.set(api, generation);
    const current = () => generations.get(api) === generation;
    void (async () => {
      const language = storedLanguage();
      const started = await api.startSession({ ...(profile ? { user_id: profile } : {}), language });
      if (!current()) return;
      api.session = started?.sessionId ?? null;
      setSession({ sessionId: started?.sessionId ?? null, operator: started?.operator, shopper: started?.shopper, language: started?.language ?? language });
    })();
    return () => {
      generations.set(api, (generations.get(api) ?? 0) + 1);
    };
  }, [api, profile]);

  return session;
}
