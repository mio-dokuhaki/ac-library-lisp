# ac-library-lisp

A Common Lisp port of [AtCoder Library (ACL)](https://github.com/atcoder/ac-library).

The library and source expander are written in Common Lisp and target SBCL,
the implementation used on AtCoder.

[日本語版 README はこちら](#日本語)

```mermaid
flowchart LR
  new["ac-lisp new"] --> edit["edit main.lisp"]
  edit --> test["ac-lisp test"]
  test --> submit["ac-lisp submit"]
```

## Setup

`ac-lisp` prepares problems, tests solutions, and submits them using SBCL,
Python 3, and [online-judge-tools](https://github.com/online-judge-tools/oj).
For example, install the tools with [uv](https://docs.astral.sh/uv/):

```sh
git clone https://github.com/mio-dokuhaki/ac-library-lisp.git
uv tool install --python 3.13 --with setuptools --with-executables-from online-judge-api-client online-judge-tools
mkdir -p ~/.local/bin
ln -s "$PWD/ac-library-lisp/bin/ac-lisp" ~/.local/bin/ac-lisp
```

Add `~/.local/bin` to `PATH` and keep the checkout in place: the symlink uses
its source files.

## Start a contest

```sh
ac-lisp new abc484
cd abc484/A
# Edit main.lisp
ac-lisp test
ac-lisp submit
```

You can also prepare a single problem by URL. Contest downloads run sequentially
with terminal progress and never overwrite an existing directory.
Before submitting, log in if needed; see the CLI guide for session import.

- [CLI guide: login, testing, and submission](document_en/cli.md)
- [Modules and API reference](document_en/index.md)
- [Manual expansion and library use](document_en/getting-started.md)
- [Differences from ACL](document_en/differences.md)

Licensed under [CC0 1.0](LICENSE).

---

## 日本語

[AtCoder Library](https://github.com/atcoder/ac-library) の Common Lisp 移植版です。SBCL で動作し、提出用のコードも展開できます。

### セットアップ

SBCL、Python 3、[online-judge-tools](https://github.com/online-judge-tools/oj) が必要です。例えば `uv` を使う場合:

```sh
git clone https://github.com/mio-dokuhaki/ac-library-lisp.git
uv tool install --python 3.13 --with setuptools --with-executables-from online-judge-api-client online-judge-tools
mkdir -p ~/.local/bin
ln -s "$PWD/ac-library-lisp/bin/ac-lisp" ~/.local/bin/ac-lisp
```

`~/.local/bin` を PATH に含めてください。

### コンテストを始める

```sh
ac-lisp new abc484
cd abc484/A
# main.lisp を編集
ac-lisp test
ac-lisp submit
```

問題 URL を指定して１問ずつ準備することもできます。コンテスト取得は直列で行い、端末に進捗を表示します。既存ディレクトリは上書きしません。
提出前に必要に応じてログインしてください。ブラウザのログイン情報を取り込む方法は下記ガイドを参照できます。

- [詳しい使い方・ログイン・提出時の注意](document_ja/cli.md)
- [モジュール一覧と API（英語）](document_en/index.md)
- [手動での展開方法（英語）](document_en/expander.md)

ライセンスは [CC0 1.0](LICENSE) です。
