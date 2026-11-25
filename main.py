import os
import re
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

import database
from states import RegistrationStates, AdminStates
from keyboards import (
    phone_keyboard,
    cancel_keyboard,
    video_experience_keyboard,
    skip_or_cancel_keyboard,
    main_menu_keyboard,
    admin_panel_keyboard,
    profile_decision_keyboard
)

# Muhit o'zgaruvchilari
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID_RAW = os.getenv("ADMIN_ID", "8245940482").strip()
try:
    ADMIN_ID = int(ADMIN_ID_RAW)
except ValueError:
    ADMIN_ID = 0

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN) if BOT_TOKEN and BOT_TOKEN != "YOUR_BOT_TOKEN_HERE" else None
dp = Dispatcher(storage=MemoryStorage())

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

# --- UMUMIY / BEKOR QILISH HANDLERLARI ---
@dp.message(F.text == "❌ Bekor qilish")
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        user = await database.get_user(message.from_user.id)
        await message.answer("Asosiy menyu:", reply_markup=main_menu_keyboard(bool(user), is_admin(message.from_user.id)))
        return
    
    await state.clear()
    user = await database.get_user(message.from_user.id)
    await message.answer("Jarayon bekor qilindi.", reply_markup=main_menu_keyboard(bool(user), is_admin(message.from_user.id)))

# --- START BUYRUG'I ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user = await database.get_user(message.from_user.id)
    admin_status = is_admin(message.from_user.id)
    
    if user:
        status_icons = {"approved": "✅ Tasdiqlangan", "pending": "⏳ Ko'rib chiqilmoqda", "rejected": "❌ Rad etilgan"}
        st_text = status_icons.get(user['status'], user['status'])
        text = (
            f"Assalomu alaykum, <b>{user['first_name']}</b>!\n\n"
            f"Siz avval ro'yxatdan o'tgansiz.\n"
            f"Holatingiz: <b>{st_text}</b>\n\n"
            f"Profilingizni ko'rish yoki yangilash uchun quyidagi tugmalardan foydalaning:"
        )
        await message.answer(text, reply_markup=main_menu_keyboard(True, admin_status), parse_mode="HTML")
    else:
        text = (
            f"Assalomu alaykum, <b>{message.from_user.first_name}</b>!\n\n"
            f"Ushbu bot orqali rasmiy ro'yxatdan o'tishingiz mumkin.\n"
            f"Ro'yxatdan o'tish uchun quyidagi <b>📝 Ro'yxatdan o'tish</b> tugmasini bosing."
        )
        await message.answer(text, reply_markup=main_menu_keyboard(False, admin_status), parse_mode="HTML")

