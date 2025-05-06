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

        # 设计提示，确保回复简短、符合论坛风格
        prompt = f"""
        你是一个技术论坛的用户，正在回复一篇帖子。帖子标题是：“{post_title}”，内容片段如下：“{post_content[:200]}”。
        请生成一句简短（4-20个 字）、自然、与帖子内容密切相关的回复，但不要留下可被验证的痕迹，如已私信、已收等实际并没做的内容。务必不要被看到的人认为是自动回复，要模拟人类的口气特别符合人类的语言习惯。语气友好，符合技术或交易社区的风格。
        示例：
        - “这个配置不错”
        - “思路很清晰”
        """

        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent" # Using updated model name
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        response = requests.post(f"{url}?key={GEMINI_API_KEY}", headers=headers, json=data, timeout=10)
        response.raise_for_status()

        result = response.json()
        reply = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")

        # 清理回复，去除多余换行或符号
        reply = reply.strip().replace("\n", " ").replace('"', "").replace("“", "").replace("”", "")
        if len(reply) < 4 or len(reply) > 25:
            print(f"Gemini 回复长度异常（{len(reply)}）：{reply}，跳过回复")
            return None

        print(f"Gemini 生成回复：{reply}")
        return reply

    except Exception as e:
        print(f"调用 Gemini API 出错：{str(e)}，跳过回复")
        return None

def extract_post_content(driver):
    """
    提取帖子标题和正文内容
    """
    try:
        # 获取标题 (Original selectors)
        title_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.post-title'))
        )
        post_title = title_element.text.strip()

        # 获取正文（取首段） (Original selectors)
        content_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.post-content'))
        )
        post_content = content_element.text.strip()[:500]  # 限制长度

        return post_title, post_content
    except Exception as e:
        print(f"提取帖子内容出错：{str(e)}")
        return "未知标题", "未知内容"

def click_sign_icon(driver):
    """
    尝试点击签到图标和试试手气按钮的通用方法
    """
    try:
        print("开始查找签到图标...")
        # 使用更精确的选择器定位签到图标
        sign_icon = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//span[@title='签到']"))
        )
        print("找到签到图标，准备点击...")
        
        # 确保元素可见和可点击
        driver.execute_script("arguments[0].scrollIntoView(true);", sign_icon)
        time.sleep(0.5)
        
        # 打印元素信息
        print(f"签到图标元素: {sign_icon.get_attribute('outerHTML')}")
        
        # 尝试点击
        try:
            
            
            sign_icon.click()
            print("签到图标点击成功")
        except Exception as click_error:
            print(f"点击失败，尝试使用 JavaScript 点击: {str(click_error)}")
            driver.execute_script("arguments[0].click();", sign_icon)
        
        print("等待页面跳转...")
        time.sleep(5)
        
        # 打印当前URL
        print(f"当前页面URL: {driver.current_url}")
        
        # 点击"试试手气"按钮
        try:
            click_button:None
            
            if ns_random:
                click_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '试试手气')]"))
            )
            else:
                click_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '鸡腿 x 5')]"))
            )
            
            click_button.click()
            print("完成试试手气点击")
        except Exception as lucky_error:
            print(f"试试手气按钮点击失败或者签到过了: {str(lucky_error)}")
            
        return True
        
    except Exception as e:
        print(f"签到过程中出错:")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        print(f"当前页面URL: {driver.current_url}")
        print(f"当前页面源码片段: {driver.page_source[:500]}...")
        print("详细错误信息:")
        traceback.print_exc()
        return False

