# main.py
import streamlit as st
import requests
import time
import hashlib
import hmac
import json
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from contextlib import contextmanager

# 設定ファイル（config/real_settings.pyから読み込み）
try:
    from config.real_settings import *
except ImportError:
    st.error("設定ファイルが見つかりません。config/real_settings.pyを作成してください")
    st.stop()

# 基本設定
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
EXCHANGE_API_URL = "https://api.binance.com/api/v3"

# ログ管理システム
class TradingLogger:
    def __init__(self, db_name="trading_logs.db"):
        self.db_name = db_name
        self._init_db()

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS trade_logs
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          timestamp DATETIME,
                          symbol TEXT,
                          action TEXT,
                          quantity REAL,
                          price REAL,
                          reason TEXT)''')
            conn.execute('''CREATE TABLE IF NOT EXISTS error_logs
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          timestamp DATETIME,
                          error_type TEXT,
                          message TEXT)''')

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_name)
        try:
            yield conn
        finally:
            conn.close()

    def log_trade(self, symbol, action, quantity, price=None, reason=""):
        with self._get_connection() as conn:
            conn.execute('''INSERT INTO trade_logs 
                         (timestamp, symbol, action, quantity, price, reason)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                         (datetime.now(), symbol, action, quantity, price, reason))

    def log_error(self, error_type, message):
        with self._get_connection() as conn:
            conn.execute('''INSERT INTO error_logs 
                         (timestamp, error_type, message)
                         VALUES (?, ?, ?)''',
                         (datetime.now(), error_type, message))

# リスク管理システム
class RiskManager:
    def __init__(self, logger):
        self.logger = logger
        self.risk_params = {
            'max_loss': 0.02,
            'max_trade': 0.1,
            'cooling': 5
        }
        self.last_trade = {}

    def check_risk(self, symbol, quantity):
        try:
            if time.time() - self.last_trade.get(symbol, 0) < self.risk_params['cooling'] * 60:
                st.error("クーリング期間中です")
                return False
            return True
        except Exception as e:
            self.logger.log_error("RiskError", str(e))
            return False

# 取引システム
class TradingSystem:
    def __init__(self):
        self.logger = TradingLogger()
        self.risk_manager = RiskManager(self.logger)
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": EXCHANGE_API['API_KEY']})

    def get_signature(self, params):
        query = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        return hmac.new(
            EXCHANGE_API['API_SECRET'].encode(),
            query.encode(),
            hashlib.sha256
        ).hexdigest()

    def get_price(self, symbol):
        try:
            params = {"symbol": symbol, "timestamp": int(time.time()*1000)}
            params["signature"] = self.get_signature(params)
            response = self.session.get(f"{EXCHANGE_API_URL}/ticker/price", params=params)
            return float(response.json()['price'])
        except Exception as e:
            self.logger.log_error("PriceError", str(e))
            return None

    def execute_trade(self, symbol, action, quantity):
        try:
            if not self.risk_manager.check_risk(symbol, quantity):
                return None

            price = self.get_price(symbol)
            if not price:
                return None

            params = {
                "symbol": symbol,
                "side": action.upper(),
                "type": "MARKET",
                "quantity": round(quantity, 3),
                "timestamp": int(time.time()*1000)
            }
            params["signature"] = self.get_signature(params)

            response = self.session.post(
                f"{EXCHANGE_API_URL}/order",
                params=params
            )
            result = response.json()

            self.logger.log_trade(
                symbol=symbol,
                action=action,
                quantity=quantity,
                price=price,
                reason="自動取引"
            )
            self.risk_manager.last_trade[symbol] = time.time()
            return result
        except Exception as e:
            self.logger.log_error("TradeError", str(e))
            return None

# UI設定
def main():
    st.set_page_config(page_title="Auto Trader", layout="wide")
    st.title("🤖 自動取引システム")

    if 'system' not in st.session_state:
        st.session_state.system = TradingSystem()

    with st.sidebar:
        st.header("設定")
        symbol = st.selectbox("通貨ペア", ["BTCUSDT", "ETHUSDT", "BNBUSDT"])
        quantity = st.number_input("数量", min_value=0.001, step=0.001, value=0.01)
        interval = st.number_input("更新間隔（秒）", 10, 3600, 60)

    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("取引実行")
        if st.button("即時取引テスト"):
            result = st.session_state.system.execute_trade(symbol, "BUY", quantity)
            if result:
                st.success("取引成功")
            else:
                st.error("取引失敗")

        st.subheader("価格表示")
        price_placeholder = st.empty()

    with col2:
        st.subheader("取引履歴")
        with sqlite3.connect("trading_logs.db") as conn:
            df = pd.read_sql("SELECT * FROM trade_logs ORDER BY timestamp DESC LIMIT 10", conn)
            st.dataframe(df)

    # 自動更新ループ
    while True:
        try:
            price = st.session_state.system.get_price(symbol)
            price_placeholder.metric(f"現在の価格 ({symbol})", f"{price:,.2f} USD")
            time.sleep(interval)
        except:
            pass

if __name__ == "__main__":
    main()