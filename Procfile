Được bro. Mình ghép lại thành **bản tổng hợp các phần đã chỉnh** để bro copy dán dần vào `app.py` / `db.py`.

> Vì code của bro rất dài, mình **không thể thay nguyên cả file một cách an toàn** nếu không có đúng toàn bộ `db.py` + web route hiện tại.  
> Nhưng dưới đây là **bản ghép đầy đủ các phần đã sửa**: menu, quyền, realtime USDT, lịch sử giao dịch, thuê bot, đơn thuê, xác nhận thanh toán, address query, broadcast.

---

# 1) THÊM IMPORT Ở ĐẦU `app.py`

```python
import os
import re
import time
import asyncio
import aiohttp
from urllib.parse import quote
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
import uvicorn
```

---

# 2) THÊM ENV

```python
BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID", "0") or 0)
SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "0") or 0)
WEB_TOKEN = os.getenv("WEB_TOKEN", "abc123")
TRONGRID_API_KEY = os.getenv("TRONGRID_API_KEY", "")
PAYMENT_ADDRESS = os.getenv("PAYMENT_ADDRESS", "TSPpLmYuFXLi6GU1W4uyG6NKGbdWPw886U")
PAYMENT_SUPPORT = os.getenv("PAYMENT_SUPPORT", "/ZZB339")
```

---

# 3) THÊM GLOBALS

```python
BEIJING_TZ = ZoneInfo("Asia/Shanghai")
TRONGRID_API_URL = "https://api.trongrid.io"
USDT_TRC20_CONTRACT = "TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj"

RATE_CACHE = {"value": None, "ts": 0}
RATE_CACHE_TTL = 30

USDT_DAILY_UPDATE_KEY = "usdt_daily_update_date"
```

---

# 4) THÊM STATES

```python
class BroadcastFSM(StatesGroup):
    waiting_content = State()
    waiting_confirm = State()

class TrialFSM(StatesGroup):
    waiting_code = State()
    waiting_create_code = State()

class AdminFSM(StatesGroup):
    waiting_add_admin = State()
    waiting_del_admin = State()
    waiting_trial_code = State()

class AddressQueryFSM(StatesGroup):
    waiting_address = State()

class HistoryFSM(StatesGroup):
    waiting_group = State()
    waiting_date = State()
```

---

# 5) THÊM HELPER QUYỀN

```python
def is_bot_owner(user_id):
    return BOT_OWNER_ID and int(user_id) == int(BOT_OWNER_ID)

def is_super_admin(user_id):
    return SUPER_ADMIN_ID and int(user_id) == int(SUPER_ADMIN_ID)

def get_user_role(user_id):
    if is_bot_owner(user_id):
        return "owner"
    if is_super_admin(user_id):
        return "super"
    role = get_admin(user_id)
    if role == "admin":
        return "admin"
    return None

def can_use_manage_panel(user_id):
    return get_user_role(user_id) in ("owner", "super", "admin")

def can_use_bot_ops(user_id):
    return get_user_role(user_id) in ("owner", "super", "admin")

def can_manage_codes(user_id):
    return get_user_role(user_id) in ("owner", "super")

def can_manage_admins(user_id):
    return get_user_role(user_id) == "owner"

def deny_text():
    return "❌ 无权限"
```

---

# 6) THÊM HELPERS CHUNG

```python
def is_tron_address(addr: str):
    if not addr:
        return False
    addr = addr.strip()
    return bool(re.fullmatch(r"T[1-9A-HJ-NP-Za-km-z]{33}", addr))

def fmt_num(x):
    if x is None:
        return "0"
    try:
        x = float(x)
        if abs(x - int(x)) < 1e-9:
            return str(int(x))
        return f"{x:.2f}".rstrip("0").rstrip(".")
    except Exception:
        return str(x)

def fmt_token_amount(amount, decimals=6):
    try:
        if amount is None:
            return "0"
        x = float(amount)
        if abs(x - int(x)) < 1e-9:
            return str(int(x))
        return f"{x:.6f}".rstrip("0").rstrip(".")
    except:
        return str(amount)

def is_cmd(message: types.Message, *cmds):
    if not message.text:
        return False
    head = message.text.strip().split()[0].lower()
    head = head.split("@")[0]
    return head in [c.lower() for c in cmds]

def is_group_message(message: types.Message):
    return message.chat.type in ("group", "supergroup")

def is_private(message: types.Message):
    return message.chat.type == "private"
```

---

# 7) MENU CHÍNH

```python
def menu_kb(user_id=None):
    keyboard = [
        [
            KeyboardButton(text="🔥 开始记账"),
            KeyboardButton(text="申请试用"),
        ],
        [
            KeyboardButton(text="📚 使用说明"),
            KeyboardButton(text="🗝 记忆Key"),
        ],
        [
            KeyboardButton(text="📊 实时U价"),
            KeyboardButton(text="📜 交易历史"),
        ],
        [
            KeyboardButton(text="🔑 续费/租用"),
            KeyboardButton(text="📍 地址查询"),
        ],
        [
            KeyboardButton(text="👥 分组功能"),
        ],
    ]

    if user_id is not None and can_use_manage_panel(user_id):
        keyboard.append([KeyboardButton(text="🛠 管理面板")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )
```

---

# 8) `/start` + HELP + QUICK KEY

