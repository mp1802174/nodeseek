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
    print("❌ 错误: 未找到 NS_COOKIE 环境变量！")
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
            except Exception:
                pass
    driver.refresh()
    time.sleep(4)

def do_checkin(driver):
    print("进入签到看板页面...")
    driver.get("https://www.nodeseek.com/board")
    time.sleep(5)
    print(f"当前页面标题: {driver.title}")
    print(f"当前页面URL: {driver.current_url}")

    btn_text = "试试手气" if ns_random else "鸡腿 x 5"
    print(f"【方式一】寻找网页签到按钮【{btn_text}】...")

    try:
        xpath = f"//button[contains(., '{btn_text}')] | //button[contains(text(), '{btn_text}')]"
        button = WebDriverWait(driver, 6).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        button.click()
        print(f"✅ 成功点击【{btn_text}】按钮！")
        time.sleep(3)
    except Exception as e:
        print(f"界面按钮未命中或已被签过: {e}")

    # 方式二: 通过浏览器上下文直接调用 NodeSeek 的 POST /api/attendance
    print("【方式二】在浏览器上下文中调用签到接口 /api/attendance...")
    try:
        js_code = """
        const cb = arguments[arguments.length - 1];
        const isRandom = arguments[0];
        fetch('/api/attendance?random=' + (isRandom ? 'true' : 'false'), {
            method: 'POST',
            headers: {
                 'Content-Type': 'application/json',
                 'Accept': 'application/json'
            }
        })
        .then(r => r.json())
        .then(d => cb(d))
        .catch(err => cb({error: err.toString()}));
        """
        res = driver.execute_async_script(js_code, ns_random)
        print(f"接口返回数据: {res}")
        if isinstance(res, dict):
            if res.get("success"):
                print(f"🎉 签到成功！{res.get('message', '')}")
            else:
                msg = res.get("message", "")
                if "已签到" in msg or "already" in msg.lower():
                    print(f"ℹ️ 提示: {msg}")
                else:
                    print(f"接口响应: {res}")
    except Exception as e:
        print(f"接口执行出错: {e}")

    # 打印页面状态提示
    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text
        for line in body_text.splitlines():
            line_str = line.strip()
            if any(k in line_str for k in ["签到", "连签", "获得鸡腿", "鸡腿"]):
                if len(line_str) < 60:
                    print(f"页面状态: {line_str}")
    except Exception:
        pass

def main():
    driver = None
    try:
        driver = setup_driver()
        load_cookies(driver, cookie)
        do_checkin(driver)
        print("=== 纯签到任务全部顺利完成 ===")
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
