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
}

const generations = new WeakMap<AgentApi, number>();

/**
 * Only the newest start installs its token. Key the caller on the profile so per-session
 * state resets with it.
 */
export function useSession(
  api: AgentApi,
  options: { profile?: string; persistKey?: string } = {},
): Session {
  const { profile, persistKey } = options;
  const [session, setSession] = useState<Session>({ sessionId: null });

  useEffect(() => {
    const generation = (generations.get(api) ?? 0) + 1;
    generations.set(api, generation);
    const current = () => generations.get(api) === generation;
    void (async () => {
      // A storefront persists its session id so a page reload resumes the same cart.
      // localStorage is best-effort: private mode or a disabled store simply starts fresh.
      let savedId: string | undefined;
      if (persistKey) {
        try {
          savedId = window.localStorage.getItem(persistKey) ?? undefined;
        } catch {
          // ignore
        }
      }
      const body = { ...(profile ? { user_id: profile } : {}), ...(savedId ? { session_id: savedId } : {}) };
      const started = await api.startSession(Object.keys(body).length ? body : undefined);
      if (!current()) return;
      const sessionId = started?.sessionId ?? null;
      if (persistKey && sessionId) {
        try {
          window.localStorage.setItem(persistKey, sessionId);
        } catch {
          // ignore
        }
      }
      api.session = sessionId;
      setSession({ sessionId, operator: started?.operator, shopper: started?.shopper });
    })();
    return () => {
      generations.set(api, (generations.get(api) ?? 0) + 1);
    };
  }, [api, profile, persistKey]);

  return session;
}
