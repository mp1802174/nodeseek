# -- coding: utf-8 --
import os
import sys
import time
import traceback
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

print("=== 开始执行 NodeSeek 纯签到任务 ===")
cookie = os.environ.get("NS_COOKIE") or os.environ.get("COOKIE")
ns_random = os.environ.get("NS_RANDOM", "true").lower() == "true"
headless = os.environ.get("HEADLESS", "true").lower() == "true"

if not cookie:
    print("错误: 未找到 NS_COOKIE 环境变量！")
    sys.exit(1)

def setup_driver():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = uc.Chrome(
        options=options,
        driver_executable_path="/usr/local/bin/chromedriver",
        browser_executable_path="/usr/bin/google-chrome",
        use_subprocess=True
    )
    return driver

def load_cookies(driver, cookie_str):
    print("正在进入 NodeSeek 并注入 Cookie...")
    driver.get("https://www.nodeseek.com")
    time.sleep(3)
    
    for item in cookie_str.split(";"):
        if "=" in item:
            name, value = item.strip().split("=", 1)
            try:
                driver.add_cookie({
                    "name": name.strip(),
                    "value": value.strip(),
                    "domain": ".nodeseek.com",
                    "path": "/"
                })
            except Exception as e:
                pass
    driver.refresh()
    time.sleep(3)

def do_checkin(driver):
    print("进入签到看板页面...")
    driver.get("https://www.nodeseek.com/board")
    time.sleep(5)
    print(f"当前页面标题: {driver.title}")
    print(f"当前页面URL: {driver.current_url}")

    btn_text = "试试手气" if ns_random else "鸡腿 x 5"
    print(f"寻找签到按钮: 【{btn_text}】...")

    try:
        xpath = f"//button[contains(text(), {btn_text})]"
        button = WebDriverWait(driver, 8).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        button.click()
        print(f"点击【{btn_text}】签到按钮成功！")
        time.sleep(3)
    except Exception as e:
        print(f"未找到未点击按钮或今日已完成签到: {e}")
        try:
            body_text = driver.find_element(By.TAG_NAME, "body").text
            if "已签到" in body_text or "今日已" in body_text:
                print("页面状态显示：今日已完成签到。")
        except Exception:
            pass

def main():
    driver = None
    try:
        driver = setup_driver()
        load_cookies(driver, cookie)
        do_checkin(driver)
        print("=== 纯签到任务顺利结束 ===")
    except Exception as e:
        print(f"运行异常: {e}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

if __name__ == "__main__":
    main()
