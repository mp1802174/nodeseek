# NodeSeek 自动签到评论脚本

这是一个用于 NodeSeek 论坛的自动化脚本，包含签到和智能评论功能。使用 Selenium 和 undetected-chromedriver 实现自动化操作，集成 Gemini API 生成自然回复。

## 功能特点

- 自动签到（点击签到图标）
- 自动点击"试试手气"或"鸡腿 x 5"按钮（可配置）
- 智能识别抽奖帖子（标题含"抽"或"奖"），优先回复
- 使用 Gemini API 生成与帖子内容相关的自然回复
- 防止重复回复同一帖子
- 防止连续使用相同回复内容
- 每日评论数20-25个（抽奖+普通帖子）
- 抽奖帖子等待30-60秒，普通帖子等待10-15分钟
- 支持 GitHub Actions 自动运行
- 支持无头模式（可配置）

## 环境变量配置

- `NS_COOKIE`: NodeSeek 的 Cookie（必需）
- `GEMINI_API_KEY`: Google Gemini API 密钥（必需）
- `NS_RANDOM`: 是否随机选择奖励，true/false（可选）
- `HEADLESS`: 是否使用无头模式，true/false（可选，默认 true）

## 本地运行

1. 克隆仓库
2. 安装依赖：`pip install -r requirements.txt`
3. 设置环境变量（可使用 .env 文件）
4. 运行脚本：`python nodeseek_daily.py`

## GitHub Actions 自动运行

1. Fork 本仓库
2. 在仓库的 Settings -> Secrets 中添加：
   - `NS_COOKIE`: NodeSeek Cookie
   - `GEMINI_API_KEY`: Google Gemini API 密钥
   - `NS_RANDOM`: 是否随机选择奖励（可选）
3. Actions 会在每天 UTC 16:00（北京时间 00:00）自动运行
4. 也可以在 Actions 页面手动触发运行

## 注意事项

- 请确保 Cookie 有效且具有足够的权限
- Gemini API 用于生成自然回复，避免被识别为 AI
- 回复内容会根据帖子内容生成，长度3-50字
- 脚本会自动避免重复回复和重复内容
- 最后更新：2026-02-22
A
