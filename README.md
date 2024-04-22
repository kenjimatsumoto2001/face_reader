# 顔認証出席登録アプリケーション
プログラミング演習2のFollow up、研究室公開の出席を管理するツールです。

出席者の顔を確認できるようになり、研究室公開に参加した人たちについての情報を共有するのに役立つと思います。

## セットアップ

### Docker Desktop のインストール  
本プロジェクトはDockerを使用しています。[Docker Desktop](https://www.docker.com/ja-jp/products/docker-desktop/)をインストールしてください。  

不明点があれば[インストール方法(mac)](https://matsuand.github.io/docs.docker.jp.onthefly/desktop/mac/install/)を参照してください。  

VScodeを使用する方であれば、拡張機能のDockerをインストールでもいいと思います。

### VScodeでのDocker起動方法
ターミナルで以下のコードを入力し、Dockerを起動してください。  
`docker compose up -d`  

以降はDocker Desktopでface_reader1内のface_reader1-nagix-1を起動することが可能です。
**必ずDocker上で動くことを確認してからGitに上げるようにお願いします。**

## 参照
- **[face_recognition]** - 顔認証機能の実装に使用。詳細はこちら: [https://github.com/ageitgey/face_recognition/blob/master/README_Japanese.md]
