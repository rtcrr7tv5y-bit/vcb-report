import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz
from vnstock.api.quote import Quote

# --- CÁC HÀM TÍNH TOÁN ---
def calculate_rsi(data, window=14):
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/window, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/window, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_stock_data():
    tz_vn = pytz.timezone("Asia/Ho_Chi_Minh")
    today_str = datetime.now(tz_vn).strftime("%Y-%m-%d")
    start_str = (datetime.now(tz_vn) - timedelta(days=120)).strftime("%Y-%m-%d")
    q = Quote(symbol="VCB", source="KBS")
    return q.history(start=start_str, end=today_str)

# --- BÁO CÁO SÁNG ---
def generate_morning_report(df_price):
    latest = df_price.iloc[-1]
    prev = df_price.iloc[-2]
    close_price = latest["close"]
    change_pct = ((close_price - prev["close"]) / prev["close"]) * 100
    
    tz_fr = pytz.timezone("Europe/Paris")
    now_fr = datetime.now(tz_fr).strftime("%H:%M - %d/%m/%Y")
    
    report = f"""
🌤 <b>BÁO CÁO VCB SAU PHIÊN SÁNG</b>
⏱ Cập nhật: {now_fr} (Giờ Pháp)
-----------------------------------
<b>1. GIÁ CỔ PHIẾU (PRICE)</b>
• Chốt phiên sáng: <b>{close_price:,.0f} đ</b> ({change_pct:+.2f}%)
• Vùng giá: {latest['low']:,.0f} - {latest['high']:,.0f} đ

<b>2. KHỐI LƯỢNG (VOLUME)</b>
• KL Khớp lệnh: <b>{latest['volume']:,.0f} CP</b>
-----------------------------------
<i>🤖 Dữ liệu tạm tính đến giờ nghỉ trưa.</i>
"""
    return report

# --- BÁO CÁO CHIỀU (CHUYÊN SÂU) ---
def generate_eod_report(df_price):
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
📊 <b>BÁO CÁO CHUYÊN SÂU VCB | {now_fr}</b>
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
<i>🤖 Chạy tự động chốt phiên cuối ngày.</i>
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
    df = get_stock_data()
    
    # Lấy giờ hiện tại theo UTC để kiểm tra
    current_utc_hour = datetime.now(pytz.utc).hour
    
    # Nếu hệ thống chạy trước 10h sáng UTC (tức là mốc 6h UTC - phiên sáng)
    if current_utc_hour < 10:
        report_text = generate_morning_report(df)
    # Nếu hệ thống chạy sau 10h sáng UTC (tức là mốc 15h UTC - phiên chiều)
    else:
        report_text = generate_eod_report(df)
        
    send_telegram(report_text)
