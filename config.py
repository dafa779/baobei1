Ok bro, mình ghép hệ thống quyền mới vào theo kiểu sạch và rõ ràng luôn.

Quyền mình set như sau
Chủ bot: toàn quyền
Super admin: thao tác bot, xem panel, tạo/thu hồi code
Admin: chỉ thao tác bot
Thường: có thể thấy nút chung, nhưng bấm nút cấm sẽ bị chặn
Quy tắc quan trọng
Chỉ chủ bot mới được thêm / xoá admin
Chủ bot + Super admin mới được tạo / thu hồi code
Admin chỉ được dùng các nút vận hành bot
1) Thêm biến môi trường
Ở đầu file
BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID", "0") or 0)
SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "0") or 0)
WEB_TOKEN = os.getenv("WEB_TOKEN", "abc123")
Trong .env
BOT_OWNER_ID=123456789
SUPER_ADMIN_ID=987654321
WEB_TOKEN=abc123
2) Thêm helper quyền
Dán vào phần # ================= HELPERS =================

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
    if role == "super":
        return "super"
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
3) Sửa menu_kb() cho đẹp và có nút quản lý theo quyền
Thay menu_kb() bằng:

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
    ]

    if user_id is not None and can_use_manage_panel(user_id):
        keyboard.append([KeyboardButton(text="🛠 管理面板")])

    keyboard.append([KeyboardButton(text="👥 分组功能")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )
4) Sửa /start để truyền user_id
Thay chỗ:

await m.answer(text, reply_markup=start_inline_kb(m.from_user.id))
thành:

await m.answer(text, reply_markup=start_inline_kb(m.from_user.id), parse_mode="HTML")
Và trong start_inline_kb() sửa nút tạo code theo quyền:

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
        buttons.append([
            InlineKeyboardButton(text="🔑 创建激活码", callback_data="manage:create_code")
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
5) Sửa các handler vận hành bot
开始记账
@dp.message(lambda m: m.text in ("开始", "开始记账", "开启记账", "🔥 开始记账"))
async def start_accounting(m: types.Message):
    if not is_group_message(m):
        return
    ensure_group(m)
    if not can_use_bot_ops(m.from_user.id):
        return await m.reply(deny_text())

    set_chat_setting(m.chat.id, "enabled", "1")
    await m.reply("✅ 记账已开启！")
关闭记账
@dp.message(lambda m: m.text in ("关闭记账", "停止记账"))
async def stop_accounting(m: types.Message):
    if not is_group_message(m):
        return
    ensure_group(m)
    if not can_use_bot_ops(m.from_user.id):
        return await m.reply(deny_text())

    set_chat_setting(m.chat.id, "enabled", "0")
    await m.reply("⛔ 记账已关闭！")
上课 / 下课
@dp.message(lambda m: m.text in ("上课", "下课"))
async def group_permission_cmd(m: types.Message):
    if not is_group_message(m):
        return
    ensure_group(m)
    if not can_use_bot_ops(m.from_user.id):
        return await m.reply(deny_text())

    try:
        if m.text == "上课":
            await bot.set_chat_permissions(
                m.chat.id,
                permissions=types.ChatPermissions(can_send_messages=True)
            )
            await m.reply("✅ 已开启发言")
        else:
            await bot.set_chat_permissions(
                m.chat.id,
                permissions=types.ChatPermissions(can_send_messages=False)
            )
            await m.reply("✅ 已禁言")
    except Exception as e:
        await m.reply("❌ 机器人没有权限修改群权限")
        print("group_permission_cmd error:", e)
Config
Trong config_cmd đổi check thành:

if not can_use_bot_ops(m.from_user.id):
    return await m.reply(deny_text())
6) Sửa 交易历史 và 实时U价
实时U价
@dp.message(lambda m: m.text in ("实时U价", "📊 实时U价"))
async def menu_rate(m: types.Message):
    if not can_use_bot_ops(m.from_user.id):
        return await m.reply(deny_text())

    rates = await get_usdt_rates_cached()
    text = format_usdt_rate_text(rates)
    await m.answer(text, reply_markup=rate_kb(), parse_mode="HTML")
交易历史
@dp.message(lambda m: m.text in ("交易历史", "📜 交易历史"))
async def menu_history(m: types.Message):
    if not can_use_bot_ops(m.from_user.id):
        return await m.reply(deny_text())

    await m.reply(
        "📜 <b>交易历史</b>\n\n请选择一个群组，点击后将打开网页历史记录。",
        reply_markup=history_groups_kb(),
        parse_mode="HTML"
    )
7) Ghép panel quản trị chung
FSM
class AdminFSM(StatesGroup):
    waiting_add_admin = State()
    waiting_del_admin = State()
    waiting_trial_code = State()
