FROM apache/airflow:2.10.5

USER root

# Cài hệ thống & Chrome (bằng root)
RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl \
    libglib2.0-0 libnss3 libgconf-2-4 libxss1 libappindicator3-1 \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 libcups2 libdbus-1-3 \
    libgdk-pixbuf2.0-0 libnspr4 libx11-xcb1 libxcomposite1 libxdamage1 \
    libxrandr2 fonts-liberation lsb-release xdg-utils --no-install-recommends

# Thêm repo Chrome & cài Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Quay lại user airflow để pip install
USER airflow

# ✅ Cài Python packages dưới quyền user airflow
RUN pip install --no-cache-dir \
    selenium \
    webdriver-manager \
    fake_useragent \
    beautifulsoup4 \
    pandas

# Biến môi trường Chrome
ENV CHROME_BIN=/usr/bin/google-chrome

# Copy code dự án (nếu có)
COPY ./dags /opt/airflow/dags
COPY ./plugins /opt/airflow/plugins
COPY ./csv /opt/airflow/csv
COPY ./csv /opt/airflow/logs
COPY ./csv /opt/airflow/configs
