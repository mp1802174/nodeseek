# -*- coding: utf-8 -*-
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
ns_random = os.environ.get("NS_RANDOM", "false").lower() == "true"
cookie = os.environ.get("NS_COOKIE") or os.environ.get("COOKIE")
headless = os.environ.get("HEADLESS", "true").lower() == "true"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 调试输出，验证环境变量
print(f"GEMINI_API_KEY loaded: {'Set' if GEMINI_API_KEY else 'Not set'}")
print(f"NS_COOKIE loaded: {'Set' if cookie else 'Not set'}")
print(f"HEADLESS: {headless}")
print(f"NS_RANDOM: {ns_random}")

def get_gemini_reply(post_title, post_content):
    """调用 Gemini API 根据帖子内容生成自然回复"""
    try:
        if not GEMINI_API_KEY:
            print("未找到 Gemini API 密钥，跳过回复")
            return None
        
        prompt = f"""
        你是一个技术论坛的用户，正在回复一篇帖子。帖子标题是："{post_title}"，内容片段如下："{post_content[:200]}"。
        请生成一句简短（4-20个字）、自然、与帖子内容密切相关的回复。
        示例：
        - "这个配置不错"
        - "思路很清晰"
        """
        
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        
        response = requests.post(f"{url}?key={GEMINI_API_KEY}", headers=headers, json=data, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        reply = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        reply = reply.strip().replace("\n", " ").replace('"', "").replace(""", "").replace(""", "")
        
        if len(reply) < 4 or len(reply) > 25:
            print(f"Gemini 回复长度异常（{len(reply)}）：{reply}，跳过回复")
            return None
        
        print(f"Gemini 生成回复：{reply}")
        return reply
        
    except Exception as e:
        print(f"调用 Gemini API 出错：{str(e)}，跳过回复")
        return None

def extract_post_content(driver):
    """提取帖子标题和正文内容"""
    try:
        title_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.post-title'))
        )
        post_title = title_element.text.strip()
        
        content_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.post-content'))
        )
        post_content = content_element.text.strip()[:500]
        
        return post_title, post_content
    except Exception as e:
        print(f"提取帖子内容出错：{str(e)}")
        return "未知标题", "未知内容"

def click_sign_icon(driver):
    """尝试点击签到图标和试试手气按钮"""
    try:
        print("准备进入签到页面...")
        driver.get("https://www.nodeseek.com/board")
        print("等待页面加载...")
        time.sleep(5)
        
        print(f"当前页面URL: {driver.current_url}")
        
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
        print(f"签到过程中出错: {str(e)}")
        traceback.print_exc()
        return False

def setup_driver_and_cookies():
    """初始化浏览器并设置 Cookie"""
    try:
        if not cookie:
            print("未找到 Cookie 配置")
            return None
            
        print("开始初始化浏览器...")
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        if headless:
            options.add_argument('--headless=new')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36')
        
        driver = None
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"尝试初始化浏览器 (尝试 {attempt + 1}/{max_retries})...")
                driver = uc.Chrome(options=options, version_main=None)
                print("浏览器初始化成功")
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
        selected_posts = random.sample(valid_posts, min(random.randint(20, 25), len(valid_posts)))
        
        selected_urls = []
        for post in selected_posts:
            try:
                post_link = post.find_element(By.CSS_SELECTOR, '.post-title a')
                selected_urls.append(post_link.get_attribute('href'))
            except:
                continue
        
        comment_count = 0
        MAX_DAILY_COMMENTS = random.randint(20, 25)
        
        for i, post_url in enumerate(selected_urls):
            if comment_count >= MAX_DAILY_COMMENTS:
                print("达到每日评论上限，停止评论")
                break
                
            try:
                print(f"正在处理第 {i+1} 个帖子")
                driver.get(post_url)
                
                driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(random.uniform(2, 5))
                
                post_title, post_content = extract_post_content(driver)
                
                input_text = get_gemini_reply(post_title, post_content)
                if input_text is None:
                    print(f"帖子 {post_url} 获取回复失败，跳过评论")
                    with open('comment_log.txt', 'a', encoding='utf-8') as f:
                        f.write(f"{time.ctime()}: Skipped comment on {post_url} due to Gemini API failure\n")
                    continue
                
                editor = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.CodeMirror'))
                )
                editor.click()
                time.sleep(0.5)
                
                actions = ActionChains(driver)
                for char in input_text:
                    actions.send_keys(char)
                    actions.pause(random.uniform(0.1, 0.3))
                actions.perform()
                time.sleep(2)
                
                submit_button = WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'submit') and contains(@class, 'btn') and contains(text(), '发布评论')]"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                time.sleep(0.5)
                submit_button.click()
                
                print(f"已在帖子 {post_url} 中完成评论：{input_text}")
                comment_count += 1
                
                with open('comment_log.txt', 'a', encoding='utf-8') as f:
                    f.write(f"{time.ctime()}: Commented on {post_url} with '{input_text}'\n")
                
                time.sleep(random.uniform(600, 900))
                
            except Exception as e:
                print(f"处理帖子 {post_url} 时出错：{str(e)}")
                continue
                
        print("NodeSeek 评论任务完成")
                
    except Exception as e:
        print(f"NodeSeek 评论出错：{str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    print("开始执行 NodeSeek 评论脚本...")
    driver = setup_driver_and_cookies()
    if not driver:
        print("浏览器初始化失败")
        exit(1)
    nodeseek_comment(driver)
    click_sign_icon(driver)
    print("脚本执行完成")
