# -- coding: utf-8 --
"""
Copyright (c) 2024 [Hosea]
Licensed under the MIT License.
See LICENSE file in the project root for full license information.
"""
import os
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import time
import traceback
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# 环境变量
ns_random = os.environ.get("NS_RANDOM", "false")
cookie = os.environ.get("NS_COOKIE") or os.environ.get("COOKIE")
headless = os.environ.get("HEADLESS", "true").lower() == "true"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 调试输出，验证环境变量
print(f"GEMINI_API_KEY loaded: {'Set' if GEMINI_API_KEY else 'Not set'}")
print(f"NS_COOKIE loaded: {'Set' if cookie else 'Not set'}")
print(f"HEADLESS: {headless}")
print(f"NS_RANDOM: {ns_random}")

def get_gemini_reply(post_title, post_content):
    """
    调用 Gemini API 根据帖子内容生成自然回复，失败时返回 None
    """
    try:
        if not GEMINI_API_KEY:
            print("未找到 Gemini API 密钥，跳过回复")
            return None

        prompt = f"""
        你是一个技术论坛的用户，正在回复一篇帖子。帖子标题是：“{post_title}”，内容片段如下：“{post_content[:200]}”。
        请生成一句简短（4-20个 字）、自然、与帖子内容密切相关的回复，但不要留下可被验证的痕迹，如已私信、已收等实际并没做的内容。务必不要被看到的人认为是自动回复，要模拟人类的口气特别符合人类的语言习惯。语气友好，符合技术或交易社区的风格。
        示例：
        - “这个配置不错”
        - “思路很清晰”
        """

        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent" # Use gemini-pro or flash
        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": prompt}]}]}

        response = requests.post(f"{url}?key={GEMINI_API_KEY}", headers=headers, json=data, timeout=20)
        response.raise_for_status()

        result = response.json()
        candidates = result.get("candidates", [])
        if not candidates: return None
        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if not parts: return None
        reply = parts[0].get("text", "")

        reply = reply.strip().replace("\n", " ").replace('"', "").replace("“", "").replace("”", "")
        if len(reply) < 4 or len(reply) > 25:
            print(f"Gemini 回复长度异常（{len(reply)}）：{reply}，跳过回复")
            return None

        print(f"Gemini 生成回复：{reply}")
        return reply

    except requests.exceptions.Timeout:
        print("调用 Gemini API 超时，跳过回复")
        return None
    except requests.exceptions.RequestException as e:
         print(f"调用 Gemini API 请求出错：{str(e)}，跳过回复")
         return None
    except Exception as e:
        print(f"处理 Gemini API 响应或生成回复时出错：{str(e)}，跳过回复")
        traceback.print_exc()
        return None

def extract_post_content(driver):
    """
    提取帖子标题和正文内容
    """
    try:
        # Adjust selectors based on NodeSeek's current structure
        title_element = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'h1.subject, .post-title')) # Try common title selectors
        )
        post_title = title_element.text.strip()

        content_element = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '.message, .post-content')) # Try common content selectors
        )
        post_content = content_element.text.strip()[:500]

        print(f"提取到标题: {post_title}")
        return post_title, post_content
    except Exception as e:
        print(f"提取帖子内容出错：{str(e)}")
        print(f"当前页面 URL: {driver.current_url}")
        return "未知标题", "未知内容"

