from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
import time
from dateutil import parser
import os
import requests
import re

# 从环境变量读取登录凭据，默认使用PTERODACTYL_SESSION，账号密码作为备用方案，请在settings-actons里设置环境变量 
EMAIL = os.getenv('EMAIL', '')        # 登录邮箱
PASSWORD = os.getenv('PASSWORD', '')  # 登录密码
SESSION_COOKIE = os.getenv('PTERODACTYL_SESSION', '')

# Telegram Bot 通知配置（可选）
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--start-maximized')
    options.add_argument('--enable-logging')
    options.add_argument('--v=1')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    return webdriver.Chrome(options=options)

def add_cookies(driver):
    print("Current cookies before adding:", driver.get_cookies())
    driver.delete_all_cookies()
    cookies = [
        {
            'name': 'PTERODACTYL_SESSION',
            'value': os.environ['PTERODACTYL_SESSION'],
            'domain': '.tickhosting.com'
        },
        {
            'name': 'pterodactyl_session',
            'value': os.environ['PTERODACTYL_SESSION'],
            'domain': '.tickhosting.com'
        }
    ]
    for cookie in cookies:
        try:
            driver.add_cookie(cookie)
            print(f"Added cookie: {cookie['name']}")
        except Exception as e:
            print(f"Error adding cookie {cookie['name']}: {str(e)}")
    
    print("Current cookies after adding:", driver.get_cookies())

def login_to_dashboard(driver):
    # try cookie login frist
    try:
        print("Attempting to login with cookies...")
        driver.get("https://tickhosting.com/")
        time.sleep(5)
        
        print("Adding cookies...")
        add_cookies(driver)
        
        print("Refreshing page after adding cookies...")
        driver.refresh()
        time.sleep(5)
        
        dashboard_urls = [
            'https://tickhosting.com'
        ]
        
        for url in dashboard_urls:
            try:
                print(f"Attempting to navigate to: {url}")
                driver.get(url)
                time.sleep(5)
                
                print(f"Current URL after navigation: {driver.current_url}")
                print(f"Current page title: {driver.title}")
                
                if driver.current_url.startswith('https://tickhosting.com') and 'Dashboard' in driver.title:
                    print("Cookie login successful!")
                    return True
            except Exception as e:
                print(f"Failed to navigate to {url}: {e}")
        
        print("Cookie login failed to reach dashboard.")
    except Exception as e:
        print(f"Cookie login error: {str(e)}")
    
    # if cookie login fails, try email and password
    try:
        if not EMAIL or not PASSWORD:
            raise ValueError("Email or password not set in environment variables")
        
        print("Attempting to login with email and password...")
        driver.get('https://tickhosting.com/auth/login')
        
        # wait for the login page to load
        time.sleep(8)
        
        # try different email and password input selectors
        email_selectors = [
            (By.NAME, 'username'),  
            (By.ID, 'email'),
            (By.NAME, 'email'),
            (By.XPATH, "//input[@type='email']"),
        ]
        
        password_selectors = [
            (By.NAME, 'password'),  
            (By.ID, 'password'),
            (By.XPATH, "//input[@type='password']"),
        ]
        
        login_button_selectors = [
            (By.XPATH, "//button[@type='submit']"),
            (By.XPATH, "//button[contains(text(), 'Login')]"),
        ]
        
        # find the email and password input fields
        email_input = None
        for selector in email_selectors:
            try:
                email_input = driver.find_element(*selector)
                print(f"Found email input with selector: {selector}")
                break
            except Exception as e:
                print(f"Failed to find email input with selector {selector}: {e}")
        
        if not email_input:
            raise Exception("Could not find email input field")
        
        password_input = None
        for selector in password_selectors:
            try:
                password_input = driver.find_element(*selector)
                print(f"Found password input with selector: {selector}")
                break
            except Exception as e:
                print(f"Failed to find password input with selector {selector}: {e}")
        
        if not password_input:
            raise Exception("Could not find password input field")
        
        login_button = None
        for selector in login_button_selectors:
            try:
                login_button = driver.find_element(*selector)
                print(f"Found login button with selector: {selector}")
                break
            except Exception as e:
                print(f"Failed to find login button with selector {selector}: {e}")
        
        if not login_button:
            raise Exception("Could not find login button")
        
        email_input.clear()
        email_input.send_keys(EMAIL)
        password_input.clear()
        password_input.send_keys(PASSWORD)
        
        login_button.click()
        
        time.sleep(10)
        
        dashboard_urls = [
            'https://tickhosting.com'
        ]
        
        for url in dashboard_urls:
            try:
                print(f"Attempting to navigate to: {url}")
                driver.get(url)
                time.sleep(5)
                
                print(f"Current URL after email login: {driver.current_url}")
                print(f"Current page title: {driver.title}")
                
                if driver.current_url.startswith('https://tickhosting.com') and 'Dashboard' in driver.title:
                    print("Email/password login successful!")
                    return True
            except Exception as e:
                print(f"Failed to navigate to {url}: {e}")
        
        raise Exception("Login did not reach dashboard")
    
    except Exception as e:
        print(f"Login failed: {str(e)}")
        # 发送 Telegram 通知
        send_telegram_message(f"Auto Renew Login Error: {str(e)}")
        return False

