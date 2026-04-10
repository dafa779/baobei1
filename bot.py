Được. Dưới đây là **full code hoàn chỉnh** đã ghép theo đúng ý bạn:

- **thông báo tiếng Trung**
- **owner**: `8704348652`
- **username admin/chủ bot**: `@ZZB339`
- **private `/start`** hiện menu chào
- **nút Help** chỉ hiện cho **chủ bot**
- **Help** chỉ chủ bot dùng được
- **trial 1 ngày**
- **redeem system**:
  - mã tạo riêng theo user
  - mã chỉ dùng 1 lần
  - người khác không dùng được
- **/createcode** chỉ owner dùng
- **2 bước chọn ngôn ngữ**
- **dịch 2 chiều**
- **AI chỉ gọi 1 lần**
- **thông báo tạm tự xoá sau 10 giây**
- **bỏ Help khỏi người thường**
- **menu admin / share / settings** đầy đủ

> Bạn hãy **xóa toàn bộ bot.py cũ** và dán nguyên file này vào.

---

```python
import os
import json
import time
import random
import string
import asyncio
import threading
from collections import defaultdict, deque
from typing import Optional, Tuple, List
from urllib.parse import quote

from openai import AsyncOpenAI
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIG
# =========================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
SETTINGS_FILE = os.getenv("SETTINGS_FILE", "group_settings.json").strip()
USER_DATA_FILE = os.getenv("USER_DATA_FILE", "user_access.json").strip()
REDEEM_FILE = os.getenv("REDEEM_FILE", "redeem_codes.json").strip()

RATE_LIMIT_COUNT = int(os.getenv("RATE_LIMIT_COUNT", "5"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
MAX_INPUT_CHARS = int(os.getenv("MAX_INPUT_CHARS", "8000"))

OWNER_ID = int(os.getenv("OWNER_ID", "8704348652"))
ADMIN_USERNAME = "ZZB339"
ADMIN_MENTION = f"@{ADMIN_USERNAME}"

client = None
BOT_USERNAME = None

# =========================
# LANGUAGES
# =========================
LANGS = {
    "vi": "🇻🇳 越南语",
    "en": "🇬🇧 英文",
    "ja": "🇯🇵 日语",
    "ko": "🇰🇷 韩语",
    "zh-CN": "🇨🇳 简体中文",
}
SUPPORTED = set(LANGS.keys())

# =========================
# LOCKS / STORAGE
# =========================
settings_lock = threading.Lock()
user_lock = threading.Lock()
redeem_lock = threading.Lock()

group_settings = {}
user_data = {}
redeem_codes = {}

# =========================
# SAVE / LOAD
# =========================
def save_settings():
    with settings_lock:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(group_settings, f, ensure_ascii=False, indent=2)


def load_settings():
    global group_settings
    if not os.path.exists(SETTINGS_FILE):
        group_settings = {}
        return
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            group_settings = data if isinstance(data, dict) else {}
    except Exception:
        group_settings = {}


def save_user_data():
    with user_lock:
        with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(user_data, f, ensure_ascii=False, indent=2)


def load_user_data():
    global user_data
    if not os.path.exists(USER_DATA_FILE):
        user_data = {}
        return
    try:
        with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            user_data = data if isinstance(data, dict) else {}
    except Exception:
        user_data = {}


def save_redeem_codes():
    with redeem_lock:
        with open(REDEEM_FILE, "w", encoding="utf-8") as f:
            json.dump(redeem_codes, f, ensure_ascii=False, indent=2)


def load_redeem_codes():
    global redeem_codes
    if not os.path.exists(REDEEM_FILE):
        redeem_codes = {}
        return
    try:
        with open(REDEEM_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            redeem_codes = data if isinstance(data, dict) else {}
    except Exception:
        redeem_codes = {}

# =========================
# GROUP SETTINGS
# =========================
def ensure_chat_settings(chat_id: int):
    key = str(chat_id)
    if key not in group_settings or not isinstance(group_settings[key], dict):
        group_settings[key] = {
            "enabled": False,
            "lang_a": "vi",
            "lang_b": "zh-CN",
        }
        save_settings()
        return

    s = group_settings[key]
    changed = False
    if "enabled" not in s:
        s["enabled"] = False
        changed = True
    if "lang_a" not in s or s["lang_a"] not in SUPPORTED:
        s["lang_a"] = "vi"
        changed = True
    if "lang_b" not in s or s["lang_b"] not in SUPPORTED:
        s["lang_b"] = "zh-CN"
        changed = True
    if changed:
        save_settings()


def get_chat_settings(chat_id: int) -> dict:
    ensure_chat_settings(chat_id)
    return group_settings[str(chat_id)]


def set_chat_enabled(chat_id: int, enabled: bool):
    ensure_chat_settings(chat_id)
    group_settings[str(chat_id)]["enabled"] = enabled
    save_settings()


def set_chat_pair(chat_id: int, lang_a: str, lang_b: str):
    ensure_chat_settings(chat_id)
    group_settings[str(chat_id)]["lang_a"] = lang_a
    group_settings[str(chat_id)]["lang_b"] = lang_b
    save_settings()

# =========================
# USER ACCESS
# =========================
def ensure_user(user_id: int):
    key = str(user_id)
    if key not in user_data or not isinstance(user_data[key], dict):
        user_data[key] = {
            "expires_at": 0,
            "lifetime": False,
            "ref_code": "",
            "referrals": 0,
            "referred_by": "",
            "used_referral": False,
            "expired_notified": False,
            "soon_warned": False,
            "redeemed_codes": [],
        }
        save_user_data()
        return

    u = user_data[key]
    changed = False
    defaults = {
        "expires_at": 0,
        "lifetime": False,
        "ref_code": "",
        "referrals": 0,
        "referred_by": "",
        "used_referral": False,
        "expired_notified": False,
        "soon_warned": False,
        "redeemed_codes": [],
    }
    for k, v in defaults.items():
        if k not in u:
            u[k] = v
            changed = True

    if changed:
        save_user_data()


def now_ts() -> int:
    return int(time.time())


def generate_ref_code(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def get_or_create_ref_code(user_id: int) -> str:
    ensure_user(user_id)
    key = str(user_id)
    if not user_data[key].get("ref_code"):
        user_data[key]["ref_code"] = generate_ref_code()
        save_user_data()
    return user_data[key]["ref_code"]


def grant_days(user_id: int, days: int):
    ensure_user(user_id)
    key = str(user_id)
    add_sec = days * 24 * 60 * 60
    current = int(user_data[key].get("expires_at", 0))
    base = max(current, now_ts())
    user_data[key]["expires_at"] = base + add_sec
    user_data[key]["expired_notified"] = False
    user_data[key]["soon_warned"] = False
    save_user_data()


def grant_lifetime(user_id: int):
    ensure_user(user_id)
    key = str(user_id)
    user_data[key]["lifetime"] = True
    user_data[key]["expires_at"] = 0
    user_data[key]["expired_notified"] = False
    user_data[key]["soon_warned"] = False
    save_user_data()


def grant_trial_if_new(user_id: int):
    ensure_user(user_id)
    key = str(user_id)
    info = user_data[key]
    if not info.get("lifetime", False) and int(info.get("expires_at", 0)) <= 0:
        grant_days(user_id, 1)


def handle_referral(new_user_id: int, ref_code: str):
    if not ref_code:
        return

    ensure_user(new_user_id)
    key_new = str(new_user_id)

    if user_data[key_new].get("used_referral", False):
        return

    inviter_id = None
    for uid, info in user_data.items():
        if isinstance(info, dict) and info.get("ref_code") == ref_code:
            inviter_id = int(uid)
            break

    if not inviter_id or inviter_id == new_user_id:
        return

    user_data[key_new]["used_referral"] = True
    user_data[key_new]["referred_by"] = str(inviter_id)
    user_data[str(inviter_id)]["referrals"] = int(user_data[str(inviter_id)].get("referrals", 0)) + 1
    save_user_data()
    grant_days(inviter_id, 3)


def is_user_active(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True

    ensure_user(user_id)
    info = user_data[str(user_id)]

    if info.get("lifetime", False):
        return True

    exp = int(info.get("expires_at", 0))
    return exp > now_ts()


def remaining_seconds(user_id: int) -> int:
    ensure_user(user_id)
    exp = int(user_data[str(user_id)].get("expires_at", 0))
    return max(0, exp - now_ts())

# =========================
# REDEEM SYSTEM
# =========================
def generate_redeem_code(user_id: int, length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    suffix = "".join(random.choice(alphabet) for _ in range(length))
    return f"RC-{user_id}-{suffix}"


def create_redeem_code(target_id: int, days: int = 0, lifetime: bool = False, created_by: int = 0) -> str:
    while True:
        code = generate_redeem_code(target_id)
        if code not in redeem_codes:
            break

    redeem_codes[code] = {
        "assigned_to": target_id,
        "days": days,
        "lifetime": lifetime,
        "used": False,
        "created_by": created_by,
        "created_at": now_ts(),
        "used_by": None,
        "used_at": None,
    }
    save_redeem_codes()
    return code


def redeem_code(user_id: int, code: str) -> Tuple[bool, str]:
    ensure_user(user_id)

    code = code.strip().upper()
    if not code:
        return False, "⚠️ 兑换码不能为空。"

    info = redeem_codes.get(code)
    if not info:
        return False, "⚠️ 兑换码无效。"

    assigned_to = int(info.get("assigned_to", 0))
    if assigned_to != int(user_id):
        return False, "⚠️ 此兑换码不属于您。"

    if info.get("used", False):
        return False, "⚠️ 此兑换码已经使用过。"

    if info.get("lifetime", False):
        grant_lifetime(user_id)
        info["used"] = True
        info["used_by"] = user_id
        info["used_at"] = now_ts()
        save_redeem_codes()
        save_user_data()
        return True, "✅ 已成功开通永久权限。"

    days = int(info.get("days", 0))
    if days <= 0:
        return False, "⚠️ 兑换码配置错误。"

    grant_days(user_id, days)
    info["used"] = True
    info["used_by"] = user_id
    info["used_at"] = now_ts()
    save_redeem_codes()
    save_user_data()
    return True, f"✅ 兑换成功，已增加 {days} 天使用时长。"

# =========================
# RATE LIMIT
# =========================
rate_log = defaultdict(deque)


def check_rate_limit(user_id: int) -> Tuple[bool, int]:
    now = time.time()
    dq = rate_log[user_id]

    while dq and now - dq[0] > RATE_LIMIT_WINDOW:
        dq.popleft()

    if len(dq) >= RATE_LIMIT_COUNT:
        wait = int(RATE_LIMIT_WINDOW - (now - dq[0]))
        return False, max(wait, 1)

    dq.append(now)
    return True, 0

# =========================
# HELPERS
# =========================
def lang_label(code: str) -> str:
    return LANGS.get(code, code)


def split_text(text: str, limit: int = 3900) -> List[str]:
    parts = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        if cut <= 0:
            cut = limit
        parts.append(text[:cut])
        text = text[cut:].lstrip("\n")
    if text:
        parts.append(text)
    return parts


async def send_chunked_message(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    text: str,
    reply_to_message_id: Optional[int] = None,
):
    parts = split_text(text)
    for i, part in enumerate(parts):
        await context.bot.send_message(
            chat_id=chat_id,
            text=part,
            reply_to_message_id=reply_to_message_id if i == 0 else None,
            disable_web_page_preview=True,
        )


async def send_temp_message(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    text: str,
    reply_to_message_id: Optional[int] = None,
    reply_markup=None,
    delete_after: int = 10,
):
    msg = await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_to_message_id=reply_to_message_id,
        reply_markup=reply_markup,
        disable_web_page_preview=True,
    )

    async def _delete_later():
        await asyncio.sleep(delete_after)
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg.message_id)
        except Exception:
            pass

    asyncio.create_task(_delete_later())
    return msg


def bot_link() -> str:
    if BOT_USERNAME:
        return f"https://t.me/{BOT_USERNAME}"
    return "https://t.me"


def user_ref_link(bot_username: str, user_id: int) -> str:
    code = get_or_create_ref_code(user_id)
    return f"https://t.me/{bot_username}?start={code}"


def add_group_url() -> str:
    return f"{bot_link()}?startgroup=true"


def share_url(text: str, url: str) -> str:
    return f"https://t.me/share/url?url={quote(url, safe='')}&text={quote(text, safe='')}"


async def notify_owner(context: ContextTypes.DEFAULT_TYPE, text: str):
    try:
        await context.bot.send_message(chat_id=OWNER_ID, text=text)
    except Exception:
        pass


def user_info_text(user) -> str:
    username = f"@{user.username}" if getattr(user, "username", None) else "无"
    return (
        f"• 用户名：{user.full_name}\n"
        f"• User ID：{user.id}\n"
        f"• Username：{username}"
    )

# =========================
# TEXTS (Chinese only)
# =========================
def private_welcome_text(remain_days: int, remain_hours: int, link: str) -> str:
    return (
        "👋 欢迎使用翻译机器人！\n"
        "🤖 现在我们开始聊天吧～\n\n"
        f"🎁 试用剩余时间：{remain_days} 天 {remain_hours} 小时\n"
        f"🔗 你的邀请链接：\n{link}\n\n"
        "✨ 输入兑换码可开通试用 / VIP / 续期。\n"
        f"💬 如需长期使用，请联系管理员 {ADMIN_MENTION}。"
    )


def expired_text() -> str:
    return (
        "⚠️ 您的使用权限已过期。\n"
        f"如需继续使用，请联系管理员 {ADMIN_MENTION} 进行续期。"
    )


def expiring_soon_text(remain_days: int, remain_hours: int) -> str:
    return (
        "⏳ 您的试用时间即将到期。\n"
        f"剩余时间：{remain_days} 天 {remain_hours} 小时。\n"
        f"请联系管理员 {ADMIN_MENTION} 进行续期。"
    )


def group_added_text() -> str:
    return (
        "👋 大家好，我是翻译机器人！\n"
        "✅ 我已经加入群组，可以开始使用了。\n\n"
        f"⏳ 当前为试用状态，如需长期使用，请联系管理员 {ADMIN_MENTION}。"
    )


def share_text() -> str:
    return (
        "📤 分享机器人\n\n"
        "邀请好友体验机器人，每成功邀请一位用户即可获得额外时长。\n"
        f"如需长期使用，请联系管理员 {ADMIN_MENTION}。"
    )


def more_text() -> str:
    return (
        "✨ 更多功能\n\n"
        f"如需长期使用，请联系管理员 {ADMIN_MENTION}。"
    )


def help_text() -> str:
    return (
        "❓ 帮助 - 群主专用\n\n"
        "使用方法：\n"
        "1) 把机器人添加到群组\n"
        "2) 先在「系统设置」选择两种翻译语言\n"
        "3) 点击「开始翻译」\n"
        "4) 群里任意成员发文字，机器人会自动双向翻译\n\n"
        "兑换码：\n"
        "• 在私聊中输入 /redeem 兑换码\n"
        "• 群主可用 /createcode 为指定用户创建专属兑换码\n\n"
        "提示：\n"
        "• 必须关闭 BotFather 的 Privacy Mode\n"
        "• 机器人仅翻译文字消息\n"
        f"• 长期使用请联系 {ADMIN_MENTION}"
    )


def admin_text(chat_id: int) -> str:
    return (
        "👮 管理员管理\n\n"
        "请选择功能："
    )


def main_menu_text(chat_id: int) -> str:
    s = get_chat_settings(chat_id)
    status = "✅ 已开启" if s["enabled"] else "⏹ 已停止"
    pair = f"{lang_label(s['lang_a'])} ⇄ {lang_label(s['lang_b'])}"

    return (
        "📌 设置菜单列表\n\n"
        f"当前状态：{status}\n"
        f"翻译模式：{pair}\n\n"
        "请选择功能："
    )


def settings_text(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> str:
    s = get_chat_settings(chat_id)
    current_pair = f"{lang_label(s['lang_a'])} ⇄ {lang_label(s['lang_b'])}"
    status = "✅ 已开启" if s["enabled"] else "⏹ 已停止"

    stage = context.chat_data.get("pair_stage", "")
    first = context.chat_data.get("pair_first_lang", "")

    if stage == "second" and first:
        return (
            "⚙️ 系统设置\n\n"
            f"当前状态：{status}\n"
            f"当前翻译模式：{current_pair}\n\n"
            f"✅ 已选择第一语言：{lang_label(first)}\n"
            "请选择第二语言："
        )

    return (
        "⚙️ 系统设置\n\n"
        f"当前状态：{status}\n"
        f"当前翻译模式：{current_pair}\n\n"
        "请选择第一语言："
    )

# =========================
# MENUS
# =========================
def build_private_menu(user_id: int) -> InlineKeyboardMarkup:
    share_link = user_ref_link(BOT_USERNAME, user_id) if BOT_USERNAME else bot_link()

    rows = [
        [InlineKeyboardButton("📤 分享机器人", url=share_link)],
        [InlineKeyboardButton("🎫 输入兑换码", callback_data="menu:redeem")],
        [InlineKeyboardButton("➕ 添加到群组", url=add_group_url())],
        [InlineKeyboardButton("🛠 联系管理员", url=f"https://t.me/{ADMIN_USERNAME}")],
    ]

    if user_id == OWNER_ID:
        rows.append([InlineKeyboardButton("❓ 帮助", callback_data="menu:help")])

    return InlineKeyboardMarkup(rows)


def build_main_menu(chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("▶️ 开始翻译", callback_data="toggle:on"),
            InlineKeyboardButton("⏹ 停止翻译", callback_data="toggle:off"),
        ],
        [
            InlineKeyboardButton("⚙️ 系统设置", callback_data="menu:settings"),
            InlineKeyboardButton("✨ 更多功能", callback_data="menu:more"),
        ],
        [
            InlineKeyboardButton("➕ 添加到群组", url=add_group_url()),
            InlineKeyboardButton("📤 分享", callback_data="menu:share"),
        ],
        [
            InlineKeyboardButton("关闭 ❌", callback_data="menu:close"),
        ],
    ])


def build_settings_menu(chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇻🇳 越南语", callback_data="setlang:vi"),
            InlineKeyboardButton("🇬🇧 英文", callback_data="setlang:en"),
        ],
        [
            InlineKeyboardButton("🇯🇵 日语", callback_data="setlang:ja"),
            InlineKeyboardButton("🇰🇷 韩语", callback_data="setlang:ko"),
        ],
        [
            InlineKeyboardButton("🇨🇳 简体中文", callback_data="setlang:zh-CN"),
        ],
        [
            InlineKeyboardButton("🔙 返回", callback_data="menu:main"),
            InlineKeyboardButton("关闭 ❌", callback_data="menu:close"),
        ],
    ])


def build_more_menu(user_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("📤 分享", callback_data="menu:share")],
    ]

    if user_id == OWNER_ID:
        buttons.append([InlineKeyboardButton("👮 管理员", callback_data="menu:admin")])

    buttons.append([InlineKeyboardButton("🔙 返回", callback_data="menu:main")])
    buttons.append([InlineKeyboardButton("关闭 ❌", callback_data="menu:close")])
    return InlineKeyboardMarkup(buttons)


def build_admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ 添加管理员", callback_data="admin:add"),
            InlineKeyboardButton("📋 管理员列表", callback_data="admin:list"),
        ],
        [
            InlineKeyboardButton("➖ 删除管理员", callback_data="admin:remove"),
        ],
        [
            InlineKeyboardButton("🔙 返回", callback_data="menu:more"),
            InlineKeyboardButton("关闭 ❌", callback_data="menu:close"),
        ],
    ])


def build_share_menu(user_id: int) -> InlineKeyboardMarkup:
    if not BOT_USERNAME:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 返回", callback_data="menu:more")],
            [InlineKeyboardButton("关闭 ❌", callback_data="menu:close")],
        ])

    link = user_ref_link(BOT_USERNAME, user_id)
    cn_share = share_url("快来体验这个翻译机器人。", link)
    non_cn_share = share_url("Try this translation bot.", link)

    return InlineKeyboardMarkup([
        [InlineKeyboardButton("分享给中文好友🔗", url=cn_share)],
        [InlineKeyboardButton("分享给非中文好友🔗", url=non_cn_share)],
        [
            InlineKeyboardButton("返回", callback_data="menu:more"),
            InlineKeyboardButton("关闭 ❌", callback_data="menu:close"),
        ],
    ])


def build_help_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 返回", callback_data="menu:main")],
        [InlineKeyboardButton("关闭 ❌", callback_data="menu:close")],
    ])

# =========================
# AI TRANSLATION
# =========================
SYSTEM_PROMPT = """
You are a bilingual translation engine.

You will receive:
- lang_a
- lang_b
- text

Task:
1) Detect the source language.
2) If source language is lang_a, translate to lang_b.
3) If source language is lang_b, translate to lang_a.
4) If source language is neither lang_a nor lang_b, translate to lang_b.
5) Return ONLY valid JSON with exactly these keys:
   source_lang
   translated_text

Rules:
- Preserve meaning, emojis, line breaks, punctuation, URLs, names, numbers.
- Do not add explanations.
- Do not wrap in markdown.
- Do not output anything except JSON.
""".strip()


async def translate_with_ai(text: str, lang_a: str, lang_b: str) -> Tuple[str, str]:
    global client
    if client is None:
        raise ValueError("OpenAI client chưa được khởi tạo.")

    prompt = f"""lang_a: {lang_a}
lang_b: {lang_b}
text:
{text}
"""

    resp = await client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    raw = resp.choices[0].message.content or "{}"
    data = json.loads(raw)

    source_lang = data.get("source_lang", "unknown")
    translated_text = (data.get("translated_text") or "").strip()

    if not translated_text:
        raise ValueError("翻译结果为空。")

    return source_lang, translated_text

# =========================
# PERMISSIONS
# =========================
async def is_owner_or_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    chat = update.effective_chat
    if not user:
        return False

    if user.id == OWNER_ID:
        return True

    if chat and chat.type in ("group", "supergroup"):
        try:
            member = await context.bot.get_chat_member(chat.id, user.id)
            return member.status in ("administrator", "creator")
        except Exception:
            return False

    return False


async def can_use_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    chat = update.effective_chat
    if not user:
        return False

    if user.id == OWNER_ID:
        return True

    if chat and chat.type in ("group", "supergroup"):
        try:
            member = await context.bot.get_chat_member(chat.id, user.id)
            if member.status in ("administrator", "creator"):
                return True
        except Exception:
            pass

    return is_user_active(user.id)

# =========================
# COMMANDS
# =========================
async def redeem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return

    if chat.type != "private":
        await update.message.reply_text("请在私聊中使用兑换码。")
        return

    if not context.args:
        await update.message.reply_text(
            "请输入兑换码，例如：/redeem RC-123456-ABC123\n\n"
            f"如需帮助，请联系 {ADMIN_MENTION}。"
        )
        return

    code = context.args[0].strip()
    ok, msg = redeem_code(user.id, code)

    await update.message.reply_text(
        msg + f"\n\n如需帮助，请联系 {ADMIN_MENTION}。"
    )


async def createcode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return

    if user.id != OWNER_ID:
        await update.message.reply_text("仅限群主使用。")
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "用法：/createcode 用户ID 天数\n"
            "例如：/createcode 123456789 30\n"
            "或者：/createcode 用户ID lifetime"
        )
        return

    try:
        target_id = int(context.args[0])
        value = context.args[1].strip().lower()

        if value == "lifetime":
            code = create_redeem_code(
                target_id=target_id,
                days=0,
                lifetime=True,
                created_by=user.id,
            )
            await update.message.reply_text(
                f"✅ 已创建永久兑换码：\n{code}\n\n"
                f"该码仅限用户 {target_id} 使用。"
            )
            return

        days = int(value)
        if days <= 0:
            await update.message.reply_text("⚠️ 天数必须大于 0。")
            return

        code = create_redeem_code(
            target_id=target_id,
            days=days,
            lifetime=False,
            created_by=user.id,
        )
        await update.message.reply_text(
            f"✅ 已创建 {days} 天兑换码：\n{code}\n\n"
            f"该码仅限用户 {target_id} 使用。"
        )

    except Exception as e:
        await update.message.reply_text(f"⚠️ 创建失败：{e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return

    # Private
    if chat.type == "private":
        ensure_user(user.id)

        if context.args:
            ref_code = context.args[0].strip()
            if ref_code:
                handle_referral(user.id, ref_code)

        grant_trial_if_new(user.id)

        exp = int(user_data[str(user.id)].get("expires_at", 0))
        remain = max(0, exp - now_ts())
        remain_days = remain // 86400
        remain_hours = (remain % 86400) // 3600

        link = user_ref_link(BOT_USERNAME, user.id) if BOT_USERNAME else "正在生成链接..."

        await update.message.reply_text(
            private_welcome_text(remain_days, remain_hours, link),
            reply_markup=build_private_menu(user.id),
        )
        return

    # Group
    if chat.type in ("group", "supergroup"):
        if not await is_owner_or_admin(update, context):
            return

        await update.message.reply_text(
            main_menu_text(chat.id),
            reply_markup=build_main_menu(chat.id),
        )


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not chat:
        return

    if chat.type in ("group", "supergroup"):
        if not await is_owner_or_admin(update, context):
            return

        await update.message.reply_text(
            main_menu_text(chat.id),
            reply_markup=build_main_menu(chat.id),
        )
        return

    # Private
    user = update.effective_user
    if not user:
        return

    ensure_user(user.id)
    exp = int(user_data[str(user.id)].get("expires_at", 0))
    remain = max(0, exp - now_ts())
    remain_days = remain // 86400
    remain_hours = (remain % 86400) // 3600
    link = user_ref_link(BOT_USERNAME, user.id) if BOT_USERNAME else "正在生成链接..."

    await update.message.reply_text(
        private_welcome_text(remain_days, remain_hours, link),
        reply_markup=build_private_menu(user.id),
    )

# =========================
# BOT ADDED TO GROUP
# =========================
async def my_chat_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    upd = update.my_chat_member
    if not upd:
        return

    chat = upd.chat
    new_member = upd.new_chat_member

    if new_member.user.id != context.bot.id:
        return

    if new_member.status in ("member", "administrator"):
        ensure_chat_settings(chat.id)

        try:
            await send_temp_message(
                context=context,
                chat_id=chat.id,
                text=group_added_text(),
                delete_after=10,
            )

            await context.bot.send_message(
                chat_id=chat.id,
                text=(
                    "⚙️ 请先选择翻译语言对。\n"
                    f"📌 如需长期使用，请联系管理员 {ADMIN_MENTION}。"
                ),
                reply_markup=build_settings_menu(chat.id),
            )

            await notify_owner(
                context,
                text=(
                    "📩 机器人已被添加到群组\n\n"
                    f"• 群组：{chat.title if chat.title else '无标题群组'}\n"
                    f"• Chat ID：{chat.id}\n"
                    f"• 管理员：{ADMIN_MENTION}\n\n"
                    "✅ 当前已进入试用状态。"
                ),
            )
        except Exception:
            pass

# =========================
# ADMIN ACTIONS
# =========================
async def admin_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    msg = update.message
    if not msg or not msg.text:
        return False

    pending = context.chat_data.get("pending_admin_action")
    if not pending:
        return False

    chat = update.effective_chat
    if not chat or chat.type not in ("group", "supergroup"):
        return False

    if not msg.reply_to_message or not msg.reply_to_message.from_user:
        await msg.reply_text("请回复目标用户的消息。")
        return True

    target = msg.reply_to_message.from_user

    if target.id == context.bot.id:
        await msg.reply_text("不能操作机器人。")
        context.chat_data.pop("pending_admin_action", None)
        return True

    try:
        member = await context.bot.get_chat_member(chat.id, target.id)

        if pending == "add_admin":
            if member.status == "creator":
                await msg.reply_text("该用户已经是群主。")
                context.chat_data.pop("pending_admin_action", None)
                return True

            if member.status == "administrator":
                await msg.reply_text("该用户已经是管理员。")
                context.chat_data.pop("pending_admin_action", None)
                return True

            await context.bot.promote_chat_member(
                chat_id=chat.id,
                user_id=target.id,
                can_manage_chat=True,
                can_delete_messages=True,
                can_manage_video_chats=True,
                can_restrict_members=True,
                can_promote_members=False,
                can_change_info=True,
                can_invite_users=True,
                can_pin_messages=True,
            )
            await msg.reply_text(f"✅ 已添加 {target.full_name} 为管理员。")

        elif pending == "remove_admin":
            if member.status == "creator":
                await msg.reply_text("不能删除群主权限。")
                context.chat_data.pop("pending_admin_action", None)
                return True

            if member.status != "administrator":
                await msg.reply_text("该用户不是管理员。")
                context.chat_data.pop("pending_admin_action", None)
                return True

            await context.bot.promote_chat_member(
                chat_id=chat.id,
                user_id=target.id,
                can_manage_chat=False,
                can_delete_messages=False,
                can_manage_video_chats=False,
                can_restrict_members=False,
                can_promote_members=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False,
            )
            await msg.reply_text(f"✅ 已移除 {target.full_name} 的管理员权限。")

    except Exception as e:
        await msg.reply_text(f"⚠️ 操作失败：{e}")

    context.chat_data.pop("pending_admin_action", None)
    return True

# =========================
# CALLBACKS
# =========================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    chat = query.message.chat if query.message else None
    if not chat:
        return

    chat_id = chat.id
    user_id = update.effective_user.id if update.effective_user else 0

    if chat.type in ("group", "supergroup") and not await is_owner_or_admin(update, context):
        return

    if data == "menu:main":
        context.chat_data.pop("pending_admin_action", None)
        context.chat_data.pop("pair_stage", None)
        context.chat_data.pop("pair_first_lang", None)
        try:
            await query.edit_message_text(
                text=main_menu_text(chat_id),
                reply_markup=build_main_menu(chat_id),
            )
        except Exception:
            pass
        return

    if data == "menu:settings":
        context.chat_data.pop("pending_admin_action", None)
        try:
            await query.edit_message_text(
                text=settings_text(chat_id, context),
                reply_markup=build_settings_menu(chat_id),
            )
        except Exception:
            pass
        return

    if data == "menu:more":
        context.chat_data.pop("pending_admin_action", None)
        context.chat_data.pop("pair_stage", None)
        context.chat_data.pop("pair_first_lang", None)
        try:
            await query.edit_message_text(
                text=more_text(),
                reply_markup=build_more_menu(user_id),
            )
        except Exception:
            pass
        return

    if data == "menu:share":
        context.chat_data.pop("pending_admin_action", None)
        try:
            await query.edit_message_text(
                text=share_text(),
                reply_markup=build_share_menu(user_id),
            )
        except Exception:
            pass
        return

    if data == "menu:redeem":
        try:
            await query.edit_message_text(
                text=(
                    "🎫 兑换码\n\n"
                    "请输入兑换码，例如：\n"
                    "/redeem RC-123456-ABC123\n"
                    "/redeem RC-123456-Z9X8Y7\n\n"
                    f"如需帮助，请联系 {ADMIN_MENTION}。"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 返回", callback_data="menu:main")],
                    [InlineKeyboardButton("关闭 ❌", callback_data="menu:close")],
                ]),
            )
        except Exception:
            pass
        return

    if data == "menu:help":
        if user_id != OWNER_ID:
            return
        try:
            await query.edit_message_text(
                text=help_text(),
                reply_markup=build_help_menu(),
            )
        except Exception:
            pass
        return

    if data == "menu:admin":
        if user_id != OWNER_ID:
            return

        context.chat_data.pop("pending_admin_action", None)
        try:
            await query.edit_message_text(
                text=admin_text(chat_id),
                reply_markup=build_admin_menu(),
            )
        except Exception:
            pass
        return

    if data == "menu:close":
        context.chat_data.pop("pending_admin_action", None)
        context.chat_data.pop("pair_stage", None)
        context.chat_data.pop("pair_first_lang", None)
        try:
            await query.edit_message_text("✅ 已关闭")
        except Exception:
            pass
        return

    if data == "toggle:on":
        set_chat_enabled(chat_id, True)
        try:
            await query.edit_message_text(
                text=main_menu_text(chat_id),
                reply_markup=build_main_menu(chat_id),
            )
        except Exception:
            pass
        return

    if data == "toggle:off":
        set_chat_enabled(chat_id, False)
        try:
            await query.edit_message_text(
                text=main_menu_text(chat_id),
                reply_markup=build_main_menu(chat_id),
            )
        except Exception:
            pass
        return

    # ===== 2-step language selection =====
    if data.startswith("setlang:"):
        lang = data.split(":", 1)[1]
        if lang not in SUPPORTED:
            return

        stage = context.chat_data.get("pair_stage", "first")

        if stage != "second":
            context.chat_data["pair_stage"] = "second"
            context.chat_data["pair_first_lang"] = lang

            try:
                await query.edit_message_text(
                    text=(
                        f"✅ 已选择第一语言：{lang_label(lang)}\n\n"
                        "请选择第二语言："
                    ),
                    reply_markup=build_settings_menu(chat_id),
                )
            except Exception:
                pass
            return

        first_lang = context.chat_data.get("pair_first_lang")
        if not first_lang:
            context.chat_data["pair_stage"] = "first"
            try:
                await query.edit_message_text(
                    text="⚠️ 请先选择第一语言。",
                    reply_markup=build_settings_menu(chat_id),
                )
            except Exception:
                pass
            return

        if lang == first_lang:
            return

        set_chat_pair(chat_id, first_lang, lang)
        set_chat_enabled(chat_id, False)

        context.chat_data.pop("pair_stage", None)
        context.chat_data.pop("pair_first_lang", None)

        try:
            await query.edit_message_text(
                text=(
                    f"✅ 已设置翻译模式：{lang_label(first_lang)} ⇄ {lang_label(lang)}\n\n"
                    "现在可以点击「开始翻译」。"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("▶️ 开始翻译", callback_data="toggle:on")],
                    [InlineKeyboardButton("🔙 返回", callback_data="menu:main")],
                    [InlineKeyboardButton("关闭 ❌", callback_data="menu:close")],
                ]),
            )
        except Exception:
            pass
        return

    if data == "admin:list":
        if user_id != OWNER_ID:
            return

        try:
            admins = await context.bot.get_chat_administrators(chat_id)
            lines = ["📋 管理员列表\n"]
            for a in admins:
                u = a.user
                name = u.full_name
                if u.username:
                    name += f" (@{u.username})"
                role = "👑 群主" if a.status == "creator" else "🛡 管理员"
                lines.append(f"• {role}：{name}")

            await query.edit_message_text(
                text="\n".join(lines),
                reply_markup=build_admin_menu(),
            )
        except Exception as e:
            await query.answer(f"无法获取管理员列表：{e}", show_alert=True)
        return

    if data == "admin:add":
        if user_id != OWNER_ID:
            return

        context.chat_data["pending_admin_action"] = "add_admin"
        try:
            await query.edit_message_text(
                text=(
                    "➕ 添加管理员\n\n"
                    "请回复你要设为管理员的那个人的消息。"
                ),
                reply_markup=build_admin_menu(),
            )
        except Exception:
            pass
        return

    if data == "admin:remove":
        if user_id != OWNER_ID:
            return

        context.chat_data["pending_admin_action"] = "remove_admin"
        try:
            await query.edit_message_text(
                text=(
                    "➖ 删除管理员\n\n"
                    "请回复你要取消管理员权限的那个人的消息。"
                ),
                reply_markup=build_admin_menu(),
            )
        except Exception:
            pass
        return

# =========================
# GROUP TRANSLATION
# =========================
async def group_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    if msg.from_user and msg.from_user.is_bot:
        return

    chat = update.effective_chat
    if not chat or chat.type not in ("group", "supergroup"):
        return

    handled = await admin_action_handler(update, context)
    if handled:
        return

    if msg.text.startswith("/"):
        return

    user = msg.from_user
    if not user:
        return

    if not await can_use_bot(update, context):
        try:
            await send_temp_message(
                context=context,
                chat_id=chat.id,
                text=expired_text(),
                reply_to_message_id=msg.message_id,
                delete_after=10,
            )
        except Exception:
            pass

        ensure_user(user.id)
        key = str(user.id)
        if not user_data[key].get("expired_notified", False):
            await notify_owner(
                context,
                text=(
                    "📩 有用户的使用权限已过期\n\n"
                    + user_info_text(user)
                    + f"\n• 群组：{chat.title if chat.title else chat.id}\n"
                    f"• 管理员：{ADMIN_MENTION}"
                ),
            )
            user_data[key]["expired_notified"] = True
            save_user_data()
        return

    remain_sec = remaining_seconds(user.id)
    if 0 < remain_sec <= 86400:
        ensure_user(user.id)
        key = str(user.id)
        if not user_data[key].get("soon_warned", False):
            remain_days = remain_sec // 86400
            remain_hours = (remain_sec % 86400) // 3600

            try:
                await send_temp_message(
                    context=context,
                    chat_id=chat.id,
                    text=expiring_soon_text(remain_days, remain_hours),
                    reply_to_message_id=msg.message_id,
                    delete_after=10,
                )
            except Exception:
                pass

            user_data[key]["soon_warned"] = True
            save_user_data()

    s = get_chat_settings(chat.id)
    if not s.get("enabled", False):
        return

    text = msg.text.strip()
    if not text:
        return

    if len(text) > MAX_INPUT_CHARS:
        try:
            await send_temp_message(
                context=context,
                chat_id=chat.id,
                text=f"⚠️ 文字过长（{len(text)} 字符），无法翻译。",
                reply_to_message_id=msg.message_id,
                delete_after=10,
            )
        except Exception:
            pass
        return

    allowed, wait_sec = check_rate_limit(user.id)
    if not allowed:
        return

    await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)

    try:
        lang_a = s["lang_a"]
        lang_b = s["lang_b"]

        _, translated_text = await translate_with_ai(
            text=text,
            lang_a=lang_a,
            lang_b=lang_b,
        )

        await send_chunked_message(
            context=context,
            chat_id=chat.id,
            text=translated_text,
            reply_to_message_id=msg.message_id,
        )

    except Exception as e:
        try:
            await send_temp_message(
                context=context,
                chat_id=chat.id,
                text=f"⚠️ 翻译失败：{e}",
                reply_to_message_id=msg.message_id,
                delete_after=10,
            )
        except Exception:
            pass

# =========================
# POST INIT
# =========================
async def post_init(application):
    global BOT_USERNAME
    me = await application.bot.get_me()
    BOT_USERNAME = me.username

# =========================
# MAIN
# =========================
def main():
    global client

    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("缺少 TELEGRAM_BOT_TOKEN")
    if not OPENAI_API_KEY:
        raise ValueError("缺少 OPENAI_API_KEY")

    client = AsyncOpenAI(api_key=OPENAI_API_KEY)

    load_settings()
    load_user_data()
    load_redeem_codes()

    app = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("redeem", redeem_command))
    app.add_handler(CommandHandler("createcode", createcode_command))
    app.add_handler(ChatMemberHandler(my_chat_member_handler, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, group_text_handler))

    print("Bot đang chạy...")
    app.run_polling()


if __name__ == "__main__":
    main()

