from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
import time
from dateutil import parser
import os

SESSION_COOKIE = os.getenv('PTERODACTYL_SESSION', '')   # 此处单引号里添加名为pterodactyl_session的cookie或在settings-actons里设置secrets环境变量

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

def update_last_renew_time(success, new_time=None, error_message=None):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "Success" if success else "Failed"
    content = f"Last renewal time: {current_time}\nStatus: {status}"
    if new_time:
        content += f"\nNew expiration time: {new_time}"
    if error_message:
        content += f"\nError message: {error_message}"
    
    with open('last_renew_data.txt', 'w', encoding='utf-8') as f:
        f.write(content)

def get_expiration_time(driver):
    expiry_selectors = [
        ("xpath", "//div[contains(text(), 'Expired')]"),
        ("xpath", "//div[contains(text(), 'EXPIRED:')]"),
        ("xpath", "//div[contains(@class, 'expiry')]"),
        ("xpath", "//div[contains(@class, 'server-details')]//div[contains(text(), 'Expires')]"),
        ("xpath", "//span[contains(text(), 'Expires')]"),
        ("xpath", "//div[contains(text(), 'Free server')]")
    ]
    
    for selector_type, selector in expiry_selectors:
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((selector_type, selector))
            )
            expiry_text = element.text
            print(f"Found expiration time: {expiry_text}")
            return expiry_text
        except Exception as e:
            print(f"Failed to find with selector {selector}: {e}")
    
    print("Could not find expiration time with any selector")
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
        
        print("Adding cookies...")
        add_cookies(driver)

        print("Refreshing page after adding cookies...")
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
        
        # Increase wait time to ensure page is fully loaded
        print("Waiting for server page to load completely...")
        time.sleep(15)  # Increase to 15 seconds

        print("Taking screenshot of server page...")
        driver.save_screenshot('debug_server_page.png')

        # Commented out button printing
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        # for idx, button in enumerate(all_buttons):
        #     print(f"Button {idx + 1}:")
        #     print(f"Text: {button.text}")
        #     print(f"Class: {button.get_attribute('class')}")
        #     print(f"HTML: {button.get_attribute('outerHTML')}\n")

        print("\nLooking for renew button...")
        renew_selectors = [
            # Match class name exactly
            ("css", "button.Button__ButtonStyle-sc-1qu1gou-0.beoWBB.RenewBox___StyledButton-sc-1inh2rq-7.hMqrbU"),
            # Match class name partially
            ("xpath", "//button[contains(@class, 'Button__ButtonStyle-sc-1qu1gou-0') and contains(@class, 'RenewBox___StyledButton')]"),
            # Match text content
            ("xpath", "//button[.//span[text()='ADD 96 HOUR(S)']]"),
            ("xpath", "//button[.//span[contains(text(), 'ADD 96 HOUR')]]"),
            # Match color attribute
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
        time.sleep(10)  # Increased wait time
        driver.refresh()
        time.sleep(5)  # Additional wait after refresh

        # Get new expiration time
        new_time = get_expiration_time(driver)

        # Compare times
        if initial_time and new_time:
            try:
                initial_datetime = parser.parse(initial_time)
                new_datetime = parser.parse(new_time)
                
                if new_datetime > initial_datetime:
                    print("Renewal successful! Time has been extended.")
                    print(f"Initial time: {initial_time}")
                    print(f"New time: {new_time}")
                    update_last_renew_time(True, new_time)
                else:
                    print("Renewal may have failed. Time was not extended.")
                    update_last_renew_time(False, error_message="Time not extended")
            except Exception as e:
                print(f"Error parsing dates: {str(e)}")
                update_last_renew_time(False, error_message=f"Date parsing error: {str(e)}")
        else:
            print("Could not verify renewal - unable to get expiration times")
            update_last_renew_time(False, error_message="Could not find expiration times")

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