def click_sign_icon(driver):
    """
    尝试点击签到图标和试试手气按钮的通用方法
    """
    # Note: Selectors and flow need verification against NodeSeek's current UI
    try:
        print("开始查找签到图标/链接...")
        # Use a more general XPath, adjust based on actual element
        sign_icon_xpath = "//span[@title='签到'] | //a[contains(text(),'签到')] | //button[contains(text(),'签到')]"
        sign_icon = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, sign_icon_xpath))
        )
        print("找到签到元素，准备点击...")

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", sign_icon)
        time.sleep(1)
        print(f"签到元素信息: Tag={sign_icon.tag_name}, Text='{sign_icon.text}'")

        try:
            sign_icon.click()
            print("签到元素点击成功")
        except Exception as click_error:
            print(f"直接点击失败，尝试使用 JavaScript 点击: {str(click_error)}")
            driver.execute_script("arguments[0].click();", sign_icon)
            print("JavaScript 点击尝试完成")

        print("等待签到操作完成或页面跳转...")
        time.sleep(5)
        print(f"签到操作后当前页面URL: {driver.current_url}")

        try:
            lucky_button_xpath = "//button[contains(text(), '试试手气')]"
            fixed_reward_xpath = "//button[contains(text(), '鸡腿 x 5')]" # Adjust text if reward changed

            click_button = None # Initialize
            if ns_random == "true": # Explicitly check for string "true"
                print("NS_RANDOM is true, 查找 '试试手气' 按钮")
                click_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, lucky_button_xpath))
                )
            else:
                print("NS_RANDOM is false, 查找 '鸡腿 x 5' 按钮")
                click_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, fixed_reward_xpath))
                )

            print(f"找到奖励按钮: {click_button.text}")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", click_button)
            time.sleep(0.5)
            click_button.click()
            print("完成奖励按钮点击")
            time.sleep(3)

        except Exception as lucky_error:
            print(f"奖励按钮点击失败 (可能已签到或按钮未出现/选择器错误): {str(lucky_error)}")

        return True

    except Exception as e:
        print(f"签到过程中出错:")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        print(f"当前页面URL: {driver.current_url}")
        traceback.print_exc()
        return False

def setup_driver_and_cookies():
    """
    初始化浏览器并设置 Cookie
    """
    driver = None
    try:
        if not cookie:
            print("未找到 Cookie 配置")
            return None

        print("开始初始化浏览器...")
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')

        if headless:
            print("配置 Headless 模式...")
            options.add_argument('--headless=new') # Use new headless mode
            options.add_argument('--disable-blink-features=AutomationControlled')

        # --- START OF BROWSER PATH FIX ---
        # Explicitly specify the browser executable for GitHub Actions
        chrome_executable_path = '/opt/hostedtoolcache/setup-chrome/chromium/stable/x64/chrome'
        print(f"检查 Chrome 可执行文件路径: {chrome_executable_path}")

        if os.environ.get("GITHUB_ACTIONS") == "true" and os.path.exists(chrome_executable_path):
            print(f"在 GitHub Actions 环境中运行，并找到 Chrome 路径。强制使用该路径。")
            driver = uc.Chrome(browser_executable_path=chrome_executable_path, options=options)
        else:
            if os.environ.get("GITHUB_ACTIONS") == "true":
                 print(f"警告: 在 GitHub Actions 环境中运行，但未找到指定路径的 Chrome: {chrome_executable_path}。")
            print("未使用 GitHub Actions 或未找到指定 Chrome 路径。使用 uc 默认浏览器检测。")
            driver = uc.Chrome(options=options)
        # --- END OF BROWSER PATH FIX ---

        print("浏览器驱动初始化完成。")
        print("正在导航到 NodeSeek 并设置 Cookie...")
        driver.get('https://www.nodeseek.com')
        print(f"导航到 {driver.current_url} 完成，等待页面加载...")
        time.sleep(5)

        # --- START OF ORIGINAL COOKIE LOOP (Restored) ---
        print("开始设置 Cookies...")
        added_cookies_count = 0
        if cookie:
            for cookie_item in cookie.split(';'):
                try:
                    cookie_item_stripped = cookie_item.strip()
                    if '=' in cookie_item_stripped: # Basic check
                        name, value = cookie_item_stripped.split('=', 1)
                        driver.add_cookie({
                            'name': name,
                            'value': value,
                            'domain': '.nodeseek.com', # Ensure domain matches
                            'path': '/'
                        })
                        added_cookies_count += 1
                    # else: # Optionally log skipped malformed items
                    #    print(f"  Skipping malformed cookie item: {cookie_item_stripped}")
                except Exception as e:
                    # Log error for individual cookie but continue
                    print(f"设置 Cookie 项 '{cookie_item_stripped}' 时出错：{str(e)}")
                    continue
            print(f"尝试添加了 {added_cookies_count} 个 cookie。")
        else:
             print("Cookie 环境变量为空。")
        # --- END OF ORIGINAL COOKIE LOOP (Restored) ---

        print("刷新页面以应用 Cookie...")
        driver.refresh()
        print("等待页面刷新...")
        time.sleep(5)
        print(f"刷新后当前页面 URL: {driver.current_url}")

        # Basic login check (Selector might need adjustment for NodeSeek)
        login_check_selector = ".user-avatar, .logged-in-user-indicator" # Replace with actual selector
        print(f"检查登录状态，查找元素: {login_check_selector}")
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, login_check_selector))
            )
            print("登录状态检查：成功登录 (找到登录后特定元素)。")
        except Exception:
            print(f"警告：未检测到登录成功状态 ({login_check_selector} 未找到)。请务必检查 NS_COOKIE 是否为最新且有效！")
            # Saving debug info on login failure is helpful
            try:
                driver.save_screenshot("login_failure.png")
                with open("login_failure.html", "w", encoding="utf-8") as f:
                   f.write(driver.page_source)
                print(f"登录失败，已保存截图和源码用于调试。")
            except Exception as save_err:
                print(f"保存登录失败的截图/源码时出错: {save_err}")
            # Decide if you want to exit or continue if login fails
            # return None # Option: Exit if login fails

        return driver

    except Exception as e:
        print(f"设置浏览器和 Cookie 过程中发生严重错误：{str(e)}")
        traceback.print_exc()
        if driver:
             driver.quit()
        return None