```python
def start_inline_kb(user_id=None):
    if BOT_USERNAME:
        add_url = f"https://t.me/{BOT_USERNAME}?startgroup=add"
    else:
        add_url = "https://t.me/"

    buttons = [
        [InlineKeyboardButton(text="➕ 添加机器人到群", url=add_url)],
        [InlineKeyboardButton(text="📚 使用说明", callback_data="menu:help")],
        [InlineKeyboardButton(text="🗝 记忆Key", callback_data="menu:keys")],
    ]

    if user_id is not None and can_manage_codes(user_id):
        buttons.append([InlineKeyboardButton(text="🔑 创建激活码", callback_data="manage:create_code")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def quick_key_text():
    return (
        "🗝 <b>记忆 Key</b>\n\n"
        "<b>开关</b>\n"
        "• 开始：<code>开始</code>\n"
        "• 关闭：<code>关闭记账</code>\n"
        "• 发言：<code>上课</code> / <code>下课</code>\n\n"
        "<b>参数</b>\n"
        "• 汇率：<code>设置汇率190</code>\n"
        "• 费率：<code>设置费率7</code>\n\n"
        "<b>记账</b>\n"
        "• 入账：<code>+1000</code>\n"
        "• 出账：<code>-1000</code>\n"
        "• 下发：<code>下发5000</code>\n"
        "• 寄存：<code>P+2000</code>\n"
        "• 备注：<code>+1000 备注</code>\n\n"
        "<b>查看</b>\n"
        "• 今日总账：<code>总账单</code>\n"
        "• 个人账单：<code>账单</code>\n"
        "• 我的账单：<code>/我</code>\n"
        "• 撤销：<code>撤销</code>\n"
    )


def quick_key_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="开始", callback_data="copy:开始"),
            InlineKeyboardButton(text="关闭记账", callback_data="copy:关闭记账"),
        ],
        [
            InlineKeyboardButton(text="上课", callback_data="copy:上课"),
            InlineKeyboardButton(text="下课", callback_data="copy:下课"),
        ],
        [
            InlineKeyboardButton(text="设置汇率190", callback_data="copy:设置汇率190"),
            InlineKeyboardButton(text="设置费率7", callback_data="copy:设置费率7"),
        ],
        [
            InlineKeyboardButton(text="+1000", callback_data="copy:+1000"),
            InlineKeyboardButton(text="-1000", callback_data="copy:-1000"),
        ],
        [
            InlineKeyboardButton(text="下发5000", callback_data="copy:下发5000"),
            InlineKeyboardButton(text="P+2000", callback_data="copy:P+2000"),
        ],
        [
            InlineKeyboardButton(text="总账单", callback_data="copy:总账单"),
            InlineKeyboardButton(text="撤销", callback_data="copy:撤销"),
        ],
        [
            InlineKeyboardButton(text="📚 使用说明", callback_data="menu:help"),
        ]
    ])


def help_text():
    return (
        "📚 <b>记账机器人使用说明</b>\n\n"
        "欢迎使用记账机器人。\n"
        "本机器人支持群内记账、参数配置、账单查看、试用授权与管理功能。\n\n"
        "<b>基础功能</b>\n"
        "• 开始记账：<code>开始</code> / <code>🔥 开始记账</code>\n"
        "• 停止记账：<code>关闭记账</code> / <code>停止记账</code>\n"
        "• 打开发言：<code>上课</code>\n"
        "• 停止发言：<code>下课</code>\n\n"
        "<b>参数设置</b>\n"
        "• 设置汇率：<code>设置汇率190</code>\n"
        "• 设置费率：<code>设置费率7</code>\n"
        "• 单笔手续费：<code>单笔手续费20</code>\n"
        "• 代付费率：<code>代付费率-5</code>\n"
        "• 代付汇率：<code>代付汇率8</code>\n"
        "• 实时汇率：<code>设置实时汇率190</code>\n\n"
        "<b>记账指令</b>\n"
        "• 入账 / 出账：<code>+1000</code> / <code>-1000</code>\n"
        "• 按汇率记账：<code>+1000/7.8</code>\n"
        "• U 币格式：<code>+1000u</code>\n"
        "• 下发：<code>下发5000</code> / <code>下发-2000</code> / <code>下发1000R</code>\n"
        "• 寄存：<code>P+2000</code> / <code>P-1000</code>\n"
        "• 备注记账：<code>+1000 备注</code>\n\n"
        "<b>查看功能</b>\n"
        "• 今日总账：<code>总账单</code>\n"
        "• 完整账单：<code>完整账单</code>\n"
        "• 个人账单：<code>账单</code>\n"
        "• 我的账单：<code>/我</code>\n"
        "• 撤销上一笔：<code>撤销</code>\n"
        "• 上月账单：<code>上个月总账单</code>\n\n"
        "<b>快捷功能</b>\n"
        "• 使用说明：<code>使用说明</code>\n"
        "• 记忆Key：<code>记忆Key</code>\n"
        "• 实时U价：<code>实时U价</code>\n"
        "• 交易历史：<code>交易历史</code>\n"
        "• 续费/租用：<code>续费/租用</code>\n"
        "• 地址查询：<code>地址查询</code>\n"
        "• 管理面板：<code>管理面板</code>\n\n"
        "如需新增功能、修改界面或定制按钮，请联系管理员。"
    )


@dp.message(lambda m: m.text and is_cmd(m, "/start"))
async def start_cmd(m: types.Message):
    if not is_private(m):
        return
    text = (
        "📊 <b>记账机器人</b>\n\n"
        "欢迎使用记账机器人。\n"
        "您可以通过下方菜单快速进入功能，\n"
        "也可以直接在群内输入指令操作。"
    )
    await m.answer(text, reply_markup=start_inline_kb(m.from_user.id), parse_mode="HTML")


@dp.message(lambda m: m.text in ("使用说明", "📚 使用说明"))
async def menu_help(m: types.Message):
    await m.answer(help_text(), reply_markup=quick_key_kb(), parse_mode="HTML")


@dp.callback_query(lambda c: c.data == "menu:help")
async def menu_help_cb(c: types.CallbackQuery):
    if not c.message:
        return
    await c.message.answer(help_text(), reply_markup=quick_key_kb(), parse_mode="HTML")
    await c.answer()


@dp.message(lambda m: m.text in ("记忆Key", "🗝 记忆Key"))
async def menu_keys(m: types.Message):
    await m.answer(quick_key_text(), reply_markup=quick_key_kb(), parse_mode="HTML")


@dp.callback_query(lambda c: c.data and c.data.startswith("copy:"))
async def copy_command_cb(c: types.CallbackQuery):
    if not c.message:
        return
    cmd = c.data.replace("copy:", "", 1)
    await c.message.answer(f"📋 <b>已复制指令</b>\n<code>{cmd}</code>", parse_mode="HTML")
    await c.answer()
```

---

# 9) REALTIME USDT + AUTO UPDATE 08:00 BJ

