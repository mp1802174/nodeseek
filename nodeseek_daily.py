# -- coding: utf-8 --
"""
Copyright (c) 2024 [Hosea]
Licensed under the MIT License.
See LICENSE file in the project root for full license information.
"""
print("=== 脚本开始执行 ===")
import sys
print(f"Python 版本: {sys.version}")

print("导入标准库...")
import os
import requests
from bs4 import BeautifulSoup
print("导入 Selenium...")
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import time
import traceback
print("导入 undetected-chromedriver...")
import undetected_chromedriver as uc
print(f"undetected-chromedriver 版本: {uc.__version__}")
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
print("所有库导入完成")


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

def get_gemini_reply(post_title, post_content, is_lottery=False, recent_replies=None):
    """
    调用 Gemini API 根据帖子内容生成自然回复，失败时返回 None
    is_lottery: 是否为抽奖帖子
    recent_replies: 最近使用的回复列表，用于避免重复
    """
    if recent_replies is None:
        recent_replies = []
    try:
        if not GEMINI_API_KEY:
            print("未找到 Gemini API 密钥，跳过回复")
            return None
        
        # 根据是否为抽奖帖子使用不同的提示词
        if is_lottery:
            # 抽奖帖子的提示词
            prompt = f"""
你是一个普通论坛用户，看到抽奖帖子想参与。

标题：{post_title}
内容：{post_content}

规则：
1. 如果帖子明确要求回复特定内容（如"回复'XXX'参与"），必须一字不差地回复那个内容
2. 如果没有明确要求，生成5-12个字的自然回复
3. 回复要像正常人类，不要太简短也不要太复杂
4. 避免AI痕迹词汇："看起来"、"感觉"、"非常"、"支持"
5. 可以表达：参与意愿、对活动的兴趣、简单评价

示例风格（根据实际内容调整）：
- "参与一下"、"试试运气"、"感谢楼主"、"不错的活动"
- 不要：单字"冲"、"蹲"，也不要"看起来很不错，支持一下"

只输出回复内容。
"""
        else:
            # 普通帖子的提示词
            prompt = f"""
你是论坛老用户，看帖后正常回复。

标题：{post_title}
内容：{post_content}

规则：
1. 必须理解帖子内容，回复要相关
2. 6-15个字，自然流畅
3. 像正常人类交流，不要太简短也不要太正式
4. 避免AI痕迹词汇："看起来"、"感觉"、"非常"、"支持"
5. 根据内容类型自然回复：
   - 技术/教程：学到了、这个有用、可以试试
   - 出售/交易：多少钱、配置怎么样、价格合适吗
   - 求助：我也遇到过、可以试试这个
   - 分享：不错、挺好的、有意思

只输出回复内容。
"""
        
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
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
        reply = reply.strip().replace("\n", " ").replace('"', "").replace(""", "").replace(""", "")
        
        # 统一长度限制：5-20字
        if len(reply) < 5 or len(reply) > 20:
            print(f"Gemini 回复长度异常（{len(reply)}）：{reply}，跳过回复")
            return None
        
        # 检查是否与最近的回复重复
        if recent_replies and reply in recent_replies:
            print(f"回复内容重复（{reply}），跳过")
            return None
        
        print(f"Gemini 生成回复（{'抽奖' if is_lottery else '普通'}）：{reply}")
        return reply
        
    except Exception as e:
        print(f"调用 Gemini API 出错：{str(e)}，跳过回复")
        return None

