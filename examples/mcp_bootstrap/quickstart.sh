#!/usr/bin/env sh
set -eu

ROOT="${1:-../..}"
aq mcp build-index --workspace "$ROOT"
aq mcp doctor --workspace "$ROOT"
aq mcp list-tools --workspace "$ROOT"
