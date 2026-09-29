import os
import time
import threading
import ccxt
import pandas as pd
import telebot
from flask import Flask

# ==========================================
# 1. WEB SERVER MINI (MENCEGAH BOT OFF DI RENDER)
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Sinyal Telegram Aktif 24/7!"

def run_flask():
    # Render akan memberikan port secara otomatis melalui environment variable PORT
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ==========================================
# 2. KONFIGURASI BOT TELEGRAM & EXCHANGE
# ==========================================
TELEGRAM_TOKEN = "8814868706:AAGrDaSZc1PPmNJg-cL0PG5ShxH9WqXQtn4"
TELEGRAM_CHAT_ID = "6840959604"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

exchange = ccxt.binance({
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
    },
    'timeout': 30000,
})

SYMBOLS = [
    "BTC/USDT",
    "ETH/USDT",
    "SOL/USDT",
    "BNB/USDT",
    "XRP/USDT"
]

TIMEFRAME = '4h'
INTERVAL_DETIK = 14400  # 4 jam

# ==========================================
# 3. FUNGSI ANALISIS MARKET
# ==========================================
def fetch_klines(symbol, timeframe=TIMEFRAME, limit=100):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"[{symbol}] Gagal mengambil data Binance: {e}", flush=True)
        return None

def analyze_market(symbol):
    df = fetch_klines(symbol)
    if df is None or df.empty:
        return

    df['SMA20'] = df['close'].rolling(window=20).mean()

    last_close = df['close'].iloc[-1]
    prev_close = df['close'].iloc[-2]
    sma20 = df['SMA20'].iloc[-1]

    signal = None
    if prev_close < sma20 and last_close > sma20:
        signal = "BUY / LONG"
    elif prev_close > sma20 and last_close < sma20:
        signal = "SELL / SHORT"

    if signal:
        pesan = (
            f"🚨 **SINYAL FUTURES (4H) DETEKSI!** 🚨\n\n"
            f"📌 **Pair:** `{symbol}`\n"
            f"📈 **Arah:** `{signal}`\n"
            f"💰 **Harga Terakhir:** `{last_close}`\n"
            f"⏱ **Timeframe:** {TIMEFRAME}\n"
            f"⚙️ **Exchange:** Binance Futures"
        )
        try:
            bot.send_message(TELEGRAM_CHAT_ID, pesan, parse_mode="Markdown")
            print(f"[{symbol}] Sinyal {signal} terkirim ke Telegram!", flush=True)
        except Exception as e:
            print(f"[{symbol}] Gagal mengirim pesan Telegram: {e}", flush=True)
    else:
        print(f"[{symbol}] Tidak ada sinyal valid pada timeframe {TIMEFRAME}.", flush=True)

def job_scanner():
    while True:
        print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Memulai pemindaian Futures (4H)...", flush=True)
        for symbol in SYMBOLS:
            analyze_market(symbol)
            time.sleep(1)
        
        print(f"[INFO] Pemindaian selesai. Tidur selama 4 jam...\n", flush=True)
        time.sleep(INTERVAL_DETIK)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "🤖 Bot Sinyal Crypto Futures (Binance 4H) Aktif 24/7 di Render Web Service!")

@bot.message_handler(commands=['cek'])
def manual_scan(message):
    bot.reply_to(message, "⏳ Memulai pemindaian manual pasar Futures...")
    for symbol in SYMBOLS:
        analyze_market(symbol)
    bot.send_message(message.chat.id, "✅ Pemindaian manual selesai.")

# ==========================================
# 4. MEMULAI SERVER & BOT
# ==========================================
if __name__ == "__main__":
    print("🚀 BOT SINYAL FUTURES AKTIF DI RENDER!", flush=True)
    
    # Jalan server Flask di background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Jalan pemindai pasar di background thread
    scanner_thread = threading.Thread(target=job_scanner, daemon=True)
    scanner_thread.start()

    # Jalan polling Telegram di thread utama
    while True:
        try:
            bot.polling(none_stop=True, interval=2, timeout=30)
        except Exception as e:
            print(f"[ERROR Telegram Polling]: {e}", flush=True)
            time.sleep(5)