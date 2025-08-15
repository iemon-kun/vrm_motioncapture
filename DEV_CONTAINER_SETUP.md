# 仮想環境(Dev Container)での実行手順

こんにちは！このアプリケーションをあなたのPCで簡単に動かすための手順を説明します。
[Visual Studio Code (VS Code)](https://code.visualstudio.com/) と [Docker](https://www.docker.com/products/docker-desktop/) というツールを使います。これらがインストールされていることを確認してください。

## 1. 準備

1.  **VS Codeの拡張機能をインストールする**
    VS Codeを開き、左側にある四角いアイコン（拡張機能マーケットプレイス）をクリックします。
    検索バーに `Dev Containers` と入力し、Microsoftが提供している拡張機能をインストールしてください。

2.  **このプロジェクトをVS Codeで開く**
    このプロジェクトのフォルダをVS Codeで開いてください。

## 2. 仮想環境（Dev Container）の起動

1.  **コマンドパレットを開く**
    -   Windows: `Ctrl+Shift+P`
    -   Mac: `Cmd+Shift+P`

2.  **Dev Containerを起動する**
    コマンドパレットに `Dev Containers: Reopen in Container` と入力し、表示されたコマンドを選択します。

3.  **待つ**
    VS Codeが自動的に仮想環境の構築を始めます。初回は少し時間がかかりますが、完了するとVS Codeの左下に緑色の「Dev Container: ...」という表示が出ます。これで仮想環境の準備は完了です！

## 3. アプリケーションの実行

仮想環境の準備ができたら、アプリケーションを動かしてみましょう。

1.  **VS Codeでターミナルを開く**
    画面上部のメニューから `ターミナル` > `新しいターミナル` を選択します。

2.  **サーバーを起動する**
    開いたターミナルに、以下のコマンドを入力して実行します。

    ```bash
    uvicorn backend.main:app --host 0.0.0.0 --port 8800 --reload
    ```

3.  **サーバーの動作確認**
    ターミナルに「Application startup complete.」というメッセージが表示されたら、サーバーは正常に起動しています。
    Webブラウザで [http://localhost:8800](http://localhost:8800) にアクセスしてみてください。
    `{"message":"Welcome to VRM MotionCapture API", ...}` という文字が表示されれば成功です！

## 4. 使い方（APIの例）

サーバーが起動している状態で、別のターミナルを開いて以下の`curl`コマンドを実行することで、APIを試すことができます。

**例：収録を開始する**
（`test.jsonl`というファイルにモーションデータが記録されます）

```bash
curl -X POST -H "Content-Type: application/json" -d '{"filepath": "test.jsonl"}' http://localhost:8800/api/pipelines/1/record/start
```

**例：収録を停止する**

```bash
curl -X POST http://localhost:8800/api/pipelines/1/record/stop
```

これで、あなたもこのアプリケーションの開発やテストができるようになりました。楽しんでください！
