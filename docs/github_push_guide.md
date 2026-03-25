# GitHub 推送与 Streamlit Cloud 部署指南

## 1. 创建 GitHub 仓库

1. 打开 https://github.com/new
2. 仓库名：`gaokao-gansu`
3. 选择 **Private**（私有）
4. **不要**勾选 "Add a README file"（本地已有内容）
5. 点击 Create repository

## 2. 推送到 GitHub

在项目目录下运行：

```powershell
cd "D:\gaokao project"
git remote add origin https://github.com/zcyang1004/gaokao-gansu.git
git branch -M main
git push -u origin main
```

首次推送可能需要登录 GitHub（浏览器弹窗或输入 token）。

## 3. 部署到 Streamlit Cloud

1. 打开 https://share.streamlit.io/
2. 用 GitHub 账号登录
3. 点击 "New app"
4. 选择仓库 `zcyang1004/gaokao-gansu`，分支 `main`
5. Main file path 填写你的 Streamlit 入口文件（如 `app.py` 或 `streamlit_app.py`）
6. 点击 Deploy

部署后会得到一个公开链接，形如 `https://zcyang1004-gaokao-gansu-app-xxxxx.streamlit.app`