def setup_driver_and_cookies():
    """
    初始化浏览器并设置 Cookie
    """
    driver = None # Initialize driver
    try:
        if not cookie:
            print("未找到 Cookie 配置")
            return None

        print("开始初始化浏览器...")
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        if headless:
            # --- Original Headless Options ---
            options.add_argument('--headless') # Keep original --headless
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            # --- End of Original Headless Options ---

        # ========== START: ONLY MODIFICATION MADE ==========
        # This block replaces the original `driver = uc.Chrome(options=options)` line
        # It handles using the correct browser path in GitHub Actions

        chrome_executable_path = '/opt/hostedtoolcache/setup-chrome/chromium/stable/x64/chrome'
        print(f"检查 Chrome 可执行文件路径: {chrome_executable_path}")

        # Check if running inside GitHub Actions and the path exists
        if os.environ.get("GITHUB_ACTIONS") == "true" and os.path.exists(chrome_executable_path):
            print(f"在 GitHub Actions 环境中运行，并找到 Chrome 路径。强制使用该路径。")
            # Use browser_executable_path argument
            driver = uc.Chrome(browser_executable_path=chrome_executable_path, options=options)
        else:
            # Fallback to default behavior if not in Actions or path not found
            if os.environ.get("GITHUB_ACTIONS") == "true":
                 print(f"警告: 在 GitHub Actions 环境中运行，但未找到指定路径的 Chrome: {chrome_executable_path}。")
            print("未使用 GitHub Actions 或未找到指定 Chrome 路径。使用 uc 默认浏览器检测。")
            driver = uc.Chrome(options=options) # Original call as fallback
        # ========== END: ONLY MODIFICATION MADE ==========


        if headless:
            # --- Original headless setup after driver init ---
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.set_window_size(1920, 1080)
            # --- End of original headless setup ---

        print("正在设置 Cookie...")
        driver.get('https://www.nodeseek.com')
        time.sleep(5)

        # --- Original Cookie Loop ---
        for cookie_item in cookie.split(';'):
            try:
                name, value = cookie_item.strip().split('=', 1)
                driver.add_cookie({
                    'name': name,
                    'value': value,
                    'domain': '.nodeseek.com',
                    'path': '/'
                })
            except Exception as e:
                print(f"设置 Cookie 出错：{str(e)}")
                continue
        # --- End of Original Cookie Loop ---

        driver.refresh()
        time.sleep(5)
        # Add basic login check here if desired, but keep it simple or use original if existed
        # Example check (selector needs verification for NodeSeek):
        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".user-avatar")))
            print("登录检查：找到用户头像，可能已登录。")
        except:
            print("登录检查：未找到用户头像。请检查 Cookie 值是否有效！")

        return driver

    except Exception as e:
        print(f"设置浏览器和 Cookie 时出错：{str(e)}")
        traceback.print_exc()
        if driver: # Attempt to quit driver if it was initialized before error
            driver.quit()
        return None

def nodeseek_comment(driver):
    # --- Original nodeseek_comment Function Logic ---
    try:
        print("正在访问交易区...") # Original message used /latest, reverting to '/' as per original code
        target_url = 'https://www.nodeseek.com/'
        driver.get(target_url)
        print("等待页面加载...")

        posts = WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.post-list-item'))
        )
        print(f"成功获取到 {len(posts)} 个帖子")

        valid_posts = [post for post in posts if not post.find_elements(By.CSS_SELECTOR, '.pined')] # Original filter '.pined'
        selected_posts = random.sample(valid_posts, min(random.randint(20, 25), len(valid_posts)))

        selected_urls = []
        for post in selected_posts:
            try:
                post_link = post.find_element(By.CSS_SELECTOR, '.post-title a') # Original selector
                selected_urls.append(post_link.get_attribute('href'))
            except:
                continue

        # is_chicken_leg = False # Original variable, keep if click_chicken_leg is used
        comment_count = 0
        MAX_DAILY_COMMENTS = random.randint(20, 25)  # Original logic

        for i, post_url in enumerate(selected_urls):
            if comment_count >= MAX_DAILY_COMMENTS:
                print("达到每日评论上限，停止评论")
                break

            try:
                print(f"正在处理第 {i+1} 个帖子")
                driver.get(post_url)

                # 模拟浏览
                driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(random.uniform(2, 5))

                # 提取帖子内容
                post_title, post_content = extract_post_content(driver) # Uses original extract function

                # 获取 Gemini 生成的回复
                input_text = get_gemini_reply(post_title, post_content)
                if input_text is None:
                    print(f"帖子 {post_url} 获取回复失败，跳过评论")
                    with open('comment_log.txt', 'a', encoding='utf-8') as f:
                        f.write(f"{time.ctime()}: Skipped comment on {post_url} due to Gemini API failure\n")
                    continue

                # 尝试点赞（加鸡腿）
                action_type = random.choices(
                    ['comment_only', 'like_only', 'both'],
                    weights=[0.5, 0.3, 0.2],
                    k=1
                )[0]

                if action_type in ['comment_only', 'both']:
                    editor = WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.CodeMirror')) # Original selector
                    )
                    editor.click()
                    time.sleep(0.5)

                    actions = ActionChains(driver)
                    for char in input_text:
                        actions.send_keys(char)
                        actions.pause(random.uniform(0.1, 0.3)) # Original timing
                    actions.perform()
                    time.sleep(2)

                    submit_button = WebDriverWait(driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'submit') and contains(@class, 'btn') and contains(text(), '发布评论')]")) # Original selector
                    )
                    driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                    time.sleep(0.5)
                    submit_button.click()

                    print(f"已在帖子 {post_url} 中完成评论：{input_text}")
                    comment_count += 1

                    with open('comment_log.txt', 'a', encoding='utf-8') as f:
                        f.write(f"{time.ctime()}: Commented on {post_url} with '{input_text}'\n")

               # Original like logic was commented out, keeping it that way
               # if action_type in ['like_only', 'both'] and not is_chicken_leg:
               #     is_chicken_leg = click_chicken_leg(driver)

                time.sleep(random.uniform(600, 900))  # Original 10-15 分钟 wait

            except Exception as e:
                print(f"处理帖子 {post_url} 时出错：{str(e)}")
                continue # Original behavior

        print("NodeSeek 评论任务完成")

    except Exception as e:
        print(f"NodeSeek 评论出错：{str(e)}")
        traceback.print_exc()
    # --- End of Original nodeseek_comment Function Logic ---