def try_login(driver):
    try:
        print("\nAttempting to navigate to dashboard...")
        driver.get("https://tickhosting.com")
        time.sleep(5)
        print(f"URL after navigation: {driver.current_url}")
        
        # Check if we're on the dashboard
        if driver.title == "Dashboard":
            print("Successfully reached dashboard")
            return True
            
        print("\nPage title:", driver.title)
        print("\nPage source preview:")
        print(driver.page_source[:2000])
        return False
        
    except Exception as e:
        print(f"Error during login attempt: {str(e)}")
        return False

def login_with_credentials(driver):
    try:
        # get the login page
        driver.get('https://tickhosting.com/auth/login')
        
        # wait for the login page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'email'))
        )
        
        # Locate the mailbox and password input box
        email_input = driver.find_element(By.NAME, 'email')
        password_input = driver.find_element(By.NAME, 'password')
        
        email_input.clear()
        email_input.send_keys(EMAIL)
        password_input.clear()
        password_input.send_keys(PASSWORD)
        
        # Locate and click the login button
        login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Login') or contains(text(), '登录')]")
        login_button.click()
        
        # wait for login to complete
        WebDriverWait(driver, 10).until(
            EC.url_contains('dashboard')
        )
        
        print("Login successful!")
        return True
    
    except Exception as e:
        print(f"Login failed: {str(e)}")
        return False

def wait_and_find_element(driver, by, value, timeout=20, description=""):
    try:
        print(f"Waiting for element: {description} ({value})")
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        time.sleep(2)
        print(f"Found element: {description}")
        return element
    except Exception as e:
        print(f"Failed to find element: {description}")
        print(f"Error: {str(e)}")
        print(f"Current URL: {driver.current_url}")
        print(f"Page source: {driver.page_source[:1000]}...")
        driver.save_screenshot(f'debug_{description.lower().replace(" ", "_")}.png')
        raise

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram bot token or chat ID not configured. Skipping Telegram notification.")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  
        print("Telegram notification sent successfully.")
        return True
    except Exception as e:
        print(f"Failed to send Telegram notification: {e}")
        return False

def update_last_renew_time(success, new_time=None, error_message=None, server_id=None):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    status = "Success" if success else "Failed"
    
    content = f"Server ID: {server_id or 'Unknown'}\n"
    content += f"Renew status: {status}\n"
    content += f"Last renewal time: {current_time}\n"
    
    # if rennew successfuul，add new expiration time
    if success and new_time:
        content += f"New expiration time: {new_time}"
    elif not success and error_message:
        content += f"Error: {error_message}"
    
    with open('last_renew_data.txt', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # send Telegram notification
    telegram_message = f"**Tickhosting Server Renewal Notification**\n{content}"
    send_telegram_message(telegram_message)

def get_expiration_time(driver):
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, ".RenewBox___StyledP-sc-1inh2rq-4")
        
        if elements:
            expiry_text = elements[0].text
            print(f"Found expiration time: {expiry_text}")
            
            if expiry_text.startswith("EXPIRED: "):
                expiry_text = expiry_text.replace("EXPIRED: ", "").strip()
            
            return expiry_text
        else:
            print("No expiration time elements found")
            return None
    
    except Exception as e:
        print(f"Error finding expiration time: {e}")
        return None

