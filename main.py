import asyncio
import http.server
import logging
import os
import threading
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# Твой токен от BotFather
TOKEN = "ТВОЙ_ТОКЕН_ОТ_БОТФАТЕРА"

router = Router()


# Состояния воронки
class BotStates(StatesGroup):
  choosing_game = State()
  choosing_prize = State()
  task_one = State()
  task_two = State()
  checking_subs = State()


# 1. Стартовое сообщение (/start)
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
  text = (
      "Что умеет этот бот?\n\n"
      "✦ В этом боте вы можете получить звёзды или NFT на выбор.\n\n"
      "✦ Нажмите /start и следуйте инструкциям, которые отправит бот."
  )
  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="⚽ Удар по воротам", callback_data="game_football"
              ),
              InlineKeyboardButton(
                  text="🏀 Бросок в кольцо", callback_data="game_basketball"
              ),
          ]
      ]
  )
  await message.answer(text, reply_markup=keyboard)
  await state.set_state(BotStates.choosing_game)


# 2. Игра (Кубик/Мяч)
@router.callback_query(
    BotStates.choosing_game, F.data.startswith("game_")
)
async def process_game(callback: CallbackQuery, state: FSMContext):
  await callback.message.delete()
  dice_emoji = "⚽" if "football" in callback.data else "🏀"
  await callback.message.answer_dice(emoji=dice_emoji)
  await asyncio.sleep(4)

  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(text="🎁 NFT", callback_data="prize_nft"),
              InlineKeyboardButton(
                  text="⭐ Звёзды", callback_data="prize_stars"
              ),
          ]
      ]
  )
  await callback.message.answer(
      "Поздравляю! Вы попали!\n\nВыберите, какой приз хотите получить 👇",
      reply_markup=keyboard,
  )
  await state.set_state(BotStates.choosing_prize)


# 3. Выбор приза -> Показываем кнопку «Посмотреть NFT» и Задание 1
@router.callback_query(
    BotStates.choosing_prize, F.data.startswith("prize_")
)
async def process_prize(callback: CallbackQuery, state: FSMContext):
  # Кнопка для просмотра NFT по твоей ссылке
  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="Посмотреть NFT",
                  url="https://t.me/nft/StellarRocket-131674",
              )
          ]
      ]
  )

  await callback.message.answer(
      "Вам выпал нфт, который вы можете посмотреть по кнопке Посмотреть НФТ",
      reply_markup=keyboard,
  )

  text = (
      "Чтобы забрать приз:\n"
      "1. ❤️ Лайк на комментарий, с которого узнали о боте\n"
      "2. 💬 Ответьте на этот комментарий: «рил сработала офигеть»\n\n"
      "📸 Отправьте 1 скриншот боту выполненного задания"
  )
  await callback.message.answer(text)
  await state.set_state(BotStates.task_one)


# Получение 1-го скриншота -> Переход к Заданию 2
@router.message(BotStates.task_one, F.photo)
async def process_first_screenshot(message: Message, state: FSMContext):
  text = (
      "Задание 2\n\n"
      "Оставьте 5 комментариев под видео о подарках или звёздах в TikTok.\n"
      "Текст: `@bypobot спс за NFT`\n\n"
      "❤️ Поставьте лайк каждому комментарию.\n"
      "📸 Отправьте боту 5 скриншотов."
  )
  await message.answer(text)
  await state.set_state(BotStates.task_two)


# Получение скриншотов задания 2 -> Финальный этап со спонсорами
@router.message(BotStates.task_two, F.photo)
async def process_second_screenshots(message: Message, state: FSMContext):
  await message.answer("Все изображения приняты!\nПодбираю задания...")
  await asyncio.sleep(2)

  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="📢 Подписаться на канал", url="https://t.me/durov"
              )
          ],
          [
              InlineKeyboardButton(
                  text="✅ Проверить", callback_data="check_subs"
              )
          ],
      ]
  )
  await message.answer(
      "Отлично! Осталось выполнить задания спонсоров.\n\n"
      "После подписки нажмите кнопку\n✅ Проверить",
      reply_markup=keyboard,
  )
  await state.set_state(BotStates.checking_subs)


@router.callback_query(BotStates.checking_subs, F.data == "check_subs")
async def final_check(callback: CallbackQuery):
  await callback.answer(
      "✅ Подписка проверена!",
      show_alert=True,
  )


# Веб-сервер для удержания Render
def run_web_server():
  port = int(os.environ.get("PORT", 10000))
  handler = http.server.SimpleHTTPRequestHandler
  with http.server.HTTPServer(("", port), handler) as httpd:
    httpd.serve_forever()


async def main():
  server_thread = threading.Thread(target=run_web_server, daemon=True)
  server_thread.start()

  bot = Bot(token=TOKEN)
  dp = Dispatcher()
  dp.include_router(router)
  await dp.start_polling(bot)


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  asyncio.run(main())
