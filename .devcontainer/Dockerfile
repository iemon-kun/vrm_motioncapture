# Python 3.11をベースイメージとして使用します
FROM python:3.11-slim

# OpenCVの動作に必要なOSのライブラリをインストールします
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# コンテナ内の作業ディレクトリを設定します
WORKDIR /app

# Pythonのライブラリをインストールします
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのソースコードをコピーします
COPY . .

# アプリケーションが使用するポート番号8800番を公開します
EXPOSE 8800
