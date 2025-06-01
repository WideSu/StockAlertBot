# Telegram Stock Watcher Bot 📈

## Requirements

Create a `requirements.txt` file with these dependencies:

```
python-telegram-bot==20.7
requests==2.31.0
pandas==2.1.4
asyncio
```

## Setup Instructions

### 1. Get Alpha Vantage API Key

1. Go to [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Sign up for a free account
3. Get your free API key (allows 25 requests per day, 5 per minute)
4. For higher limits, consider their premium plans

### 2. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Start a chat with BotFather and send `/newbot`
3. Follow the prompts to create your bot:
   - Choose a name (e.g., "Stock Watcher Bot")
   - Choose a username (e.g., "mystockwatcher_bot")
4. BotFather will give you a bot token that looks like: `123526789:ABCdefGHIjklMNOpqrsTUVwxyz`
5. Copy this token and replace `YOUR_BOT_TOKEN_HERE` in the code

### 3. Configure API Keys

In the bot code, replace these placeholders:
- `YOUR_BOT_TOKEN_HERE` - Your Telegram bot token from BotFather
- `YOUR_ALPHA_VANTAGE_API_KEY_HERE` - Your Alpha Vantage API key

### 4. Set Bot Description and Commands

Send these commands to @BotFather:

**Set Description:**
```
/setdescription
```
Then paste:
```
👋 Welcome to Stock Watcher Bot!

You can use these commands:
/add <symbol> - Add stock to your watchlist
/remove <symbol> - Remove stock from your watchlist
/list - Show your watchlist
/price <symbol> - Show current price for a stock
/check - Check all watchlist stocks against 52-week MA condition

Start monitoring your favorite stocks today! 📈
```

**Set Commands:**
```
/setcommands
```
Then paste:
```
start - Start the bot
help - Show help message
add - Add stock to watchlist
remove - Remove stock from watchlist
list - Show your watchlist
price - Get stock price info
check - Check watchlist against 52-week MA
```

**Set About Text:**
```
/setabouttext
```
Then paste:
```
🤖 Your intelligent stock monitoring assistant. Track your favorite stocks and monitor their performance against the 52-week moving average for technical analysis.
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Run the Bot

```bash
python stock_watcher_bot.py
```

## Features

### ✅ Implemented Commands

- **`/start`** - Welcome message with inline buttons
- **`/add <symbol>`** - Add stocks to personal watchlist
- **`/remove <symbol>`** - Remove stocks from watchlist
- **`/list`** - Display current watchlist with action buttons
- **`/price <symbol>`** - Get current price and 52-week MA analysis
- **`/check`** - Analyze all watchlist stocks against 52-week MA
- **`/help`** - Show detailed help message

### 🎯 Key Features

1. **Personal Watchlists** - Each user has their own watchlist stored persistently
2. **Real Stock Data** - Uses Alpha Vantage API for live stock prices and historical data
3. **52-Week Moving Average** - Technical analysis comparing current price to 52-week MA
4. **Interactive Buttons** - Inline keyboards for better user experience
5. **Multi-stock Support** - Add/remove multiple stocks in one command
6. **Error Handling** - Validates stock symbols and handles API errors/rate limits
7. **Smart Input** - Accepts direct stock symbols (e.g., just type "AAPL")
8. **Rate Limit Handling** - Gracefully handles Alpha Vantage API limits

### 📊 Data Storage

- User watchlists are stored in `user_watchlists.json`
- Data persists between bot restarts
- Each user has independent watchlist

### 🔧 Customization Options

**Stock Data Source:**
- Now uses Alpha Vantage API for reliable, professional-grade financial data
- Provides real-time quotes and historical weekly data
- Better data accuracy compared to free alternatives

**API Rate Limits:**
- Free tier: 25 requests per day, 5 per minute
- The bot includes rate limit detection and error handling
- Consider premium plans for higher usage

**Moving Average Period:**
- Uses weekly data for more accurate 52-week calculations
- Requires minimum 52 weeks of historical data
- Falls back gracefully when insufficient data available

**Watchlist Limits:**
- No current limits, but can be added in `add_to_watchlist` method

## Example Usage

```
User: /start
Bot: 📈 Welcome to Stock Watcher Bot! [Interactive buttons]

User: /add AAPL GOOGL MSFT
Bot: ✅ Added to watchlist:
     • AAPL (Apple Inc.)
     • GOOGL (Alphabet Inc.)
     • MSFT (Microsoft Corporation)

User: /price TSLA
Bot: 📈 TSLA - TSLA
     💰 Current Price: $252.30
     📊 52-Week MA: $260.75
     📈 Status: Below 52-Week MA
     📊 Difference: -5.93%

User: /check
Bot: 📊 52-Week MA Analysis (3 stocks)
     ✅ Above 52-Week MA:
     📈 AAPL: $175.50 (+6.26%)
     📈 MSFT: $385.90 (+4.16%)
     ❌ Below 52-Week MA:
     📉 GOOGL: $2750.80 (-2.64%)
```

## Production Deployment

### Using Webhooks (Recommended for production)

Replace the polling method with webhooks for better performance:

```python
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    # Add handlers...
    
    # For webhooks (replace with your domain)
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get('PORT', 8443)),
        url_path=BOT_TOKEN,
        webhook_url=f"https://yourdomain.com/{BOT_TOKEN}"
    )
```

### Environment Variables

For production, use environment variables for security:

```python
import os
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY')
```

**Setting Environment Variables:**

Linux/Mac:
```bash
export BOT_TOKEN="your_bot_token_here"
export ALPHA_VANTAGE_API_KEY="your_alpha_vantage_key_here"
python stock_watcher_bot.py
```

Windows:
```cmd
set BOT_TOKEN=your_bot_token_here
set ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
python stock_watcher_bot.py
```

### Database Integration

For scalability, replace JSON file storage with a database:

```python
# Example with SQLite
import sqlite3

def setup_database():
    conn = sqlite3.connect('watchlists.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS watchlists (
            user_id INTEGER,
            symbol TEXT,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, symbol)
        )
    ''')
    conn.close()
```

## Troubleshooting

**Common Issues:**

1. **Invalid Token Error**: Make sure you copied the complete token from BotFather
2. **Module Not Found**: Run `pip install -r requirements.txt`
3. **Alpha Vantage API Errors**: 
   - Check your API key is correct
   - Verify you haven't exceeded rate limits (25 requests/day for free tier)
   - Some symbols might not be available
4. **Rate Limit Exceeded**: Free tier has limits - wait or upgrade to premium
5. **Network Timeouts**: Alpha Vantage API calls have 10-second timeout built-in

**API Rate Limit Management:**
- Free tier: 25 requests per day, 5 per minute
- Each `/price` command uses 2 API calls (quote + historical data)
- Each `/check` command uses 2 API calls per stock in watchlist
- Monitor usage to avoid hitting limits

**Logs:**
The bot includes comprehensive logging. Check console output for debugging API issues.

## License

This bot is provided as-is for educational purposes. Please respect API rate limits and terms of service for data providers.
