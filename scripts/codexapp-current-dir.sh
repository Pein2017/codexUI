#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
launch_dir="$(pwd -P)"
codex_home="${launch_dir}/.codex"
local_entry="${repo_root}/dist-cli/index.js"

export CODEX_HOME="${codex_home}"
export http_proxy="http://127.0.0.1:9091"
export https_proxy="http://127.0.0.1:9091"
export HTTP_PROXY="${http_proxy}"
export HTTPS_PROXY="${https_proxy}"
export TELEGRAM_DEFAULT_CWD="${launch_dir}"
export CODEXUI_LAUNCH_SCOPE="${launch_dir}"
export CODEXUI_REPO_ROOT="${repo_root}"
export CODEXUI_SERENA_REPO_ROOT="${CODEXUI_SERENA_REPO_ROOT:-${launch_dir}/mcp/serena}"
export CODEXUI_SERENA_READY_DELAY_MS="3000"
export CODEXUI_SERENA_READY_TIMEOUT_MS="30000"
export CODEXUI_SERENA_RETRY_DELAY_MS="1500"
export CODEXUI_SERENA_MAX_RETRIES="3"

mkdir -p "${CODEX_HOME}"

if [[ ! -d "${repo_root}/node_modules" ]]; then
  npm --prefix "${repo_root}" install
fi

if [[ ! -f "${local_entry}" ]]; then
  (
    cd "${repo_root}"
    ./node_modules/.bin/vue-tsc --noEmit
    ./node_modules/.bin/vite build
    ./node_modules/.bin/tsup
  )
fi

exec node "${local_entry}" "${launch_dir}" --no-login --no-open --no-tunnel
