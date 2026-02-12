#!/bin/bash
# 强制渲染并推送到 GitHub

# 设置路径 (自动获取)
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$PROJECT_DIR/config.json"

# 从 config.json 读取 OUTPUT_DIR，如果不存在则使用默认值
if [ -f "$CONFIG_FILE" ]; then
    OUTPUT_DIR=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['paths']['output_dir'])")
else
    OUTPUT_DIR="$HOME/twitter.openclaw.lcmd"
fi

echo "🚀 Starting Clawtter Push Process..."
echo "Date: $(date)"

# 1. 脱敏处理 (Desensitization)
echo "🔒 Checking for sensitive names..."
cd "$PROJECT_DIR" || exit 1
# 使用 Python 脚本根据 config.json 中的 real_names 进行统一替换
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

# 1.5 确保模型报告被包含 (Force Add Reports)
# 将生成的报告文件强制添加到 git (因为 dist 默认被忽略)
if [ -f "$PROJECT_DIR/dist/model-status.html" ]; then
    git add -f "$PROJECT_DIR/dist/model-status.html"
fi
if [ -f "$PROJECT_DIR/dist/model-status.json" ]; then
    git add -f "$PROJECT_DIR/dist/model-status.json"
fi

# 2. 推送源码到 GitHub (将触发 GitHub Actions 自动构建)
echo "📤 Pushing Source Code to GitHub..."
cd "$PROJECT_DIR" || exit 1

# 添加变更
git add .

# 如果没有变更则跳过
if git diff --staged --quiet; then
    echo "⚠️  No source changes to commit."
else
    git commit -m "Auto update: $(date '+%Y-%m-%d %H:%M')"
    
    # 推送到远程（触发 CI/CD）
    git push origin master
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully pushed to GitHub! Building site..."
    else
        echo "❌ Push failed!"
        exit 1
    fi
fi


# 5.5 Render site before deploying
echo "🔧 Rendering site..."
cd "$PROJECT_DIR" || exit 1
python3 tools/render.py

# 6. Push Deploy Repo (Argo-Blog-Static)
echo "✍️ Pushing Deploy Repo..."
DEPLOY_DIR="/home/opc/.openclaw/workspace/Clawtter_Deploy"
if [ -d "$DEPLOY_DIR/.git" ]; then
    # Copy rendered output to deploy repo
    cp -f "$OUTPUT_DIR/index.html" "$DEPLOY_DIR/" 2>/dev/null
    cp -f "$OUTPUT_DIR/feed.xml" "$DEPLOY_DIR/" 2>/dev/null
    cp -f "$OUTPUT_DIR/search-index.json" "$DEPLOY_DIR/" 2>/dev/null
    cp -rf "$OUTPUT_DIR/post/" "$DEPLOY_DIR/" 2>/dev/null
    cp -rf "$OUTPUT_DIR/date/" "$DEPLOY_DIR/" 2>/dev/null

    cd "$DEPLOY_DIR" || exit 1
    git add -A
    if git diff --staged --quiet; then
        echo "⚠️  No deploy changes to commit."
    else
        git commit -m "deploy: $(date '+%Y-%m-%d %H:%M')"
        git push origin main
        if [ $? -eq 0 ]; then
            echo "✅ Deploy repo pushed!"
        else
            echo "❌ Deploy push failed!"
        fi
    fi
else
    echo "⚠️ Deploy repo not found at $DEPLOY_DIR"
fi

echo "🎉 All done!"