```python
async def fetch_usdt_rates():
    urls = [
        "https://open.er-api.com/v6/latest/USD",
        "https://api.exchangerate.host/latest?base=USD&symbols=CNY,VND",
    ]

    for url in urls:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=8) as resp:
                    data = await resp.json()

                    if data.get("result") == "success" and "rates" in data:
                        rates = data["rates"]
                        return {
                            "usd_cny": float(rates.get("CNY")) if rates.get("CNY") else None,
                            "usd_vnd": float(rates.get("VND")) if rates.get("VND") else None,
                        }

                    rates = data.get("rates", {})
                    return {
                        "usd_cny": float(rates.get("CNY")) if rates.get("CNY") else None,
                        "usd_vnd": float(rates.get("VND")) if rates.get("VND") else None,
                    }

        except Exception as e:
            print("fetch_usdt_rates error:", e)

    return None


def format_usdt_rate_text(rates):
    now_str = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")
    cny = rates.get("usd_cny") if rates else None
    vnd = rates.get("usd_vnd") if rates else None

    lines = ["📈 <b>实时U价</b>", ""]
    if cny:
        lines.append(f"🇨🇳 市场价：<code>{cny:.4f}</code> CNY / USDT")
        lines.append(f"• 1 CNY ≈ <code>{1/cny:.4f}</code> USDT")
    else:
        lines.append("🇨🇳 市场价：<i>获取失败</i>")

    if vnd:
        lines.append(f"🇻🇳 市场价：<code>{vnd:,.0f}</code> VND / USDT")
        lines.append(f"• 1 VND ≈ <code>{1/vnd:.8f}</code> USDT")
    else:
        lines.append("🇻🇳 市场价：<i>获取失败</i>")

    lines += ["", f"🕒 更新时间：<code>{now_str}</code>"]
    return "\n".join(lines)


def rate_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 刷新价格", callback_data="rate:refresh")],
        [InlineKeyboardButton(text="📚 使用说明", callback_data="menu:help")],
    ])


async def get_usdt_rates_cached(force=False):
    now = time.time()
    if not force and RATE_CACHE["value"] and (now - RATE_CACHE["ts"] < RATE_CACHE_TTL):
        return RATE_CACHE["value"]
    rates = await fetch_usdt_rates()
    if rates:
        RATE_CACHE["value"] = rates
        RATE_CACHE["ts"] = now
        return rates
    return RATE_CACHE["value"]


async def daily_usdt_update_loop():
    while True:
        try:
            now = datetime.now(BEIJING_TZ)
            today_key = now.strftime("%Y-%m-%d")
            target_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
            last_update_date = get_setting(-1, USDT_DAILY_UPDATE_KEY, "")

            if now >= target_time and last_update_date != today_key:
                rates = await fetch_usdt_rates()
                if rates:
                    RATE_CACHE["value"] = rates
                    RATE_CACHE["ts"] = time.time()
                    set_setting(-1, USDT_DAILY_UPDATE_KEY, today_key)
                    print(f"[USDT] Updated at {now.strftime('%Y-%m-%d %H:%M:%S')} Beijing time")

            if now < target_time:
                sleep_seconds = (target_time - now).total_seconds()
                await asyncio.sleep(min(sleep_seconds, 60))
            else:
                await asyncio.sleep(60)

        except Exception as e:
            print("daily_usdt_update_loop error:", e)
            await asyncio.sleep(60)


@dp.message(lambda m: m.text in ("实时U价", "📊 实时U价"))
async def menu_rate(m: types.Message):
    if not can_use_bot_ops(m.from_user.id):
        return await m.reply(deny_text())
    rates = await get_usdt_rates_cached()
    await m.answer(format_usdt_rate_text(rates), reply_markup=rate_kb(), parse_mode="HTML")


@dp.callback_query(lambda c: c.data == "rate:refresh")
async def rate_refresh_cb(c: types.CallbackQuery):
    rates = await get_usdt_rates_cached(force=True)
    await c.message.answer(format_usdt_rate_text(rates), reply_markup=rate_kb(), parse_mode="HTML")
    await c.answer("✅ 已刷新")
```

---

# 10) QUYỀN + PANEL QUẢN LÝ

```python
def manage_panel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ 添加管理员", callback_data="manage:add_admin"),
            InlineKeyboardButton(text="➖ 删除管理员", callback_data="manage:del_admin"),
        ],
        [
            InlineKeyboardButton(text="📋 管理员列表", callback_data="manage:list_admin"),
        ],
        [
            InlineKeyboardButton(text="🔑 创建续费码", callback_data="manage:create_code"),
            InlineKeyboardButton(text="🗑 回收续费码", callback_data="manage:revoke_code"),
        ],
    ])


@dp.message(lambda m: m.text in ("管理面板", "管理员快捷面板", "续费管理面板", "🛠 管理面板"))
async def manage_panel_cmd(m: types.Message):
    if not can_use_manage_panel(m.from_user.id):
        return await m.reply(deny_text())
    await m.reply("🛠 <b>管理面板</b>\n\n点击下方按钮执行操作。", reply_markup=manage_panel_kb(), parse_mode="HTML")


@dp.callback_query(lambda c: c.data == "manage:list_admin")
async def manage_list_admin_cb(c: types.CallbackQuery):
    if not can_use_manage_panel(c.from_user.id):
        return await c.answer("无权限", show_alert=True)
    rows = get_all_admins()
    if not rows:
        await c.message.answer("暂无管理员")
        return await c.answer()
    text = "📋 <b>管理员列表</b>\n\n"
    for uid, role in rows:
        text += f"• <code>{uid}</code> — {role}\n"
    await c.message.answer(text, parse_mode="HTML")
    await c.answer()


@dp.callback_query(lambda c: c.data == "manage:create_code")
async def manage_create_code_cb(c: types.CallbackQuery, state: FSMContext):
    if not can_manage_codes(c.from_user.id):
        return await c.answer("无权限", show_alert=True)
    await state.set_state(AdminFSM.waiting_trial_code)
    await c.message.answer("🔑 <b>创建续费码</b>\n\n请发送新的续费码，例如：<code>ABC123</code>", parse_mode="HTML")
    await c.answer()


@dp.message(AdminFSM.waiting_trial_code)
async def receive_trial_code(m: types.Message, state: FSMContext):
    if not can_manage_codes(m.from_user.id):
        return await m.reply(deny_text())
    code = (m.text or "").strip()
    if not code:
        return await m.reply("❌ 请输入有效续费码。")
    set_trial_code(code)
    await state.clear()
    await m.reply(f"✅ 已设置续费码：<code>{code}</code>", parse_mode="HTML")
```

---

# 11) CHỈ CHỦ BOT MỚI THÊM/XÓA ADMIN

```python
@dp.callback_query(lambda c: c.data == "manage:add_admin")
async def manage_add_admin_cb(c: types.CallbackQuery, state: FSMContext):
    if not can_manage_admins(c.from_user.id):
        return await c.answer("无权限", show_alert=True)
    await state.set_state(AdminFSM.waiting_add_admin)
    await c.message.answer("➕ <b>添加管理员</b>\n\n请回复目标用户消息，或直接发送用户ID。", parse_mode="HTML")
    await c.answer()

@dp.message(AdminFSM.waiting_add_admin)
async def receive_add_admin(m: types.Message, state: FSMContext):
    if not can_manage_admins(m.from_user.id):
        return await m.reply(deny_text())
    uid = None
    if m.reply_to_message and m.reply_to_message.from_user:
        uid = m.reply_to_message.from_user.id
    elif m.text and m.text.strip().isdigit():
        uid = int(m.text.strip())
    if not uid:
        return await m.reply("❌ 格式错误，请回复某人消息或发送用户ID。")
    add_admin(uid, "admin")
    await state.clear()
    await m.reply(f"✅ 已添加管理员：<code>{uid}</code>", parse_mode="HTML")


@dp.callback_query(lambda c: c.data == "manage:del_admin")
async def manage_del_admin_cb(c: types.CallbackQuery, state: FSMContext):
    if not can_manage_admins(c.from_user.id):
        return await c.answer("无权限", show_alert=True)
    await state.set_state(AdminFSM.waiting_del_admin)
    await c.message.answer("➖ <b>删除管理员</b>\n\n请回复目标用户消息，或直接发送用户ID。", parse_mode="HTML")
    await c.answer()

@dp.message(AdminFSM.waiting_del_admin)
async def receive_del_admin(m: types.Message, state: FSMContext):
    if not can_manage_admins(m.from_user.id):
        return await m.reply(deny_text())
    uid = None
    if m.reply_to_message and m.reply_to_message.from_user:
        uid = m.reply_to_message.from_user.id
    elif m.text and m.text.strip().isdigit():
        uid = int(m.text.strip())
    if not uid:
        return await m.reply("❌ 格式错误，请回复某人消息或发送用户ID。")
    remove_admin(uid)
    await state.clear()
    await m.reply(f"✅ 已删除管理员：<code>{uid}</code>", parse_mode="HTML")
```

