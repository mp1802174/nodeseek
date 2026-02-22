# -*- coding: utf-8 -*-
"""
NodeSeek 脚本诊断和修复工具
用于解决 ChromeDriver 版本不匹配问题
"""
import subprocess
import os
import sys
import re

def check_chrome_installed():
    """检查 Chrome 是否已安装"""
    chrome_paths = [
        '/opt/hostedtoolcache/setup-chrome/chromium/stable/x64/chrome',
        '/usr/bin/google-chrome',
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✓ 找到 Chrome: {path}")
            return path
    
    print("✗ 未找到 Chrome 浏览器")
    return None

def get_chrome_version(chrome_path):
    """获取 Chrome 版本"""
    try:
        result = subprocess.run(
            [chrome_path, '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_str = result.stdout.strip()
            match = re.search(r'(\d+)', version_str)
            if match:
                version = int(match.group(1))
                print(f"✓ Chrome 版本: {version_str.strip()}")
                return version
    except Exception as e:
        print(f"✗ 获取 Chrome 版本失败: {str(e)}")
    
    return None

def check_python_packages():
    """检查必要的 Python 包"""
    packages = [
        'selenium',
        'undetected_chromedriver',
        'requests',
        'beautifulsoup4',
        'webdriver_manager'
    ]
    
    print("\n检查 Python 包...")
    missing = []
    for package in packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} (缺失)")
            missing.append(package)
    
    return missing

def install_packages(packages):
    """安装缺失的包"""
    if not packages:
        return True
    
    print(f"\n安装缺失的包: {', '.join(packages)}")
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install'] + packages,
            check=True
        )
        print("✓ 包安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 包安装失败: {str(e)}")
        return False

def diagnose():
    """运行诊断"""
    print("=" * 50)
    print("NodeSeek 脚本诊断工具")
    print("=" * 50)
    
    # 检查 Chrome
    print("\n1. 检查 Chrome 浏览器...")
    chrome_path = check_chrome_installed()
    if not chrome_path:
        print("请安装 Chrome 或 Chromium 浏览器")
        return False
    
    chrome_version = get_chrome_version(chrome_path)
    if not chrome_version:
        print("无法获取 Chrome 版本")
        return False
    
    # 检查 Python 包
    print("\n2. 检查 Python 依赖...")
    missing = check_python_packages()
    if missing:
        print(f"\n缺失的包: {', '.join(missing)}")
        if not install_packages(missing):
            return False
    
    print("\n" + "=" * 50)
    print("✓ 诊断完成，所有检查通过")
    print("=" * 50)
    print("\n建议:")
    print("1. 使用 nodeseek_daily_enhanced.py 替代原始脚本")
    print("2. 确保设置了 NS_COOKIE 环境变量")
    print("3. 可选：设置 GEMINI_API_KEY 以使用 AI 生成评论")
    print("4. 运行: python3 nodeseek_daily_enhanced.py")
    
    return True

if __name__ == "__main__":
    success = diagnose()
    sys.exit(0 if success else 1)
