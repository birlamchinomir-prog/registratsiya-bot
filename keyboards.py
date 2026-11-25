from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def phone_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )

def video_experience_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Ha, oldin tushganman"), KeyboardButton(text="❌ Yo'q, tushmaganman")],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )

def skip_or_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏭ O'tkazib yuborish")],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )

def main_menu_keyboard(is_registered: bool = False, is_admin: bool = False):
    buttons = []
    if is_registered:
        buttons.append([KeyboardButton(text="👤 Mening profilim"), KeyboardButton(text="✏️ Qayta ro'yxatdan o'tish")])
    else:
        buttons.append([KeyboardButton(text="📝 Ro'yxatdan o'tish")])

    if is_admin:
        buttons.append([KeyboardButton(text="⚙️ Admin Panel")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def admin_panel_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"),
                InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin_users_1")
            ],
            [
                InlineKeyboardButton(text="📢 Hammaga xabar yuborish", callback_data="admin_broadcast")
            ],
            [
                InlineKeyboardButton(text="❌ Yopish", callback_data="admin_close")
            ]
        ]
    )

def profile_decision_keyboard(user_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"adm_app_{user_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"adm_rej_{user_id}")
            ]
        ]
    )

