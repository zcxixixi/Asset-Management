import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime

from telegram import Bot
from telegram.constants import ParseMode


def load_data(filepath: str) -> dict:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading data from {filepath}: {e}")
        return {}


def format_message(time_of_day: str, data: dict) -> str:
    total_balance = data.get("total_balance", "Unknown")
    
    # 1. Greeting
    if time_of_day == "morning":
        greeting = "🌅 <b>Morning Report: Pre-Market Briefing</b>"
    elif time_of_day == "afternoon":
        greeting = "☀️ <b>Mid-day Pulse: Market Update</b>"
    elif time_of_day == "evening":
        greeting = "🌙 <b>Evening Summary: End of Day Review</b>"
    else:
        greeting = "🤖 <b>Nanobot Advisory Update</b>"

    # 2. Portfolio Value
    msg = f"{greeting}\n\n"
    msg += f"💰 <b>Total NAV:</b> ${total_balance}\n"
    msg += f"🕒 <b>Updated:</b> {data.get('last_updated', 'Unknown')}\n\n"

    briefing = data.get("advisor_briefing", {})
    if not briefing:
        msg += "⚠️ <i>No advisor briefing available in current dataset.</i>"
        return msg

    # 3. LLM Verdict & Headline
    verdict = briefing.get("verdict", "NEUTRAL")
    v_emoji = "🟢" if verdict == "BULLISH" else "🔴" if verdict == "BEARISH" else "🟡"
    msg += f"{v_emoji} <b>AI Verdict:</b> {verdict}\n"
    msg += f"📰 <b>Headline:</b> <i>{briefing.get('headline', '')}</i>\n\n"

    # 4. Macro Summary
    summary = briefing.get("macro_summary", "")
    if summary:
        msg += f"📊 <b>Market Context:</b>\n{summary}\n\n"

    # 5. Top Suggestions
    suggestions = briefing.get("suggestions", [])
    if suggestions:
        msg += "🎯 <b>Actionable Insights:</b>\n"
        # Only show top 2 or 3 to avoid spam
        for s in suggestions[:3]:
            action_emoji = "📈 BUY" if s["action"] == "BUY" else "📉 SELL" if s["action"] == "SELL" else "⏸️ HOLD"
            msg += f"• <b>{s['asset']}</b> ({action_emoji})\n"
            msg += f"  <i>{s['rationale']}</i>\n"
        msg += "\n"

    # 6. Top Risks
    risks = briefing.get("risks", [])
    if risks:
        msg += "⚠️ <b>Key Risks:</b>\n"
        for r in risks[:2]:  # Top 2 risks
            msg += f"• {r}\n"
        msg += "\n"

    # 7. Top News with Links
    daily_news = data.get("daily_news", [])
    linked_news = [n for n in daily_news if n.get("url") and n["url"] != "#"]
    if linked_news:
        msg += "📎 <b>Read More:</b>\n"
        for n in linked_news[:4]:
            title = n.get("title", "News")
            url = n["url"]
            source = n.get("publisher", "")
            source_tag = f" ({source})" if source else ""
            msg += f'• <a href="{url}">{title}</a>{source_tag}\n'
        msg += "\n"

    msg += f"🔗 <a href='http://localhost:5173/Asset-Management/'>View Full Dashboard</a>"
    return msg


async def send_broadcast(message: str):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables are required.")
        sys.exit(1)

    try:
        bot = Bot(token=bot_token)
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        print("Message broadcasted successfully!")
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Nanobot Telegram Broadcaster")
    parser.add_argument(
        "--time_of_day",
        type=str,
        choices=["morning", "afternoon", "evening", "test"],
        default="test",
        help="The style of the greeting for the broadcast."
    )
    args = parser.parse_args()

    # Determine which data to load
    base_dir = Path(__file__).parent.parent
    data_path = base_dir / "public" / "data.json"
    if not data_path.exists():
        data_path = base_dir / "src" / "data.json"
    
    if not data_path.exists():
        print(f"Error: Could not find data.json at {data_path}")
        sys.exit(1)

    print(f"Reading data from {data_path}...")
    data = load_data(str(data_path))
    
    if not data:
         print("Data is empty. Aborting broadcast.")
         sys.exit(1)

    # Format the HTML string
    print(f"Formatting {args.time_of_day} message...")
    message = format_message(args.time_of_day, data)

    # Send the message asynchronously
    asyncio.run(send_broadcast(message))


if __name__ == "__main__":
    main()