---

# 12) RENT / THUÊ BOT

```python
RENT_CATEGORIES = {
    "group_admin": {"title": "🤖 Bot quản trị nhóm"},
    "computer": {"title": "💻 Bot máy tính"},
    "translator": {"title": "🌐 Bot dịch thuật"},
}

RENT_PLANS = {
    "1m": {"label": "一个月", "amount": 100},
    "3m": {"label": "三个月", "amount": 230},
    "6m": {"label": "六个月", "amount": 400},
    "1y": {"label": "一年", "amount": 700},
}

def rent_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Bot quản trị nhóm", callback_data="rent:group_admin")],
        [InlineKeyboardButton(text="💻 Bot máy tính", callback_data="rent:computer")],
        [InlineKeyboardButton(text="🌐 Bot dịch thuật", callback_data="rent:translator")],
        [InlineKeyboardButton(text="⬅️ Quay lại", callback_data="rent:back")],
    ])

def rent_plan_kb(category_key):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="一个月 (100U)", callback_data=f"rent:plan:{category_key}:1m")],
        [InlineKeyboardButton(text="三个月 (230U)", callback_data=f"rent:plan:{category_key}:3m")],
        [InlineKeyboardButton(text="六个月 (400U)", callback_data=f"rent:plan:{category_key}:6m")],
        [InlineKeyboardButton(text="一年 (700U)", callback_data=f"rent:plan:{category_key}:1y")],
        [InlineKeyboardButton(text="⬅️ 返回套餐", callback_data="rent:main")],
    ])

def rent_payment_text(category_key, plan_key, order_code):
    cat = RENT_CATEGORIES.get(category_key, {})
    plan = RENT_PLANS.get(plan_key, {})
    title = cat.get("title", "套餐")
    plan_label = plan.get("label", "")
    amount = plan.get("amount", 0)

    return (
        f"✅ <b>{title}</b>\n"
        f"📦 套餐：<b>{plan_label}</b>\n"
        f"🧾 订单号：<code>{order_code}</code>\n\n"
        f"🌿 <b>收款地址：TRC20-USDT</b>\n"
        f"┆\n"
        f"├ 💰订单金额：<b>{amount} U</b>\n"
        f"┆\n"
        f"└➤ <code>{PAYMENT_ADDRESS}</code>\n\n"
        f"🦉 点击(地址和金额)自动复制\n"
        f"- - - - - - - - - - - - - - - - - - - - -\n"
        f"注意：请务必按指定金额 <b>{amount} U</b> 转账\n"
        f"付款后10秒钟自动开通成功\n"
        f"- - - - - - - - - - - - - - - - - - - - -\n"
        f"🗣️ 在线24小时客服 <code>{PAYMENT_SUPPORT}</code>"
    )

def rent_payment_kb(amount):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 复制地址", callback_data=f"copy:{PAYMENT_ADDRESS}"),
            InlineKeyboardButton(text=f"📋 复制金额 {amount}U", callback_data=f"copy:{amount}"),
        ],
        [
            InlineKeyboardButton(text="⬅️ 返回套餐", callback_data="rent:main"),
            InlineKeyboardButton(text="🔄 重新选择", callback_data="rent:back"),
        ],
    ])

@dp.message(lambda m: m.text in ("续费/租用", "🔑 续费/租用", "自助续费"))
async def menu_rent(m: types.Message):
    await m.answer("🔑 <b>请选择要租用的机器人类型</b>", reply_markup=rent_main_kb(), parse_mode="HTML")

@dp.callback_query(lambda c: c.data == "rent:main")
async def rent_main_cb(c: types.CallbackQuery):
    if not c.message:
        return
    await c.message.answer("🔑 <b>请选择要租用的机器人类型</b>", reply_markup=rent_main_kb(), parse_mode="HTML")
    await c.answer()

@dp.callback_query(lambda c: c.data == "rent:back")
async def rent_back_cb(c: types.CallbackQuery):
    if not c.message:
        return
    await c.message.answer("🔑 <b>请选择要租用的机器人类型</b>", reply_markup=rent_main_kb(), parse_mode="HTML")
    await c.answer()

@dp.callback_query(lambda c: c.data in ("rent:group_admin", "rent:computer", "rent:translator"))
async def rent_category_cb(c: types.CallbackQuery):
    if not c.message:
        return
    category_key = c.data.split(":")[1]
    title = RENT_CATEGORIES.get(category_key, {}).get("title", "套餐")
    await c.message.answer(f"📦 <b>{title}</b>\n\n请选择租用时长：", reply_markup=rent_plan_kb(category_key), parse_mode="HTML")
    await c.answer()
```

---

# 13) CẦN CÓ TRONG `db.py`

Bro thêm các bảng / hàm sau vào `db.py`:

## rental_orders table
```python
def init_rental_orders_table():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS rental_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_code TEXT UNIQUE,
        user_id INTEGER,
        username TEXT,
        full_name TEXT,
        category_key TEXT,
        category_title TEXT,
        plan_key TEXT,
        plan_label TEXT,
        amount REAL,
        status TEXT DEFAULT 'pending',
        created_at INTEGER,
        paid_at INTEGER,
        expires_at INTEGER,
        note TEXT
    )
    """)
    conn.commit()
    conn.close()
```

## expiry_notices table
```python
def init_expiry_notice_table():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS expiry_notices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        notice_key TEXT,
        created_at INTEGER,
        UNIQUE(user_id, notice_key)
    )
    """)
    conn.commit()
    conn.close()
```

## Gọi trong `init_db()`
```python
init_rental_orders_table()
init_expiry_notice_table()
```

