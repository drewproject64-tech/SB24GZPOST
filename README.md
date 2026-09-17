# SB24GZ – ប៉ុស្តិ៍​ច្បាស់ៗ

A Telegram-native clear posts and announcements bot.

## Bot identity
- Name: SB24GZ – ប៉ុស្តិ៍​ច្បាស់ៗ
- Username: @SB24GZ_PostBot
- Purpose: Clear posts, announcements, and text drafting inside Telegram

## Core functions
1. Clear Posts — browse built-in general posts.
2. Latest Post — read the newest built-in post.
3. Create Post — prepare and clean a text draft inside Telegram.

## Commands
- /start — open the main menu
- /help — show help
- /cancel — cancel a draft

## Safety and destination behavior
- No external websites or redirect buttons.
- No gambling or betting content is included in the built-in feed.
- User drafts containing common gambling/betting terms are rejected.
- Create Post prepares a draft only; it does not redirect users elsewhere.
- The bot responds through Telegram on mobile and desktop.

## Environment
Set `BOT_TOKEN` in the deployment environment. Never commit the real token.

## Run
```bash
python bot.py
```
