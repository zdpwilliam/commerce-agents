// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

import { AgentApi } from "web-shared";
import type { AlertsResponse, ListingDetailResponse, ListingsResponse, OverviewResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = new AgentApi(API_URL, "/api/merchant");

export const UNREACHABLE =
  "无法连接到 8000 端口的零售 API。请先启动服务：" +
  "`uvicorn retail.api.main:app --app-dir examples --port 8000`，然后重试。";

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
