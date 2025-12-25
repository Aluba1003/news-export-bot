# 使用官方 Python 映像
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 複製程式碼到容器
COPY . .

# 安裝必要套件
RUN pip install --no-cache-dir -r requirements.txt && playwright install

# Cloud Run 預設會提供 PORT 環境變數
ENV PORT=8080

# 啟動程式
CMD ["python", "export_bot.py"]
