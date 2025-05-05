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
print(f"NS_RANDOM: {ns_random}") # Check if NS_RANDOM needs a default or specific value if empty

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

        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent" # Using gemini-pro as flash model might change, adjust if needed
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        response = requests.post(f"{url}?key={GEMINI_API_KEY}", headers=headers, json=data, timeout=20) # Increased timeout slightly
        response.raise_for_status()

        result = response.json()
        # Handle potential API response structure variations
        candidates = result.get("candidates", [])
        if not candidates:
            print("Gemini API 返回无候选回复")
            return None
        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if not parts:
             print("Gemini API 返回无内容部分")
             return None
        reply = parts[0].get("text", "")

        # 清理回复，去除多余换行或符号
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
        traceback.print_exc() # Print traceback for unexpected errors
        return None

def extract_post_content(driver):
    """
    提取帖子标题和正文内容
    """
    try:
        # 获取标题
        title_element = WebDriverWait(driver, 15).until( # Slightly increased wait
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'h1.subject')) # More specific selector for title if possible, adjust if needed
        )
        post_title = title_element.text.strip()

        # 获取正文（取首段） - Adjust selector based on actual NodeSeek structure
        content_element = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '.message')) # Assuming post content is within a div with class 'message', adjust if needed
        )
        # Get text from all relevant child elements if content is split
        post_content = ' '.join(p.text for p in content_element.find_elements(By.TAG_NAME, 'p'))[:500] # Limit length
        if not post_content: # Fallback if content is directly in the element
             post_content = content_element.text.strip()[:500]

        print(f"提取到标题: {post_title}")
        # print(f"提取到内容片段: {post_content[:100]}...") # Optionally print content snippet for debug
        return post_title, post_content
    except Exception as e:
        print(f"提取帖子内容出错：{str(e)}")
        print(f"当前页面 URL: {driver.current_url}") # Log URL on error
        # Optionally save page source for debugging
        # with open("extract_error_page.html", "w", encoding="utf-8") as f:
        #    f.write(driver.page_source)
        return "未知标题", "未知内容"

def click_sign_icon(driver):
    """
    尝试点击签到图标和试试手气按钮的通用方法
    """
    try:
        print("尝试导航到签到页面 (通常在用户中心)...")
        # NodeSeek sign-in might be on a specific page, not just an icon on homepage
        # Try navigating directly if URL is known, e.g., driver.get('https://www.nodeseek.com/usr/xxx')
        # If it's triggered by a dropdown, need to simulate clicks
        # Example: Click user avatar, then click sign-in link
        # This part needs accurate selectors based on NodeSeek's current layout

        # Assuming direct navigation or icon is available after login
        # Attempting to find the sign-in button/link - **SELECTOR NEEDS VERIFICATION**
        sign_in_button_xpath = "//a[contains(text(), '签到')] | //button[contains(text(), '签到')] | //span[contains(@title, '签到') or contains(text(),'签到')]" # More flexible XPath
        print(f"查找签到按钮/链接，XPath: {sign_in_button_xpath}")
        sign_icon = WebDriverWait(driver, 30).until(
             EC.element_to_be_clickable((By.XPATH, sign_in_button_xpath))
        )
        print("找到签到元素，准备点击...")

        # 确保元素可见和可点击
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", sign_icon)
        time.sleep(1) # Increased sleep after scroll

        print(f"签到元素: {sign_icon.tag_name}, Text: {sign_icon.text}, OuterHTML snippet: {sign_icon.get_attribute('outerHTML')[:100]}")

        # 尝试点击
        try:
            sign_icon.click()
            print("签到元素点击成功")
        except Exception as click_error:
            print(f"直接点击失败，尝试使用 JavaScript 点击: {str(click_error)}")
            driver.execute_script("arguments[0].click();", sign_icon)
            print("JavaScript 点击尝试完成")

        print("等待签到操作完成或页面跳转...")
        time.sleep(5) # Wait for potential modal or page change

        # 打印当前URL
        print(f"签到操作后当前页面URL: {driver.current_url}")

        # 点击"试试手气"或"鸡腿 x 5"按钮 (Selectors need verification)
        # These buttons might appear in a modal after clicking sign-in
        try:
            lucky_button_xpath = "//button[contains(text(), '试试手气')]"
            fixed_reward_xpath = "//button[contains(text(), '鸡腿 x 5')]" # Adjust text if needed

            if ns_random == "true": # Check string "true"
                print("NS_RANDOM is true, looking for '试试手气' button")
                click_button = WebDriverWait(driver, 10).until( # Increased wait for modal
                    EC.element_to_be_clickable((By.XPATH, lucky_button_xpath))
                )
                print("找到'试试手气'按钮")
            else:
                print("NS_RANDOM is not true, looking for '鸡腿 x 5' button")
                click_button = WebDriverWait(driver, 10).until( # Increased wait for modal
                    EC.element_to_be_clickable((By.XPATH, fixed_reward_xpath))
                )
                print("找到'鸡腿 x 5'按钮")

            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", click_button)
            time.sleep(0.5)
            click_button.click()
            print("完成奖励按钮点击")
            time.sleep(3) # Wait for action to complete

        except Exception as lucky_error:
            print(f"奖励按钮点击失败 (可能已签到或按钮未出现/选择器错误): {str(lucky_error)}")

        return True

    except Exception as e:
        print(f"签到过程中出错:")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        print(f"当前页面URL: {driver.current_url}")
        # print(f"当前页面源码片段: {driver.page_source[:500]}...") # Uncomment for debugging source
        print("详细错误信息:")
        traceback.print_exc()
        return False