## Hàm rental
```python
def generate_rental_order_code():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"RB{today}"
    cur.execute("SELECT COUNT(*) FROM rental_orders WHERE order_code LIKE ?", (f"{prefix}-%",))
    count = cur.fetchone()[0] or 0
    conn.close()
    return f"{prefix}-{count + 1:04d}"

def create_rental_order(user_id, username, full_name, category_key, category_title, plan_key, plan_label, amount, note=""):
    order_code = generate_rental_order_code()
    created_at = int(time.time())
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO rental_orders (
            order_code, user_id, username, full_name,
            category_key, category_title, plan_key, plan_label,
            amount, status, created_at, paid_at, expires_at, note
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, NULL, NULL, ?)
    """, (
        order_code, user_id, username, full_name,
        category_key, category_title, plan_key, plan_label,
        amount, created_at, note
    ))
    conn.commit()
    conn.close()
    return order_code

def get_rental_order(order_code):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        SELECT order_code, user_id, username, full_name, category_key, category_title,
               plan_key, plan_label, amount, status, created_at, paid_at, expires_at, note
        FROM rental_orders
        WHERE order_code = ?
    """, (order_code,))
    row = cur.fetchone()
    conn.close()
    return row

def get_pending_rental_orders(limit=50):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        SELECT order_code, user_id, username, full_name, category_title, plan_label, amount, created_at
        FROM rental_orders
        WHERE status = 'pending'
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_rental_orders_by_status(status=None, limit=50):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    if status:
        cur.execute("""
            SELECT order_code, user_id, username, full_name, category_title, plan_label,
                   amount, status, created_at, paid_at, expires_at
            FROM rental_orders
            WHERE status = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (status, limit))
    else:
        cur.execute("""
            SELECT order_code, user_id, username, full_name, category_title, plan_label,
                   amount, status, created_at, paid_at, expires_at
            FROM rental_orders
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

def mark_rental_order_paid(order_code, expires_at=None):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        UPDATE rental_orders
        SET status = 'paid', paid_at = ?, expires_at = ?
        WHERE order_code = ?
    """, (int(time.time()), expires_at, order_code))
    conn.commit()
    conn.close()

def mark_rental_order_rejected(order_code):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        UPDATE rental_orders
        SET status = 'rejected'
        WHERE order_code = ?
    """, (order_code,))
    conn.commit()
    conn.close()
```

## access user by id
```python
def get_access_user_by_id(user_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, username, granted_by, granted_at, expires_at
        FROM access_users
        WHERE user_id = ?
    """, (user_id,))
    row = cur.fetchone()
    conn.close()
    return row
```

## expiry notice
```python
def has_expiry_notice(user_id, notice_key):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        SELECT 1 FROM expiry_notices
        WHERE user_id = ? AND notice_key = ?
        LIMIT 1
    """, (user_id, notice_key))
    row = cur.fetchone()
    conn.close()
    return row is not None

def add_expiry_notice(user_id, notice_key):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT OR IGNORE INTO expiry_notices (user_id, notice_key, created_at)
            VALUES (?, ?, ?)
        """, (user_id, notice_key, int(time.time())))
        conn.commit()
    finally:
        conn.close()
```

---

# 14) XÁC NHẬN THANH TOÁN + REJECT + RENEW

```python
def plan_duration_seconds(plan_key):
    if plan_key == "1m":
        return 30 * 24 * 60 * 60
    if plan_key == "3m":
        return 90 * 24 * 60 * 60
    if plan_key == "6m":
        return 180 * 24 * 60 * 60
    if plan_key == "1y":
        return 365 * 24 * 60 * 60
    return 30 * 24 * 60 * 60

def calc_renew_expire_at(user_id, plan_key):
    now_ts = int(time.time())
    duration = plan_duration_seconds(plan_key)
    access_row = get_access_user_by_id(user_id)
    current_exp = None
    if access_row and len(access_row) >= 5:
        current_exp = access_row[4]
    base_ts = now_ts
    if current_exp and int(current_exp) > now_ts:
        base_ts = int(current_exp)
    return base_ts + duration

async def activate_rental_order(order_code, granted_by=None):
    row = get_rental_order(order_code)
    if not row:
        return None, "订单不存在"
    (
        order_code, user_id, username, full_name, category_key, category_title,
        plan_key, plan_label, amount, status, created_at, paid_at, expires_at, note
    ) = row

    if status == "paid":
        return row, "订单已支付"

    new_expires_at = calc_renew_expire_at(user_id, plan_key)
    mark_rental_order_paid(order_code, expires_at=new_expires_at)
    add_access_user(
        user_id=user_id,
        username=username or "",
        granted_by=granted_by,
        expires_at=new_expires_at
    )
    return row, None
```

## View order
```python
@dp.callback_query(lambda c: c.data and c.data.startswith("order:view:"))
async def view_order_cb(c: types.CallbackQuery):
    if not c.message:
        return
    order_code = c.data.split(":", 2)[2]
    row = get_rental_order(order_code)
    if not row:
        return await c.answer("订单不存在", show_alert=True)

    (
        order_code, user_id, username, full_name, category_key, category_title,
        plan_key, plan_label, amount, status, created_at, paid_at, expires_at, note
    ) = row

    created_str = datetime.fromtimestamp(created_at).strftime("%Y-%m-%d %H:%M:%S")
    paid_str = "-" if not paid_at else datetime.fromtimestamp(paid_at).strftime("%Y-%m-%d %H:%M:%S")
    expire_str = "-" if not expires_at else datetime.fromtimestamp(expires_at).strftime("%Y-%m-%d %H:%M:%S")

    text = (
        f"🧾 <b>订单详情</b>\n\n"
        f"订单号：<code>{order_code}</code>\n"
        f"用户：<code>{user_id}</code> @{username or '-'}\n"
        f"姓名：{full_name or '-'}\n"
        f"类型：{category_title}\n"
        f"套餐：{plan_label}\n"
        f"金额：<b>{amount} U</b>\n"
        f"状态：<b>{status}</b>\n"
        f"创建时间：{created_str}\n"
        f"支付时间：{paid_str}\n"
        f"到期时间：{expire_str}\n"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ 确认已付款", callback_data=f"order:approve:{order_code}"),
            InlineKeyboardButton(text="❌ 拒绝", callback_data=f"order:reject:{order_code}"),
        ],
        [
            InlineKeyboardButton(text="⬅️ 返回订单列表", callback_data="order:list_pending")
        ]
    ])

    await c.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await c.answer()
```

