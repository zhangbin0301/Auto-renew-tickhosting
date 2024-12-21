# Auto Renew Tickhosting

自动续期 TickHosting 免费游戏机的脚本，使用 GitHub Actions 每96小时自动运行一次。
- 部署文件：https://github.com/eooce/all-games/blob/main/msh_server.bin
- 将files里的原msh_server.bin文件改名为LICENSE.bin，再上传此文件，修改变量，保存文件类型为shell，权限改为444，运行即可

## 功能特点

- 自动登录 TickHosting
- 自动点击续期按钮
- 验证续期是否成功
- 每96小时自动运行
- telegram消息推送
- 支持手动触发运行

## 使用方法

### 1. 使用邮箱密码注册 并获取 Cookie

1. 打开 [TickHosting](https://tickhosting.com/auth/login)，使用邮箱密码注册账号
2. 打开浏览器开发者工具（F12）
3. 切换到 Appcation 选项
4. 刷新页面
5. 在请求中找到 `pterodactyl_session` cookie 的值

### 2. 设置 GitHub Actions

1. Fork 这个仓库
2. 在仓库中设置 Secret：
   - 进入仓库的 Settings
   - 点击 Secrets and variables -> Actions
   - 点击 New repository secret
   - 添加```EMAIL```和```PASSWORD```环境便量
   - 添加`PTERODACTYL_SESSION`环境便量
   - Value: 您获取到的 pterodactyl_session cookie 值
   - ![PixPin_2024-12-18_12-40-50](https://github.com/user-attachments/assets/3ce6fa9e-611e-4810-a0ca-f35ddbe91400)
   - ![image](https://github.com/user-attachments/assets/97aa8e73-ba70-42ee-8882-ce3d3161894f)

3. telegram消息推送功能可选，如需要请在secrets中添加```TELEGRAM_BOT_TOKEN```和```TELEGRAM_CHAT_ID```环境变量

### 3. 验证运行

- Actions 将每96小时(4天)自动运行一次
- 您可以在 Actions 页面查看运行状态和日志
- 需要立即运行时，可以在 Actions 页面手动触发

## 注意事项

- 请确保 cookie及邮箱密码正确
- 建议定期检查 Actions 运行日志，确保脚本正常运行
- 如果需要修改运行频率，可以调整 `.github/workflows/auto_renew.yml` 中的 cron 表达式
