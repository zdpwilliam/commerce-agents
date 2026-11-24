// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

import type { NextConfig } from "next";

// When served behind a reverse proxy under a subpath (e.g. nginx location /agent-merchant/),
// set BASE_PATH at build time so generated asset URLs and routes carry that prefix.
const basePath = process.env.BASE_PATH?.replace(/\/$/, "") || "";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  transpilePackages: ["web-shared"],
  basePath,
};

export default nextConfig;