## Approve / Reject
```python
@dp.callback_query(lambda c: c.data and c.data.startswith("order:approve:"))
async def order_approve_cb(c: types.CallbackQuery):
    if not c.message or not c.from_user:
        return
    if not can_use_manage_panel(c.from_user.id):
        return await c.answer("无权限", show_alert=True)

    order_code = c.data.split(":", 2)[2]
    row = get_rental_order(order_code)
    if not row:
        return await c.answer("订单不存在", show_alert=True)

    (
        order_code, user_id, username, full_name, category_key, category_title,
        plan_key, plan_label, amount, status, created_at, paid_at, expires_at, note
    ) = row

    if status == "paid":
        return await c.answer("订单已支付", show_alert=True)

    row2, err = await activate_rental_order(order_code, granted_by=c.from_user.id)
    if err:
        return await c.answer(err, show_alert=True)

    new_expires_at = calc_renew_expire_at(user_id, plan_key)
    expire_str = datetime.fromtimestamp(new_expires_at).strftime("%Y-%m-%d %H:%M:%S")

    try:
        await bot.send_message(
            user_id,
            (
                "✅ <b>续费/租用成功</b>\n\n"
                f"订单号：<code>{order_code}</code>\n"
                f"类型：{category_title}\n"
                f"套餐：{plan_label}\n"
                f"到期时间：<b>{expire_str}</b>\n\n"
                "权限已自动开通/续期。"
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        print("notify paid user failed:", e)

    await c.message.answer(
        (
            f"✅ <b>已确认付款</b>\n\n"
            f"订单号：<code>{order_code}</code>\n"
            f"用户：<code>{user_id}</code>\n"
            f"到期时间：<b>{expire_str}</b>\n"
            f"权限已开通/已续期。"
        ),
        parse_mode="HTML"
    )
    await c.answer("✅ 已开通/续期")


@dp.callback_query(lambda c: c.data and c.data.startswith("order:reject:"))
async def order_reject_cb(c: types.CallbackQuery):
    if not c.message or not c.from_user:
        return
    if not can_use_manage_panel(c.from_user.id):
        return await c.answer("无权限", show_alert=True)

    order_code = c.data.split(":", 2)[2]
    row = get_rental_order(order_code)
    if not row:
        return await c.answer("订单不存在", show_alert=True)

    (
        order_code, user_id, username, full_name, category_key, category_title,
        plan_key, plan_label, amount, status, created_at, paid_at, expires_at, note
    ) = row

    if status == "paid":
        return await c.answer("订单已支付", show_alert=True)

    mark_rental_order_rejected(order_code)

    await c.message.answer(
        (
            f"❌ <b>订单已拒绝</b>\n\n"
            f"订单号：<code>{order_code}</code>\n"
            f"用户：<code>{user_id}</code>\n"
            f"套餐：{plan_label}\n"
            f"金额：<b>{amount} U</b>\n"
            f"状态：<b>rejected</b>"
        ),
        parse_mode="HTML"
    )

    try:
        await bot.send_message(
            user_id,
            (
                "❌ <b>您的订单未通过</b>\n\n"
                f"订单号：<code>{order_code}</code>\n"
                f"套餐：{plan_label}\n"
                "如有疑问，请联系管理员。"
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        print("notify reject user failed:", e)

    await c.answer("✅ 已拒绝")
```

---

# 15) LỊCH SỬ ĐƠN + CẢNH BÁO HẾT HẠN

```python
def order_history_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 全部订单", callback_data="order:history:all")],
        [
            InlineKeyboardButton(text="⏳ 待支付", callback_data="order:history:pending"),
            InlineKeyboardButton(text="✅ 已支付", callback_data="order:history:paid"),
        ],
        [InlineKeyboardButton(text="❌ 已拒绝", callback_data="order:history:rejected")],
    ])


@dp.message(lambda m: m.text in ("订单历史", "租用历史", "历史订单"))
async def order_history_cmd(m: types.Message):
    if not can_use_manage_panel(m.from_user.id):
        return await m.reply("❌ 无权限")
    await m.reply("🧾 <b>订单历史</b>\n\n请选择查看类型：", reply_markup=order_history_kb(), parse_mode="HTML")


@dp.callback_query(lambda c: c.data and c.data.startswith("order:history:"))
async def order_history_cb(c: types.CallbackQuery):
    if not c.message or not c.from_user:
        return
    if not can_use_manage_panel(c.from_user.id):
        return await c.answer("无权限", show_alert=True)

    status = c.data.split(":")[2]
    if status == "all":
        rows = get_rental_orders_by_status(None, limit=20)
        title = "📦 全部订单"
    else:
        rows = get_rental_orders_by_status(status, limit=20)
        title = f"📦 {status}"

    if not rows:
        await c.message.answer(f"{title}\n\n暂无记录")
        return await c.answer()

    text = f"{title}\n\n"
    for row in rows:
        order_code, user_id, username, full_name, category_title, plan_label, amount, st, created_at, paid_at, expires_at = row
        created_str = datetime.fromtimestamp(created_at).strftime("%Y-%m-%d %H:%M:%S")
        text += (
            f"• <code>{order_code}</code>\n"
            f"  {category_title} | {plan_label} | {amount}U | {st}\n"
            f"  用户：<code>{user_id}</code> @{username or '-'}\n"
            f"  时间：{created_str}\n\n"
        )

    await send_long_text(c.message.chat.id, text)
    await c.answer()


async def expiry_warning_loop():
    while True:
        try:
            now_ts = int(time.time())
            rows = get_access_users()

            for row in rows:
                user_id, username, granted_by, granted_at, expires_at = row
                if not expires_at:
                    continue

                expires_at = int(expires_at)
                remain = expires_at - now_ts

                if remain <= 0:
                    notice_key = "expired"
                    if not has_expiry_notice(user_id, notice_key):
                        add_expiry_notice(user_id, notice_key)
                        try:
                            await bot.send_message(user_id, "⏳ 您的使用权限已到期，请尽快续费。")
                        except Exception as e:
                            print("expired notify failed:", e)
                    continue

                warning_map = [
                    (7 * 24 * 3600, "7d", "7 天"),
                    (3 * 24 * 3600, "3d", "3 天"),
                    (1 * 24 * 3600, "1d", "1 天"),
                    (1 * 3600, "1h", "1 小时"),
                ]

                for threshold, key, label in warning_map:
                    if remain <= threshold and remain > threshold - 3600:
                        notice_key = f"warn_{key}"
                        if not has_expiry_notice(user_id, notice_key):
                            add_expiry_notice(user_id, notice_key)
                            try:
                                await bot.send_message(
                                    user_id,
                                    (
                                        f"⚠️ 您的权限将在 <b>{label}</b> 后到期。\n\n"
                                        f"到期时间：<code>{datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d %H:%M:%S')}</code>\n"
                                        f"请及时续费。"
                                    ),
                                    parse_mode="HTML",
                                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                        [InlineKeyboardButton(text="🔑 立即续费", callback_data="rent:main")]
                                    ])
                                )
                            except Exception as e:
                                print("warn notify failed:", e)
                        break

        except Exception as e:
            print("expiry_warning_loop error:", e)

        await asyncio.sleep(300)
```

---

# 16) ADDRESS QUERY + ON-CHAIN THẬT

