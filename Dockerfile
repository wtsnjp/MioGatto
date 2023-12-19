# ベースイメージを選択（Python 3.9を使用）
FROM python:3.9

# アプリケーションのディレクトリを作成
WORKDIR /MioGatto

# ホストのカレントディレクトリにあるファイルをコンテナの/MioGattoディレクトリにコピー
COPY .. /MioGatto/

# アプリケーションに必要なパッケージをインストール
RUN apt-get update
RUN apt-get install -y python3-pip
RUN chmod a+x startup.sh
RUN pip install -r requirements.txt

# アプリケーションを実行
ENTRYPOINT ["./startup.sh"]