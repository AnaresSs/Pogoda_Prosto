from aiogram.fsm.state import State, StatesGroup



class Registration(StatesGroup):
    waiting_for_locality = State()


class Mailing(StatesGroup):
    waiting_for_message = State()
    waiting_for_audience = State()