```python
TRONGRID_API_URL = "https://api.trongrid.io"
USDT_TRC20_CONTRACT = "TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj"

def address_query_text():
    return (
        "🔍 <b>地址查询</b>\n\n"
        "请直接发送 TRON 地址进行查询。\n\n"
        "<b>示例：</b>\n"
        "<code>TSPpLmYuFXLi6GU1W4uyG6NKGbdWPw886U</code>"
    )

def address_result_kb(address, page=1):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📜 群组交易记录", callback_data=f"addr:tx:{address}:{page}"),
            InlineKeyboardButton(text="🔄 重新查询", callback_data="addr:again")
        ],
        [InlineKeyboardButton(text="⬅️ 返回菜单", callback_data="addr:back")]
    ])

def tx_history_kb(address, page=1):
    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton(text="⬅️ 上一页", callback_data=f"addr:tx:{address}:{page-1}"))
    buttons.append(InlineKeyboardButton(text=f"📄 第 {page} 页", callback_data="noop"))
    buttons.append(InlineKeyboardButton(text="下一页 ➡️", callback_data=f"addr:tx:{address}:{page+1}"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

async def trongrid_get(path, params=None):
    url = f"{TRONGRID_API_URL}{path}"
    headers = {}
    if TRONGRID_API_KEY:
        headers["TRON-PRO-API-KEY"] = TRONGRID_API_KEY
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers, timeout=12) as resp:
            return await resp.json()

async def get_tron_account_info(address):
    account_data = await trongrid_get(f"/v1/accounts/{address}")
    if not account_data:
        return None

    found = bool(account_data.get("data"))
    trx_balance = 0.0
    usdt_balance = 0.0
    tx_count = 0
    first_tx_time = "-"
    last_tx_time = "-"
    is_multisig = False
    energy = {"free": 0, "used": 0}
    bandwidth = {"free": 0, "used": 0}

    if found:
        acc = account_data["data"][0]
        trx_balance = float(acc.get("balance", 0)) / 1_000_000
        tx_count = int(acc.get("total_transaction_count", 0) or 0)

        active_perm = acc.get("active_permission")
        if active_perm and isinstance(active_perm, list) and len(active_perm) > 1:
            is_multisig = True

        acc_res = acc.get("account_resource", {}) or {}
        energy = {
            "free": int(acc_res.get("energy_limit", 0) or 0),
            "used": int(acc_res.get("energy_used", 0) or 0),
        }
        bandwidth = {
            "free": int(acc_res.get("free_net_limit", 0) or 0),
            "used": int(acc_res.get("free_net_used", 0) or 0),
        }

        trc20 = acc.get("trc20", [])
        if trc20 and isinstance(trc20, list):
            for token_map in trc20:
                if isinstance(token_map, dict):
                    for contract, raw_amount in token_map.items():
                        if contract == USDT_TRC20_CONTRACT:
                            try:
                                usdt_balance = float(raw_amount) / 1_000_000
                            except:
                                usdt_balance = 0.0

    tx_data = await trongrid_get(
        f"/v1/accounts/{address}/transactions",
        params={"limit": 20, "only_confirmed": "true", "order_by": "block_timestamp,desc"}
    )
    txs = tx_data.get("data", []) if tx_data else []

    if txs:
        last_ts = txs[0].get("block_timestamp")
        first_ts = txs[-1].get("block_timestamp")
        if last_ts:
            last_tx_time = datetime.fromtimestamp(last_ts / 1000).strftime("%Y-%m-%d %H:%M:%S")
        if first_ts:
            first_tx_time = datetime.fromtimestamp(first_ts / 1000).strftime("%Y-%m-%d %H:%M:%S")

    return {
        "found": found,
        "trx_balance": trx_balance,
        "usdt_balance": usdt_balance,
        "tx_count": tx_count,
        "first_tx_time": first_tx_time,
        "last_tx_time": last_tx_time,
        "is_multisig": is_multisig,
        "energy": energy,
        "bandwidth": bandwidth,
        "txs": txs,
    }

def format_address_info_text(address, info):
    if not info:
        return (
            f"🔎 查询地址：<code>{address}</code>\n\n"
            "⚠️ 无法获取链上数据，请稍后重试。"
        )

    trx_balance = info.get("trx_balance", 0)
    usdt_balance = info.get("usdt_balance", 0)
    tx_count = info.get("tx_count", 0)
    first_tx = info.get("first_tx_time", "-")
    last_active = info.get("last_tx_time", "-")
    is_multisig = info.get("is_multisig", False)
    energy = info.get("energy", {"free": 0, "used": 0})
    bandwidth = info.get("bandwidth", {"free": 0, "used": 0})
    sig_status = "多签地址" if is_multisig else "未多签地址"

    return (
        f"🔎 查询地址：<code>{address}</code>\n\n"
        f"💡 交易次数：{tx_count}\n"
        f"⏰ 首次交易：{first_tx}\n"
        f"🌟 最后活跃：{last_active}\n"
        f"🔰 签名状态：{sig_status}\n\n"
        f"🔋 能量：剩余：{energy.get('free', 0)} / {energy.get('used', 0)}\n"
        f"🌈 带宽：剩余：{bandwidth.get('free', 0)} / {bandwidth.get('used', 0)}\n\n"
        f"💰 USDT余额：{fmt_token_amount(usdt_balance)} USDT\n"
        f"💰 TRX 余额：{fmt_token_amount(trx_balance)} TRX"
    )

async def get_tron_transactions(address, page=1, page_size=10):
    offset = (page - 1) * page_size
    tx_data = await trongrid_get(
        f"/v1/accounts/{address}/transactions",
        params={"limit": page_size, "only_confirmed": "true", "order_by": "block_timestamp,desc", "offset": offset}
    )
    return tx_data.get("data", []) if tx_data else []

def format_tron_tx_row(tx):
    try:
        ts = tx.get("block_timestamp")
        dt = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M:%S") if ts else "-"
        txid = tx.get("txID", "-")
        contract = tx.get("raw_data", {}).get("contract", [])
        tx_type = "-"
        if contract:
            tx_type = contract[0].get("type", "-")
        return f"• {dt} | {tx_type}\n  <code>{txid}</code>"
    except:
        return "• 无法解析交易"

@dp.message(lambda m: m.text in ("地址查询", "📍 地址查询", "🔍 地址查询"))
async def menu_address_query(m: types.Message, state: FSMContext):
    if not can_use_bot_ops(m.from_user.id):
        return await m.reply("❌ 无权限")
    await state.set_state(AddressQueryFSM.waiting_address)
    await m.reply(address_query_text(), parse_mode="HTML")

@dp.message(AddressQueryFSM.waiting_address)
async def receive_address_query(m: types.Message, state: FSMContext):
    if not can_use_bot_ops(m.from_user.id):
        return await m.reply("❌ 无权限")

    addr = (m.text or "").strip()
    if not is_tron_address(addr):
        return await m.reply(
            "❌ 地址格式不正确，请重新输入 TRON 地址。\n"
            "示例：<code>TSPpLmYuFXLi6GU1W4uyG6NKGbdWPw886U</code>",
            parse_mode="HTML"
        )

    await m.reply("⏳ 正在查询链上数据，请稍候...")
    try:
        info = await get_tron_account_info(addr)
        text = format_address_info_text(addr, info)
    except Exception as e:
        print("on-chain query error:", e)
        text = f"🔎 查询地址：<code>{addr}</code>\n\n⚠️ 查询失败，请稍后再试。"

    await state.clear()
    await m.reply(text, parse_mode="HTML", reply_markup=address_result_kb(addr, page=1))


@dp.callback_query(lambda c: c.data == "addr:again")
async def addr_again_cb(c: types.CallbackQuery, state: FSMContext):
    if not c.message:
        return
    await state.set_state(AddressQueryFSM.waiting_address)
    await c.message.answer("🔍 <b>地址查询</b>\n\n请直接发送 TRON 地址进行查询。", parse_mode="HTML")
    await c.answer()

@dp.callback_query(lambda c: c.data == "addr:back")
async def addr_back_cb(c: types.CallbackQuery, state: FSMContext):
    if not c.message:
        return
    await state.clear()
    await c.message.answer("✅ 已返回主菜单")
    await c.answer()

@dp.callback_query(lambda c: c.data and c.data.startswith("addr:tx:"))
async def addr_tx_cb(c: types.CallbackQuery):
    if not c.message:
        return

    parts = c.data.split(":")
    address = parts[2]
    page = int(parts[3]) if len(parts) >= 4 and parts[3].isdigit() else 1

    await c.message.answer("⏳ 正在加载交易记录，请稍候...")

    try:
        txs = await get_tron_transactions(address, page=page, page_size=10)
        if not txs:
            await c.message.answer(f"🔎 查询地址：<code>{address}</code>\n📄 当前页无交易记录", parse_mode="HTML")
            return await c.answer()

        text = f"🔎 查询地址：<code>{address}</code>\n🗂 当前页码：第 {page} 页\n\n📄 交易记录：\n"
        for tx in txs:
            text += format_tron_tx_row(tx) + "\n\n"

        await c.message.answer(text, parse_mode="HTML", reply_markup=tx_history_kb(address, page))
    except Exception as e:
        print("addr tx cb error:", e)
        await c.message.answer("⚠️ 交易记录加载失败，请稍后再试.")

    await c.answer()
```

