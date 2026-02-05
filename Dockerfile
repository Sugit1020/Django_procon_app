# 1. ベースとなるOSと環境
FROM python:3.10-slim

# 2. C++のコンパイラ(g++)をインストール
RUN apt-get update && apt-get install -y gcc g++


# 3. 作業ディレクトリの設定
WORKDIR /app