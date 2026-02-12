#!/bin/bash
# Clawtter: 脱敏 → 源码推送 → 渲染 → 部署
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$PROJECT_DIR/config.json"

if [ -f "$CONFIG_FILE" ]; then
    OUTPUT_DIR=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['paths']['output_dir'])")
else
    OUTPUT_DIR="$HOME/twitter.openclaw.lcmd"
fi

DEPLOY_DIR="/home/opc/.openclaw/workspace/Clawtter_Deploy"

VENV="/home/opc/.openclaw/workspace/venv/bin/activate"
[ -f "$VENV" ] && source "$VENV"

echo "🚀 Starting Clawtter Push Process..."
echo "Date: $(date)"

# === 1. 脱敏 ===
echo "🔒 Checking for sensitive names..."
cd "$PROJECT_DIR" || exit 1
python3 -c "
import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))
from core.utils_security import load_config, desensitize_text
config = load_config()
names = config['profile'].get('real_names', [])
for p in Path('posts').rglob('*.md'):
    content = p.read_text(encoding='utf-8')
    new_content = desensitize_text(content, names)
    if content != new_content:
        p.write_text(new_content, encoding='utf-8')
        print(f'  ✓ Desensitized: {p}')
"

# === 2. 源码推送 ===
echo "📤 Pushing Source Code to GitHub..."
cd "$PROJECT_DIR" || exit 1

# 强制添加 model-status 报告（dist/ 被 gitignore）
for f in dist/model-status.html dist/model-status.json; do
    [ -f "$PROJECT_DIR/$f" ] && git add -f "$PROJECT_DIR/$f"
done

git add .
if git diff --staged --quiet; then
    echo "⚠️  No source changes to commit."
else
    git commit -m "Auto update: $(date '+%Y-%m-%d %H:%M')"
    if git push origin master; then
        echo "✅ Source pushed!"
    else
        echo "❌ Source push failed!"
        exit 1
    fi
fi

# === 3. 渲染 ===
echo "🔧 Rendering site..."
cd "$PROJECT_DIR" || exit 1
if ! python3 tools/render.py; then
    echo "❌ Render failed!"
    exit 1
fi

# === 4. 部署 ===
echo "✍️ Deploying to Argo-Blog-Static..."
if [ ! -d "$DEPLOY_DIR/.git" ]; then
    echo "❌ Deploy repo not found at $DEPLOY_DIR"
    exit 1
fi

# 同步渲染产物（使用 rsync 确保完整同步）
if command -v rsync &>/dev/null; then
    rsync -a --delete "$OUTPUT_DIR/post/" "$DEPLOY_DIR/post/"
    rsync -a --delete "$OUTPUT_DIR/date/" "$DEPLOY_DIR/date/"
    rsync -a --delete "$OUTPUT_DIR/static/" "$DEPLOY_DIR/static/" 2>/dev/null || true
else
    cp -rf "$OUTPUT_DIR/post/" "$DEPLOY_DIR/"
    cp -rf "$OUTPUT_DIR/date/" "$DEPLOY_DIR/"
    cp -rf "$OUTPUT_DIR/static/" "$DEPLOY_DIR/" 2>/dev/null || true
fi
cp -f "$OUTPUT_DIR/index.html" "$DEPLOY_DIR/"
cp -f "$OUTPUT_DIR/feed.xml" "$DEPLOY_DIR/" 2>/dev/null || true
cp -f "$OUTPUT_DIR/search-index.json" "$DEPLOY_DIR/" 2>/dev/null || true
cp -f "$OUTPUT_DIR/.nojekyll" "$DEPLOY_DIR/" 2>/dev/null || true

cd "$DEPLOY_DIR" || exit 1
git add -A
if git diff --staged --quiet; then
    echo "⚠️  No deploy changes to commit."
else
    git commit -m "deploy: $(date '+%Y-%m-%d %H:%M')"
    if git push origin main; then
        echo "✅ Deploy pushed!"
    else
        echo "❌ Deploy push failed!"
        exit 1
    fi
fi

echo "🎉 All done!"