# --- RO'YXATDAN O'TISHNI BOSHLASH ---
@dp.message(F.text.in_(["📝 Ro'yxatdan o'tish", "✏️ Qayta ro'yxatdan o'tish"]))
async def start_registration(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(RegistrationStates.waiting_for_first_name)
    await message.answer("Iltimos, <b>Ismingizni</b> kiriting:", reply_markup=cancel_keyboard(), parse_mode="HTML")

# 1. ISM
@dp.message(RegistrationStates.waiting_for_first_name, F.text)
async def process_first_name(message: types.Message, state: FSMContext):
    first_name = message.text.strip()
    if len(first_name) < 2 or len(first_name) > 50:
        await message.answer("Iltimos, haqiqiy ismingizni kiriting (2 tadan 50 tagacha belgi):")
        return
    await state.update_data(first_name=first_name)
    await state.set_state(RegistrationStates.waiting_for_last_name)
    await message.answer("Rahmat! Endi <b>Familiyangizni</b> kiriting:", reply_markup=cancel_keyboard(), parse_mode="HTML")

# 2. FAMILIYA
@dp.message(RegistrationStates.waiting_for_last_name, F.text)
async def process_last_name(message: types.Message, state: FSMContext):
    last_name = message.text.strip()
    if len(last_name) < 2 or len(last_name) > 50:
        await message.answer("Iltimos, haqiqiy familiyangizni kiriting (2 tadan 50 tagacha belgi):")
        return
    await state.update_data(last_name=last_name)
    await state.set_state(RegistrationStates.waiting_for_age)
    await message.answer("Yoshingizni kiriting (Masalan: <b>22</b>):", reply_markup=cancel_keyboard(), parse_mode="HTML")

# 3. YOSH
@dp.message(RegistrationStates.waiting_for_age, F.text)
async def process_age(message: types.Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("Iltimos, yoshingizni faqat raqamda kiriting (Masalan: 20):")
        return
    age = int(message.text.strip())
    if age < 7 or age > 100:
        await message.answer("Iltimos, to'g'ri yosh kiriting (7 dan 100 gacha):")
        return
    await state.update_data(age=age)
    await state.set_state(RegistrationStates.waiting_for_phone)
    await message.answer(
        "Telefon raqamingizni yuboring.\nQuyidagi <b>📱 Telefon raqamni yuborish</b> tugmasini bosing yoki qo'lda yozing (+998901234567):",
        reply_markup=phone_keyboard(),
        parse_mode="HTML"
    )

# 4. TELEFON
@dp.message(RegistrationStates.waiting_for_phone, F.contact)
async def process_phone_contact(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    await state.update_data(phone=phone)
    await state.set_state(RegistrationStates.waiting_for_profession)
    await message.answer("Oldin videoga tushganmisiz?", reply_markup=video_experience_keyboard())

@dp.message(RegistrationStates.waiting_for_phone, F.text)
async def process_phone_text(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    if not re.match(r'^\+?[0-9]{9,15}$', cleaned):
        await message.answer("Iltimos, telefon raqamingizni to'g'ri formatda kiriting (Masalan: +998901234567) yoki pastdagi tugmani bosing:")
        return
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned
    await state.update_data(phone=cleaned)
    await state.set_state(RegistrationStates.waiting_for_profession)
    await message.answer("Oldin videoga tushganmisiz?", reply_markup=video_experience_keyboard())

# 5. KASB
@dp.message(RegistrationStates.waiting_for_profession, F.text)
async def process_profession(message: types.Message, state: FSMContext):
    profession = message.text.strip()
    await state.update_data(profession=profession)
    await state.set_state(RegistrationStates.waiting_for_photo)
    await message.answer("Endi o'zingizning aniq, sifatli <b>Fotosuratingizni</b> yuboring:", reply_markup=cancel_keyboard(), parse_mode="HTML")

# 6. RASM
@dp.message(RegistrationStates.waiting_for_photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    await state.set_state(RegistrationStates.waiting_for_bio)
    await message.answer(
        "O'zingiz haqingizda qo'shimcha ma'lumot (bio/qiziqishlaringiz) yozing:\n"
        "<i>(Xohlamasangiz 'O'tkazib yuborish' tugmasini bosishingiz mumkin)</i>",
        reply_markup=skip_or_cancel_keyboard(),
        parse_mode="HTML"
    )

@dp.message(RegistrationStates.waiting_for_photo)
async def process_photo_invalid(message: types.Message):
    await message.answer("Iltimos, fotosurat yuboring!")

# 7. QO'SHIMCHA MA'LUMOT (BIO) VA YAKUNLASH
@dp.message(RegistrationStates.waiting_for_bio, F.text)
async def process_bio(message: types.Message, state: FSMContext):
    bio_text = message.text.strip()
    if bio_text == "⏭ O'tkazib yuborish":
        bio_text = "Mavjud emas"

    data = await state.get_data()
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
    
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    age = data.get("age")
    phone = data.get("phone")
    profession = data.get("profession")
    photo_id = data.get("photo_id")

    # Bazaga yozish
    await database.add_or_update_user(
        user_id=user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        age=age,
        phone=phone,
        profession=profession,
        photo_id=photo_id,
        bio=bio_text
    )

    await state.clear()

    # Foydalanuvchiga profili ko'rinishi
    caption = (
        f"🎉 <b>Arizangiz muvaffaqiyatli qabul qilindi!</b>\n\n"
        f"👤 <b>Ism:</b> {first_name} {last_name}\n"
        f"🎂 <b>Yosh:</b> {age}\n"
        f"📱 <b>Telefon:</b> {phone}\n"
        f"🎬 <b>Videoga tushganmisiz:</b> {profession}\n"
        f"💬 <b>Haqida:</b> {bio_text}\n"
        f"📌 <b>Holat:</b> ⏳ Ko'rib chiqilmoqda\n\n"
        f"<i>Tez orada admin arizangizni ko'rib chiqib, tasdiqlaydi.</i>"
    )

    await message.answer_photo(
        photo=photo_id,
        caption=caption,
        reply_markup=main_menu_keyboard(True, is_admin(user_id)),
        parse_mode="HTML"
    )

    # Adminga xabar va tugmalar yuborish
    if ADMIN_ID and ADMIN_ID != user_id:
        try:
            admin_caption = (
                f"🆕 <b>Yangi ariza kelib tushdi!</b>\n\n"
                f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
                f"👤 <b>Foydalanuvchi:</b> {username}\n"
                f"📛 <b>Ism Familiya:</b> {first_name} {last_name}\n"
                f"🎂 <b>Yoshi:</b> {age}\n"
                f"📱 <b>Tel:</b> {phone}\n"
                f"🎬 <b>Videoga tushganmi:</b> {profession}\n"
                f"📝 <b>Bio:</b> {bio_text}"
            )
            await message.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=photo_id,
                caption=admin_caption,
                reply_markup=profile_decision_keyboard(user_id),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Adminga yuborishda xatolik: {e}")

# --- PROFILNI KO'RISH ---
@dp.message(F.text == "👤 Mening profilim")
async def show_my_profile(message: types.Message):
    user = await database.get_user(message.from_user.id)
    if not user:
        await message.answer("Siz hali ro'yxatdan o'tmagansiz.", reply_markup=main_menu_keyboard(False, is_admin(message.from_user.id)))
        return
    
    status_icons = {"approved": "✅ Tasdiqlangan", "pending": "⏳ Ko'rib chiqilmoqda", "rejected": "❌ Rad etilgan"}
    st_text = status_icons.get(user['status'], user['status'])
    caption = (
        f"👤 <b>Sizning profilingiz:</b>\n\n"
        f"📛 <b>Ism:</b> {user['first_name']} {user['last_name']}\n"
        f"🎂 <b>Yosh:</b> {user['age']}\n"
        f"📱 <b>Telefon:</b> {user['phone']}\n"
        f"🎬 <b>Videoga tushganmisiz:</b> {user['profession']}\n"
        f"📝 <b>Haqida:</b> {user['bio']}\n"
        f"📌 <b>Holat:</b> <b>{st_text}</b>"
    )

    if user['photo_id']:
        await message.answer_photo(photo=user['photo_id'], caption=caption, parse_mode="HTML")
    else:
        await message.answer(caption, parse_mode="HTML")

# --- ADMIN PANEL ---
@dp.message(F.text == "⚙️ Admin Panel")
async def admin_panel_handler(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("Sizda admin huquqi yo'q!")
        return
    stats = await database.get_stats()
    text = (
        f"👑 <b>Admin Boshqaruv Paneli</b>\n\n"
        f"👥 Jami arizalar: <b>{stats['total']}</b>\n"
        f"✅ Tasdiqlangan: <b>{stats['approved']}</b>\n"
        f"⏳ Ko'rib chiqilmoqda: <b>{stats['pending']}</b>\n"
        f"❌ Rad etilgan: <b>{stats['rejected']}</b>\n\n"
        f"Kerakli bo'limni tanlang:"
    )
    await message.answer(text, reply_markup=admin_panel_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data == "admin_stats")
async def callback_admin_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return
    stats = await database.get_stats()
    text = (
        f"📊 <b>Batafsil Statistika</b>\n\n"
        f"👥 Jami ro'yxatdan o'tganlar: <b>{stats['total']}</b> ta\n"
        f"✅ Tasdiqlanganlar: <b>{stats['approved']}</b> ta\n"
        f"⏳ Kutilayotganlar: <b>{stats['pending']}</b> ta\n"
        f"❌ Rad etilganlar: <b>{stats['rejected']}</b> ta"
    )
    await callback.message.edit_text(text, reply_markup=admin_panel_keyboard(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_users_"))
async def callback_admin_users(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return
    
    users = await database.get_all_users()
    if not users:
        await callback.answer("Hozircha foydalanuvchilar mavjud emas.", show_alert=True)
        return
    
    page = int(callback.data.split("_")[2])
    per_page = 5
    total_pages = (len(users) + per_page - 1) // per_page
    page = max(1, min(page, total_pages))

    start = (page - 1) * per_page
    end = start + per_page
    current_users = users[start:end]

    text = f"👥 <b>Foydalanuvchilar ro'yxati (Sahifa {page}/{total_pages}):</b>\n\n"
    for i, u in enumerate(current_users, start=start+1):
        st_icon = "✅" if u['status'] == 'approved' else ("⏳" if u['status'] == 'pending' else "❌")
        text += f"{i}. {st_icon} <b>{u['first_name']} {u['last_name']}</b> (Video: {u['profession']})\n"
        text += f"   📱 {u['phone']} | ID: <code>{u['user_id']}</code>\n"

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"admin_users_{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"admin_users_{page+1}"))

    keyboard = []
    if nav_buttons:
        keyboard.append(nav_buttons)
    keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_stats")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "admin_close")
async def callback_admin_close(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer("Admin panel yopildi.")

# --- ADMIN TASDIQLASH VA RAD ETISH ---
@dp.callback_query(F.data.startswith("adm_app_"))
async def approve_user(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return
    target_user_id = int(callback.data.replace("adm_app_", ""))
    await database.set_user_status(target_user_id, "approved")
    
    await callback.message.edit_caption(
        caption=f"{callback.message.caption}\n\n✅ <b>ADMIN TOMONIDAN TASDIQLANDI!</b>",
        parse_mode="HTML"
    )
    await callback.answer("Profil tasdiqlandi!")

    try:
        await callback.bot.send_message(
            chat_id=target_user_id,
            text="🎉 <b>Xushxabar!</b>\nSizning profilingiz admin tomonidan muvaffaqiyatli <b>tasdiqlandi</b>! ✅",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Foydalanuvchiga tasdiq xabarini yuborib bo'lmadi: {e}")

@dp.callback_query(F.data.startswith("adm_rej_"))
async def reject_user(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return
    target_user_id = int(callback.data.replace("adm_rej_", ""))
    await database.set_user_status(target_user_id, "rejected")

    await callback.message.edit_caption(
        caption=f"{callback.message.caption}\n\n❌ <b>ADMIN TOMONIDAN RAD ETILDI!</b>",
        parse_mode="HTML"
    )
    await callback.answer("Profil rad etildi!")

    try:
        await callback.bot.send_message(
            chat_id=target_user_id,
            text="⚠️ <b>Afsuski</b>, sizning arizangiz admin tomonidan rad etildi.\nMa'lumotlarni tekshirib, qayta ro'yxatdan o'tishingiz mumkin.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Foydalanuvchiga rad xabarini yuborib bo'lmadi: {e}")

# --- HAMMAGA XABAR YUBORISH (BROADCAST) ---
@dp.callback_query(F.data == "admin_broadcast")
async def start_broadcast(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_for_broadcast_msg)
    await callback.message.answer("Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yozing (yoki '❌ Bekor qilish' deb yozing):")
    await callback.answer()

@dp.message(AdminStates.waiting_for_broadcast_msg)
async def process_broadcast_message(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    
    users = await database.get_all_users()
    count = 0
    progress_msg = await message.answer(f"Xabar yuborilmoqda: 0/{len(users)}...")
    
    for u in users:
        try:
            await message.send_copy(chat_id=u['user_id'])
            count += 1
        except Exception:
            pass

    await progress_msg.edit_text(f"✅ Xabar muvaffaqiyatli tarqatildi: <b>{count}/{len(users)}</b> ta foydalanuvchiga yetkazildi.", parse_mode="HTML")

from aiohttp import web

async def start_health_check_server():
    port = int(os.getenv("PORT", 8080))
    app = web.Application()
    async def handle_ping(request):
        return web.Response(text="Bot is running!")
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Render health-check server {port}-portda ishga tushdi")

# --- ASOSIY ISHGA TUSHIRISH ---
async def main():
    await database.init_db()
    logger.info("Ma'lumotlar bazasi tayyorlandi.")
    
    if not bot:
        logger.error("BOT_TOKEN aniqlanmadi! .env fayliga BOT_TOKEN ni kiriting.")
        print("\n" + "="*50)
        print("DIQQAT: .env faylida BOT_TOKEN topilmadi!")
        print("Iltimos, .env faylini oching va bot tokeningizni kiriting.")
        print("="*50 + "\n")
        return

    logger.info("Bot ishga tushmoqda...")
    try:
        await start_health_check_server()
    except Exception as e:
        logger.warning(f"Health-check server ishga tushmadi: {e}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
