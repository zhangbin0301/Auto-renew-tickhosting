import os
from playwright.sync_api import sync_playwright
from datetime import datetime
import time
from dateutil import parser
import requests
import re

# 配置
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram notification not configured")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Telegram notification sent")
        return True
    except Exception as e:
        print(f"Failed to send Telegram notification: {e}")
        return False

def update_last_renew_time(success, new_time=None, error_message=None, server_id=None):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "SUCCESS" if success else "FAILED"
    
    content = f"*Tickhosting Auto Renew Report*\n\n"
    content += f"• *Status*: `{status}`\n"
    content += f"• *Server ID*: `{server_id or 'UNKNOWN'}`\n"
    content += f"• *Time*: `{current_time}`\n"
    
    if success and new_time:
        content += f"• *New Expiry*: `{new_time}`"
    elif not success and error_message:
        content += f"• *Error*: `{error_message}`"
    
    with open('last_renew_data.txt', 'w', encoding='utf-8') as f:
        f.write(content)
    
    send_telegram_message(content)

def handle_cloudflare(page):
    print("Detected Cloudflare challenge...")
    
    # 等待验证自动完成
    try:
        page.wait_for_selector("text=Verify you are human", state="detached", timeout=120000)
        print("Cloudflare verification passed automatically")
        return True
    except:
        print("Manual verification may be required")
        return False

def login_to_dashboard(page):
    try:
        page.goto("https://tickhosting.com/auth/login", wait_until="networkidle", timeout=120000)
        
        # 检查Cloudflare验证
        if "challenge" in page.url:
            if not handle_cloudflare(page):
                raise Exception("Cloudflare verification failed")
        
        # 填写登录表单
        page.fill('input[name="email"]', EMAIL)
        page.fill('input[name="password"]', PASSWORD)
        page.click('button[type="submit"]:has-text("Login")')
        
        # 等待登录完成
        try:
            page.wait_for_selector("text=Dashboard", timeout=30000)
            print("Login successful")
            return True
        except:
            if "login" in page.url:
                raise Exception("Login failed - possible wrong credentials")
            return True
            
    except Exception as e:
        print(f"Login error: {e}")
        update_last_renew_time(False, error_message=f"Login failed: {str(e)}")
        return False

def get_expiration_time(page):
    try:
        # 尝试多种选择器
        selectors = [
            "div:has-text('Expires') >> nth=0",
            "text=EXPIRED",
            ".renew-time"
        ]
        
        for selector in selectors:
            if page.locator(selector).count() > 0:
                return page.locator(selector).first.text_content().strip()
        return None
    except Exception as e:
        print(f"Error getting expiry time: {e}")
        return None

def renew_server(page):
    try:
        # 获取服务器ID
        server_id = re.search(r'/server/([a-f0-9]+)', page.url)
        server_id = server_id.group(1) if server_id else 'UNKNOWN'
        print(f"Processing server: {server_id}")
        
        # 获取当前到期时间
        expiry_text = get_expiration_time(page)
        if not expiry_text:
            raise Exception("Could not get current expiry time")
        print(f"Current expiry: {expiry_text}")
        
        # 查找续期按钮
        renew_button = page.locator("button:has-text('ADD 96 HOUR')").first
        if not renew_button.is_visible():
            raise Exception("Renew button not found")
        
        # 点击续期按钮
        renew_button.click()
        print("Clicked renew button")
        
        # 等待续期完成
        time.sleep(15)
        page.wait_for_load_state("networkidle")
        
        # 获取新的到期时间
        new_expiry_text = get_expiration_time(page)
        if not new_expiry_text:
            raise Exception("Could not get new expiry time")
        print(f"New expiry: {new_expiry_text}")
        
        # 验证续期结果
        if expiry_text and new_expiry_text:
            initial_time = parser.parse(expiry_text.replace("EXPIRED: ", ""))
            new_time = parser.parse(new_expiry_text.replace("EXPIRED: ", ""))
            
            if new_time > initial_time:
                print("Renewal successful!")
                update_last_renew_time(True, new_expiry_text, server_id=server_id)
                return True
            else:
                raise Exception("Expiry time not extended")
        
    except Exception as e:
        print(f"Renewal error: {e}")
        update_last_renew_time(False, error_message=str(e), server_id=server_id)
        return False

def process_server_renewal(page):
    try:
        page.goto("https://tickhosting.com/server", wait_until="networkidle", timeout=60000)
        
        # 查找服务器卡片
        server_card = page.locator(".server-card").first
        if not server_card.is_visible():
            raise Exception("No server cards found")
        
        # 点击进入服务器详情页
        server_card.click()
        page.wait_for_selector(".server-details", timeout=30000)
        
        return renew_server(page)
    except Exception as e:
        print(f"Server renewal process error: {e}")
        return False

def save_debug_info(page, context, success):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    status = "success" if success else "error"
    
    # 保存截图
    screenshot_path = f"debug_{status}_{timestamp}.png"
    page.screenshot(path=screenshot_path, full_page=True)
    
    # 保存页面HTML
    html_path = f"debug_{status}_{timestamp}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(page.content())
    
    print(f"Saved debug info: {screenshot_path}, {html_path}")

def main():
    with sync_playwright() as p:
        browser = None
        try:
            # 启动浏览器
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            # 创建上下文
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-US"
            )
            
            page = context.new_page()
            
            # 登录
            if not login_to_dashboard(page):
                save_debug_info(page, context, False)
                raise Exception("Login failed")
            
            # 执行续期
            if not process_server_renewal(page):
                save_debug_info(page, context, False)
                raise Exception("Renewal process failed")
            
            print("Renewal completed successfully")
            save_debug_info(page, context, True)
            
        except Exception as e:
            print(f"Execution error: {e}")
            if browser:
                save_debug_info(page, context, False)
            update_last_renew_time(False, error_message=str(e))
            
        finally:
            if browser:
                browser.close()

if __name__ == "__main__":
    main()
