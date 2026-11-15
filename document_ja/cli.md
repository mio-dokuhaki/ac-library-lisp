# AtCoder での使い方


`ac-lisp` コマンドを使うと、問題のサンプル取得、ライブラリの展開、コンパイルと
テスト、提出をターミナルから行えます。SBCL、Python 3、
[online-judge-tools](https://github.com/online-judge-tools/oj) が必要です。
例えば uv を使う場合:

```sh
uv tool install --python 3.13 --with setuptools --with-executables-from online-judge-api-client online-judge-tools
ln -s /path/to/ac-library-lisp/bin/ac-lisp ~/.local/bin/ac-lisp
```

`~/.local/bin` を PATH に含めてください。シンボリックリンクは、このリポジトリの
expander とライブラリを参照します。

```sh
ac-lisp new https://atcoder.jp/contests/practice2/tasks/practice2_a
cd practice2_a
# main.lisp を編集
ac-lisp test
ac-lisp submit
```

`new URL [DIR]` は問題 URL とサンプルを保存し、既存ディレクトリは上書きしません。

## コンテスト全体を準備

AtCoder のコンテスト ID、コンテスト URL、または `/tasks` URL を渡すと、
コンテストの全問題をまとめて準備できます。`?lang=ja` などのクエリや URL の
アンカーが付いていても指定できます。

```sh
ac-lisp new typical90
# URL も使用でき、第2引数で作成先のディレクトリを指定できます。
ac-lisp new https://atcoder.jp/contests/abc484/tasks abc484-work
cd typical90/007
# main.lisp を編集してから ac-lisp test を実行
```

作成先の既定名はコンテスト ID です。各問題は `001` や `A` のような公式の問題
ラベルを名前とするディレクトリに作られ、解答の雛形、問題 URL、取得できたサンプルが入ります。
コンテストの一括作成には PATH 上の `python3`、`oj`、`oj-api` が必要です。
サンプルは直列に取得し、各処理の開始を 1 秒以上空けます。ダウンロード時間も
この間隔に含まれます。端末では進捗バー、リダイレクト時は問題ごとの進捗を表示します。
サンプルが見つからない問題は警告して他の問題を
続け、最後に非ゼロの終了状態を返します。通信エラーなどその他の失敗では停止します。
いずれの場合も作成済みファイルは残り、既存の作成先は上書きしません。
インタラクティブ問題には別途対話用のジャッジが必要です。現在の `test` と `submit` は
通常のサンプルファイルを必要とするため、インタラクティブ問題には対応していません。
自動再開機能はありません。途中で停止した場合は作成済みファイルを確認し、まだ作成されて
いない問題ごとに `ac-lisp new 問題URL workspace/問題ラベル` を実行してください。

## テストと提出

`test [DIR]` は展開したコードを SBCL でコンパイルし、サンプルを実行します。
`submit [DIR]` はテスト後に `oj` を呼び出し、確認を経て提出します。言語は
コンテストの一覧から `SBCL` を選択し、必要なら `--language ID` で指定できます。
サンプルは `test/` 直下の通常ファイルとし、同名の `.in` と `.out` を用意してください。
隠し入力・シンボリックリンク・サブディレクトリはエラーになり、その他のファイルは
実行しません。テストにはサンプルの一時コピーを使用します。

コンテスト一覧の取得、サンプルのダウンロード、`submit` 時には、AtCoder の
メモリ制限 `KiB` / `MiB` を読み取れない古い
`online-judge-api-client` を検出した場合、そのプロセス内だけに互換修正を適用します。
インストール済みの `oj` 自体は変更しません。起動時に `sitecustomize` を読み込む通常の
Python 版 `oj` が必要です。修正済みの新しいクライアントには適用せず、既存の
`PYTHONPATH` と `sitecustomize` も維持します。

## ブラウザからログイン

AtCoder のログインには Turnstile があるため、通常の `oj login` が失敗する場合が
あります。ブラウザで先にログインし、そのプロファイルのセッションを取り込めます。
Firefox、LibreWolf、Edge、Chrome、Chromium、Brave、Opera、Opera GX、Vivaldi に対応しています。

```sh
ac-lisp login --browser edge --profile ~/.config/microsoft-edge/Default
# Firefox の場合: ac-lisp login --browser firefox --profile ~/.mozilla/firefox/YOUR_PROFILE
ac-lisp login --check
```

Chromium 系ブラウザでは `browser-cookie3` と、ロック解除されたシステムのキーリングが
必要です。例えば専用環境には次のようにインストールできます。

```sh
uv venv ~/.local/share/ac-lisp/venv
uv pip install --python ~/.local/share/ac-lisp/venv/bin/python 'browser-cookie3==0.20.1'
```

別の Python 環境を使う場合は `browser-cookie3` を導入し、その実行ファイルを
`AC_LISP_PYTHON` で指定してください。セッションを検証してから `oj` の AtCoder 用
Cookie を更新し、他サイトの Cookie は保持します。Firefox と LibreWolf は
`cookies.sqlite` に保存された Cookie が対象で、メモリやセッション復元データにのみ
保持されるセッションは取り込めません。取り込み中は他の `oj` コマンドを
実行しないでください。更新前の変更は検知しますが、最終確認から置換までの間の
書き込みは防げません。

セッション Cookie は認証情報なので、`oj` の Cookie ファイルは他人に公開しないで
ください。終了済みコンテストでは提出時にも Turnstile が必要な場合があり、
[acrust](https://github.com/okaponta/acrust) と同様、CLI だけでは提出できません。
その場合は `ac-lisp copy [DIR]` で展開コードをコピーし、ブラウザの提出画面に貼り付けて
認証してください。コピーには Wayland では `wl-copy`、X11 では `xclip` が必要です。
送信後にエラーが出た場合は、再送前に提出履歴を確認してください。通信エラーでも
提出自体は受理されていることがあります。

## 手動で展開

手動で展開することもできます。

解答ファイルの先頭に `(acl-include :dsu)` のように使いたいモジュールを書き、

```sh
sbcl --script expander.lisp main.lisp -o combined.lisp
```

で展開した `combined.lisp` を提出してください。`(acl-include :all)` で全モジュールを展開します。

`acl-include` はトップレベルに、それだけで 1 行に書いてください。他のフォームの中、`'` や `#+` などのリーダー記号の直後、コメントや文字列の中にある `acl-include` は展開されません（前の 2 つの場合は警告が表示されます）。詳しいルールは [`document_en/expander.md`](../document_en/expander.md) にあります。


## C++ 版との違い

* 添字は 0-indexed、区間は半開区間 `[l, r)` で ACL と同じです。
* モノイドは関数で渡します (`(make-segtree n :op #'max :e 0)`)。単位元 `e` / `id` は関数ではなく値です。
* 高速化したい場合は `define-segtree` / `define-lazy-segtree` を使うと、`op` などがインライン展開された専用関数が生成されます (C++ のテンプレートに相当)。
* modint は `[0, mod)` の普通の整数です。`define-modint` で `name+` `name*` `name/` などの関数が作られます。
* 各モジュールの詳しい説明は [`document_en/`](../document_en/index.md) にあります。

## テスト

```sh
sbcl --script test/run.lisp
sbcl --script test/expander-test.lisp
python3 test/cli-test.py
```

1つ目は全モジュールをランダム入力で愚直解と比較します。2つ目は expander のテストで、各モジュールを単体で展開しても未定義関数なくコンパイルできること、コメント・文字列・`|...|` シンボル・他のフォームの中や、`'` や `#+` などの直後にある `acl-include` が展開されないことを確認します。
`(asdf:test-system :ac-library)` でもテストを実行でき、失敗するとエラーになります。3つ目は実際の SBCL と模擬 `oj` を使い、サンプルテスト、提出準備、ブラウザのセッション取り込みを検証します。3つとも GitHub Actions で実行されます。

