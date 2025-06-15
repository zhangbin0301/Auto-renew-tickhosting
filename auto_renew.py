import os
from playwright.sync_api import sync_playwright
from datetime import datetime
import time
from dateutil import parser
import requests
import re

# 配置
EMAIL = os.getenv('EMAIL', 'your_email@example.com')
PASSWORD = os.getenv('PASSWORD', 'your_password')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram 通知未配置")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Telegram 通知发送成功")
    except Exception as e:
        print(f"发送 Telegram 通知失败: {e}")

def update_last_renew_time(success, new_time=None, error_message=None, server_id=None):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "成功" if success else "失败"
    
    content = f"服务器ID: {server_id or '未知'}\n"
    content += f"续期状态: {status}\n"
    content += f"操作时间: {current_time}\n"
    
    if success and new_time:
        content += f"新的到期时间: {new_time}"
    elif not success and error_message:
        content += f"错误信息: {error_message}"
    
    with open('last_renew_data.txt', 'w', encoding='utf-8') as f:
        f.write(content)
    
    telegram_message = f"Tickhosting 续期通知\n{content}"
    send_telegram_message(telegram_message)

def handle_cloudflare(page):
    print("检测到 Cloudflare 验证...")
    
    try:
        # 等待验证自动完成
        page.wait_for_selector("#challenge-stage", state="hidden", timeout=60000)
        print("Cloudflare 验证已自动通过")
        return True
    except:
        print("自动验证未通过，尝试模拟人类行为...")
        
        # 模拟人类操作
        page.mouse.move(100, 100)
        page.mouse.move(200, 200)
        page.mouse.wheel(0, 100)
        page.mouse.wheel(0, -50)
        time.sleep(10)
        
        if "challenge" not in page.url:
            print("验证通过")
            return True
        
        print("需要手动干预完成验证")
        input("请在浏览器中完成验证后按回车继续...")
        return True

def login_to_dashboard(page):
    try:
        page.goto("https://tickhosting.com/auth/login", wait_until="networkidle", timeout=60000)
        
        if "challenge" in page.url and not handle_cloudflare(page):
            raise Exception("Cloudflare 验证失败")
        
        page.fill('input[name="email"]', EMAIL)
        page.fill('input[name="password"]', PASSWORD)
        page.click('button[type="submit"]:has-text("Login")')
        
        try:
            page.wait_for_selector(".dashboard", timeout=30000)
            print("登录成功")
            return True
        except:
            if "login" in page.url:
                raise Exception("登录失败，可能凭证错误或验证未完成")
            return True
            
    except Exception as e:
        print(f"登录过程中出错: {e}")
        send_telegram_message(f"登录失败: {str(e)}")
        return False

def get_expiration_time(page):
    try:
        selectors = [
            ".RenewBox___StyledP-sc-1inh2rq-4",
            ".expiry-time",
            "div:has-text('Expires')"
        ]
        
        for selector in selectors:
            if page.locator(selector).count() > 0:
                return page.locator(selector).first.text_content()
        return None
    except Exception as e:
        print(f"获取到期时间出错: {e}")
        return None

def renew_server(page):
    try:
        server_id = re.search(r'/server/([a-f0-9]+)', page.url)
        server_id = server_id.group(1) if server_id else '未知'
        
        print(f"正在处理服务器: {server_id}")
        
        expiry_text = get_expiration_time(page)
        if not expiry_text:
            raise Exception("无法获取当前到期时间")
        print(f"当前到期时间: {expiry_text}")
        
        renew_button = page.locator('button:has-text("ADD 96 HOUR")').first
        if not renew_button.is_visible():
            raise Exception("未找到续期按钮")
        
        renew_button.click()
        time.sleep(10)
        
        new_expiry_text = get_expiration_time(page)
        if not new_expiry_text:
            raise Exception("无法获取新的到期时间")
        print(f"新的到期时间: {new_expiry_text}")
        
        if expiry_text and new_expiry_text:
            initial_time = parser.parse(expiry_text.replace("EXPIRED: ", ""))
            new_time = parser.parse(new_expiry_text.replace("EXPIRED: ", ""))
            
            if new_time > initial_time:
                print("续期成功")
                update_last_renew_time(True, new_expiry_text, server_id=server_id)
                return True
            else:
                raise Exception("到期时间未更新")
        
    except Exception as e:
        print(f"续期过程中出错: {e}")
        update_last_renew_time(False, error_message=str(e), server_id=server_id)
        return False

def process_server_renewal(page):
    try:
        page.goto("https://tickhosting.com/server", wait_until="networkidle")
        
        server_link = page.locator(".server-card a").first
        if not server_link.is_visible():
            raise Exception("未找到服务器卡片")
        
        server_link.click()
        page.wait_for_selector(".server-status", timeout=30000)
        
        return renew_server(page)
    except Exception as e:
        print(f"服务器续期流程出错: {e}")
        return False

def save_debug_info(page, context):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    page.screenshot(path=f"debug_{timestamp}.png", full_page=True)
    with open(f"debug_{timestamp}.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    print(f"已保存调试信息: debug_{timestamp}.png/html")

def main():
    with sync_playwright() as p:
        browser = None
        try:
            browser = p.chromium.launch(
                headless=False,  # 生产环境改为 True
                slow_mo=100,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                timezone_id="America/New_York",
                # storage_state="auth.json"  # 取消注释以使用持久化登录
            )
            
            page = context.new_page()
            
            if not login_to_dashboard(page):
                save_debug_info(page, context)
                raise Exception("登录失败")
            
            if not process_server_renewal(page):
                save_debug_info(page, context)
                raise Exception("续期流程失败")
            
            print("续期流程完成")
            
        except Exception as e:
            print(f"执行出错: {e}")
            if browser:
                save_debug_info(page, context)
            send_telegram_message(f"自动续期失败: {str(e)}")
            update_last_renew_time(False, error_message=str(e))
            
        finally:
            if browser:
                browser.close()

if __name__ == "__main__":
    # 安装 Playwright 浏览器（首次运行需要）
    # import playwright
    # playwright.install()
    main()
