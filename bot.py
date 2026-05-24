#!/usr/bin/env python
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   BLACK PRO CYBER BOT - Complete Single File
#   Admin: @jiolinhacker
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import asyncio
import logging
import sqlite3
import time
import os
from datetime import datetime, timedelta
from functools import wraps

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove, CallbackQuery, Message
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BOT_TOKEN = "8647373567:AAFhBObiZr738fZ82FZQPD8-DqmNYilT7qs"
BOT_USERNAME = "VIP_HACKING_CORSE_BOT"  # Change to your bot username after creation
BOT_NAME = "BLACK PRO CYBER BOT"

ADMIN_IDS = [8210146346, 2104373286]
ADMIN_USERNAME = "@jiolinhacker"

CHANNEL_1 = "@bpcback"
CHANNEL_2 = "@bpc_hub"
CHANNEL_1_URL = "https://t.me/bpcback"
CHANNEL_2_URL = "https://t.me/bpc_hub"

TELEGRAM_GROUP_URL = "https://t.me/bpcback"
FACEBOOK_GROUP_URL = "https://facebook.com/groups/3489135951233643/"
FACEBOOK_PAGE_URL = "https://www.facebook.com/profile.php?id=61589544165698"

APK_REFER_REQUIRED = 3
COURSE_REFER_REQUIRED = 5
DAILY_BONUS_AMOUNT = 1
DAILY_BONUS_COOLDOWN = 86400
DB_PATH = "bot_database.db"

