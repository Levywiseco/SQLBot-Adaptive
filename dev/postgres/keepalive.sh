#!/usr/bin/env bash

set -euo pipefail

sudo pg_ctlcluster 17 main start >/dev/null 2>&1 || true
exec sleep infinity
