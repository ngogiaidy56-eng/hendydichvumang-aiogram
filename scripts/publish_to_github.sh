#!/usr/bin/env bash
set -euo pipefail

REPOSITORY="ngogiaidy56-eng/hendydichvumang-aiogram"
REMOTE_URL="https://github.com/$REPOSITORY.git"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) chưa được cài. Cài từ https://cli.github.com/ rồi chạy lại." >&2
  exit 1
fi
if ! command -v git >/dev/null 2>&1; then
  echo "Git chưa được cài." >&2
  exit 1
fi

gh auth status >/dev/null
gh repo view "$REPOSITORY" >/dev/null

if [ ! -d .git ]; then
  git init
fi
if git remote get-url origin >/dev/null 2>&1; then
  CURRENT_REMOTE="$(git remote get-url origin)"
  if [[ "$CURRENT_REMOTE" != "$REMOTE_URL" && "$CURRENT_REMOTE" != "git@github.com:$REPOSITORY.git" ]]; then
    echo "Remote origin hiện tại không khớp: $CURRENT_REMOTE" >&2
    exit 1
  fi
else
  git remote add origin "$REMOTE_URL"
fi

git add .
if ! git diff --cached --quiet; then
  git commit -m "Build Hendy Dịch Vụ Mạng aiogram v3"
fi
git branch -M main
if git ls-remote --exit-code --heads origin main >/dev/null 2>&1; then
  git pull --rebase origin main
fi
git push -u origin main
printf 'Đã push mã nguồn lên %s\n' "$REMOTE_URL"