def setup_driver_and_cookies():
    """
    初始化浏览器并设置 Cookie
    """
    driver = None # Initialize driver to None
    try:
        if not cookie:
            print("未找到 Cookie 配置")
            return None

        print("开始初始化浏览器...")
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu') # Often needed in headless
        options.add_argument('--window-size=1920,1080') # Set window size

        if headless:
            print("配置 Headless 模式...")
            options.add_argument('--headless=new') # Use new headless mode
            options.add_argument('--disable-blink-features=AutomationControlled') # Keep attempts to hide automation
            # Removed fixed user-agent, let uc handle it unless specifically needed
            # options.add_argument('--user-agent=...')

        # --- START OF MODIFIED SECTION ---
        # Explicitly specify the browser executable installed by setup-chrome in GitHub Actions
        chrome_executable_path = '/opt/hostedtoolcache/setup-chrome/chromium/stable/x64/chrome'

        print(f"检查 Chrome 可执行文件路径: {chrome_executable_path}")

        # Check if running inside GitHub Actions and the path exists
        # Use GITHUB_ACTIONS env var which is 'true' inside Actions
        if os.environ.get("GITHUB_ACTIONS") == "true" and os.path.exists(chrome_executable_path):
            print(f"在 GitHub Actions 环境中运行，并找到 Chrome 路径。强制使用该路径。")
            # Use browser_executable_path argument
            driver = uc.Chrome(browser_executable_path=chrome_executable_path, options=options)
        else:
            if os.environ.get("GITHUB_ACTIONS") == "true":
                 print(f"警告: 在 GitHub Actions 环境中运行，但未找到指定路径的 Chrome: {chrome_executable_path}。")
            print("未使用 GitHub Actions 或未找到指定 Chrome 路径。使用 uc 默认浏览器检测。")
            # Fallback to default behavior (might fail with version mismatch if setup is wrong)
            driver = uc.Chrome(options=options)
        # --- END OF MODIFIED SECTION ---

        print("浏览器驱动初始化完成。")

        # uc aims to handle webdriver flag automatically, these might be redundant/harmful
        # if headless:
        #     try:
        #         driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        #         print("尝试隐藏 navigator.webdriver 标志")
        #     except Exception as script_err:
        #          print(f"隐藏 webdriver 标志时出错: {script_err}")

        print("正在导航到 NodeSeek 并设置 Cookie...")
        driver.get('https://www.nodeseek.com')
        print(f"导航到 {driver.current_url} 完成，等待页面加载...")
        time.sleep(5) # Wait for initial page load

        print("开始设置 Cookies...")
        added_cookies_count = 0
        for cookie_item in cookie.split(';'):
            cookie_item = cookie_item.strip()
            if '=' not in cookie_item:
                print(f"跳过格式错误的 cookie 项: '{cookie_item}'")
                continue
            try:
                name, value = cookie_item.split('=', 1)
                cookie_dict = {
                    'name': name,
                    'value': value,
                    'domain': '.nodeseek.com', # Ensure domain starts with dot
                    'path': '/',
                    'secure': True, # Assume secure cookies are needed for HTTPS
                    'httpOnly': False, # Set httpOnly based on actual cookie, often false for session cookies set via JS
                    'sameSite': 'Lax' # Common value, adjust if needed ('Strict', 'None')
                }
                # print(f"  添加 cookie: Name={name}") # Verbose log if needed
                driver.add_cookie(cookie_dict)
                added_cookies_count += 1
            except Exception as e:
                print(f"设置 Cookie 项 '{name}' 时出错：{str(e)}")
                continue
        print(f"尝试添加了 {added_cookies_count} 个 cookie。")

        print("刷新页面以应用 Cookie...")
        driver.refresh()
        print("等待页面刷新...")
        time.sleep(5) # Wait for page reload after setting cookies
        print(f"刷新后当前页面 URL: {driver.current_url}")
        # Add a check to see if login was successful (e.g., check for username element)
        try:
             WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".user-avatar, .user-name"))) # Adjust selector
             print("登录状态检查：似乎已成功登录 (找到用户元素)。")
        except:
             print("警告：未检测到登录成功状态 (用户元素未找到)。Cookie 可能无效或页面结构已更改。")


        return driver

    except Exception as e:
        print(f"设置浏览器和 Cookie 过程中发生严重错误：{str(e)}")
        traceback.print_exc()
        if driver:
             print("尝试关闭浏览器...")
             driver.quit()
        return None


