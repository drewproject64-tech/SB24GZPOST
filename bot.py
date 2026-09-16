import asyncio
import html
import logging
import os

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is required")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("sb24gz_posts")
router = Router()


class PostState(StatesGroup):
    waiting_for_post = State()


POSTS = [
    {
        "title": "SB24GZ Update",
        "body": "Welcome to the SB24GZ clear-posts feed. Posts and announcements are displayed directly inside Telegram.",
    }
]


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📌 Clear Posts", callback_data="clear_posts")],
            [InlineKeyboardButton(text="📰 Latest Post", callback_data="latest_post")],
            [InlineKeyboardButton(text="✍️ Create Post", callback_data="create_post")],
            [InlineKeyboardButton(text="ℹ️ Help", callback_data="help")],
        ]
    )


def back_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="↩️ Main Menu", callback_data="main_menu")]]
    )


def retry_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Try Again", callback_data="create_post")],
            [InlineKeyboardButton(text="↩️ Main Menu", callback_data="main_menu")],
        ]
    )


WELCOME = (
    "<b>SB24GZ – ប៉ុស្តិ៍​ច្បាស់ៗ</b>\n\n"
    "A Telegram-native space for clear posts and announcements.\n\n"
    "📌 <b>Clear Posts</b> — browse available posts.\n"
    "📰 <b>Latest Post</b> — read the newest post.\n"
    "✍️ <b>Create Post</b> — clean and format your text.\n\n"
    "Everything happens directly inside Telegram."
)

HELP_TEXT = (
    "<b>SB24GZ – ប៉ុស្តិ៍​ច្បាស់ៗ</b>\n\n"
    "Use the bot to view clear posts and announcements or prepare your own text as a readable post.\n\n"
    "📌 Clear Posts\n"
    "📰 Latest Post\n"
    "✍️ Create Post\n\n"
    "Use /start at any time to return to the main menu."
)


def format_post(post: dict) -> str:
    return (
        f"<b>📌 {html.escape(post['title'])}</b>\n\n"
        f"{html.escape(post['body'])}"
    )


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(WELCOME, reply_markup=main_menu())


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=main_menu())


@router.callback_query(F.data == "main_menu")
async def main_menu_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(WELCOME, reply_markup=main_menu())


@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(HELP_TEXT, reply_markup=back_menu())


@router.callback_query(F.data == "clear_posts")
async def clear_posts_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        content = "<b>📌 Clear Posts</b>\n\n" + "\n\n".join(
            format_post(post) for post in POSTS
        )
        await callback.message.edit_text(content, reply_markup=back_menu())


@router.callback_query(F.data == "latest_post")
async def latest_post_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(
            "<b>📰 Latest Post</b>\n\n" + format_post(POSTS[-1]),
            reply_markup=back_menu(),
        )


@router.callback_query(F.data == "create_post")
async def create_post_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(PostState.waiting_for_post)
    if callback.message:
        await callback.message.edit_text(
            "<b>✍️ Create Post</b>\n\n"
            "Send your text and the bot will clean spacing and return a readable post.\n\n"
            "Maximum: 3,000 characters. Send /start to cancel.",
            reply_markup=back_menu(),
        )


@router.message(PostState.waiting_for_post, F.text)
async def receive_post(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("Please send some text.", reply_markup=retry_menu())
        return

    if len(text) > 3000:
        await message.answer(
            "That post is too long. Please keep it under 3,000 characters.",
            reply_markup=retry_menu(),
        )
        return

    cleaned = " ".join(line.strip() for line in text.splitlines() if line.strip())
    cleaned = " ".join(cleaned.split())
    safe = html.escape(cleaned)

    await state.clear()
    await message.answer(
        "<b>✅ Post prepared</b>\n\n"
        f"<blockquote>{safe}</blockquote>",
        reply_markup=main_menu(),
    )


@router.message(PostState.waiting_for_post)
async def reject_non_text(message: Message) -> None:
    await message.answer(
        "Please send a text message for the post.",
        reply_markup=retry_menu(),
    )


async def main() -> None:
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(router)

    logger.info("Starting SB24GZ clear posts bot")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("SB24GZ clear posts bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
