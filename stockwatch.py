import logging
import requests
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, JobQueue
from collections import defaultdict

ALPHA_VANTAGE_API_KEY = 'XXX'
BOT_TOKEN = 'XXX'
TELEGRAM_CHAT_ID = 'XXX'
import logging
import json
import os
from typing import Dict, List
import asyncio
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# File to store user watchlists
WATCHLIST_FILE = "user_watchlists.json"

class StockWatcherBot:
    def __init__(self):
        self.watchlists = self.load_watchlists()
    
    def load_watchlists(self) -> Dict:
        """Load user watchlists from file"""
        try:
            if os.path.exists(WATCHLIST_FILE):
                with open(WATCHLIST_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading watchlists: {e}")
        return {}
    
    def save_watchlists(self):
        """Save user watchlists to file"""
        try:
            with open(WATCHLIST_FILE, 'w') as f:
                json.dump(self.watchlists, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving watchlists: {e}")
    
    def get_user_watchlist(self, user_id: str) -> List[str]:
        """Get watchlist for a specific user"""
        return self.watchlists.get(str(user_id), [])
    
    def add_to_watchlist(self, user_id: str, symbol: str) -> bool:
        """Add stock to user's watchlist"""
        user_id = str(user_id)
        if user_id not in self.watchlists:
            self.watchlists[user_id] = []
        
        symbol = symbol.upper()
        if symbol not in self.watchlists[user_id]:
            self.watchlists[user_id].append(symbol)
            self.save_watchlists()
            return True
        return False
    
    def remove_from_watchlist(self, user_id: str, symbol: str) -> bool:
        """Remove stock from user's watchlist"""
        user_id = str(user_id)
        symbol = symbol.upper()
        
        if user_id in self.watchlists and symbol in self.watchlists[user_id]:
            self.watchlists[user_id].remove(symbol)
            self.save_watchlists()
            return True
        return False
    
    def get_stock_price(self, symbol: str) -> Dict:
        """Get current stock price and 52-week MA using Alpha Vantage API"""
        try:
            # Get current quote
            quote_url = f"https://www.alphavantage.co/query"
            quote_params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': ALPHA_VANTAGE_API_KEY
            }
            
            quote_response = requests.get(quote_url, params=quote_params, timeout=10)
            quote_data = quote_response.json()
            
            # Check for API errors
            if 'Error Message' in quote_data:
                logger.error(f"Alpha Vantage API error for {symbol}: {quote_data['Error Message']}")
                return None
            
            if 'Note' in quote_data:
                logger.warning(f"Alpha Vantage API rate limit for {symbol}: {quote_data['Note']}")
                return None
            
            if 'Global Quote' not in quote_data:
                logger.error(f"Unexpected response format for {symbol}: {quote_data}")
                return None
            
            quote = quote_data['Global Quote']
            current_price = float(quote['05. price'])
            company_name = symbol  # Alpha Vantage doesn't provide company name in quote
            
            # Get historical data for 52-week MA calculation
            # Using weekly data to reduce API calls
            hist_url = f"https://www.alphavantage.co/query"
            hist_params = {
                'function': 'TIME_SERIES_WEEKLY',
                'symbol': symbol,
                'apikey': ALPHA_VANTAGE_API_KEY
            }
            
            hist_response = requests.get(hist_url, params=hist_params, timeout=10)
            hist_data = hist_response.json()
            
            if 'Weekly Time Series' not in hist_data:
                logger.error(f"No historical data available for {symbol}")
                # Return current price without MA if historical data unavailable
                return {
                    'symbol': symbol,
                    'company_name': company_name,
                    'current_price': round(current_price, 2),
                    'ma_52_week': None,
                    'above_ma': None,
                    'change_percent': None
                }
            
            # Calculate 52-week moving average
            weekly_data = hist_data['Weekly Time Series']
            dates = sorted(weekly_data.keys(), reverse=True)  # Most recent first
            
            if len(dates) < 52:
                logger.warning(f"Not enough historical data for {symbol} (only {len(dates)} weeks)")
                ma_52_week = None
                above_ma = None
                change_percent = None
            else:
                # Get closing prices for last 52 weeks
                closing_prices = []
                for date in dates[:52]:
                    closing_prices.append(float(weekly_data[date]['4. close']))
                
                ma_52_week = sum(closing_prices) / len(closing_prices)
                above_ma = current_price > ma_52_week
                change_percent = round(((current_price - ma_52_week) / ma_52_week) * 100, 2)
                ma_52_week = round(ma_52_week, 2)
            
            return {
                'symbol': symbol,
                'company_name': company_name,
                'current_price': round(current_price, 2),
                'ma_52_week': ma_52_week,
                'above_ma': above_ma,
                'change_percent': change_percent
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error getting stock price for {symbol}: {e}")
            return None
        except KeyError as e:
            logger.error(f"Key error parsing data for {symbol}: {e}")
            return None
        except ValueError as e:
            logger.error(f"Value error parsing data for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting stock price for {symbol}: {e}")
            return None

# Initialize bot
bot = StockWatcherBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    """Start command handler"""
    welcome_message = f"""
📈 **Welcome to Stock Watcher Bot!**
Hello {update.effective_user.first_name}!👋
I'll help you monitor your favorite stocks and track their performance against the 52-week moving average.

**Available Commands:**
/add <symbol> - Add stock to your watchlist
/remove <symbol> - Remove stock from your watchlist
/list - Show your watchlist
/price <symbol> - Show current price for a stock
/check - Check all watchlist stocks against 52-week MA
/help - Show this help message

**Example:**
`/add AAPL` - Add Apple stock to your watchlist
`/price TSLA` - Get Tesla's current price info

Start by adding some stocks to your watchlist! 🚀
    """
    
    keyboard = [
        [InlineKeyboardButton("📊 View Watchlist", callback_data="list")],
        [InlineKeyboardButton("💡 Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_message, 
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command handler"""
    help_text = """
🤖 **Stock Watcher Bot Commands:**

**Watchlist Management:**
/add <symbol> - Add stock to your watchlist
/remove <symbol> - Remove stock from watchlist
/list - Show your current watchlist

**Price Information:**
/price <symbol> - Get current price and 52-week MA info
/check - Analyze all your watchlist stocks

**Other:**
/help - Show this help message
/start - Restart the bot

**Tips:**
• Use official stock symbols (e.g., AAPL for Apple)
• The bot tracks 52-week moving average for technical analysis
• You can add multiple stocks to monitor them easily

**Example Usage:**
`/add AAPL GOOGL MSFT` - Add multiple stocks
`/price TSLA` - Check Tesla's current price
`/check` - Analyze all your stocks at once
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def add_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add stock to watchlist"""
    if not context.args:
        await update.message.reply_text(
            "❌ Please specify a stock symbol.\n\n**Usage:** `/add AAPL`",
            parse_mode='Markdown'
        )
        return
    
    user_id = update.effective_user.id
    added_stocks = []
    already_exists = []
    invalid_stocks = []
    
    for symbol in context.args:
        symbol = symbol.upper()
        
        # Validate stock symbol by trying to get its info
        stock_data = bot.get_stock_price(symbol)
        if stock_data is None:
            invalid_stocks.append(symbol)
            continue
        
        if bot.add_to_watchlist(user_id, symbol):
            added_stocks.append(f"{symbol} ({stock_data['company_name']})")
        else:
            already_exists.append(symbol)
    
    response = ""
    if added_stocks:
        response += f"✅ **Added to watchlist:**\n" + "\n".join([f"• {stock}" for stock in added_stocks])
    
    if already_exists:
        response += f"\n\n📊 **Already in watchlist:**\n" + "\n".join([f"• {stock}" for stock in already_exists])
    
    if invalid_stocks:
        response += f"\n\n❌ **Invalid symbols:**\n" + "\n".join([f"• {stock}" for stock in invalid_stocks])
    
    if not response:
        response = "❌ No valid stocks were processed."
    
    # Add current watchlist size
    watchlist_size = len(bot.get_user_watchlist(user_id))
    response += f"\n\n📋 **Total watchlist size:** {watchlist_size} stocks"
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def remove_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove stock from watchlist"""
    if not context.args:
        await update.message.reply_text(
            "❌ Please specify a stock symbol.\n\n**Usage:** `/remove AAPL`",
            parse_mode='Markdown'
        )
        return
    
    user_id = update.effective_user.id
    removed_stocks = []
    not_found = []
    
    for symbol in context.args:
        symbol = symbol.upper()
        if bot.remove_from_watchlist(user_id, symbol):
            removed_stocks.append(symbol)
        else:
            not_found.append(symbol)
    
    response = ""
    if removed_stocks:
        response += f"✅ **Removed from watchlist:**\n" + "\n".join([f"• {stock}" for stock in removed_stocks])
    
    if not_found:
        response += f"\n\n❌ **Not in watchlist:**\n" + "\n".join([f"• {stock}" for stock in not_found])
    
    # Add current watchlist size
    watchlist_size = len(bot.get_user_watchlist(user_id))
    response += f"\n\n📋 **Total watchlist size:** {watchlist_size} stocks"
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def list_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's watchlist"""
    user_id = update.effective_user.id
    watchlist = bot.get_user_watchlist(user_id)
    
    if not watchlist:
        keyboard = [[InlineKeyboardButton("➕ Add Stock", callback_data="add_help")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📝 Your watchlist is empty.\n\nUse `/add <symbol>` to add stocks!\n\n**Example:** `/add AAPL GOOGL MSFT`",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return
    
    response = f"📋 **Your Watchlist ({len(watchlist)} stocks):**\n\n"
    
    for i, symbol in enumerate(watchlist, 1):
        response += f"{i}. 📈 **{symbol}**\n"
    
    keyboard = [
        [InlineKeyboardButton("💰 Check Prices", callback_data="check_all")],
        [InlineKeyboardButton("➕ Add More", callback_data="add_help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        response, 
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get stock price information"""
    if not context.args:
        await update.message.reply_text(
            "❌ Please specify a stock symbol.\n\n**Usage:** `/price AAPL`",
            parse_mode='Markdown'
        )
        return
    
    symbol = context.args[0].upper()
    
    # Send "typing" action
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    stock_data = bot.get_stock_price(symbol)
    
    if stock_data is None:
        await update.message.reply_text(
            f"❌ Could not find data for symbol **{symbol}**.\n\nPlease check the symbol and try again.",
            parse_mode='Markdown'
        )
        return
    
    # Determine trend emoji and status
    if stock_data['ma_52_week'] is not None:
        trend_emoji = "📈" if stock_data['above_ma'] else "📉"
        status = "Above 52-Week MA" if stock_data['above_ma'] else "Below 52-Week MA"
        ma_text = f"📊 **52-Week MA:** ${stock_data['ma_52_week']}\n📈 **Status:** {status}\n📊 **Difference:** {stock_data['change_percent']:+.2f}%"
    else:
        trend_emoji = "📊"
        ma_text = "📊 **52-Week MA:** Data unavailable\n⚠️ **Note:** Insufficient historical data for MA calculation"
    
    response = f"""
{trend_emoji} **{stock_data['symbol']} - {stock_data['company_name']}**

💰 **Current Price:** ${stock_data['current_price']}
{ma_text}

*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*
    """
    
    # Add action buttons
    keyboard = [
        [InlineKeyboardButton("➕ Add to Watchlist", callback_data=f"add_{symbol}")],
        [InlineKeyboardButton("🔄 Refresh", callback_data=f"price_{symbol}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        response, 
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def check_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check all stocks in watchlist against 52-week MA"""
    user_id = update.effective_user.id
    watchlist = bot.get_user_watchlist(user_id)
    
    if not watchlist:
        await update.message.reply_text(
            "📝 Your watchlist is empty.\n\nUse `/add <symbol>` to add stocks first!",
            parse_mode='Markdown'
        )
        return
    
    # Send "typing" action for longer operations
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    response = f"📊 **52-Week MA Analysis** ({len(watchlist)} stocks)\n\n"
    
    above_ma = []
    below_ma = []
    errors = []
    
    for symbol in watchlist:
        stock_data = bot.get_stock_price(symbol)
        
        if stock_data is None:
            errors.append(symbol)
            continue
        
        # Handle cases where MA data is unavailable
        if stock_data['ma_52_week'] is None:
            errors.append(f"{symbol} (insufficient data)")
            continue
        
        trend_emoji = "📈" if stock_data['above_ma'] else "📉"
        change_text = f"{stock_data['change_percent']:+.2f}%"
        
        stock_line = f"{trend_emoji} **{symbol}**: ${stock_data['current_price']} ({change_text})"
        
        if stock_data['above_ma']:
            above_ma.append(stock_line)
        else:
            below_ma.append(stock_line)
    
    # Format results
    if above_ma:
        response += "✅ **Above 52-Week MA:**\n" + "\n".join(above_ma) + "\n\n"
    
    if below_ma:
        response += "❌ **Below 52-Week MA:**\n" + "\n".join(below_ma) + "\n\n"
    
    if errors:
        response += "⚠️ **Data Unavailable:**\n" + "\n".join([f"• {symbol}" for symbol in errors]) + "\n\n"
    
    response += f"*Analysis completed at {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*"
    
    # Add refresh button
    keyboard = [[InlineKeyboardButton("🔄 Refresh Analysis", callback_data="check_all")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        response, 
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "list":
        await list_watchlist(update, context)
    elif data == "help":
        await help_command(update, context)
    elif data == "check_all":
        await check_watchlist(update, context)
    elif data == "add_help":
        await query.edit_message_text(
            "➕ **Add stocks to your watchlist:**\n\n"
            "Use the command: `/add <symbol>`\n\n"
            "**Examples:**\n"
            "• `/add AAPL` - Add Apple\n"
            "• `/add GOOGL MSFT TSLA` - Add multiple stocks\n\n"
            "**Popular stocks:** AAPL, GOOGL, MSFT, TSLA, AMZN, NVDA, META",
            parse_mode='Markdown'
        )
    elif data.startswith("add_"):
        symbol = data[4:]
        user_id = query.from_user.id
        if bot.add_to_watchlist(user_id, symbol):
            await query.edit_message_text(f"✅ Added **{symbol}** to your watchlist!")
        else:
            await query.edit_message_text(f"📊 **{symbol}** is already in your watchlist!")
    elif data.startswith("price_"):
        symbol = data[6:]
        # Simulate price command
        context.args = [symbol]
        await get_price(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle non-command messages"""
    message_text = update.message.text.strip()
    
    # Check if it looks like a stock symbol
    if message_text.isalpha() and 1 <= len(message_text) <= 5:
        symbol = message_text.upper()
        context.args = [symbol]
        await get_price(update, context)
    else:
        await update.message.reply_text(
            "🤔 I didn't understand that command.\n\n"
            "Type /help to see available commands, or just send a stock symbol like 'AAPL' to get its price!",
            parse_mode='Markdown'
        )

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add", add_stock))
    application.add_handler(CommandHandler("remove", remove_stock))
    application.add_handler(CommandHandler("list", list_watchlist))
    application.add_handler(CommandHandler("price", get_price))
    application.add_handler(CommandHandler("check", check_watchlist))
    
    # Add callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add message handler for non-command messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    print("🚀 Stock Watcher Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()