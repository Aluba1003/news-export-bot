FROM python:3.11-slim

WORKDIR /app

# 安裝 Playwright 需要的系統套件
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libxrender1 \
    libxext6 \
    libxi6 \
    libxss1 \
    libxtst6 \
    libglib2.0-0 \
    libgtk-3-0 \
    libdrm2 \
    libgbm1 \
    libasound2 \
    libdbus-1-3 \
    libfreetype6 \
    libfontconfig1 \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式碼
COPY . .

# 安裝 Playwright 瀏覽器與依賴
RUN playwright install --with-deps

# 啟動程式
CMD ["python", "export_bot.py"]
