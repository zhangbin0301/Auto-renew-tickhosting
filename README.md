# Auto Renew Tickhosting

自动续期 TickHosting 免费游戏机的脚本，使用 GitHub Actions 每96小时自动运行一次。
## 部署
- 部署文件：https://github.com/eooce/all-games/blob/main/java.tar.gz
- 将files里的原server.jar文件改名为LICENSE.jar，将eula.txt改名为eula.txt1，再上传此压缩包解压得到server.jar和start.sh文件
- server.jar的权限为444，start.sh的权限为777，此时还无法启动，会报错不支持的jar文件
- 点开左侧的schedules菜单---右上角的Create schedule，随便给个名字创建，中间的Only When Server Is Online选项关闭，然后点击创建好的任务进入
- 点击右上角的New Task，Action选项选择Send power action，打开Continue on Failure开关，点击Create Task创建
- 点击Run now运行，返回左侧菜单栏中的terminal,显示提示已经开始下载文件点击进入files，将eula.txt1改回eula.txt
- 返回左侧菜单栏中的terminal，查看运行完后是否运行游戏，运行中的弹窗需点击Accept
- 完成

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
