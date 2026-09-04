#!/usr/bin/env bash
# The one definition of my local-env commands.
#
# Both callers reach the same bodies:
#   - my interactive shell, via thin `~/.zshrc` aliases (`alias run-be='… envctl.sh run-be'`)
#   - the env-manager skill, which invokes this path directly
#
# Why a script rather than the aliases the skill used to call: a worktree-isolated
# session refuses `zsh -ic '<alias>'` AND `zsh -c 'source ~/.zshrc; …'` — it cannot
# prove sourced shell text won't run git against the wrong checkout. Since the
# `worktree` skill enters every funnel worktree via EnterWorktree, that refusal hit
# every env-manager row exactly where the funnel puts you. A plain command has
# nothing to source, so it passes.
#
# Every subcommand is cwd-dependent, exactly as the aliases were: run it from the
# sub-repo it belongs to (salestech-be, frontend-monorepo, reevo-realtime).
set -uo pipefail

usage() {
  cat <<'USAGE'
Usage: envctl.sh <command>   (run from the relevant sub-repo — cwd matters)

  salestech-be:      run-be  kill-be-f  gen-be  alembic-up  awssso  d-up  d-down
  frontend-monorepo: run-fe-2  kill-fe  gen-fe
  reevo-realtime:    run-rt  kill-rt
USAGE
}

cmd="${1:-}"
case "$cmd" in
  run-be)
    mkdir -p logs
    uv run python -m salestech_be > logs/backend_logs.txt 2>&1 &
    uv run python -m salestech_be.temporal.workers.integrity_job > logs/integrity_job_logs.txt 2>&1 &
    uv run python -m salestech_be.temporal.workers.falkor --worker workflow > logs/falkor_workflow_logs.txt 2>&1 &
    uv run python -m salestech_be.temporal.workers.falkor --worker activity > logs/falkor_activity_logs.txt 2>&1 &
    uv run python -m salestech_be.temporal.workers.chat > logs/chat_worker_logs.txt 2>&1 &
    make start-flow-dep LOG_DIR=logs &
    ;;
  kill-be-f)
    lsof -ti tcp:8000 | xargs kill -9 2>/dev/null
    pkill -9 -f salestech_be 2>/dev/null
    true
    ;;
  gen-be)      uv run generate_openapi.py ;;
  alembic-up)  uv run alembic upgrade head ;;
  awssso)      env -u BROWSER aws sso login --profile "${AWS_PROFILE:-workflow}" ;;
  d-up)
    mkdir -p logs
    make docker-start-dep > logs/docker_up_logs.txt 2>&1
    ;;
  d-down)
    mkdir -p logs
    make docker-suspend-dep > logs/docker_down_logs.txt 2>&1
    ;;
  run-fe-2)
    mkdir -p logs
    pnpm -F ./apps/reevo-webapp dev > logs/frontend_logs.txt 2>&1 &
    ;;
  kill-fe)
    lsof -ti tcp:3000 -sTCP:LISTEN | xargs kill -9 2>/dev/null
    true
    ;;
  gen-fe)      pnpm generate-openapi-client:local ;;
  run-rt)
    mkdir -p logs
    pnpm dev > logs/dev.log 2>&1 &
    ;;
  kill-rt)
    pkill -f "pnpm.*dev" 2>/dev/null
    true
    ;;
  ""|-h|--help) usage; exit 0 ;;
  *) echo "envctl.sh: unknown command '$cmd'" >&2; usage >&2; exit 2 ;;
esac
