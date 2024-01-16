# ベースイメージを選択（Python 3.9を使用）
FROM python:3.9

# アプリケーションのディレクトリを作成
WORKDIR /MioGatto

# ホストのカレントディレクトリにあるファイルをコンテナの/MioGattoディレクトリにコピー
COPY .. /MioGatto/

# アプリケーションに必要なパッケージをインストール
RUN apt-get update\
 && apt-get install -y python3-pip\
 && pip install -r requirements.txt

# アプリケーションを実行
ENTRYPOINT ["python", "-m", "server", "--host", "0.0.0.0"]