// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

import { AgentApi } from "web-shared";
import type { CartPayload, Product, ProductDetails } from "./types";

// Behind the nginx gateway the API is exposed at /agent/api/. AgentApi appends its own
// "/api" prefix, so the final request is /agent/api/api/...; the gateway's proxy_pass
// strips /agent/api/ and FastAPI receives /api/... as expected.
// Override NEXT_PUBLIC_API_URL only if the API lives on a different origin (absolute URL).
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "/agent/api";

export const api = new AgentApi(API_URL, "/api");

export const UNREACHABLE =
  "无法连接到零售 API。请确认 API 服务已启动，且反向代理已把 /api 转发到 API 服务。";

export async function fetchProducts(): Promise<Product[] | null> {
  const data = await api.get<{ products: Product[] }>("/products", { limit: "100" });
  return data?.products ?? null;
}

export function fetchProduct(productId: string): Promise<ProductDetails | null> {
  return api.get<ProductDetails>(`/products/${encodeURIComponent(productId)}`);
}

export async function addToCart(productId: string, quantity = 1): Promise<CartPayload | null> {
  const data = await api.post<{ cart: CartPayload }>("/cart/add", { product_id: productId, quantity });
  return data?.cart ?? null;
}