---

# 17) BROADCAST GỌN / KHÔNG BỊ NGƯỜI KHÁC CHÈN

```python
@dp.message(lambda m: m.text == "群发广播")
async def menu_broadcast(m: types.Message, state: FSMContext):
    if is_private(m):
        if get_admin(m.from_user.id) != "super":
            return await m.answer("❌ 只有超级管理员可在私聊里全局群发。")
        scope = "all"
        target_chat_id = -1
    else:
        ensure_group(m)
        if not can_use_manage_panel(m.from_user.id):
            return await m.reply("❌ 无权限")
        scope = "current"
        target_chat_id = m.chat.id

    await state.set_state(BroadcastFSM.waiting_content)
    await state.update_data(scope=scope, target_chat_id=target_chat_id, creator_id=m.from_user.id)
    await m.reply("📢 请发送要广播的内容。\n\n提示：只有你本人发送的内容会被接收。")


@dp.message(BroadcastFSM.waiting_content)
async def broadcast_receive_content(m: types.Message, state: FSMContext):
    data = await state.get_data()
    creator_id = data.get("creator_id")
    if creator_id and m.from_user and m.from_user.id != creator_id:
        return

    scope = data.get("scope", "current")
    target_chat_id = data.get("target_chat_id", m.chat.id)

    await state.update_data(
        source_chat_id=m.chat.id,
        source_message_id=m.message_id,
        scope=scope,
        target_chat_id=target_chat_id
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="确认群发(普通)", callback_data="bc:copy"),
            InlineKeyboardButton(text="确认群发(转发)", callback_data="bc:fwd"),
        ],
        [InlineKeyboardButton(text="取消群发", callback_data="bc:cancel")]
    ])

    await m.reply("请确认广播方式：", reply_markup=kb)
    await state.set_state(BroadcastFSM.waiting_confirm)


@dp.callback_query(lambda c: c.data and c.data.startswith("bc:"))
async def broadcast_callback(c: types.CallbackQuery, state: FSMContext):
    if not c.from_user:
        return

    data = await state.get_data()
    creator_id = data.get("creator_id")
    if creator_id and c.from_user.id != creator_id:
        return await c.answer("❌ 无权限", show_alert=True)

    scope = data.get("scope", "current")
    source_chat_id = data.get("source_chat_id")
    source_message_id = data.get("source_message_id")

    if c.data == "bc:cancel":
        await state.clear()
        return await c.message.edit_text("✅ 已取消群发")

    if c.data not in ("bc:copy", "bc:fwd"):
        return

    if scope == "all":
        targets = [g[0] for g in get_groups()]
    else:
        target_chat_id = data.get("target_chat_id")
        targets = [target_chat_id]

    if not source_chat_id or not source_message_id:
        await state.clear()
        return await c.message.edit_text("❌ 广播内容已失效，请重新发送。")

    ok = 0
    fail = 0
    for chat_id in targets:
        try:
            if c.data == "bc:copy":
                await bot.copy_message(chat_id=chat_id, from_chat_id=source_chat_id, message_id=source_message_id)
            else:
                await bot.forward_message(chat_id=chat_id, from_chat_id=source_chat_id, message_id=source_message_id)
            ok += 1
        except Exception as e:
            fail += 1
            print("broadcast error:", e)

    await state.clear()
    await c.message.edit_text(f"✅ 群发完成\n成功：{ok}\n失败：{fail}")
```

---

# 18) LỊCH SỬ GIAO DỊCH GROUP → WEB DASHBOARD

```python
def history_groups_kb():
    groups = get_groups()
    rows = []
    for chat_id, title in groups:
        today = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d")
        url = f"{BASE_URL}/group/{chat_id}?date={today}&token={WEB_TOKEN}"
        rows.append([InlineKeyboardButton(text=f"📂 {title}", url=url)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@dp.message(lambda m: m.text in ("交易历史", "📜 交易历史"))
async def menu_history(m: types.Message):
    if not can_use_bot_ops(m.from_user.id):
        return await m.reply("❌ 无权限")
    await m.reply(
        "📜 <b>交易历史</b>\n\n请选择一个群组，点击后将打开网页历史记录。",
        reply_markup=history_groups_kb(),
        parse_mode="HTML"
    )
```

---

# 19) LIFESPAN CẦN THÊM TASK

Trong `lifespan()`:

```python
task1 = asyncio.create_task(daily_cut_loop())
task2 = asyncio.create_task(trial_expire_loop())
task3 = asyncio.create_task(daily_usdt_update_loop())
task4 = asyncio.create_task(expiry_warning_loop())
```

Trong `finally`:

```python
task1.cancel()
task2.cancel()
task3.cancel()
task4.cancel()
try:
    await task1
except:
    pass
try:
    await task2
except:
    pass
try:
    await task3
except:
    pass
try:
    await task4
except:
    pass
```

---

# 20) CẦN XOÁ CÁC PHẦN CŨ BỊ TRÙNG

Bro nhớ xoá / thay các handler cũ:

- `管理客服` bị trùng
- `自助续费` cũ
- `地址查询` cũ
- `交易历史` cũ
- `实时U价` cũ
- `群发广播` cũ nếu đang còn bản khác
- `manage:add_admin`, `manage:del_admin`, `manage:create_code` cũ nếu khác logic

---

# 21) TÓM TẮT QUYỀN

- **Chủ bot**: toàn quyền
- **Super admin**: thao tác bot + tạo/thu hồi code
- **Admin**: thao tác bot
- **Người thường**: bấm nút thì bị từ chối nếu không có quyền

---

Nếu bro muốn, bước tiếp theo mình làm tiếp cho bro một bản **“clean patch”** theo đúng kiểu:

- `app.py` phần nào thay
- `db.py` phần nào thêm
- `xoá gì`
- `giữ gì`

để bro **copy dán 1 lần cho khỏi lẫn**.