# Anti-spam tracker
user_last_action = {}
flood_tracker = {}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOGGING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FSM STATES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AdminStates(StatesGroup):
    waiting_apk = State()
    waiting_apk_caption = State()
    waiting_course = State()
    waiting_course_caption = State()
    waiting_broadcast = State()
    waiting_ban_id = State()
    waiting_unban_id = State()
    waiting_user_info_id = State()
    waiting_add_admin = State()
    waiting_remove_admin = State()
    waiting_refer_limit = State()
    waiting_broadcast_confirm = State()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATABASE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        refer_balance INTEGER DEFAULT 0,
        total_referrals INTEGER DEFAULT 0,
        referred_by INTEGER DEFAULT NULL,
        join_date TEXT,
        is_banned INTEGER DEFAULT 0,
        last_bonus TEXT DEFAULT NULL,
        total_claims INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referrer_id INTEGER,
        referred_id INTEGER,
        date TEXT,
        UNIQUE(referred_id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS apk_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id TEXT,
        file_name TEXT,
        file_size TEXT,
        caption TEXT,
        version TEXT,
        upload_date TEXT,
        uploaded_by INTEGER,
        is_active INTEGER DEFAULT 1
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS course_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id TEXT,
        file_name TEXT,
        file_type TEXT,
        caption TEXT,
        upload_date TEXT,
        uploaded_by INTEGER,
        is_active INTEGER DEFAULT 1
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        claim_type TEXT,
        item_id INTEGER,
        date TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY,
        added_by INTEGER,
        added_date TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT,
        user_id INTEGER,
        details TEXT,
        date TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS banned_users (
        user_id INTEGER PRIMARY KEY,
        banned_by INTEGER,
        reason TEXT,
        ban_date TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS bonuses (
        user_id INTEGER PRIMARY KEY,
        last_claim TEXT,
        total_bonus INTEGER DEFAULT 0
    )''')

    # Insert default settings
    defaults = [
        ("apk_refer_limit", str(APK_REFER_REQUIRED)),
        ("course_refer_limit", str(COURSE_REFER_REQUIRED)),
        ("maintenance_mode", "0"),
        ("force_join", "1"),
    ]
    for key, val in defaults:
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))

    # Insert default admins
    for admin_id in ADMIN_IDS:
        c.execute("INSERT OR IGNORE INTO admins (user_id, added_by, added_date) VALUES (?, ?, ?)",
                  (admin_id, admin_id, datetime.now().isoformat()))

    conn.commit()
    conn.close()
    logger.info("✅ Database initialized successfully")

def get_setting(key: str, default=None):
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default

def set_setting(key: str, value: str):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_user(user_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def create_user(user_id: int, username: str, full_name: str, referred_by: int = None):
    conn = get_db()
    conn.execute('''INSERT OR IGNORE INTO users 
        (user_id, username, full_name, referred_by, join_date)
        VALUES (?, ?, ?, ?, ?)''',
        (user_id, username, full_name, referred_by, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def update_user(user_id: int, **kwargs):
    conn = get_db()
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [user_id]
    conn.execute(f"UPDATE users SET {sets} WHERE user_id=?", vals)
    conn.commit()
    conn.close()

def add_referral(referrer_id: int, referred_id: int) -> bool:
    conn = get_db()
    try:
        conn.execute('''INSERT INTO referrals (referrer_id, referred_id, date) VALUES (?, ?, ?)''',
                     (referrer_id, referred_id, datetime.now().isoformat()))
        conn.execute("UPDATE users SET refer_balance=refer_balance+1, total_referrals=total_referrals+1 WHERE user_id=?",
                     (referrer_id,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def is_admin(user_id: int) -> bool:
    if user_id in ADMIN_IDS:
        return True
    conn = get_db()
    row = conn.execute("SELECT user_id FROM admins WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return row is not None

def is_banned(user_id: int) -> bool:
    conn = get_db()
    row = conn.execute("SELECT user_id FROM banned_users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return row is not None

def add_log(event_type: str, user_id: int, details: str):
    conn = get_db()
    conn.execute("INSERT INTO logs (event_type, user_id, details, date) VALUES (?, ?, ?, ?)",
                 (event_type, user_id, details, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_apk_list():
    conn = get_db()
    rows = conn.execute("SELECT * FROM apk_files WHERE is_active=1 ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_course_list():
    conn = get_db()
    rows = conn.execute("SELECT * FROM course_files WHERE is_active=1 ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_stats():
    conn = get_db()
    total_users = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    total_refs = conn.execute("SELECT COUNT(*) as c FROM referrals").fetchone()["c"]
    total_claims = conn.execute("SELECT COUNT(*) as c FROM claims").fetchone()["c"]
    total_apks = conn.execute("SELECT COUNT(*) as c FROM apk_files WHERE is_active=1").fetchone()["c"]
    total_courses = conn.execute("SELECT COUNT(*) as c FROM course_files WHERE is_active=1").fetchone()["c"]
    banned = conn.execute("SELECT COUNT(*) as c FROM banned_users").fetchone()["c"]
    conn.close()
    return {
        "users": total_users,
        "referrals": total_refs,
        "claims": total_claims,
        "apks": total_apks,
        "courses": total_courses,
        "banned": banned
    }

def get_ranking():
    conn = get_db()
    rows = conn.execute('''SELECT user_id, full_name, username, total_referrals 
                           FROM users WHERE is_banned=0 
                           ORDER BY total_referrals DESC LIMIT 10''').fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# KEYBOARDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="🔗 আমার Refer Link"), KeyboardButton(text="💰 আমার Balance")],
        [KeyboardButton(text="📥 APK নিন"), KeyboardButton(text="🎓 Course নিন")],
        [KeyboardButton(text="👤 আমার Profile"), KeyboardButton(text="🏆 Ranking")],
        [KeyboardButton(text="🎁 Daily Bonus"), KeyboardButton(text="📋 Redeem History")],
        [KeyboardButton(text="📞 Admin Contact"), KeyboardButton(text="🔔 Bot Updates")],
    ])
    return kb

def admin_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Live Stats", callback_data="admin_stats"),
         InlineKeyboardButton(text="👥 User Count", callback_data="admin_users")],
        [InlineKeyboardButton(text="📤 APK Upload", callback_data="admin_upload_apk"),
         InlineKeyboardButton(text="📚 Course Upload", callback_data="admin_upload_course")],
        [InlineKeyboardButton(text="📋 APK List", callback_data="admin_apk_list"),
         InlineKeyboardButton(text="📖 Course List", callback_data="admin_course_list")],
        [InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast"),
         InlineKeyboardButton(text="🔇 Maintenance", callback_data="admin_maintenance")],
        [InlineKeyboardButton(text="🚫 Ban User", callback_data="admin_ban"),
         InlineKeyboardButton(text="✅ Unban User", callback_data="admin_unban")],
        [InlineKeyboardButton(text="🔍 User Info", callback_data="admin_userinfo"),
         InlineKeyboardButton(text="🗑 Delete User", callback_data="admin_delete_user")],
        [InlineKeyboardButton(text="⚙️ Refer Limit", callback_data="admin_refer_limit"),
         InlineKeyboardButton(text="👑 Add Admin", callback_data="admin_add_admin")],
        [InlineKeyboardButton(text="❌ Remove Admin", callback_data="admin_remove_admin"),
         InlineKeyboardButton(text="📜 Logs", callback_data="admin_logs")],
        [InlineKeyboardButton(text="💾 DB Backup", callback_data="admin_backup"),
         InlineKeyboardButton(text="🔄 Restart Bot", callback_data="admin_restart")],
    ])
    return kb

def force_join_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Channel 1 Join করুন", url=CHANNEL_1_URL)],
        [InlineKeyboardButton(text="📢 Channel 2 Join করুন", url=CHANNEL_2_URL)],
        [InlineKeyboardButton(text="👥 Telegram Group", url=TELEGRAM_GROUP_URL)],
        [InlineKeyboardButton(text="📘 Facebook Group", url=FACEBOOK_GROUP_URL)],
        [InlineKeyboardButton(text="✅ Join করেছি - Verify করুন", callback_data="verify_join")],
    ])
    return kb

def apk_select_keyboard(apks):
    buttons = []
    for apk in apks:
        btn_text = f"📱 {apk['file_name']} ({apk['upload_date'][:10]})"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"get_apk_{apk['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def course_select_keyboard(courses):
    buttons = []
    for course in courses:
        btn_text = f"🎓 {course['file_name']} ({course['upload_date'][:10]})"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"get_course_{course['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def contact_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Admin: @jiolinhacker", url="https://t.me/jiolinhacker")],
        [InlineKeyboardButton(text="📘 Facebook Page", url=FACEBOOK_PAGE_URL)],
        [InlineKeyboardButton(text="👥 Facebook Group", url=FACEBOOK_GROUP_URL)],
        [InlineKeyboardButton(text="💬 Telegram Group", url=TELEGRAM_GROUP_URL)],
    ])
    return kb

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ANTI-SPAM / FLOOD CONTROL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def anti_flood(user_id: int) -> bool:
    """Returns True if user is flooding"""
    now = time.time()
    if user_id not in flood_tracker:
        flood_tracker[user_id] = []
    flood_tracker[user_id] = [t for t in flood_tracker[user_id] if now - t < 10]
    if len(flood_tracker[user_id]) >= 8:
        return True
    flood_tracker[user_id].append(now)
    return False

def cooldown_check(user_id: int, action: str, seconds: int = 2) -> bool:
    """Returns True if user is in cooldown"""
    key = f"{user_id}_{action}"
    now = time.time()
    if key in user_last_action:
        if now - user_last_action[key] < seconds:
            return True
    user_last_action[key] = now
    return False

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELPER FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def check_membership(bot: Bot, user_id: int) -> bool:
    """Check if user joined both required channels"""
    force_join = get_setting("force_join", "1")
    if force_join != "1":
        return True
    try:
        ch1 = await bot.get_chat_member(CHANNEL_1, user_id)
        ch2 = await bot.get_chat_member(CHANNEL_2, user_id)
        valid = ["member", "administrator", "creator"]
        return ch1.status in valid and ch2.status in valid
    except Exception as e:
        logger.warning(f"Membership check error: {e}")
        return False

def get_refer_link(user_id: int) -> str:
    return f"https://t.me/{BOT_USERNAME}?start={user_id}"

def format_profile(user: dict, rank: int = 0) -> str:
    join_date = user.get("join_date", "")[:10] if user.get("join_date") else "N/A"
    username_display = f"@{user['username']}" if user.get("username") else "নেই"
    apk_limit = int(get_setting("apk_refer_limit", "3"))
    course_limit = int(get_setting("course_refer_limit", "5"))
    bal = user.get("refer_balance", 0)
    needed_apk = max(0, apk_limit - bal)
    needed_course = max(0, course_limit - bal)
    rank_str = f"#{rank}" if rank else "N/A"
    return (
        f"╔══════════════════════╗\n"
        f"║  👤 আমার প্রোফাইল  ║\n"
        f"╚══════════════════════╝\n\n"
        f"🏷 নাম: **{user.get('full_name', 'N/A')}**\n"
        f"🔖 Username: {username_display}\n"
        f"🆔 User ID: `{user['user_id']}`\n"
        f"📅 Join Date: {join_date}\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"💰 Refer Balance: **{bal}** টি\n"
        f"📊 Total Referrals: **{user.get('total_referrals', 0)}** টি\n"
        f"🏆 Rank: {rank_str}\n"
        f"🎁 Total Claims: {user.get('total_claims', 0)} টি\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"📱 APK নিতে আরো: **{needed_apk}** টি Refer দরকার\n"
        f"🎓 Course নিতে আরো: **{needed_course}** টি Refer দরকার\n"
        f"━━━━━━━━━━━━━━━━━"
    )

async def send_log(bot: Bot, text: str):
    logs_channel = get_setting("logs_channel", None)
    if logs_channel:
        try:
            await bot.send_message(logs_channel, text)
        except Exception:
            pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BOT INIT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MIDDLEWARE: BAN + FLOOD CHECK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.message.middleware()
async def security_middleware(handler, event: Message, data: dict):
    user_id = event.from_user.id if event.from_user else None
    if not user_id:
        return await handler(event, data)

    if is_banned(user_id):
        await event.answer("🚫 আপনাকে এই বট থেকে Ban করা হয়েছে।\nAdmin: @jiolinhacker")
        return

    if anti_flood(user_id):
        await event.answer("⚠️ অনেক বেশি message পাঠাচ্ছেন! একটু অপেক্ষা করুন।")
        return

    maintenance = get_setting("maintenance_mode", "0")
    if maintenance == "1" and not is_admin(user_id):
        await event.answer("🔧 বট এখন Maintenance Mode এ আছে। কিছুক্ষণ পর try করুন।")
        return

    return await handler(event, data)

@dp.callback_query.middleware()
async def callback_security_middleware(handler, event: CallbackQuery, data: dict):
    user_id = event.from_user.id if event.from_user else None
    if not user_id:
        return await handler(event, data)

    if is_banned(user_id):
        await event.answer("🚫 আপনাকে Ban করা হয়েছে!", show_alert=True)
        return

    if anti_flood(user_id):
        await event.answer("⚠️ Flood detected! একটু অপেক্ষা করুন।", show_alert=True)
        return

    return await handler(event, data)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# /START HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.message(CommandStart())
async def start_handler(message: Message):
    user = message.from_user
    user_id = user.id
    args = message.text.split()
    referrer_id = None

    if len(args) > 1:
        try:
            referrer_id = int(args[1])
            if referrer_id == user_id:
                referrer_id = None
        except (ValueError, TypeError):
            referrer_id = None

    # Register user
    existing = get_user(user_id)
    if not existing:
        create_user(
            user_id=user_id,
            username=user.username or "",
            full_name=user.full_name or "Unknown",
            referred_by=referrer_id
        )
        # Credit referrer
        if referrer_id and referrer_id != user_id:
            referrer = get_user(referrer_id)
            if referrer and not is_banned(referrer_id):
                success = add_referral(referrer_id, user_id)
                if success:
                    referrer_updated = get_user(referrer_id)
                    new_bal = referrer_updated.get("refer_balance", 0)
                    apk_limit = int(get_setting("apk_refer_limit", "3"))
                    course_limit = int(get_setting("course_refer_limit", "5"))
                    try:
                        await bot.send_message(
                            referrer_id,
                            f"🎉 **নতুন Refer পেয়েছেন!**\n\n"
                            f"👤 নাম: {user.full_name}\n"
                            f"💰 আপনার Balance: **{new_bal}** টি\n\n"
                            f"📱 APK নিতে লাগবে: {apk_limit} টি Refer\n"
                            f"🎓 Course নিতে লাগবে: {course_limit} টি Refer"
                        )
                    except Exception:
                        pass
                    add_log("referral", user_id, f"Referred by {referrer_id}")
    else:
        # Update username/name
        update_user(user_id, username=user.username or "", full_name=user.full_name or "Unknown")

    # Force join check
    joined = await check_membership(bot, user_id)
    if not joined:
        await message.answer(
            f"⚠️ **Channel Join না করলে Bot ব্যবহার করা যাবে না!**\n\n"
            f"নিচের Channel গুলো Join করে Verify বাটনে ক্লিক করুন:",
            reply_markup=force_join_keyboard()
        )
        return

    # Welcome message
    welcome_text = (
        f"╔══════════════════════════╗\n"
        f"║   🌙 Assalamualaikum 🌸  ║\n"
        f"╚══════════════════════════╝\n\n"
        f"🔥 **{BOT_NAME}** এ আপনাদের স্বাগতম!\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💎 এই বটের মাধ্যমে আপনারা Refer করে\n"
        f"   **Premium APK** এবং **Course** নিতে পারবেন!\n\n"
        f"📱 **APK নিতে:** {get_setting('apk_refer_limit', '3')} টি Refer\n"
        f"🎓 **Course নিতে:** {get_setting('course_refer_limit', '5')} টি Refer\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 আপনার Refer Link:\n"
        f"`{get_refer_link(user_id)}`\n\n"
        f"✨ **Secure • Premium • Cyber • Fast** ✨\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    await message.answer(welcome_text, reply_markup=main_keyboard())

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VERIFY JOIN CALLBACK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.callback_query(F.data == "verify_join")
async def verify_join_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    joined = await check_membership(bot, user_id)
    if not joined:
        await callback.answer(
            "❌ আপনি এখনো সব Channel Join করেননি!\nসব Channel Join করে আবার try করুন।",
            show_alert=True
        )
        return
    await callback.message.delete()
    await callback.message.answer(
        f"✅ **Channel Join Verified!**\n\n"
        f"🔥 **{BOT_NAME}** এ আপনাকে স্বাগতম!\n\n"
        f"নিচের বাটন গুলো ব্যবহার করুন 👇",
        reply_markup=main_keyboard()
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FORCE JOIN CHECK DECORATOR HELPER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def require_join(message: Message) -> bool:
    """Returns False and sends join message if not joined"""
    joined = await check_membership(bot, message.from_user.id)
    if not joined:
        await message.answer(
            "⚠️ প্রথমে নিচের Channel গুলো Join করুন!",
            reply_markup=force_join_keyboard()
        )
        return False
    return True

async def require_join_cb(callback: CallbackQuery) -> bool:
    joined = await check_membership(bot, callback.from_user.id)
    if not joined:
        await callback.answer("⚠️ প্রথমে Channel Join করুন!", show_alert=True)
        return False
    return True

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REFER LINK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.message(F.text == "🔗 আমার Refer Link")
async def my_refer_link(message: Message):
    if not await require_join(message):
        return
    user_id = message.from_user.id
    link = get_refer_link(user_id)
    apk_limit = get_setting("apk_refer_limit", "3")
    course_limit = get_setting("course_refer_limit", "5")
    text = (
        f"╔════════════════════╗\n"
        f"║  🔗 আপনার Refer Link  ║\n"
        f"╚════════════════════╝\n\n"
        f"📋 নিচের Link টি Copy করুন এবং বন্ধুদের সাথে Share করুন:\n\n"
        f"`{link}`\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"📱 APK নিতে: **{apk_limit}** টি Refer লাগবে\n"
        f"🎓 Course নিতে: **{course_limit}** টি Refer লাগবে\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"💡 Link Share করলে নতুন user bot join করলে আপনার Balance বাড়বে!"
    )
    await message.answer(text)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BALANCE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.message(F.text == "💰 আমার Balance")
async def my_balance(message: Message):
    if not await require_join(message):
        return
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("❌ আপনার Account খুঁজে পাওয়া যায়নি। /start দিন।")
        return
    bal = user.get("refer_balance", 0)
    total = user.get("total_referrals", 0)
    apk_limit = int(get_setting("apk_refer_limit", "3"))
    course_limit = int(get_setting("course_refer_limit", "5"))
    text = (
        f"╔════════════════════╗\n"
        f"║  💰 Refer Balance  ║\n"
        f"╚════════════════════╝\n\n"
        f"💎 বর্তমান Balance: **{bal}** টি Refer\n"
        f"📊 মোট Refer: **{total}** টি\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"📱 APK নিতে: **{apk_limit}** টি (আরো {max(0, apk_limit - bal)} টি দরকার)\n"
        f"🎓 Course নিতে: **{course_limit}** টি (আরো {max(0, course_limit - bal)} টি দরকার)\n"
        f"━━━━━━━━━━━━━━━━━"
    )
    await message.answer(text)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# APK CLAIM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.message(F.text == "📥 APK নিন")
async def apk_menu(message: Message):
    if not await require_join(message):
        return
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("❌ /start দিন।")
        return
    apk_limit = int(get_setting("apk_refer_limit", "3"))
    bal = user.get("refer_balance", 0)
    if bal < apk_limit:
        await message.answer(
            f"❌ **পর্যাপ্ত Refer নেই!**\n\n"
            f"📱 APK নিতে **{apk_limit}** টি Refer লাগবে\n"
            f"💰 আপনার Balance: **{bal}** টি\n"
            f"⬆️ আরো **{apk_limit - bal}** টি Refer দরকার\n\n"
            f"🔗 আপনার Refer Link:\n`{get_refer_link(message.from_user.id)}`"
        )
        return
    apks = get_apk_list()
    if not apks:
        await message.answer("❌ এখন কোনো APK Available নেই। পরে আবার try করুন।")
        return
    await message.answer(
        f"✅ আপনার Balance: **{bal}** Refer\n\n"
        f"📱 নিচের APK গুলো থেকে একটি Choose করুন:",
        reply_markup=apk_select_keyboard(apks)
    )

@dp.callback_query(F.data.startswith("get_apk_"))
async def deliver_apk(callback: CallbackQuery):
    if not await require_join_cb(callback):
        return
    user_id = callback.from_user.id
    if cooldown_check(user_id, "get_apk", 5):
        await callback.answer("⏳ একটু অপেক্ষা করুন...", show_alert=True)
        return
    apk_id = int(callback.data.split("_")[2])
    user = get_user(user_id)
    if not user:
        await callback.answer("❌ /start দিন।", show_alert=True)
        return
    apk_limit = int(get_setting("apk_refer_limit", "3"))
    bal = user.get("refer_balance", 0)
    if bal < apk_limit:
        await callback.answer(
            f"❌ পর্যাপ্ত Refer নেই! {apk_limit} টি লাগবে, আপনার আছে {bal} টি",
            show_alert=True
        )
        return
    conn = get_db()
    apk = conn.execute("SELECT * FROM apk_files WHERE id=? AND is_active=1", (apk_id,)).fetchone()
    conn.close()
    if not apk:
        await callback.answer("❌ APK পাওয়া যায়নি।", show_alert=True)
        return
    apk = dict(apk)
    # Deduct balance
    update_user(user_id, refer_balance=bal - apk_limit, total_claims=user.get("total_claims", 0) + 1)
    # Save claim
    conn = get_db()
    conn.execute("INSERT INTO claims (user_id, claim_type, item_id, date) VALUES (?, 'apk', ?, ?)",
                 (user_id, apk_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    add_log("apk_claim", user_id, f"Claimed APK ID {apk_id}: {apk['file_name']}")
    try:
        await callback.message.answer_document(
            document=apk["file_id"],
            caption=(
                f"📱 **APK Delivered!**\n\n"
                f"📦 Name: {apk['file_name']}\n"
                f"📝 Caption: {apk.get('caption', 'N/A')}\n"
                f"📅 Date: {apk['upload_date'][:10]}\n\n"
                f"━━━━━━━━━━━━━━━\n"
                f"✅ আপনার Balance থেকে **{apk_limit}** Refer কাটা হয়েছে\n"
                f"💰 বাকি Balance: **{bal - apk_limit}** টি\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🤖 {BOT_NAME}"
            )
        )
        await callback.answer("✅ APK পাঠানো হয়েছে!", show_alert=True)
        # Notify admins
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    f"📥 **APK Claimed!**\n"
                    f"👤 User: {callback.from_user.full_name} (`{user_id}`)\n"
                    f"📱 APK: {apk['file_name']}\n"
                    f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
            except Exception:
                pass
    except Exception as e:
        logger.error(f"APK delivery error: {e}")
        # Refund
        update_user(user_id, refer_balance=bal, total_claims=user.get("total_claims", 0))
        await callback.answer("❌ APK পাঠাতে সমস্যা হয়েছে। Balance ফেরত দেওয়া হয়েছে।", show_alert=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COURSE CLAIM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.message(F.text == "🎓 Course নিন")
async def course_menu(message: Message):
    if not await require_join(message):
        return
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("❌ /start দিন।")
        return
    course_limit = int(get_setting("course_refer_limit", "5"))
    bal = user.get("refer_balance", 0)
    if bal < course_limit:
        await message.answer(
            f"❌ **পর্যাপ্ত Refer নেই!**\n\n"
            f"🎓 Course নিতে **{course_limit}** টি Refer লাগবে\n"
            f"💰 আপনার Balance: **{bal}** টি\n"
            f"⬆️ আরো **{course_limit - bal}** টি Refer দরকার\n\n"
            f"🔗 আপনার Refer Link:\n`{get_refer_link(message.from_user.id)}`"
        )
        return
    courses = get_course_list()
    if not courses:
        await message.answer("❌ এখন কোনো Course Available নেই। পরে আবার try করুন।")
        return
    await message.answer(
        f"✅ আপনার Balance: **{bal}** Refer\n\n"
        f"🎓 নিচের Course গুলো থেকে একটি Choose করুন:",
        reply_markup=course_select_keyboard(courses)
    )

@dp.callback_query(F.data.startswith("get_course_"))
async def deliver_course(callback: CallbackQuery):
    if not await require_join_cb(callback):
        return
    user_id = callback.from_user.id
    if cooldown_check(user_id, "get_course", 5):
        await callback.answer("⏳ একটু অপেক্ষা করুন...", show_alert=True)
        return
    course_id = int(callback.data.split("_")[2])
    user = get_user(user_id)
    if not user:
        await callback.answer("❌ /start দিন।", show_alert=True)
        return
    course_limit = int(get_setting("course_refer_limit", "5"))
    bal = user.get("refer_balance", 0)
    if bal < course_limit:
        await callback.answer(
            f"❌ পর্যাপ্ত Refer নেই! {course_limit} টি লাগবে, আপনার আছে {bal} টি",
            show_alert=True
        )
        return
    conn = get_db()
    course = conn.execute("SELECT * FROM course_files WHERE id=? AND is_active=1", (course_id,)).fetchone()
    conn.close()
    if not course:
        await callback.answer("❌ Course পাওয়া যায়নি।", show_alert=True)
        return
    course = dict(course)
    update_user(user_id, refer_balance=bal - course_limit, total_claims=user.get("total_claims", 0) + 1)
    conn = get_db()
    conn.execute("INSERT INTO claims (user_id, claim_type, item_id, date) VALUES (?, 'course', ?, ?)",
                 (user_id, course_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    add_log("course_claim", user_id, f"Claimed Course ID {course_id}: {course['file_name']}")
    try:
        caption_text = (
            f"🎓 **Course Delivered!**\n\n"
            f"📦 Name: {course['file_name']}\n"
            f"📝 Info: {course.get('caption', 'N/A')}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"✅ Balance থেকে **{course_limit}** Refer কাটা হয়েছে\n"
            f"💰 বাকি Balance: **{bal - course_limit}** টি\n"
            f"🤖 {BOT_NAME}"
        )
        file_type = course.get("file_type", "document")
        if file_type == "video":
            await callback.message.answer_video(video=course["file_id"], caption=caption_text)
        elif file_type == "photo":
            await callback.message.answer_photo(photo=course["file_id"], caption=caption_text)
        else:
            await callback.message.answer_document(document=course["file_id"], caption=caption_text)
        await callback.answer("✅ Course পাঠানো হয়েছে!", show_alert=True)
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    f"🎓 **Course Claimed!**\n"
                    f"👤 User: {callback.from_user.full_name} (`{user_id}`)\n"
                    f"📚 Course: {course['file_name']}\n"
                    f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Course delivery error: {e}")
        update_user(user_id, refer_balance=bal, total_claims=user.get("total_claims", 0))
        await callback.answer("❌ Course পাঠাতে সমস্যা। Balance ফেরত দেওয়া হয়েছে।", show_alert=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PROFILE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.message(F.text == "👤 আমার Profile")
async def my_profile(message: Message):
    if not await require_join(message):
        return
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("❌ /start দিন।")
        return
    ranking = get_ranking()
    rank = 0
    for i, r in enumerate(ranking, 1):
        if r["user_id"] == message.from_user.id:
            rank = i
            break
    await message.answer(format_profile(user, rank))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RANKING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.message(F.text == "🏆 Ranking")
async def ranking_handler(message: Message):
    if not await require_join(message):
        return
    ranking = get_ranking()
    if not ranking:
        await message.answer("❌ কোনো Ranking পাওয়া যায়নি।")
        return
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    text = "╔══════════════════════╗\n║  🏆 TOP REFERRERS  ║\n╚══════════════════════╝\n\n"
    for i, user in enumerate(ranking):
        medal = medals[i] if i < len(medals) else f"{i+1}."
        name = user["full_name"] or "Unknown"
        uname = f"@{user['username']}" if user.get("username") else "—"
        text += f"{medal} **{name}** ({uname})\n   📊 Referrals: **{user['total_referrals']}** টি\n\n"
    await message.answer(text)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DAILY BONUS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.message(F.text == "🎁 Daily Bonus")
async def daily_bonus(message: Message):
    if not await require_join(message):
        return
    user_id = message.from_user.id
    conn = get_db()
    bonus_row = conn.execute("SELECT * FROM bonuses WHERE user_id=?", (user_id,)).fetchone()
    now = datetime.now()
    if bonus_row:
        bonus_row = dict(bonus_row)
        last_claim = datetime.fromisoformat(bonus_row["last_claim"]) if bonus_row.get("last_claim") else None
        if last_claim:
            diff = (now - last_claim).total_seconds()
            if diff < DAILY_BONUS_COOLDOWN:
                remaining = DAILY_BONUS_COOLDOWN - diff
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)
                seconds = int(remaining % 60)
                conn.close()
                await message.answer(
                    f"⏳ **Daily Bonus ইতিমধ্যে নেওয়া হয়েছে!**\n\n"
                    f"⏰ পরবর্তী Bonus পাওয়া যাবে:\n"
                    f"**{hours}h {minutes}m {seconds}s** পরে"
                )
                return
        conn.execute("UPDATE bonuses SET last_claim=?, total_bonus=total_bonus+? WHERE user_id=?",
                     (now.isoformat(), DAILY_BONUS_AMOUNT, user_id))
    else:
        conn.execute("INSERT INTO bonuses (user_id, last_claim, total_bonus) VALUES (?, ?, ?)",
                     (user_id, now.isoformat(), DAILY_BONUS_AMOUNT))
    conn.commit()
    conn.close()
    user = get_user(user_id)
    new_bal = user.get("refer_balance", 0) + DAILY_BONUS_AMOUNT
    update_user(user_id, refer_balance=new_bal)
    add_log("daily_bonus", user_id, f"Claimed daily bonus +{DAILY_BONUS_AMOUNT}")
    await message.answer(
        f"🎁 **Daily Bonus পেয়েছেন!**\n\n"
        f"✅ +{DAILY_BONUS_AMOUNT} Refer Balance যোগ হয়েছে\n"
        f"💰 বর্তমান Balance: **{new_bal}** টি\n\n"
        f"⏰ পরবর্তী Bonus: **24 ঘণ্টা** পরে"
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REDEEM HISTORY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.message(F.text == "📋 Redeem History")
async def redeem_history(message: Message):
    if not await require_join(message):
        return
    user_id = message.from_user.id
    conn = get_db()
    claims = conn.execute(
        "SELECT * FROM claims WHERE user_id=? ORDER BY id DESC LIMIT 10", (user_id,)
    ).fetchall()
    conn.close()
    if not claims:
        await message.answer("📋 আপনার কোনো Redeem History নেই।")
        return
    text = "╔══════════════════════╗\n║  📋 Redeem History  ║\n╚══════════════════════╝\n\n"
    for claim in claims:
        claim = dict(claim)
        ctype = "📱 APK" if claim["claim_type"] == "apk" else "🎓 Course"
        date = claim["date"][:16] if claim.get("date") else "N/A"
        text += f"{ctype} - ID: {claim['item_id']}\n📅 {date}\n\n"
    await message.answer(text)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONTACT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.message(F.text == "📞 Admin Contact")
async def admin_contact(message: Message):
    await message.answer(
        f"╔════════════════════╗\n"
        f"║  📞 যোগাযোগ করুন  ║\n"
        f"╚════════════════════╝\n\n"
        f"👤 Admin: @jiolinhacker\n\n"
        f"নিচের লিংক থেকে যোগাযোগ করুন:",
        reply_markup=contact_keyboard()
    )

@dp.message(F.text == "🔔 Bot Updates")
async def bot_updates(message: Message):
    await message.answer(
        f"🔔 **Bot Updates পেতে Channel Join করুন:**\n\n"
        f"📢 Channel 1: {CHANNEL_1_URL}\n"
        f"📢 Channel 2: {CHANNEL_2_URL}\n\n"
        f"💬 Group: {TELEGRAM_GROUP_URL}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Channel 1", url=CHANNEL_1_URL)],
            [InlineKeyboardButton(text="📢 Channel 2", url=CHANNEL_2_URL)],
        ])
    )

@dp.callback_query(F.data == "back_main")
async def back_main_cb(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ADMIN COMMAND
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ আপনি Admin নন!")
        return
    stats = get_stats()
    text = (
        f"╔══════════════════════════╗\n"
        f"║  ⚙️ ADMIN PANEL  ║\n"
        f"╚══════════════════════════╝\n\n"
        f"📊 **Live Stats:**\n"
        f"👥 Total Users: **{stats['users']}**\n"
        f"🔗 Total Referrals: **{stats['referrals']}**\n"
        f"🎁 Total Claims: **{stats['claims']}**\n"
        f"📱 Active APKs: **{stats['apks']}**\n"
        f"🎓 Active Courses: **{stats['courses']}**\n"
        f"🚫 Banned Users: **{stats['banned']}**\n\n"
        f"নিচের বাটন থেকে কাজ করুন:"
    )
    await message.answer(text, reply_markup=admin_keyboard())

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ADMIN CALLBACKS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.callback_query(F.data == "admin_stats")
async def admin_stats_cb(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin নন!", show_alert=True)
        return
    stats = get_stats()
    text = (
        f"📊 **Live Bot Stats**\n\n"
        f"👥 Total Users: **{stats['users']}**\n"
        f"🔗 Total Referrals: **{stats['referrals']}**\n"
        f"🎁 Total Claims: **{stats['claims']}**\n"
        f"📱 Active APKs: **{stats['apks']}**\n"
        f"🎓 Active Courses: **{stats['courses']}**\n"
        f"🚫 Banned Users: **{stats['banned']}**\n"
        f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back", callback_data="admin_back")]
    ]))
    await callback.answer()

@dp.callback_query(F.data == "admin_upload_apk")
async def admin_upload_apk_cb(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin নন!", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_apk)
    await callback.message.answer(
        "📱 **APK Upload করুন**\n\n"
        "এখন APK File পাঠান।\n"
        "Caption দিলে সেটি save হবে।\n"
        "Cancel করতে /cancel লিখুন।"
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_upload_course")
async def admin_upload_course_cb(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin নন!", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_course)
    await callback.message.answer(
        "🎓 **Course Upload করুন**\n\n"
        "এখন Video/File পাঠান।\n"
        "Caption দিলে সেটি save হবে।\n"
        "Cancel করতে /cancel লিখুন।"
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_apk_list")
async def admin_apk_list_cb(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin নন!", show_alert=True)
        return
    apks = get_apk_list()
    if not apks:
        await callback.answer("❌ কোনো APK নেই!", show_alert=True)
        return
    text = "📱 **APK List:**\n\n"
    buttons = []
    for apk in apks:
        text += f"🆔 ID: {apk['id']} | 📦 {apk['file_name']} | 📅 {apk['upload_date'][:10]}\n"
        buttons.append([InlineKeyboardButton(text=f"🗑 Delete APK #{apk['id']}", callback_data=f"del_apk_{apk['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="admin_back")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("del_apk_"))
async def delete_apk_cb(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin নন!", show_alert=True)
        return
    apk_id = int(callback.data.split("_")[2])
    conn = get_db()
    conn.execute("UPDATE apk_files SET is_active=0 WHERE id=?", (apk_id,))
    conn.commit()
    conn.close()
    add_log("delete_apk", callback.from_user.id, f"Deleted APK ID {apk_id}")
    await callback.answer(f"✅ APK #{apk_id} Delete করা হয়েছে!", show_alert=True)
    await callback.message.edit_text("✅ APK Deleted!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back", callback_data="admin_back")]
    ]))

@dp.callback_query(F.data == "admin_course_list")
async def admin_course_list_cb(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin নন!", show_alert=True)
        return
    courses = get_course_list()
    if not courses:
        await callback.answer("❌ কোনো Course নেই!", show_alert=True)
        return
    text = "🎓 **Course List:**\n\n"
    buttons = []
    for c in courses:
        text += f"🆔 ID: {c['id']} | 📦 {c['file_name']} | 📅 {c['upload_date'][:10]}\n"
        buttons.append([InlineKeyboardButton(text=f"🗑 Delete Course #{c['id']}", callback_data=f"del_course_{c['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="admin_back")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith("del_course_"))
async def delete_course_cb(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin নন!", show_alert=True)
        return
    course_id = int(callback.data.split("_")[2])
    conn = get_db()
    conn.execute("UPDATE course_files SET is_active=0 WHERE id=?", (course_id,))
    conn.commit()
    conn.close()
    await callback.answer(f"✅ Course #{course_id} Delete করা হয়েছে!", show_alert=True)
    await callback.message.edit_text("✅ Course Deleted!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back", callback_data="admin_back")]
    ]))

@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_cb(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin নন!", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_broadcast)
    await callback.message.answer(
        "📢 **Broadcast Message পাঠান**\n\n"
        "Text, Photo, Video বা File পাঠাতে পারবেন।\n"
        "Cancel করতে /cancel লিখুন।"
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_maintenance")
async def admin_maintenance_cb(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin নন!", show_alert=True)
        return
    current = get_setting("maintenance_mode", "0")
    new_val = "0" if current == "1" else "1"
    set_setting("maintenance_mode", new_val)
    status = "ON 🔧" if new_val == "1" else "OFF ✅"
    await callback.answer(f"Maintenance Mode: {status}", show_alert=True)

@dp.callback_query(F.data == "admin_ban")
async def admin_ban_cb(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin নন!", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_ban_id)
    await callback.message.answer("🚫 যে User কে Ban করতে চান তার **User ID** পাঠান:\n/cancel করতে লিখুন /cancel")
    await callback.answer()

@dp.callback_query(F.data == "admin_unban")
async def admin_unban_cb(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin নন!", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_unban_id)
    await callback.message.answer("✅ যে User কে Unban করতে চান তার **User ID** পাঠান:")
    await callback.answer()

@dp.callback_query(F.data == "admin_userinfo")
async def admin_userinfo_cb(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin নন!", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_user_info_id)
    await callback.message.answer("🔍 যে User এর Info দেখতে চান তার **User ID** পাঠান:")
    await callback.answer()

@dp.callback_query(F.data == "admin_refer_limit")
async def admin_refer_limit_cb(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin নন!", show_alert=True)
        return
    apk_lim = get_setting("apk_refer_limit", "3")
    course_lim = get_setting("course_refer_limit", "5")
    await state.set_state(AdminStates.waiting_refer_limit)
    await callback.message.answer(
        f"⚙️ **Refer Limit Change করুন**\n\n"
        f"📱 APK: **{apk_lim}** টি Refer\n"
        f"🎓 Course: **{course_lim}** টি Refer\n\n"
        f"Format এ পাঠান:\n`apk 3` অথবা `course 5`"
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_add_admin")
async def admin_add_admin_cb(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Super Admin নন!", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_add_admin)
    await callback.message.answer("👑 নতুন Admin এর **User ID** পাঠান:")
    await callback.answer()

@dp.callback_query(F.data == "admin_remove_admin")
async def admin_remove_admin_cb(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Super Admin নন!", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_remove_admin)
    await callback.message.answer("❌ যে Admin কে Remove করতে চান তার **User ID** পাঠান:")
    await callback.answer()

@dp.callback_query(F.data == "admin_logs")
async def admin_logs_cb(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin নন!", show_alert=True)
        return
    conn = get_db()
    logs = conn.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 15").fetchall()
    conn.close()
    if not logs:
        await callback.answer("❌ কোনো Log নেই!", show_alert=True)
        return
    text = "📜 **Recent Logs (Last 15):**\n\n"
    for log in logs:
        log = dict(log)
        date = log["date"][:16] if log.get("date") else "N/A"
        text += f"[{date}] {log['event_type']} | UID:{log['user_id']} | {log['details']}\n"
    await callback.message.answer(text)
    await callback.answer()

@dp.callback_query(F.data == "admin_backup")
async def admin_backup_cb(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin নন!", show_alert=True)
        return
    try:
        await callback.message.answer_document(
            document=types.FSInputFile(DB_PATH),
            caption=f"💾 **Database Backup**\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await callback.answer("✅ Backup sent!", show_alert=True)
    except Exception as e:
        await callback.answer(f"❌ Error: {str(e)}", show_alert=True)

@dp.callback_query(F.data == "admin_restart")
async def admin_restart_cb(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin নন!", show_alert=True)
        return
    await callback.answer("🔄 Bot Restart হচ্ছে...", show_alert=True)
    await callback.message.answer("🔄 Restarting...")
    os.execv(__file__, ['python'] + [__file__])

@dp.callback_query(F.data == "admin_users")
async def admin_users_cb(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin নন!", show_alert=True)
        return
    stats = get_stats()
    conn = get_db()
    recent = conn.execute("SELECT full_name, user_id, join_date FROM users ORDER BY join_date DESC LIMIT 5").fetchall()
    conn.close()
    text = f"👥 **Total Users: {stats['users']}**\n\n🆕 Recent Users:\n"
    for u in recent:
        u = dict(u)
        date = u["join_date"][:10] if u.get("join_date") else "N/A"
        text += f"👤 {u['full_name']} (`{u['user_id']}`) - {date}\n"
    await callback.message.answer(text)
    await callback.answer()

@dp.callback_query(F.data == "admin_delete_user")
async def admin_delete_user_cb(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin নন!", show_alert=True)
        return
    await callback.message.answer("🗑 যে User কে Delete করতে চান তার User ID পাঠান:")
    await callback.answer()

@dp.callback_query(F.data == "admin_back")
async def admin_back_cb(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Admin নন!", show_alert=True)
        return
    stats = get_stats()
    text = (
        f"⚙️ **ADMIN PANEL**\n\n"
        f"👥 Users: {stats['users']} | 🔗 Referrals: {stats['referrals']}\n"
        f"📱 APKs: {stats['apks']} | 🎓 Courses: {stats['courses']}"
    )
    await callback.message.edit_text(text, reply_markup=admin_keyboard())
    await callback.answer()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ADMIN STATE HANDLERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    current = await state.get_state()
    if current:
        await state.clear()
        await message.answer("❌ Operation cancel করা হয়েছে।", reply_markup=main_keyboard())
    else:
        await message.answer("কোনো active operation নেই।")

@dp.message(AdminStates.waiting_apk)
async def handle_apk_upload(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    doc = message.document
    if not doc:
        await message.answer("❌ APK File পাঠান (Document হিসেবে)।")
        return
    file_name = doc.file_name or "Unknown APK"
    file_id = doc.file_id
    file_size = f"{doc.file_size // 1024} KB" if doc.file_size else "Unknown"
    caption = message.caption or ""
    version = "1.0"
    for part in file_name.split("_"):
        if part.replace(".", "").isdigit():
            version = part
            break
    conn = get_db()
    conn.execute('''INSERT INTO apk_files (file_id, file_name, file_size, caption, version, upload_date, uploaded_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 (file_id, file_name, file_size, caption, version, datetime.now().isoformat(), message.from_user.id))
    conn.commit()
    conn.close()
    add_log("apk_upload", message.from_user.id, f"Uploaded: {file_name}")
    await state.clear()
    await message.answer(
        f"✅ **APK Upload সফল!**\n\n"
        f"📦 Name: {file_name}\n"
        f"📏 Size: {file_size}\n"
        f"🔢 Version: {version}\n"
        f"📝 Caption: {caption or 'নেই'}\n"
        f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

@dp.message(AdminStates.waiting_course)
async def handle_course_upload(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    file_id = None
    file_name = "Unknown Course"
    file_type = "document"
    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name or "Course File"
        file_type = "document"
    elif message.video:
        file_id = message.video.file_id
        file_name = message.video.file_name or "Course Video"
        file_type = "video"
    elif message.photo:
        file_id = message.photo[-1].file_id
        file_name = "Course Photo"
        file_type = "photo"
    else:
        await message.answer("❌ Document, Video বা Photo পাঠান।")
        return
    caption = message.caption or ""
    conn = get_db()
    conn.execute('''INSERT INTO course_files (file_id, file_name, file_type, caption, upload_date, uploaded_by)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                 (file_id, file_name, file_type, caption, datetime.now().isoformat(), message.from_user.id))
    conn.commit()
    conn.close()
    add_log("course_upload", message.from_user.id, f"Uploaded: {file_name}")
    await state.clear()
    await message.answer(
        f"✅ **Course Upload সফল!**\n\n"
        f"📦 Name: {file_name}\n"
        f"📂 Type: {file_type}\n"
        f"📝 Caption: {caption or 'নেই'}\n"
        f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

@dp.message(AdminStates.waiting_broadcast)
async def handle_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    conn = get_db()
    users = conn.execute("SELECT user_id FROM users WHERE is_banned=0").fetchall()
    conn.close()
    total = len(users)
    sent = 0
    failed = 0
    progress_msg = await message.answer(f"📢 Broadcasting to {total} users...")
    for user_row in users:
        uid = user_row["user_id"]
        try:
            if message.text:
                await bot.send_message(uid, f"📢 **Bot Update:**\n\n{message.text}")
            elif message.photo:
                await bot.send_photo(uid, message.photo[-1].file_id, caption=message.caption or "📢 Bot Update")
            elif message.video:
                await bot.send_video(uid, message.video.file_id, caption=message.caption or "📢 Bot Update")
            elif message.document:
                await bot.send_document(uid, message.document.file_id, caption=message.caption or "📢 Bot Update")
            sent += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            failed += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    add_log("broadcast", message.from_user.id, f"Sent: {sent}, Failed: {failed}")
    await progress_msg.edit_text(
        f"✅ **Broadcast Complete!**\n\n"
        f"👥 Total: {total}\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}"
    )

@dp.message(AdminStates.waiting_ban_id)
async def handle_ban(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Valid User ID দিন!")
        return
    if target_id in ADMIN_IDS:
        await message.answer("❌ Super Admin কে Ban করা যাবে না!")
        return
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO banned_users (user_id, banned_by, ban_date) VALUES (?, ?, ?)",
                 (target_id, message.from_user.id, datetime.now().isoformat()))
    conn.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (target_id,))
    conn.commit()
    conn.close()
    add_log("ban", message.from_user.id, f"Banned user {target_id}")
    await message.answer(f"🚫 User `{target_id}` কে Ban করা হয়েছে!")
    try:
        await bot.send_message(target_id, "🚫 আপনাকে এই Bot থেকে Ban করা হয়েছে।")
    except Exception:
        pass

@dp.message(AdminStates.waiting_unban_id)
async def handle_unban(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Valid User ID দিন!")
        return
    conn = get_db()
    conn.execute("DELETE FROM banned_users WHERE user_id=?", (target_id,))
    conn.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (target_id,))
    conn.commit()
    conn.close()
    add_log("unban", message.from_user.id, f"Unbanned user {target_id}")
    await message.answer(f"✅ User `{target_id}` কে Unban করা হয়েছে!")
    try:
        await bot.send_message(target_id, "✅ আপনার Ban তুলে নেওয়া হয়েছে! /start দিন।")
    except Exception:
        pass

@dp.message(AdminStates.waiting_user_info_id)
async def handle_user_info(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Valid User ID দিন!")
        return
    user = get_user(target_id)
    if not user:
        await message.answer("❌ User পাওয়া যায়নি!")
        return
    conn = get_db()
    claim_count = conn.execute("SELECT COUNT(*) as c FROM claims WHERE user_id=?", (target_id,)).fetchone()["c"]
    ref_count = conn.execute("SELECT COUNT(*) as c FROM referrals WHERE referrer_id=?", (target_id,)).fetchone()["c"]
    conn.close()
    banned_status = "🚫 Banned" if is_banned(target_id) else "✅ Active"
    admin_status = "👑 Admin" if is_admin(target_id) else "👤 User"
    username_display = f"@{user['username']}" if user.get("username") else "নেই"
    text = (
        f"🔍 **User Info:**\n\n"
        f"👤 Name: {user.get('full_name', 'N/A')}\n"
        f"🔖 Username: {username_display}\n"
        f"🆔 ID: `{target_id}`\n"
        f"📅 Joined: {user.get('join_date', 'N/A')[:10]}\n"
        f"💰 Balance: {user.get('refer_balance', 0)}\n"
        f"📊 Total Refs: {ref_count}\n"
        f"🎁 Claims: {claim_count}\n"
        f"🔰 Status: {banned_status}\n"
        f"🏷 Role: {admin_status}\n"
        f"👨‍👦 Referred by: {user.get('referred_by', 'N/A')}"
    )
    await message.answer(text)

@dp.message(AdminStates.waiting_refer_limit)
async def handle_refer_limit(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            raise ValueError
        type_ = parts[0].lower()
        amount = int(parts[1])
        if type_ == "apk":
            set_setting("apk_refer_limit", str(amount))
            await message.answer(f"✅ APK Refer Limit: **{amount}** এ সেট করা হয়েছে!")
        elif type_ == "course":
            set_setting("course_refer_limit", str(amount))
            await message.answer(f"✅ Course Refer Limit: **{amount}** এ সেট করা হয়েছে!")
        else:
            await message.answer("❌ `apk 3` অথবা `course 5` format এ লিখুন!")
    except (ValueError, IndexError):
        await message.answer("❌ Format: `apk 3` অথবা `course 5`")

@dp.message(AdminStates.waiting_add_admin)
async def handle_add_admin(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.clear()
    try:
        new_admin_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Valid User ID দিন!")
        return
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO admins (user_id, added_by, added_date) VALUES (?, ?, ?)",
                 (new_admin_id, message.from_user.id, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    add_log("add_admin", message.from_user.id, f"Added admin {new_admin_id}")
    await message.answer(f"✅ User `{new_admin_id}` কে Admin করা হয়েছে!")
    try:
        await bot.send_message(new_admin_id, f"✅ আপনাকে **{BOT_NAME}** এর Admin করা হয়েছে!")
    except Exception:
        pass

@dp.message(AdminStates.waiting_remove_admin)
async def handle_remove_admin(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.clear()
    try:
        rm_admin_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Valid User ID দিন!")
        return
    if rm_admin_id in ADMIN_IDS:
        await message.answer("❌ Super Admin কে Remove করা যাবে না!")
        return
    conn = get_db()
    conn.execute("DELETE FROM admins WHERE user_id=?", (rm_admin_id,))
    conn.commit()
    conn.close()
    await message.answer(f"✅ User `{rm_admin_id}` এর Admin Permission সরানো হয়েছে!")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELP COMMAND
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.message(Command("help"))
async def help_handler(message: Message):
    text = (
        f"╔══════════════════════╗\n"
        f"║  ❓ Help Menu  ║\n"
        f"╚══════════════════════╝\n\n"
        f"**User Commands:**\n"
        f"🔗 আমার Refer Link - Refer Link দেখুন\n"
        f"💰 আমার Balance - Balance দেখুন\n"
        f"📥 APK নিন - APK Claim করুন\n"
        f"🎓 Course নিন - Course Claim করুন\n"
        f"👤 আমার Profile - Profile দেখুন\n"
        f"🏆 Ranking - Top Referrers দেখুন\n"
        f"🎁 Daily Bonus - দৈনিক Bonus নিন\n"
        f"📋 Redeem History - History দেখুন\n\n"
        f"**Admin Commands:**\n"
        f"/admin - Admin Panel\n"
        f"/cancel - Operation Cancel করুন\n\n"
        f"📞 Support: @jiolinhacker"
    )
    await message.answer(text)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CATCH ALL UNKNOWN MESSAGES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.message()
async def unknown_message(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        return
    await message.answer(
        "❓ বুঝতে পারিনি। নিচের বাটন ব্যবহার করুন অথবা /help লিখুন।",
        reply_markup=main_keyboard()
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STARTUP / SHUTDOWN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def on_startup():
    init_db()
    me = await bot.get_me()
    global BOT_USERNAME
    BOT_USERNAME = me.username or BOT_USERNAME
    logger.info(f"✅ Bot started: @{BOT_USERNAME}")
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"✅ **{BOT_NAME} Started!**\n\n"
                f"🤖 @{BOT_USERNAME}\n"
                f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"Use /admin to manage."
            )
        except Exception:
            pass

async def on_shutdown():
    logger.info("⛔ Bot shutting down...")
    await bot.session.close()

async def main():
    await on_startup()
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await on_shutdown()

if __name__ == "__main__":
    asyncio.run(main())
