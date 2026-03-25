# 甘肃高考志愿推荐系统 — 部署指南

## 1. 快速开始

### 前置条件
- Docker 20.10+
- Docker Compose v2+

### 构建与运行

```bash
# 构建镜像
docker compose build

# 启动服务（后台运行）
docker compose up -d

# 查看日志
docker compose logs -f gaokao

# 停止服务
docker compose down
```

访问 `http://localhost:8501` 即可使用。

## 2. 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `STREAMLIT_SERVER_HEADLESS` | `true` | 无头模式，服务器部署必须为 true |
| `STREAMLIT_SERVER_PORT` | `8501` | 服务端口 |

## 3. 云服务器部署

### 3.1 阿里云 ECS

1. 购买 ECS 实例（推荐 2核4G 以上，Ubuntu 22.04）
2. 安全组放行 8501 端口（或用 Nginx 反代到 80/443）
3. SSH 登录后安装 Docker：
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   ```
4. 上传项目文件或 `git clone`
5. `docker compose up -d`

### 3.2 腾讯云 CVM

步骤同上，安全组配置在「云服务器 → 安全组」中操作。

### 3.3 使用 Nginx 反向代理（推荐）

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Streamlit 使用 WebSocket，必须配置 `Upgrade` 和 `Connection` 头。

## 4. 安全建议

- **不要暴露 8501 端口到公网**，使用 Nginx 反代 + HTTPS
- 申请免费 SSL 证书（Let's Encrypt）：`certbot --nginx`
- 设置防火墙，仅开放 22、80、443
- 定期更新基础镜像：`docker compose build --pull`
- 数据文件以只读模式挂载（docker-compose.yml 已配置 `:ro`）
- 系统不存储用户数据，无需额外数据库备份

## 5. 更新部署

```bash
git pull
docker compose build
docker compose up -d
```