def main():
    driver = None
    try:
        print("Starting browser...")
        driver = setup_driver()
        driver.set_page_load_timeout(30)
        
        print("Navigating to website...")
        driver.get("https://tickhosting.com")
        time.sleep(5)
        
        # try login to dashboard
        if not login_to_dashboard(driver):
            raise Exception("Unable to login to dashboard")
        
        print("Refreshing page after login...")
        driver.refresh()
        time.sleep(5)  # Give more time for the page to load

        print(f"Current URL after refresh: {driver.current_url}")
        print("Taking screenshot of current page state...")
        driver.save_screenshot('debug_after_refresh.png')

        if not try_login(driver):
            raise Exception("Failed to reach dashboard")
        
        print("\nLooking for server elements...")
        selectors = [
            ("xpath", "//div[contains(@class, 'status-bar')]"),
            ("xpath", "//div[contains(@class, 'server-status')]"),
            ("xpath", "//div[contains(@class, 'server-card')]"),
            ("css", ".status-bar"),
            ("css", ".server-card")
        ]

        # Wait for page to fully load
        print("Waiting for page to fully load...")
        time.sleep(10)
        
        print("Taking screenshot before looking for status elements...")
        driver.save_screenshot('debug_before_status.png')
        
        print("Current page title:", driver.title)
        print("Current URL:", driver.current_url)
        
        server_element = None
        for selector_type, selector in selectors:
            try:
                print(f"Trying {selector_type} selector: {selector}")
                if selector_type == "xpath":
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                if elements:
                    print(f"Found {len(elements)} elements with {selector_type} selector: {selector}")
                    for element in elements:
                        try:
                            print(f"Element text: {element.text}")
                            print(f"Element HTML: {element.get_attribute('outerHTML')}")
                        except:
                            pass
                    server_element = elements[0]
                    break
            except Exception as e:
                print(f"Failed with {selector_type} selector {selector}: {str(e)}")
                continue

        if not server_element:
            raise Exception("Could not find server element with any selector")

        print("Clicking server element...")
        driver.execute_script("arguments[0].click();", server_element)
        
        # Wait for server page to load completely
        print("Waiting for server page to load completely...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Print current URL immediately after page load
        print(f"Server page URL after load: {driver.current_url}")
        
        # Print page title for additional verification
        print(f"Server page title: {driver.title}")

        print("Taking screenshot of server page...")
        driver.save_screenshot('debug_server_page.png')

        # Additional logging to ensure URL is captured
        print(f"Confirmed server page URL: {driver.current_url}")

        # Print full page source
        print("\nFull Page Source (first 10000 characters):")
        print(driver.page_source[:10000])
        
        # print button elements
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"\nTotal buttons found: {len(all_buttons)}")
        for idx, button in enumerate(all_buttons, 1):
            try:
                print(f"Button {idx}:")
                print(f"  Text: '{button.text}'")
                print(f"  Visible: {button.is_displayed()}")
                print(f"  Enabled: {button.is_enabled()}")
                print(f"  Class: '{button.get_attribute('class')}'")
                print(f"  Outer HTML: '{button.get_attribute('outerHTML')}'")
                print("---")
            except Exception as e:
                print(f"Error processing button {idx}: {e}")
        
        # print span elements
        all_spans = driver.find_elements(By.TAG_NAME, "span")
        print(f"\nTotal spans found: {len(all_spans)}")
        for idx, span in enumerate(all_spans, 1):
            try:
                print(f"Span {idx}:")
                print(f"  Text: '{span.text}'")
                print(f"  Class: '{span.get_attribute('class')}'")
                print(f"  Outer HTML: '{span.get_attribute('outerHTML')}'")
                print("---")
            except Exception as e:
                print(f"Error processing span {idx}: {e}")
        
        # get server ID
        try:
            current_url = driver.current_url
            print(f"\nCurrent URL: {current_url}")
            
            server_id_match = re.search(r'/server/([a-f0-9]+)', current_url)
            server_id = server_id_match.group(1) if server_id_match else 'Unknown'
            
            print(f"Extracted Server ID: {server_id}")
        except Exception as e:
            print(f"Error extracting server ID: {e}")
            server_id = 'Unknown'

        renew_selectors = [
            ("xpath", "//span[contains(@class, 'Button___StyledSpan-sc-1qu1gou-2')]/parent::button"),
            ("css", "button.Button__ButtonStyle-sc-1qu1gou-0.beoWBB.RenewBox___StyledButton-sc-1inh2rq-7.hMqrbU"),
            ("xpath", "//button[contains(@class, 'Button__ButtonStyle-sc-1qu1gou-0') and contains(@class, 'RenewBox___StyledButton')]"),
            ("xpath", "//button[.//span[text()='ADD 96 HOUR(S)']]"),
            ("xpath", "//button[.//span[contains(text(), 'ADD 96 HOUR')]]"),
            ("xpath", "//button[@color='primary' and contains(@class, 'Button__ButtonStyle')]")
        ]

        print("\nWaiting for any button to become visible...")
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "button"))
            )
            print("Found at least one button on the page")
        except TimeoutException:
            print("No buttons found after waiting")

        renew_button = None
        for selector_type, selector in renew_selectors:
            try:
                print(f"Looking for renew button with {selector_type}: {selector}")
                if selector_type == "xpath":
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                if elements:
                    print(f"Found {len(elements)} elements with {selector_type}: {selector}")
                    for element in elements:
                        print(f"Element text: {element.text}")
                        print(f"Element HTML: {element.get_attribute('outerHTML')}")
                    renew_button = elements[0]
                    break
            except Exception as e:
                print(f"Failed with {selector_type} selector {selector}: {str(e)}")
                continue

        if not renew_button:
            raise Exception("Could not find renew button")

        # Get initial expiration time
        initial_time = get_expiration_time(driver)
        
        # Click renew button
        renew_button.click()

        # Wait for page to update
        time.sleep(70)  # Increased wait time
        driver.refresh()
        time.sleep(8)  # Additional wait after refresh

        new_expiration_time = get_expiration_time(driver)

        if initial_time and new_expiration_time:
            try:
                initial_datetime = parser.parse(initial_time)
                new_datetime = parser.parse(new_expiration_time)
                
                if new_datetime > initial_datetime:
                    print("Renewal successful! Time has been extended.")
                    print(f"Initial time: {initial_time}")
                    print(f"New time: {new_expiration_time}")
                    update_last_renew_time(
                        success=True, 
                        new_time=new_expiration_time, 
                        server_id=server_id
                    )
                else:
                    print("Renewal may have failed. Time was not extended.")
                    update_last_renew_time(
                        success=False, 
                        error_message="Time not extended",
                        server_id=server_id
                    )
            except Exception as e:
                print(f"Error parsing dates: {str(e)}")
                update_last_renew_time(
                    success=False, 
                    error_message=f"Date parsing error: {str(e)}",
                    server_id=server_id
                )
        else:
            print("Could not verify renewal - unable to get expiration times")
            update_last_renew_time(
                success=False, 
                error_message="Could not find expiration times",
                server_id=server_id
            )

    except TimeoutException as e:
        error_msg = f"Timeout error: {str(e)}"
        print(error_msg)
        if driver:
            print(f"Current URL: {driver.current_url}")
            driver.save_screenshot('error_timeout.png')
        update_last_renew_time(False, error_message=error_msg)
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        print(error_msg)
        if driver:
            print(f"Current URL: {driver.current_url}")
            driver.save_screenshot('error_general.png')
        update_last_renew_time(False, error_message=error_msg)
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                print(f"Error closing browser: {str(e)}")

if __name__ == "__main__":
    main()
