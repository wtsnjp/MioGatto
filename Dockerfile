#FROM ubuntu:latest

# ベースイメージを選択（Python 3.10を使用）
FROM python:3.10

# アプリケーションのディレクトリを作成
WORKDIR /miogatto

# ホストのカレントディレクトリにあるファイルをコンテナの/appディレクトリにコピー
COPY  MioGatto/ /miogatto/MioGatto/
COPY  grounding-dataset/ /miogatto/grounding-dataset/
#COPY  startup.sh /miogatto/

# アプリケーションに必要なパッケージをインストール
RUN apt-get update
RUN apt-get install -y python3-pip
#RUN chmod a+x startup.sh
RUN pip install -r MioGatto/requirements.txt

# アプリケーションを実行
CMD ["/bin/bash"]
