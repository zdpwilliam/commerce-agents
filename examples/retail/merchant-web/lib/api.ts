// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

import { AgentApi } from "web-shared";
import type { AlertsResponse, ListingDetailResponse, ListingsResponse, OverviewResponse } from "./types";

// Behind the nginx gateway the API is exposed at /agent/api/. AgentApi appends its own
// "/api/merchant" prefix, so the final request is /agent/api/api/merchant/...; the
// gateway strips /agent/api/ and FastAPI receives /api/merchant/... as expected.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "/agent/api";

export const api = new AgentApi(API_URL, "/api/merchant");

export const UNREACHABLE =
  "无法连接到零售 API。请确认 API 服务已启动，且反向代理已把 /api 转发到 API 服务。";

export function fetchOverview(): Promise<OverviewResponse | null> {
  return api.get<OverviewResponse>("/overview");
}

export function fetchListings(query?: string): Promise<ListingsResponse | null> {
  return api.get<ListingsResponse>("/listings", query ? { query } : undefined);
}

export function fetchListingDetail(listingId: string): Promise<ListingDetailResponse | null> {
  return api.get<ListingDetailResponse>(`/listings/${encodeURIComponent(listingId)}`);
}

export function fetchAlerts(): Promise<AlertsResponse | null> {
  return api.get<AlertsResponse>("/alerts");
}
