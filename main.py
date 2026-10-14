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

# Токен берется из настроек Render (Environment Variables)
TOKEN = os.getenv("TOKEN")

router = Router()


# Состояния для воронки
class BotStates(StatesGroup):
  choosing_game = State()
  choosing_prize = State()
  waiting_for_screenshot = State()
  checking_subs = State()


# 1. Команда /start
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
  text = (
      "✨ **Что умеет этот бот?**\n\n"
      "✦ В этом боте вы можете получить звёзды или другие бонусы на выбор.\n\n"
      "✦ Нажмите кнопку ниже, чтобы испытать удачу!"
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
  await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
  await state.set_state(BotStates.choosing_game)


# 2. Выбор игры
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
              InlineKeyboardButton(
                  text="🎁 Бонус А", callback_data="prize_a"
              ),
              InlineKeyboardButton(
                  text="⭐ Звёзды", callback_data="prize_stars"
              ),
          ]
      ]
  )
  await callback.message.answer(
      "🎉 **Поздравляю! Вы попали!**\n\nВыберите, какой приз хотите получить 👇",
      reply_markup=keyboard,
      parse_mode="Markdown",
  )
  await state.set_state(BotStates.choosing_prize)


# 3. Выбор приза
@router.callback_query(
    BotStates.choosing_prize, F.data.startswith("prize_")
)
async def process_prize(callback: CallbackQuery, state: FSMContext):
  text = (
      "Чтобы забрать приз:\n\n"
      "1. Оставьте комментарий под нашим видео.\n"
      "2. Отправьте **1 скриншот** подтверждения боту 📸"
  )
  await callback.message.edit_text(text)
  await state.set_state(BotStates.waiting_for_screenshot)


# 4. Получение скриншота
@router.message(BotStates.waiting_for_screenshot, F.photo)
async def process_screenshot(message: Message, state: FSMContext):
  await message.answer("✅ **Все изображения приняты!**\n\nПодбираю задания...")
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
                  text="✅ Проверить подписку", callback_data="check_subs"
              )
          ],
      ]
  )
  await message.answer(
      "📢 **Подпишитесь на каналы спонсоров.**\n\n"
      "После подписки нажмите кнопку «Проверить» 👇",
      reply_markup=keyboard,
      parse_mode="Markdown",
  )
  await state.set_state(BotStates.checking_subs)


@router.callback_query(BotStates.checking_subs, F.data == "check_subs")
async def final_check(callback: CallbackQuery):
  await callback.answer(
      "✅ Подписка подтверждена!",
      show_alert=True,
  )


# Запуск простейшего веб-сервера для Render (чтобы Web Service не падал)
def run_web_server():
  port = int(os.environ.get("PORT", 10000))
  handler = http.server.SimpleHTTPRequestHandler
  with http.server.HTTPServer(("", port), handler) as httpd:
    httpd.serve_forever()


async def main():
  # Запускаем веб-сервер в отдельном потоке
  server_thread = threading.Thread(target=run_web_server, daemon=True)
  server_thread.start()

  bot = Bot(token=TOKEN)
  dp = Dispatcher()
  dp.include_router(router)
  await dp.start_polling(bot)


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  asyncio.run(main())