def extract_post_content(driver):
    """
    提取帖子标题和正文内容
    """
    try:
        # 获取标题
        title_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.post-title'))
        )
        post_title = title_element.text.strip()
        
        # 获取正文（取首段）
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
            click_button = None
            
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
    try:
        if not cookie:
            print("未找到 Cookie 配置")
            return None
            
        print("开始初始化浏览器...")
        print(f"当前工作目录: {os.getcwd()}")
        
        # 检查 Chrome 是否已安装
        import subprocess
        try:
            chrome_version = subprocess.check_output(['google-chrome', '--version'], stderr=subprocess.STDOUT).decode().strip()
            print(f"检测到 Chrome: {chrome_version}")
        except Exception as e:
            print(f"无法检测 Chrome 版本: {e}")
        
        # 添加重试机制
        driver = None
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"尝试初始化浏览器 (尝试 {attempt + 1}/{max_retries})...")
                print(f"时间戳: {time.time()}")
                
                # 每次重试都创建新的 ChromeOptions 对象
                options = uc.ChromeOptions()
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-blink-features=AutomationControlled')
                if headless:
                    options.add_argument('--headless=new')
                    options.add_argument('--disable-gpu')
                    options.add_argument('--window-size=1920,1080')
                    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36')
                
                print("ChromeOptions 配置完成，开始创建 Chrome 实例...")
                # 强制使用系统安装的 Chrome 和 ChromeDriver
                driver = uc.Chrome(
                    options=options,
                    driver_executable_path='/usr/local/bin/chromedriver',
                    browser_executable_path='/usr/bin/google-chrome',
                    use_subprocess=True
                )
                
                print(f"浏览器初始化成功，时间戳: {time.time()}")
                break
            except Exception as e:
                print(f"初始化尝试 {attempt + 1} 失败：{str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    raise
        
        if not driver:
            print("无法初始化浏览器")
            return None
        
        if headless:
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.set_window_size(1920, 1080)
        
        print("正在设置 Cookie...")
        driver.get('https://www.nodeseek.com')
        time.sleep(5)
        
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
        
        driver.refresh()
        time.sleep(5)
        return driver
        
    except Exception as e:
        print(f"设置浏览器和 Cookie 时出错：{str(e)}")
        traceback.print_exc()
        return None

def post_comment_on_url(driver, post_url, input_text):
    """
    在指定帖子 URL 上发表评论，返回 True/False 表示是否成功
    """
    try:
        driver.get(post_url)
        # 模拟浏览
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(random.uniform(2, 5))
        
        editor = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.CodeMirror'))
        )
        # 点击编辑器获取焦点
        try:
            editor.click()
        except:
            driver.execute_script("arguments[0].click();", editor)
        time.sleep(0.5)
        
        # 模拟真实打字，速度随机变化
        actions = ActionChains(driver)
        for char in input_text:
            actions.send_keys(char)
            actions.pause(random.uniform(0.05, 0.2))
        actions.perform()
        time.sleep(2)
        
        submit_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'submit') and contains(@class, 'btn') and contains(text(), '发布评论')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
        time.sleep(0.5)
        submit_button.click()
        
        print(f"已在帖子 {post_url} 中完成评论：{input_text}")
        with open('comment_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"{time.ctime()}: Commented on {post_url} with '{input_text}'\n")
        return True
    except Exception as e:
        print(f"在帖子 {post_url} 上评论失败：{str(e)}")
        traceback.print_exc()
        return False

def nodeseek_comment(driver):
    try:
        print("正在访问交易区...")
        target_url = 'https://www.nodeseek.com/'
        driver.get(target_url)
        print("等待页面加载...")
        
        posts = WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.post-list-item'))
        )
        print(f"成功获取到 {len(posts)} 个帖子")
        
        valid_posts = [post for post in posts if not post.find_elements(By.CSS_SELECTOR, '.pined')]
        
        # 第一步：识别抽奖帖子（标题包含"抽"或"奖"）
        lottery_urls = set()  # 使用 set 避免重复
        for post in valid_posts:
            try:
                post_link_el = post.find_element(By.CSS_SELECTOR, '.post-title a')
                post_title_text = post_link_el.text.strip()
                post_href = post_link_el.get_attribute('href')
                # 检查标题是否包含"抽"或"奖"
                if '抽' in post_title_text or '奖' in post_title_text:
                    lottery_urls.add(post_href)
                    print(f"发现抽奖帖子：{post_title_text}")
            except Exception:
                continue
        
        lottery_urls = list(lottery_urls)  # 转回列表
        
        comment_count = 0
        MAX_DAILY_COMMENTS = random.randint(20, 25)
        commented_urls = set()  # 跟踪已回复的帖子URL，避免重复
        recent_replies = []  # 跟踪最近的回复内容，避免重复
        
        # 第二步：优先回复抽奖帖子
        if lottery_urls:
            print(f"\n发现 {len(lottery_urls)} 个抽奖帖子，优先回复")
        for lurl in lottery_urls:
            if comment_count >= MAX_DAILY_COMMENTS:
                print("达到每日评论上限，停止评论")
                break
            
            # 检查是否已回复过此帖子
            if lurl in commented_urls:
                print(f"帖子 {lurl} 已回复过，跳过")
                continue
            
            try:
                print(f"\n正在处理抽奖帖子 ({comment_count + 1}/{MAX_DAILY_COMMENTS})")
                driver.get(lurl)
                time.sleep(random.uniform(2, 4))
                
                post_title, post_content = extract_post_content(driver)
                # 使用抽奖模式生成回复
                input_text = get_gemini_reply(post_title, post_content, is_lottery=True, recent_replies=recent_replies)
                if input_text is None:
                    print(f"帖子 {lurl} 获取回复失败，跳过")
                    with open('comment_log.txt', 'a', encoding='utf-8') as f:
                        f.write(f"{time.ctime()}: Skipped lottery post {lurl} due to Gemini API failure\n")
                    continue
                
                success = post_comment_on_url(driver, lurl, input_text)
                if success:
                    comment_count += 1
                    commented_urls.add(lurl)  # 记录已回复的URL
                    recent_replies.append(input_text)  # 记录回复内容
                    if len(recent_replies) > 10:  # 只保留最近10个回复
                        recent_replies.pop(0)
                    # 抽奖帖子评论后等待 5-6 分钟
                    wait_time = random.uniform(300, 360)
                    print(f"等待 {wait_time/60:.1f} 分钟...")
                    time.sleep(wait_time)
                
            except Exception as e:
                print(f"处理抽奖帖子 {lurl} 时出错：{str(e)}")
                continue
        
        # 第三步：从剩余帖子中随机选择进行评论
        remaining_quota = MAX_DAILY_COMMENTS - comment_count
        if remaining_quota > 0:
            print(f"\n开始随机回复普通帖子，还需回复 {remaining_quota} 个")
            
            # 重新访问首页获取帖子列表（因为之前的WebElement已失效）
            driver.get(target_url)
            time.sleep(3)
            posts = WebDriverWait(driver, 30).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.post-list-item'))
            )
            valid_posts_refresh = [post for post in posts if not post.find_elements(By.CSS_SELECTOR, '.pined')]
            
            # 筛选出未回复过的帖子（排除抽奖帖子和已回复的帖子）
            remaining_urls = []
            for post in valid_posts_refresh:
                try:
                    post_link_el = post.find_element(By.CSS_SELECTOR, '.post-title a')
                    post_href = post_link_el.get_attribute('href')
                    # 排除已回复的帖子
                    if post_href not in commented_urls:
                        remaining_urls.append(post_href)
                except Exception:
                    continue
            
            # 随机选择需要评论的帖子
            if remaining_urls:
                selected_urls = random.sample(remaining_urls, min(remaining_quota, len(remaining_urls)))
            else:
                print("没有找到可评论的普通帖子")
                selected_urls = []
            
            for i, post_url in enumerate(selected_urls):
                if comment_count >= MAX_DAILY_COMMENTS:
                    print("达到每日评论上限，停止评论")
                    break
                
                # 检查是否已回复过此帖子
                if post_url in commented_urls:
                    print(f"帖子 {post_url} 已回复过，跳过")
                    continue
                
                try:
                    print(f"\n正在处理普通帖子 {i+1}/{len(selected_urls)} ({comment_count + 1}/{MAX_DAILY_COMMENTS})")
                    driver.get(post_url)
                    
                    # 模拟浏览
                    driver.execute_script("window.scrollBy(0, 500);")
                    time.sleep(random.uniform(2, 5))
                    
                    # 提取帖子内容
                    post_title, post_content = extract_post_content(driver)
                    
                    # 使用普通模式生成回复
                    input_text = get_gemini_reply(post_title, post_content, is_lottery=False, recent_replies=recent_replies)
                    if input_text is None:
                        print(f"帖子 {post_url} 获取回复失败，跳过评论")
                        with open('comment_log.txt', 'a', encoding='utf-8') as f:
                            f.write(f"{time.ctime()}: Skipped comment on {post_url} due to Gemini API failure\n")
                        continue
                    
                    success = post_comment_on_url(driver, post_url, input_text)
                    if success:
                        comment_count += 1
                        commented_urls.add(post_url)  # 记录已回复的URL
                        recent_replies.append(input_text)  # 记录回复内容
                        if len(recent_replies) > 10:  # 只保留最近10个回复
                            recent_replies.pop(0)
                        # 普通帖子评论后等待 10-15 分钟
                        wait_time = random.uniform(600, 900)
                        print(f"等待 {wait_time/60:.1f} 分钟...")
                        time.sleep(wait_time)
                    
                except Exception as e:
                    print(f"处理帖子 {post_url} 时出错：{str(e)}")
                    continue
        
        print(f"\nNodeSeek 评论任务完成，共评论 {comment_count} 个帖子")
                
    except Exception as e:
        print(f"NodeSeek 评论出错：{str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    print("=== 开始执行 NodeSeek 评论脚本 ===")
    print(f"时间戳: {time.time()}")
    
    print("\n步骤 1: 初始化浏览器和设置 Cookie...")
    driver = setup_driver_and_cookies()
    if not driver:
        print("浏览器初始化失败")
        exit(1)
    print(f"浏览器初始化成功，时间戳: {time.time()}")
    
    print("\n步骤 2: 执行评论任务...")
    nodeseek_comment(driver)
    print(f"评论任务完成，时间戳: {time.time()}")
    
    print("\n步骤 3: 执行签到任务...")
    click_sign_icon(driver)
    print(f"签到任务完成，时间戳: {time.time()}")
    
    print("\n=== 脚本执行完成 ===")
