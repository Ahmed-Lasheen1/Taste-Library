#!/usr/bin/env bash
# Convenience wrapper. serve.py does the real work and is cross-platform.
exec python3 "$(dirname "$0")/serve.py" "$@"
