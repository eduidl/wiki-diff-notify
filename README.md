# Wiki Diff Notify
GitLab wikiの差分のSlack通知

## Requirements

- Git
- Python 3.6+
- Poetry

## 準備

1. `./wikis` 以下にGitLabのWikiのリポジトリをclone
- 右上にある `Clone repository` のリンク先でURLはわかる．

![image](https://user-images.githubusercontent.com/25898373/64052256-cde0e600-cbb8-11e9-8b11-df597713e635.png)

2. Slack Appの作成
- https://api.slack.com/apps?new_app=1 から作成する．

![image](https://user-images.githubusercontent.com/25898373/64052432-624b4880-cbb9-11e9-914b-407eeb38426c.png)

- `Add features and functionality` ではBotsを選択

![image](https://user-images.githubusercontent.com/25898373/64052980-7e4fe980-cbbb-11e9-8954-36b76a4db501.png)

- `Install your app to your workspace` -> `Install App to Workspace`

![image](https://user-images.githubusercontent.com/25898373/64053178-41d0bd80-cbbc-11e9-83d3-665750f0eb8d.png)

- 左の `Features` の中にある `OAuth & Permissions` から `Bot User OAuth Access Token` の値をコピーする．

3. `sample.ini` を参考に `config.ini` を作成

```
[Slack]
APIToken = <2.で得たBot User OAuth Access Token>

[NotifyTo]
test.wiki = random
<1.でcloneしたリポジトリのディレクトリ> = <投稿したいchannel>
# 以降必要な分だけ
```

- `test.wiki = random` の場合，`./wikis/test.wiki` の更新情報が `#random` に通知される．

4. 通知させたいchannelがprivateの場合は，2.でインストールしたアプリを `/invite` 等してそのchannelに追加する

## Setup of Poetry

```terminal
$ poetry env use python3.6
$ poetry install
```

## Execute

```terminal
$ poetry run python -m wiki_diff_notify --config <config_path>
```

## その他
- 適当に5分sleepしているので，気に食わない場合は不正アクセスにならない範囲で調整のこと．
- 以下のような場合には多分異常終了する．
  - private channelからbotが取り除かれた
  - botが参加していないpublic channelがprivateになった
  - channelがアーカイブ・削除された
  - リポジトリが削除された
  - リポジトリのアクセス権がなくなった等
