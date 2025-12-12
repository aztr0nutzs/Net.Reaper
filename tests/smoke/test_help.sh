#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

echo "Testing --help..."
"$ROOT/netreaper" --help >/dev/null
echo "PASS: --help"

echo "Testing netreaper-install --help..."
"$ROOT/netreaper-install" --help >/dev/null
echo "PASS: netreaper-install --help"