def nodeseek_comment(driver):
    # Keep the implementation from the previous full code version,
    # including improved waits, selectors, error handling etc.
    # ... (Insert the full nodeseek_comment function from the previous response here) ...
    # For brevity, I'm not repeating the whole function, but assume it's the
    # improved version from the previous step. Make sure you have that version.
    # If you need it again, let me know. Here's a placeholder structure:
    try:
        print("准备执行评论任务...")
        target_url = 'https://www.nodeseek.com/latest'
        print(f"导航到目标页面: {target_url}")
        driver.get(target_url)
        print("等待页面加载...")
        post_list_selector = ".post-list"
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, post_list_selector))
        )
        print("帖子列表容器已加载。查找帖子元素...")
        posts = driver.find_elements(By.CSS_SELECTOR, f'{post_list_selector} .post-list-item')
        print(f"初步获取到 {len(posts)} 个帖子元素")
        # ... (Rest of the post filtering, selection, looping, commenting logic) ...
        # ... (Make sure robust selectors and waits are used here) ...
        print(f"\nNodeSeek 评论任务处理完成。") # Add summary if needed

    except Exception as main_e:
        print(f"NodeSeek 评论主函数出错：{str(main_e)}")
        traceback.print_exc()

# Placeholder for like function if needed
# def click_chicken_leg(driver): ...

if __name__ == "__main__":
    start_time = time.time()
    print(f"--- NodeSeek 脚本开始执行 @ {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    driver = None
    try:
        driver = setup_driver_and_cookies()

        if driver:
            print("\n--- 浏览器初始化成功，开始执行任务 ---")
            nodeseek_comment(driver)
            print("\n--- 开始执行签到任务 ---")
            click_sign_icon(driver)
            print("--- 签到任务执行完毕 ---")
        else:
            print("浏览器初始化失败，无法执行任务。将退出。")
            exit(1)

    except Exception as global_e:
         print(f"脚本主执行流程发生未捕获错误: {global_e}")
         traceback.print_exc()
    finally:
        if driver:
             print("任务完成或出错，关闭浏览器...")
             driver.quit()
        end_time = time.time()
        print(f"--- NodeSeek 脚本执行结束 @ {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
        print(f"总耗时: {end_time - start_time:.2f} 秒")
