#!/bin/bash

# Quick Verification Script

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║              🔍 NOTIFICATION SERVICE - QUICK VERIFICATION                ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check structure
echo "📁 Checking structure..."
if [ -d "notification" ]; then
    echo -e "${GREEN}✓${NC} notification/ exists"
    
    file_count=$(find notification -type f -name "*.py" | wc -l | tr -d ' ')
    echo -e "${GREEN}✓${NC} Found $file_count Python files"
    
    if [ -f "notification/global_service.py" ]; then
        echo -e "${GREEN}✓${NC} global_service.py (main service)"
    else
        echo -e "${RED}✗${NC} global_service.py MISSING!"
    fi
    
    if [ -f "notification/notification_templates.py" ]; then
        echo -e "${GREEN}✓${NC} notification_templates.py (templates)"
    else
        echo -e "${RED}✗${NC} notification_templates.py MISSING!"
    fi
    
    if [ -f "notification/models.py" ]; then
        echo -e "${GREEN}✓${NC} models.py (PostgreSQL models)"
    else
        echo -e "${RED}✗${NC} models.py MISSING!"
    fi
else
    echo -e "${RED}✗${NC} notification/ directory NOT found!"
    exit 1
fi

# Check settings
echo ""
echo "⚙️  Checking settings..."
if grep -q "'notification'" settings/base.py 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Registered in INSTALLED_APPS"
else
    echo -e "${YELLOW}⚠${NC}  Not registered in INSTALLED_APPS"
    echo "   Add 'notification' to INSTALLED_APPS in settings/base.py"
fi

# Check migrations
echo ""
echo "📊 Checking migrations..."
if [ -f "notification/migrations/0001_initial.py" ]; then
    echo -e "${GREEN}✓${NC} Initial migration exists"
else
    echo -e "${YELLOW}⚠${NC}  Initial migration not found"
    echo "   Run: python manage.py makemigrations notification"
fi

# Check management commands
echo ""
echo "🛠️  Checking management commands..."
if [ -f "notification/management/commands/test_notification.py" ]; then
    echo -e "${GREEN}✓${NC} test_notification command"
else
    echo -e "${RED}✗${NC} test_notification command MISSING!"
fi

if [ -f "notification/management/commands/notification_stats.py" ]; then
    echo -e "${GREEN}✓${NC} notification_stats command"
else
    echo -e "${RED}✗${NC} notification_stats command MISSING!"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                         ✅ VERIFICATION COMPLETE                         ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 To test the service, run:"
echo "   ./test_notification_service.sh"
echo ""
echo "📖 Or run commands manually:"
echo "   python manage.py makemigrations notification"
echo "   python manage.py migrate notification"
echo "   python manage.py test_notification"
echo ""


