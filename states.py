from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    waiting_for_first_name = State()
    waiting_for_last_name = State()
    waiting_for_age = State()
    waiting_for_phone = State()
    waiting_for_profession = State()
    waiting_for_photo = State()
    waiting_for_bio = State()
    waiting_for_confirmation = State()

class AdminStates(StatesGroup):
    waiting_for_broadcast_msg = State()
    waiting_for_rejection_reason = State()

