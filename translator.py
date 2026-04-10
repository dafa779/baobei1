Ok bro, mình ghép tiếp luôn lịch sử đơn + cảnh báo hết hạn cho trọn bộ.

Mình làm theo hướng:

Có 2 phần
Lịch sử đơn thuê

xem tất cả đơn
lọc pending / paid / rejected
Cảnh báo hết hạn

bot tự nhắc user khi sắp hết hạn
ví dụ: trước 7 ngày / 3 ngày / 1 ngày / 1 giờ
chỉ nhắc 1 lần mỗi mốc, tránh spam
1) Thêm hàm lấy lịch sử đơn vào db.py
Dán vào db.py:

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
2) Thêm hàm cập nhật nhắc hết hạn vào db.py
Để tránh nhắc lặp, tạo bảng log nhắc:

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
Gọi nó trong init_db():

init_expiry_notice_table()
Hàm kiểm tra đã nhắc chưa
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
Hàm ghi log nhắc
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
3) Import thêm vào app.py
Thêm vào phần import từ db:

from db import (
    ...
    get_rental_orders_by_status,
    has_expiry_notice,
    add_expiry_notice,
)
4) Làm menu lịch sử đơn thuê
Bàn phím
def order_history_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📦 全部订单", callback_data="order:history:all"),
        ],
        [
            InlineKeyboardButton(text="⏳ 待支付", callback_data="order:history:pending"),
            InlineKeyboardButton(text="✅ 已支付", callback_data="order:history:paid"),
        ],
        [
            InlineKeyboardButton(text="❌ 已拒绝", callback_data="order:history:rejected"),
        ],
    ])
Lệnh mở lịch sử đơn
@dp.message(lambda m: m.text in ("订单历史", "租用历史", "历史订单"))
async def order_history_cmd(m: types.Message):
    if not can_use_manage_panel(m.from_user.id):
        return await m.reply("❌ 无权限")

    await m.reply(
        "🧾 <b>订单历史</b>\n\n请选择查看类型：",
        reply_markup=order_history_kb(),
        parse_mode="HTML"
    )
Callback xem từng loại
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
5) Làm cảnh báo hết hạn
Mình sẽ làm loop nhắc tự động.

Các mốc nhắc
còn 7 ngày
còn 3 ngày
còn 1 ngày
còn 1 giờ
đã hết hạn
Helper lấy danh sách user có quyền
Nếu get_access_users() của bro đã có rồi thì dùng luôn.
Nếu chưa, thêm vào db.py:

def get_access_users():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, username, granted_by, granted_at, expires_at
        FROM access_users
    """)
    rows = cur.fetchall()
    conn.close()
    return rows
Loop cảnh báo
Dán vào app.py:

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
                            await bot.send_message(
                                user_id,
                                "⏳ 您的使用权限已到期，请尽快续费。"
                            )
                        except Exception as e:
                            print("expired notify failed:", e)
                    continue

                # các mốc nhắc
                warning_map = [
                    (7 * 24 * 3600, "7d", "7 天"),
                    (3 * 24 * 3600, "3d", "3 天"),
                    (1 * 24 * 3600, "1d", "1 天"),
                    (1 * 3600, "1h", "1 小时"),
                ]

                for threshold, key, label in warning_map:
                    # nếu còn <= threshold và > threshold - 60*60 (tránh spam quá nhiều)
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
                                    parse_mode="HTML"
                                )
                            except Exception as e:
                                print("warn notify failed:", e)
                        break

        except Exception as e:
            print("expiry_warning_loop error:", e)

        await asyncio.sleep(300)
6) Gọi loop này trong lifespan
Trong phần:

task1 = asyncio.create_task(daily_cut_loop())
task2 = asyncio.create_task(trial_expire_loop())
task3 = asyncio.create_task(daily_usdt_update_loop())
thêm:

task4 = asyncio.create_task(expiry_warning_loop())
Và finally nhớ cancel:

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
7) Làm nút gia hạn lại ngay trong tin nhắc
Nếu muốn xịn hơn, trong tin nhắc hết hạn có thể thêm nút:

InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔑 立即续费", callback_data="rent:main")]
])
Ví dụ sửa phần notify:

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
8) Kết quả sau khi ghép
Lịch sử đơn
xem tất cả đơn
lọc pending / paid / rejected
Cảnh báo hết hạn
user được nhắc trước khi hết hạn
không spam lặp
mỗi mốc chỉ nhắc 1 lần
Renew
bấm ngay nút thuê/renew từ thông báo
mua lại thì tự cộng dồn nếu còn hạn
9) Một lưu ý nhỏ
Nếu access_users của bro đang là:

chỉ lưu 1 record/user
thì hàm renew hiện tại là ổn.
Nếu bro muốn lưu lịch sử từng lần mua thì mình sẽ tách thêm bảng access_history.

10) Nếu muốn, mình làm tiếp cho bro phần cuối:
ghép thêm trang “lịch sử quyền / lịch sử gia hạn”
để xem:

ai mua
mua lúc nào
gia hạn bao nhiêu lần
còn hạn đến ngày nào
Chỉ cần nhắn:
“ghép tiếp lịch sử quyền + gia hạn”
là mình ráp tiếp cho bro ngay.

