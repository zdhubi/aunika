FROM python:3.9-slim

# Nastavení pracovní složky
WORKDIR /app

# Instalace závislostí pro Chrome
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    gnupg \
    wget \
    fonts-liberation \
    libasound2 \
    libnss3 \
    libxss1 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm-dev \
    libgtk-3-0 \
    libu2f-udev \
    libvulkan1 \
    xdg-utils \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Zajištění cesty k Chrome (pro webdriver_manager)
ENV PATH="/usr/bin:$PATH"
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Instalace Python knihoven
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopírování zbytku kódu
COPY . .

# Spuštění skriptu
CMD ["python", "main.py"]
