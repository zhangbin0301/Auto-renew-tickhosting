# Auto Renew Tickhosting

自动续期 TickHosting 免费服务器的脚本，使用 GitHub Actions 每96小时自动运行一次。

## 功能特点

- 自动登录 TickHosting
- 自动点击续期按钮
- 验证续期是否成功
- 每96小时自动运行
- 支持手动触发运行

## 使用方法

### 1. 获取 Cookie

1. 登录 [TickHosting](https://tickhosting.com/auth/login)
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
   - Name: `PTERODACTYL_SESSION`
   - Value: 您获取到的 pterodactyl_session cookie 值
   - ![PixPin_2024-12-18_12-40-50](https://github.com/user-attachments/assets/3ce6fa9e-611e-4810-a0ca-f35ddbe91400)


### 3. 验证运行

- Actions 将每96小时(4天)自动运行一次
- 您可以在 Actions 页面查看运行状态和日志
- 需要立即运行时，可以在 Actions 页面手动触发

## 注意事项

- 请确保 cookie 值保密，不要泄露给他人
- 如果登录失败，请更新 cookie 值
- 建议定期检查 Actions 运行日志，确保脚本正常运行
- 如果需要修改运行频率，可以调整 `.github/workflows/auto_renew.yml` 中的 cron 表达式
