# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BLACK PRO CYBER BOT - Configuration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import os
from dotenv import load_dotenv

load_dotenv()

# Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "8494463675:AAGTr-bYZ30dOZ9t_nxVKk57fTx8kVg2-JQ")

# Bot Info
BOT_USERNAME = os.getenv("BOT_USERNAME", "VIP_HACKING_CORSE_BOT")
BOT_NAME = "BLACK PRO CYBER BOT"

# Admins
ADMIN_IDS = [8210146346, 2104373286]
ADMIN_USERNAME = "@jiolinhacker"

# Force Join Channels
CHANNEL_1 = "@bpcback"
CHANNEL_2 = "@bpc_hub"
CHANNEL_1_URL = "https://t.me/bpcback"
CHANNEL_2_URL = "https://t.me/bpc_hub"

# Social Links
TELEGRAM_GROUP_URL = "https://t.me/bpcback"
FACEBOOK_GROUP_URL = "https://facebook.com/groups/3489135951233643/"
FACEBOOK_PAGE_URL = "https://www.facebook.com/profile.php?id=61589544165698"

# Referral Requirements
APK_REFER_REQUIRED = 3
COURSE_REFER_REQUIRED = 5

# Daily Bonus
DAILY_BONUS_AMOUNT = 1
DAILY_BONUS_COOLDOWN = 86400  # 24 hours in seconds

# Anti-Spam
FLOOD_LIMIT = 5          # max messages
FLOOD_TIME = 10          # per seconds
COOLDOWN_TIME = 2        # seconds between actions

# Database
DB_PATH = "bot_database.db"

# Logs Channel (set your logs channel here, optional)
LOGS_CHANNEL = None  # e.g. "@bpc_logs"
