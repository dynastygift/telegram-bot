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

# Твой новый токен
TOKEN = "8654427408:AAG_vGFYQJ2ozaBhJ4FPCEL3Cgd-ajdJB6g"

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
      "Испытайте удачу!\n\n"
      ">Выберите, бросите мяч в кольцо или дротик в цель чтобы получить приз 🏀🎯"
  )
  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🏀 Бросок в кольцо", callback_data="game_basketball"
              ),
              InlineKeyboardButton(
                  text="🎯 Бросок в цель", callback_data="game_darts"
              ),
          ]
      ]
  )
  await message.answer_photo(
      photo="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe",
      caption=text,
      reply_markup=keyboard,
      parse_mode="Markdown",
  )
  await state.set_state(BotStates.choosing_game)


# 2. Игра (Бросок)
@router.callback_query(
    BotStates.choosing_game, F.data.startswith("game_")
)
async def process_game(callback: CallbackQuery, state: FSMContext):
  await callback.message.delete()
  dice_emoji = "🏀" if "basketball" in callback.data else "🎯"
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

  text = (
      "К сожалению, вы промахнулись\n\n"
      ">Но мы всё равно можем выдать вам приз за простое задание! "
      "Выберите, что хотите получить"
  )
  await callback.message.answer_photo(
      photo="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe",
      caption=text,
      reply_markup=keyboard,
      parse_mode="Markdown",
  )
  await state.set_state(BotStates.choosing_prize)


# 3. Выбор приза -> Задание 1 (1 скриншот)
@router.callback_query(
    BotStates.choosing_prize, F.data.startswith("prize_")
)
async def process_prize(callback: CallbackQuery, state: FSMContext):
  await callback.message.delete()

  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="🔍 Посмотреть NFT",
                  url="https://t.me/nft/StellarRocket-131674",
              )
          ],
          [InlineKeyboardButton(text="🔄 Перекрутить", callback_data="reroll")],
      ]
  )

  text = (
      "Вам выпал нфт, который вы можете посмотреть по кнопке Посмотреть НФТ\n\n"
      ">Для получения необходимо поставить лайк на комментарий из TikTok, "
      "с моим юзом с которого узнали обо мне и написать в ответ на него "
      "«всё прошло легко»\n\n"
      "Отправьте боту 1 скриншот боту"
  )
  await callback.message.answer_photo(
      photo="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe",
      caption=text,
      reply_markup=keyboard,
      parse_mode="Markdown",
  )
  await state.set_state(BotStates.task_one)


# 4. Получение 1-го скриншота -> Задание 2 (10 скриншотов)
@router.message(BotStates.task_one, F.photo)
async def process_first_screenshot(message: Message, state: FSMContext):
  text = (
      "Отлично вы справились с первым заданием\n\n"
      "Вам надо написать 10 комментариев под любые видео из TikTok "
      "с текстом лайкая свои комментарии:\n\n"
      ">Найдите подходящие видео через поиск «тг подарки» или «тг звезды» "
      "и выберите любые ролики.\n\n"
      "Текст комментария:\n"
      ">@ovapobo спс за колечко 💍\n\n"
      "после чего необходимо отправить ровно 10 скриншотов боту"
  )
  await message.answer_photo(
      photo="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe",
      caption=text,
      parse_mode="Markdown",
  )
  await state.update_data(screenshots_count=0)
  await state.set_state(BotStates.task_two)


# 5. Сбор 10 скриншотов по одному
@router.message(BotStates.task_two, F.photo)
async def collect_ten_screenshots(message: Message, state: FSMContext):
  data = await state.get_data()
  count = data.get("screenshots_count", 0) + 1
  await state.update_data(screenshots_count=count)

  remaining = 10 - count

  if count < 10:
    await message.answer(
        f"Принято {count} из 10 скриншотов. Осталось: {remaining}."
    )
  else:
    await message.answer(
        "✅ Все 10 изображений приняты!\nПодбираю задания..."
    )
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
  await callback.answer("✅ Подписка проверена!", show_alert=True)


# Веб-сервер для удержания Render (Free Web Service)
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
