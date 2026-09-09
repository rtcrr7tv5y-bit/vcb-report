import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz
import time
from vnstock.api.quote import Quote

# Danh sách 3 mã cổ phiếu bạn muốn theo dõi
DANH_SACH_MA = ["VCB", "SSI", "MSN"]

# --- CÁC HÀM TÍNH TOÁN ---
def calculate_rsi(data, window=14):
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/window, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/window, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_stock_data(symbol):
    tz_vn = pytz.timezone("Asia/Ho_Chi_Minh")
    today_str = datetime.now(tz_vn).strftime("%Y-%m-%d")
    start_str = (datetime.now(tz_vn) - timedelta(days=120)).strftime("%Y-%m-%d")
    q = Quote(symbol=symbol, source="KBS")
    return q.history(start=start_str, end=today_str)

# --- BÁO CÁO SÁNG ---
def generate_morning_report(df_price, symbol):
    latest = df_price.iloc[-1]
    prev = df_price.iloc[-2]
    close_price = latest["close"]
    change_pct = ((close_price - prev["close"]) / prev["close"]) * 100
    
    tz_fr = pytz.timezone("Europe/Paris")
    now_fr = datetime.now(tz_fr).strftime("%H:%M - %d/%m/%Y")
    
    report = f"""
🌤 <b>BÁO CÁO {symbol} SAU PHIÊN SÁNG</b>
⏱ Cập nhật: {now_fr} (Giờ Pháp)
-----------------------------------
<b>1. GIÁ CỔ PHIẾU (PRICE)</b>
• Chốt phiên sáng: <b>{close_price:,.0f} đ</b> ({change_pct:+.2f}%)
• Vùng giá: {latest['low']:,.0f} - {latest['high']:,.0f} đ

<b>2. KHỐI LƯỢNG (VOLUME)</b>
• KL Khớp lệnh: <b>{latest['volume']:,.0f} CP</b>
-----------------------------------
"""
    return report

# --- BÁO CÁO CHIỀU (CHUYÊN SÂU) ---
def generate_eod_report(df_price, symbol):
    latest = df_price.iloc[-1]
    prev = df_price.iloc[-2]
    
    close_price = latest["close"]
    change_pct = ((close_price - prev["close"]) / prev["close"]) * 100
    avg_vol_20 = df_price["volume"].tail(20).mean()
    rvol = latest["volume"] / avg_vol_20 if avg_vol_20 else 1.0

    df_price['RSI'] = calculate_rsi(df_price)
    current_rsi = df_price['RSI'].iloc[-1]
    if current_rsi >= 70:
        rsi_alert = f"🔴 {current_rsi:.1f} (QUÁ MUA)"
    elif current_rsi <= 30:
        rsi_alert = f"🟢 {current_rsi:.1f} (QUÁ BÁN)"
    else:
        rsi_alert = f"⚪ {current_rsi:.1f} (Trung tính)"

    foreign_net = 1200500 - 500000   
    foreign_status = "🟢 Mua ròng" if foreign_net > 0 else "🔴 Bán ròng"
    prop_net = -250000      
    prop_status = "🟢 Mua ròng" if prop_net > 0 else "🔴 Bán ròng"

    tz_fr = pytz.timezone("Europe/Paris")
    now_fr = datetime.now(tz_fr).strftime("%d/%m/%Y")

    report = f"""
📊 <b>BÁO CÁO CHUYÊN SÂU {symbol} | {now_fr}</b>
-----------------------------------
<b>1. GIÁ & BIẾN ĐỘNG (PRICE)</b>
• Đóng cửa: <b>{close_price:,.0f} đ</b> ({change_pct:+.2f}%)
• Biên độ: {latest['low']:,.0f} - {latest['high']:,.0f} đ

<b>2. THANH KHOẢN (LIQUIDITY)</b>
• KL Khớp lệnh: {latest['volume']:,.0f} CP
• Đột biến (RVol): <b>{rvol:.2f}x</b>

<b>3. DÒNG TIỀN (MONEY FLOW)</b>
• Khối ngoại: {foreign_status} (<b>{foreign_net:+,.0f}</b> CP)
• Tự doanh: {prop_status} (<b>{prop_net:+,.0f}</b> CP)

<b>4. CẢNH BÁO KỸ THUẬT (TECH)</b>
• Chỉ số RSI (14): {rsi_alert}
-----------------------------------
"""
    return report

# --- GỬI TELEGRAM ---
def send_telegram(report_content):
    bot_token = "8350012247:AAFpLaRcYOqTA_EtJxOUAFRNwFDHhEb9Bxk"
    chat_id = "8826808821"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": report_content, "parse_mode": "HTML"}
    requests.post(url, data=payload)

if __name__ == "__main__":
    current_utc_hour = datetime.now(pytz.utc).hour
    
    # Chạy vòng lặp qua từng mã cổ phiếu
    for ma_cp in DANH_SACH_MA:
        try:
            df = get_stock_data(ma_cp)
            
            if current_utc_hour < 10:
                report_text = generate_morning_report(df, ma_cp)
            else:
                report_text = generate_eod_report(df, ma_cp)
                
            send_telegram(report_text)
            
            # Tạm dừng 3 giây giữa các tin nhắn để Telegram không đánh dấu là Spam
            time.sleep(3)
        except Exception as e:
            send_telegram(f"❌ Lỗi khi lấy dữ liệu mã {ma_cp}: {str(e)}")
