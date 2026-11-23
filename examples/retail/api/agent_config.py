# Copyright 2026 Anthropic PBC
# SPDX-License-Identifier: Apache-2.0

"""The 恒信 retail deployment's two agent configs; the only place this example reads
deployment knobs from the environment."""

from __future__ import annotations

import os

from demo_common import host_approval_default
from merchant_agent import MerchantAgentConfig
from shopping_agent import ShoppingAgentConfig


def build_shopping_config() -> ShoppingAgentConfig:
    return ShoppingAgentConfig(
        brand_name="恒信",
        assistant_name="恒信助手",
        brand_voice="professional, warm, and brief",
        model=os.environ.get("SHOPPING_MODEL") or "claude-sonnet-5",
        memory_model=os.environ.get("MEMORY_MODEL") or "claude-haiku-4-5-20251001",
    )


def build_merchant_config(store_name: str) -> MerchantAgentConfig:
    return MerchantAgentConfig(
        brand_name=store_name,
        require_host_approval=host_approval_default(),
        approval_surface="变更预览卡片上的「批准」按钮",
        model=os.environ.get("MERCHANT_MODEL") or "claude-opus-5",
        memory_model=os.environ.get("MEMORY_MODEL") or "claude-haiku-4-5-20251001",
        # This deployment runs the run_analysis delegate over MockRetailMerchant's
        # read-only SQL view of the fixtures. MERCHANT_ANALYSIS_CODE_EXECUTION=1 adds the
        # code-execution sandbox (first-party API only); MERCHANT_ANALYSIS_MODEL overrides
        # the delegate's model, which otherwise inherits the main one.
        enable_analysis=True,
        analysis_use_code_execution=os.environ.get("MERCHANT_ANALYSIS_CODE_EXECUTION", "0") == "1",
        analysis_model=os.environ.get("MERCHANT_ANALYSIS_MODEL") or None,
    )
