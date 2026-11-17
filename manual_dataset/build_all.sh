#!/usr/bin/env bash
# Rebuild everything from raw sources, in order.
set -euo pipefail
cd "$(dirname "$0")"
python3 tools/build.py
python3 tools/build_rules.py
python3 convert_to_chat.py
python3 tools/make_stats.py
python3 validate.py
