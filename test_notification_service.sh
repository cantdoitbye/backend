#!/bin/bash

# Comprehensive Test Script for Notification Service

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║        📨 NOTIFICATION SERVICE - COMPREHENSIVE TEST                      ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check if notification app exists
echo "Step 1: Checking notification app..."
if [ -d "notification" ]; then
    echo -e "${GREEN}✓${NC} notification/ directory exists"
else
    echo -e "${RED}✗${NC} notification/ directory NOT found!"
    exit 1
fi

# Step 2: Check core files
echo ""
echo "Step 2: Checking core files..."

files=(
    "notification/__init__.py"
    "notification/apps.py"
    "notification/models.py"
    "notification/admin.py"
    "notification/global_service.py"
    "notification/notification_templates.py"
    "notification/migrations/0001_initial.py"
    "notification/management/commands/test_notification.py"
)

all_files_present=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file MISSING!"
        all_files_present=false
    fi
done

if [ "$all_files_present" = false ]; then
    echo -e "${RED}Some files are missing! Please restore them.${NC}"
    exit 1
fi

# Step 3: Check if app is registered in settings
echo ""
echo "Step 3: Checking if app is registered..."
if grep -q "'notification'" settings/base.py 2>/dev/null || grep -q "'notification'" settings.py 2>/dev/null; then
    echo -e "${GREEN}✓${NC} 'notification' is in INSTALLED_APPS"
else
    echo -e "${YELLOW}⚠${NC}  'notification' might not be in INSTALLED_APPS"
    echo "   Please add 'notification' to INSTALLED_APPS in settings/base.py"
fi

# Step 4: Check Python environment
echo ""
echo "Step 4: Checking Python environment..."
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓${NC} Python 3 is available"
    python3 --version
else
    echo -e "${RED}✗${NC} Python 3 not found!"
    exit 1
fi

# Step 5: Run migrations
echo ""
echo "Step 5: Running migrations..."
echo -e "${YELLOW}Running: python manage.py makemigrations notification${NC}"
python3 manage.py makemigrations notification

echo ""
echo -e "${YELLOW}Running: python manage.py migrate notification${NC}"
python3 manage.py migrate notification

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Migrations completed successfully"
else
    echo -e "${RED}✗${NC} Migration failed!"
    exit 1
fi

# Step 6: Test notification sending
echo ""
echo "Step 6: Testing notification service..."
echo -e "${YELLOW}Running: python manage.py test_notification${NC}"
echo ""
python3 manage.py test_notification

# Step 7: Show statistics
echo ""
echo "Step 7: Showing notification statistics..."
echo -e "${YELLOW}Running: python manage.py notification_stats${NC}"
echo ""
python3 manage.py notification_stats

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ COMPREHENSIVE TEST COMPLETE                        ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "🎯 NEXT STEPS:"
echo ""
echo "1. Check Django Admin:"
echo "   http://localhost:8000/admin/notification/usernotification/"
echo ""
echo "2. Use in your code:"
echo "   from notification.global_service import GlobalNotificationService"
echo "   "
echo "   service = GlobalNotificationService()"
echo "   service.send("
echo "       event_type='new_comment_on_post',"
echo "       recipients=[{'device_id': '...', 'uid': '...'}],"
echo "       username='John Doe',"
echo "       comment_text='Great post!',"
echo "       post_id='123'"
echo "   )"
echo ""
echo "3. Read documentation:"
echo "   - notification/README.md"
echo "   - notification/SIMPLE_USAGE.md"
echo "   - notification/MIGRATION_EXAMPLES.md"
echo ""
echo "🚀 Notification service is ready to use!"
echo ""


