#!/usr/bin/env bash
# Copyright 2026 Anthropic PBC
# SPDX-License-Identifier: Apache-2.0
#
# Install the repository's packages and their pinned dependencies. Creates and uses a
# local .venv automatically when needed, so it also works on PEP 668 systems (Debian
# 12+/Ubuntu 23.04+), where pip refuses to write into the OS-managed Python.
#
#   ./scripts/install.sh            # requirements.txt: the seven packages plus what they need
#   ./scripts/install.sh dev        # requirements-dev.txt: the above plus pytest and ruff
#
# Runs from any directory. Pass VENV=0 to install into an already-active environment.
set -euo pipefail

cd "$(dirname "$0")/.."

# Detect PEP 668 (externally managed): pip reports it via sysconfig, or we can simply
# check for the marker file. If we're not already in a venv, create/activate .venv.
in_venv() { python3 -c 'import sys; sys.exit(0 if sys.prefix != sys.base_prefix else 1)' 2>/dev/null; }

if [ "${VENV:-1}" != "0" ] && ! in_venv; then
  if [ ! -x .venv/bin/python ]; then
    echo "Creating virtualenv .venv (PEP 668-safe; system Python may be externally managed)…" >&2
    if ! python3 -m venv .venv; then
      echo "Failed to create .venv. On Debian/Ubuntu install python3-venv first:" >&2
      echo "  sudo apt install python3-venv" >&2
      exit 1
    fi
  fi
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

case "${1:-all}" in
  all) python3 -m pip install -r requirements.txt ;;
  dev) python3 -m pip install -r requirements-dev.txt ;;
  *) echo "usage: $0 [all|dev]" >&2; exit 2 ;;
esac
