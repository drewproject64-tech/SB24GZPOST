import asyncio
import html
import logging
import os
import re

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BotCommand, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is required")

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("sb24gz_posts")
router = Router()


class PostState(StatesGroup):
    waiting_for_post = State()


# Keep the promoted destination focused on general posts and announcements.
# User drafts containing common gambling/betting terms are rejected before display.
BLOCKED_TERMS = (
    "casino", "casinos", "sports betting", "sportsbook", "betting", "bet", "bets",
    "odds", "lottery", "lotteries", "bingo", "picks", "sports picks", "wager",
    "wagering", "gambling", "jackpot", "poker", "roulette", "blackjack",
    "slot machine", "slots", "fantasy sports", "tipster", "bookmaker", "bookie",
)

POSTS = [
    {
        "title": "SB24GZ Update",
        "body": "Welcome to the SB24GZ clear-posts feed. Posts and announcements are displayed directly inside Telegram.",
    },
    {
        "title": "How It Works",
        "body": "Use Clear Posts to browse the feed, Latest Post to read the newest item, or Create Post to prepare clean text directly in Telegram.",
    },
]


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📌 Clear Posts", callback_data="clear_posts")],
        [InlineKeyboardButton(text="📰 Latest Post", callback_data="latest_post")],
        [InlineKeyboardButton(text="✍️ Create Post", callback_data="create_post")],
        [InlineKeyboardButton(text="ℹ️ Help", callback_data="help")],
    ])


def back_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Main Menu", callback_data="main_menu")]
    ])


def retry_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Try Again", callback_data="create_post")],
        [InlineKeyboardButton(text="↩️ Main Menu", callback_data="main_menu")],
    ])


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
    "This bot provides a simple Telegram-native post reader and text preparation tool.\n\n"
    "📌 Clear Posts\n"
    "📰 Latest Post\n"
    "✍️ Create Post\n\n"
    "Create Post only prepares text inside Telegram; it does not publish to an external website.\n\n"
    "Use /start to return to the main menu or /cancel to stop a draft."
)


def format_post(post: dict) -> str:
    return f"<b>📌 {html.escape(post['title'])}</b>\n\n{html.escape(post['body'])}"


def contains_blocked_content(text: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    return any(re.search(rf"\b{re.escape(term)}\b", normalized) for term in BLOCKED_TERMS)


def clean_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " ".join(" ".join(lines).split())


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(WELCOME, reply_markup=main_menu())


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=main_menu())


@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Draft cancelled. Choose an option below.", reply_markup=main_menu())


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
        content = "<b>📌 Clear Posts</b>\n\n" + "\n\n".join(format_post(post) for post in POSTS)
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
            "Send text and the bot will clean extra spacing and return a readable draft.\n\n"
            "Maximum: 3,000 characters. Use /cancel to stop.",
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
            "That draft is too long. Please keep it under 3,000 characters.",
            reply_markup=retry_menu(),
        )
        return

    if contains_blocked_content(text):
        await state.clear()
        await message.answer(
            "This bot only supports general posts and announcements. Please remove restricted gambling or betting content.",
            reply_markup=main_menu(),
        )
        return

    cleaned = clean_text(text)
    safe = html.escape(cleaned)

    await state.clear()
    await message.answer(
        "<b>✅ Post prepared</b>\n\n"
        f"<blockquote>{safe}</blockquote>\n\n"
        "This is a draft prepared inside Telegram.",
        reply_markup=main_menu(),
    )


@router.message(PostState.waiting_for_post)
async def reject_non_text(message: Message) -> None:
    await message.answer("Please send a text message for the draft.", reply_markup=retry_menu())


async def configure_commands(bot: Bot) -> None:
    await bot.set_my_commands([
        BotCommand(command="start", description="Open the main menu"),
        BotCommand(command="help", description="Show help"),
        BotCommand(command="cancel", description="Cancel a draft"),
    ])


async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)

    logger.info("Starting SB24GZ clear posts bot")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await configure_commands(bot)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("SB24GZ clear posts bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