Panel
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
Mở panel
@dp.message(lambda m: m.text in ("管理面板", "管理员快捷面板", "续费管理面板", "🛠 管理面板"))
async def manage_panel_cmd(m: types.Message):
    if not can_use_manage_panel(m.from_user.id):
        return await m.reply(deny_text())

    await m.reply(
        "🛠 <b>管理面板</b>\n\n点击下方按钮执行操作。",
        reply_markup=manage_panel_kb(),
        parse_mode="HTML"
    )
8) Chỉ CHỦ BOT mới thêm/xoá admin
Add admin
@dp.callback_query(lambda c: c.data == "manage:add_admin")
async def manage_add_admin_cb(c: types.CallbackQuery, state: FSMContext):
    if not can_manage_admins(c.from_user.id):
        return await c.answer("无权限", show_alert=True)

    await state.set_state(AdminFSM.waiting_add_admin)
    await c.message.answer(
        "➕ <b>添加管理员</b>\n\n请回复目标用户消息，或直接发送用户ID。",
        parse_mode="HTML"
    )
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
Delete admin
@dp.callback_query(lambda c: c.data == "manage:del_admin")
async def manage_del_admin_cb(c: types.CallbackQuery, state: FSMContext):
    if not can_manage_admins(c.from_user.id):
        return await c.answer("无权限", show_alert=True)

    await state.set_state(AdminFSM.waiting_del_admin)
    await c.message.answer(
        "➖ <b>删除管理员</b>\n\n请回复目标用户消息，或直接发送用户ID。",
        parse_mode="HTML"
    )
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
9) Chỉ chủ bot + super admin mới tạo/thu hồi code
@dp.callback_query(lambda c: c.data == "manage:create_code")
async def manage_create_code_cb(c: types.CallbackQuery, state: FSMContext):
    if not can_manage_codes(c.from_user.id):
        return await c.answer("无权限", show_alert=True)

    await state.set_state(AdminFSM.waiting_trial_code)
    await c.message.answer(
        "🔑 <b>创建续费码</b>\n\n请发送新的续费码，例如：<code>ABC123</code>",
        parse_mode="HTML"
    )
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
@dp.callback_query(lambda c: c.data == "manage:revoke_code")
async def manage_revoke_code_cb(c: types.CallbackQuery):
    if not can_manage_codes(c.from_user.id):
        return await c.answer("无权限", show_alert=True)

    set_trial_code("")
    await c.message.answer("🗑 <b>续费码已回收</b>", parse_mode="HTML")
    await c.answer()
10) Giữ 管理员列表 cho super/admin/owner
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
11) group_history web buttons
def history_groups_kb():
    groups = get_groups()
    rows = []

    for chat_id, title in groups:
        today = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d")
        url = f"{BASE_URL}/group/{chat_id}?date={today}&token={WEB_TOKEN}"
        rows.append([
            InlineKeyboardButton(text=f"📂 {title}", url=url)
        ])

    return InlineKeyboardMarkup(inline_keyboard=rows)
12) copy: buttons và 使用说明
Những nút copy nhanh vẫn giữ bình thường.
Nhưng manage:* thì đã bị khóa theo quyền mới.

13) Thêm task tự update giá 08:00 Bắc Kinh trong lifespan
task1 = asyncio.create_task(daily_cut_loop())
task2 = asyncio.create_task(trial_expire_loop())
task3 = asyncio.create_task(daily_usdt_update_loop())
Phần finally:

task1.cancel()
task2.cancel()
task3.cancel()
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
14) Chỗ cần xoá / đổi nếu đang trùng
Bro nên xoá hoặc sửa các chỗ cũ này:

các handler 管理客服 bị trùng
panel admin cũ riêng lẻ
panel renew cũ riêng lẻ
check quyền kiểu cũ:
get_admin(...) != "super"
get_admin(...) in ("super","admin")
đổi sang helper mới ở trên.

15) Tóm tắt quyền cuối cùng
Chủ bot
toàn quyền
thêm/xoá admin
tạo/thu hồi code
mọi nút
Super admin
thao tác bot
xem panel
tạo/thu hồi code
không thêm/xoá admin
Admin
thao tác bot
xem lịch sử, realtime, help
không đụng admin management
không tạo/thu hồi code
Người thường
thấy nút chung nếu bro muốn
bấm nút cấm sẽ báo ❌ 无权限
Nếu bro muốn, bước tiếp theo mình sẽ làm tiếp cho bro bản “patch gộp sạch”:

mình gom lại thành 1 khối code cuối
bro chỉ việc copy dán vào app.py
mình sẽ đánh dấu rõ: xóa đoạn nào, thay đoạn nào để đỡ lẫn.