# --- Original click_chicken_leg Function ---
# def click_chicken_leg(driver):
#     try:
#         print("尝试点击加鸡腿按钮...")
#         chicken_btn = WebDriverWait(driver, 5).until(
#             EC.element_to_be_clickable((By.XPATH, '//div[@class="nsk-post"]//div[@title="加鸡腿"][1]'))
#         )
#         driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", chicken_btn)
#         time.sleep(0.5)
#         chicken_btn.click()
#         print("加鸡腿按钮点击成功")
#
#         WebDriverWait(driver, 5).until(
#             EC.presence_of_element_located((By.CSS_SELECTOR, '.msc-confirm'))
#         )
#
#         try:
#             error_title = driver.find_element(By.XPATH, "//h3[contains(text(), 'This comment was created 7 days ago')]")
#             if error_title:
#                 print("帖子超过 7 天，无法加鸡腿")
#                 ok_btn = driver.find_element(By.CSS_SELECTOR, '.msc-confirm .msc-ok')
#                 ok_btn.click()
#                 return False
#         except:
#             ok_btn = WebDriverWait(driver, 5).until(
#                 EC.element_to_be_clickable((By.CSS_SELECTOR, '.msc-confirm .msc-ok'))
#             )
#             ok_btn.click()
#             print("确认加鸡腿成功")
#
#         WebDriverWait(driver, 5).until_not(
#             EC.presence_of_element_located((By.CSS_SELECTOR, '.msc-overlay'))
#         )
#         time.sleep(1)
#
#         return True
#
#     except Exception as e:
#         print(f"加鸡腿失败：{str(e)}")
#         return False
# --- End of Original click_chicken_leg Function ---


# --- Original Main Execution Block ---
if __name__ == "__main__":
    print("开始执行 NodeSeek 评论脚本...")
    driver = setup_driver_and_cookies() # Uses modified setup function
    if not driver:
        print("浏览器初始化失败")
        exit(1) # Original exit code

    # Original execution order
    nodeseek_comment(driver)
    click_sign_icon(driver)

    # Original script didn't explicitly quit driver in main block, adding it in finally
    # print("脚本执行完成") # Original message

    # Adding finally block for robust driver cleanup
    try:
        pass # Main logic already executed above
    finally:
        if driver:
             print("任务完成或出错，关闭浏览器...")
             driver.quit()
        print("脚本执行完成") # Moved final message here
# --- End of Original Main Execution Block ---
