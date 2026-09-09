import requests
from datetime import datetime
import pytz
from vnstock.api.quote import Quote

def generate_morning_report():
    # 1. Lấy dữ liệu VCB (Chạy lúc 11:30 VN sẽ lấy dữ liệu chốt phiên sáng)
    q = Quote(symbol="VCB", source="KBS")
    df_price = q.history(start="2026-08-01", end="2026-09-10")
    
    latest = df_price.iloc[-1]
    prev = df_price.iloc[-2]

    # Tính toán thông số
    close_price = latest["close"]
    change_pct = ((close_price - prev["close"]) / prev["close"]) * 100
    volume = latest["volume"]

    # 2. Định dạng ngày giờ hiện tại
    tz_fr = pytz.timezone("Europe/Paris")
    tz_vn = pytz.timezone("Asia/Ho_Chi_Minh")
    now_fr = datetime.now(tz_fr).strftime("%H:%M")
    now_vn = datetime.now(tz_vn).strftime("%H:%M")
    date_str = datetime.now(tz_vn).strftime("%d/%m/%Y")

    # 3. Khuôn báo cáo phiên sáng
    report = f"""
🌤 <b>BÁO CÁO VCB SAU PHIÊN SÁNG | {date_str}</b>
⏱ Cập nhật: {now_vn} (VN) | {now_fr} (Pháp)
-----------------------------------
<b>1. GIÁ CỔ PHIẾU (PRICE)</b>
• Chốt phiên sáng: <b>{close_price:,.0f} đ</b> ({change_pct:+.2f}%)
• Vùng giá dao động: {latest['low']:,.0f} - {latest['high']:,.0f} đ

<b>2. KHỐI LƯỢNG (VOLUME)</b>
• KL Khớp lệnh: <b>{volume:,.0f} CP</b>
-----------------------------------
<i>🤖 Dữ liệu tạm tính đến giờ nghỉ trưa.</i>
"""
    return report

def send_telegram(report_content):
    bot_token = "8350012247:AAFpLaRcYOqTA_EtJxOUAFRNwFDHhEb9Bxk"
    chat_id = "8826808821"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": report_content,
        "parse_mode": "HTML"
    }
    
    requests.post(url, data=payload)
    print("Đã gửi báo cáo phiên sáng thành công!")

if __name__ == "__main__":
    report_text = generate_morning_report()
    send_telegram(report_text)
