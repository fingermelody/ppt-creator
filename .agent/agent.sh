#!/usr/bin/env bash
# PPT-RSD 智能体框架管理工具
# 用于查看项目状态、管理功能进度

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FEATURE_FILE="$SCRIPT_DIR/feature_list.json"
PROGRESS_FILE="$SCRIPT_DIR/claude-progress.txt"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

show_help() {
    echo "PPT-RSD 智能体框架管理工具"
    echo ""
    echo "用法: $0 <命令>"
    echo ""
    echo "命令:"
    echo "  status    显示项目状态和进度"
    echo "  next      显示下一个待完成的功能"
    echo "  todo      显示所有待完成功能列表"
    echo "  done      显示所有已完成功能列表"
    echo "  feature   显示指定功能的详情"
    echo "  start     开始开发环境"
    echo "  help      显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 status        # 查看整体状态"
    echo "  $0 next          # 查看下一个任务"
    echo "  $0 feature feat-001  # 查看指定功能详情"
}

check_jq() {
    if ! command -v jq &> /dev/null; then
        echo -e "${YELLOW}警告: jq 未安装，部分功能受限${NC}"
        echo "安装: brew install jq"
        return 1
    fi
    return 0
}

show_status() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}    PPT-RSD 项目状态${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
    
    # Git 状态
    echo -e "${YELLOW}📂 Git 状态:${NC}"
    cd "$PROJECT_ROOT"
    BRANCH=$(git branch --show-current)
    echo "   分支: $BRANCH"
    echo ""
    
    # 功能统计
    if check_jq; then
        TOTAL=$(jq '.features | length' "$FEATURE_FILE")
        DONE=$(jq '[.features[] | select(.passes == true)] | length' "$FEATURE_FILE")
        TODO=$(jq '[.features[] | select(.passes == false)] | length' "$FEATURE_FILE")
        PERCENT=$((DONE * 100 / TOTAL))
        
        echo -e "${YELLOW}📊 功能进度:${NC}"
        echo "   总计: $TOTAL 个功能"
        echo -e "   已完成: ${GREEN}$DONE${NC}"
        echo -e "   待完成: ${YELLOW}$TODO${NC}"
        echo "   完成率: $PERCENT%"
        echo ""
        
        # 按优先级统计
        HIGH=$(jq '[.features[] | select(.passes == false and .priority == "high")] | length' "$FEATURE_FILE")
        MEDIUM=$(jq '[.features[] | select(.passes == false and .priority == "medium")] | length' "$FEATURE_FILE")
        LOW=$(jq '[.features[] | select(.passes == false and .priority == "low")] | length' "$FEATURE_FILE")
        
        echo -e "${YELLOW}📈 待办优先级:${NC}"
        echo -e "   高: ${RED}$HIGH${NC}"
        echo -e "   中: ${YELLOW}$MEDIUM${NC}"
        echo -e "   低: ${BLUE}$LOW${NC}"
        echo ""
    fi
    
    # 最近会话
    echo -e "${YELLOW}📝 最近工作:${NC}"
    if [ -f "$PROGRESS_FILE" ]; then
        tail -20 "$PROGRESS_FILE" | head -15
    fi
    echo ""
}

show_next() {
    if ! check_jq; then
        echo "需要安装 jq 才能使用此功能"
        exit 1
    fi
    
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}    下一个待办任务${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
    
    # 按优先级选择
    NEXT=$(jq -r '.features[] | select(.passes == false) | select(.priority == "high") | .id' "$FEATURE_FILE" | head -1)
    
    if [ -z "$NEXT" ]; then
        NEXT=$(jq -r '.features[] | select(.passes == false) | select(.priority == "medium") | .id' "$FEATURE_FILE" | head -1)
    fi
    
    if [ -z "$NEXT" ]; then
        NEXT=$(jq -r '.features[] | select(.passes == false) | .id' "$FEATURE_FILE" | head -1)
    fi
    
    if [ -z "$NEXT" ]; then
        echo -e "${GREEN}🎉 所有功能已完成！${NC}"
        exit 0
    fi
    
    show_feature "$NEXT"
}

show_todo() {
    if ! check_jq; then
        echo "需要安装 jq 才能使用此功能"
        exit 1
    fi
    
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}    待完成功能列表${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
    
    jq -r '.features[] | select(.passes == false) | "[\(.id)] \(.name) (\(.priority))"' "$FEATURE_FILE" | while read -r line; do
        PRIORITY=$(echo "$line" | grep -o '(high)\|(medium)\|(low)')
        
        if echo "$PRIORITY" | grep -q "high"; then
            echo -e "${RED}$line${NC}"
        elif echo "$PRIORITY" | grep -q "medium"; then
            echo -e "${YELLOW}$line${NC}"
        else
            echo -e "${BLUE}$line${NC}"
        fi
    done
    echo ""
}

show_done() {
    if ! check_jq; then
        echo "需要安装 jq 才能使用此功能"
        exit 1
    fi
    
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}    已完成功能列表${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
    
    jq -r '.features[] | select(.passes == true) | "[\(.id)] \(.name)"' "$FEATURE_FILE"
    echo ""
}

show_feature() {
    local FEATURE_ID="$1"
    
    if [ -z "$FEATURE_ID" ]; then
        echo "用法: $0 feature <feature-id>"
        echo "示例: $0 feature feat-001"
        exit 1
    fi
    
    if ! check_jq; then
        echo "需要安装 jq 才能使用此功能"
        exit 1
    fi
    
    FEATURE=$(jq -e ".features[] | select(.id == \"$FEATURE_ID\")" "$FEATURE_FILE")
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}错误: 找不到功能 $FEATURE_ID${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}    功能详情: $FEATURE_ID${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
    
    echo "$FEATURE" | jq -r '
        "名称: \(.name)",
        "分类: \(.category)",
        "优先级: \(.priority)",
        "状态: \(if .passes then "✅ 已完成" else "⏳ 进行中" end)",
        "",
        "描述:",
        "  \(.description)",
        "",
        "测试用例:"
    '
    
    echo "$FEATURE" | jq -r '.tests[]' | while read -r test; do
        echo "  - $test"
    done
    echo ""
}

start_env() {
    if [ -f "$SCRIPT_DIR/init.sh" ]; then
        bash "$SCRIPT_DIR/init.sh"
    else
        echo -e "${RED}错误: init.sh 不存在${NC}"
        exit 1
    fi
}

# 主逻辑
case "$1" in
    status)
        show_status
        ;;
    next)
        show_next
        ;;
    todo)
        show_todo
        ;;
    done)
        show_done
        ;;
    feature)
        show_feature "$2"
        ;;
    start)
        start_env
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        echo -e "${RED}未知命令: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