def nodeseek_comment(driver):
    try:
        print("准备执行评论任务...")
        # Navigate to a section likely to have many posts, e.g., latest posts or specific forum
        target_url = 'https://www.nodeseek.com/latest' # Or specific forum URL
        print(f"导航到目标页面: {target_url}")
        driver.get(target_url)
        print("等待页面加载...")

        # Use a more reliable wait condition for posts
        post_list_selector = ".post-list" # Adjust if needed
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, post_list_selector))
        )
        print("帖子列表容器已加载。查找帖子元素...")

        # Find post items within the list
        posts = driver.find_elements(By.CSS_SELECTOR, f'{post_list_selector} .post-list-item') # Adjust selector as needed
        print(f"初步获取到 {len(posts)} 个帖子元素")

        valid_posts = []
        for post in posts:
             # Check if the post is pinned (often has a specific class or icon)
             is_pinned = post.find_elements(By.CSS_SELECTOR, '.pinned-icon, .icon-thumbtack') # Adjust selector for pinned icon/class
             if not is_pinned:
                 valid_posts.append(post)
        print(f"筛选后得到 {len(valid_posts)} 个非置顶帖子")

        if not valid_posts:
            print("未找到符合条件的帖子进行评论。")
            return

        # Select a random number of posts to interact with
        num_to_select = min(random.randint(20, 25), len(valid_posts))
        selected_posts = random.sample(valid_posts, num_to_select)
        print(f"随机选取 {len(selected_posts)} 个帖子进行处理")

        selected_urls = []
        for post in selected_posts:
            try:
                # Find the link within the post item
                post_link_element = post.find_element(By.CSS_SELECTOR, '.topic-title a, .post-title a') # Adjust selector for post title link
                post_url = post_link_element.get_attribute('href')
                if post_url and post_url.startswith('http'): # Basic validation
                     selected_urls.append(post_url)
                else:
                     print(f"跳过无效 URL: {post_url}")
            except Exception as link_e:
                print(f"从帖子元素提取链接时出错: {link_e}")
                continue

        print(f"准备处理 {len(selected_urls)} 个帖子的 URL")
        comment_count = 0
        MAX_DAILY_COMMENTS = random.randint(20, 25) # Daily limit

        for i, post_url in enumerate(selected_urls):
            if comment_count >= MAX_DAILY_COMMENTS:
                print(f"已达到设置的评论上限 ({MAX_DAILY_COMMENTS})，停止评论")
                break

            try:
                print(f"\n--- 处理第 {i+1}/{len(selected_urls)} 个帖子: {post_url} ---")
                driver.get(post_url)
                print(f"导航到帖子页面完成，等待内容加载...")
                # Wait for main content area to be visible
                WebDriverWait(driver, 20).until(
                     EC.visibility_of_element_located((By.CSS_SELECTOR, 'h1.subject, .message')) # Wait for title or content
                )

                # Simulate reading behavior
                scroll_amount = random.randint(300, 800)
                driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                read_time = random.uniform(3, 7)
                print(f"模拟阅读 {read_time:.1f} 秒...")
                time.sleep(read_time)

                # Extract post title and content
                post_title, post_content = extract_post_content(driver)
                if post_title == "未知标题":
                    print("无法提取帖子标题/内容，跳过此帖")
                    continue

                # Get Gemini reply
                print("正在获取 Gemini 回复...")
                input_text = get_gemini_reply(post_title, post_content)
                if input_text is None:
                    print(f"帖子 {post_url} 获取 Gemini 回复失败，跳过评论")
                    # Log skip
                    with open('comment_log.txt', 'a', encoding='utf-8') as f:
                        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: Skipped comment on {post_url} due to Gemini API failure or invalid reply\n")
                    continue

                # Decide action type (comment, like, both) - keep previous logic
                action_type = random.choices(
                    ['comment_only', 'like_only', 'both'], weights=[0.5, 0.3, 0.2], k=1
                )[0]
                print(f"决定执行操作: {action_type}")

                # Perform Commenting
                if action_type in ['comment_only', 'both']:
                    print("尝试进行评论...")
                    try:
                        # Wait for the comment editor (CodeMirror or textarea)
                        editor_selector = ".CodeMirror" # Assuming CodeMirror, adjust if it's a textarea
                        editor = WebDriverWait(driver, 30).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, editor_selector))
                        )
                        # Scroll editor into view
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", editor)
                        time.sleep(1)

                        # Click editor to focus (CodeMirror might need specific interaction)
                        # For CodeMirror, clicking the element itself might work
                        editor.click()
                        print("编辑器已点击")
                        time.sleep(1)

                        # Input text using ActionChains for more human-like typing
                        actions = ActionChains(driver)
                        print(f"模拟输入评论: {input_text}")
                        # Find the actual input area within CodeMirror if needed
                        # Sometimes it's a hidden textarea or needs actions.click(editor) first
                        # If direct send_keys to editor fails, try finding internal textarea
                        # actions.send_keys_to_element(editor, input_text) # Alternative if direct send_keys fails
                        for char in input_text:
                            actions.send_keys(char)
                            actions.pause(random.uniform(0.08, 0.25)) # Adjust typing speed
                        actions.perform()
                        print("评论内容输入完成")
                        time.sleep(2)

                        # Find and click the submit button
                        submit_button_xpath = "//button[contains(@class, 'submit') and contains(@class, 'btn') and (contains(text(), '发布评论') or contains(text(), 'Reply'))]" # More flexible xpath
                        submit_button = WebDriverWait(driver, 30).until(
                            EC.element_to_be_clickable((By.XPATH, submit_button_xpath))
                        )
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button)
                        time.sleep(1)
                        submit_button.click()
                        print(f"评论已提交。")
                        comment_count += 1

                        # Log success
                        with open('comment_log.txt', 'a', encoding='utf-8') as f:
                            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: Commented on {post_url} with '{input_text}'\n")

                    except Exception as comment_err:
                         print(f"评论过程中出错: {comment_err}")
                         # Optionally save page source on comment error
                         # with open(f"comment_error_{i}.html", "w", encoding="utf-8") as f:
                         #     f.write(driver.page_source)

                # Perform Liking (加鸡腿) - Function needs implementation or removal
                # if action_type in ['like_only', 'both']:
                #     print("尝试进行点赞 (加鸡腿)...")
                #     # success = click_chicken_leg(driver) # Call your like function here
                #     # print(f"点赞操作完成，结果: {success}")
                #     pass # Placeholder

                # Wait between posts
                wait_time = random.uniform(60, 120) # Reduced wait time to 1-2 minutes for testing, adjust as needed
                print(f"等待 {wait_time:.1f} 秒后处理下一个帖子...")
                time.sleep(wait_time)

            except Exception as post_proc_err:
                print(f"处理帖子 {post_url} 时发生主循环错误：{str(post_proc_err)}")
                traceback.print_exc() # Print full traceback for post processing errors
                continue # Continue to the next post

        print(f"\nNodeSeek 评论任务处理完成。共成功评论 {comment_count} 次。")

    except Exception as main_e:
        print(f"NodeSeek 评论主函数出错：{str(main_e)}")
        traceback.print_exc()
        # Optionally try to save final page source or screenshot
        # driver.save_screenshot("main_error_screenshot.png")

# Placeholder for the like function if you implement it
# def click_chicken_leg(driver):
#     try:
#         print("尝试点击加鸡腿按钮...")
#         # Add robust selectors and logic for clicking like/chicken leg button
#         # Handle confirmations, errors (e.g., already liked, post too old)
#         # Return True on success, False on failure
#         pass
#     except Exception as e:
#         print(f"加鸡腿失败：{str(e)}")
#         return False

if __name__ == "__main__":
    start_time = time.time()
    print(f"--- NodeSeek 脚本开始执行 @ {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    driver = None # Ensure driver is initialized
    try:
        driver = setup_driver_and_cookies()

        if driver:
            print("\n--- 浏览器初始化成功，开始执行任务 ---")
            # Perform comment task first
            nodeseek_comment(driver)

            # Then perform sign-in task
            print("\n--- 开始执行签到任务 ---")
            click_sign_icon(driver)
            print("--- 签到任务执行完毕 ---")

        else:
            print("浏览器初始化失败，无法执行任务。")
            exit(1) # Exit if setup failed

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
