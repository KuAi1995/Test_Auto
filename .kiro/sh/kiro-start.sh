#!/bin/bash
# Test_Auto 项目 Kiro CLI 启动脚本
cd "$(dirname "$0")/../.." || exit 1

echo "🔄 开始 Kiro 配置同步..."

# 确保 kiro-agents 仓库存在并更新
KIRO_AGENTS_DIR="$HOME/Project/Python/kiro-agents"
if [ -d "$KIRO_AGENTS_DIR" ]; then
    echo "📥 更新 kiro-agents 仓库..."
    cd "$KIRO_AGENTS_DIR" || exit 1
    git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || {
        echo "⚠️  无法更新 kiro-agents 仓库，使用现有版本"
    }
    cd - > /dev/null || exit 1

    # 执行同步
    SYNC_SCRIPT="$KIRO_AGENTS_DIR/sync.sh"
    if [ -f "$SYNC_SCRIPT" ]; then
        echo "🔄 执行全局同步..."
        bash "$SYNC_SCRIPT"
    fi
else
    echo "⚠️  kiro-agents 仓库不存在: $KIRO_AGENTS_DIR"
fi

echo ""
echo "🚀 启动 Kiro CLI..."

PROMPT="开始对话恢复（按 kiro-usage.md 规则执行）：
1. 读取 docs/kiro-log.md 最近 3 个日期条目，恢复工作上下文
2. 检查未关闭的 [问题] 和 [待办] 标签，列出提醒
3. 阅读 docs/progress.md 了解当前状态
4. 汇报上下文摘要，然后等待指令"

exec kiro-cli chat --trust-all-tools "$PROMPT"
