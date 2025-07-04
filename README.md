# AI Discord Bot

ローカルAIを使用した日本語対応のDiscord botです。

## 特徴

- 🤖 ローカルAIによる日本語会話（デバッグモード対応）
- 🧠 ユーザーごとの会話履歴管理
- ⚙️ システム状態監視
- 🔧 管理者機能
- 📝 スラッシュコマンド対応

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境設定

`.env`ファイルを編集して、Discord Bot の設定を行います：

```bash
# 必須設定
DISCORD_TOKEN=your_actual_discord_bot_token_here

# オプション: スラッシュコマンドの即時適用（推奨）
GUILD_ID=your_discord_server_id

# AI設定（オプション）
AI_MODEL_NAME=rinna/japanese-gpt2-medium
AI_MAX_TOKENS=100
AI_TEMPERATURE=0.8
```

**GUILD_ID について:**
- Discordサーバーの設定から「サーバーID」をコピーして設定
- 設定すると、スラッシュコマンドが即座に利用可能になります
- 未設定の場合、グローバル同期となり最大1時間かかります

### 3. ボット起動

**重要**: OpenMP競合エラーを回避するため、以下のコマンドで起動してください：

```bash
export KMP_DUPLICATE_LIB_OK=TRUE && python main.py
```

または、起動スクリプトを使用：

```bash
./start_bot.sh
```

## 利用可能なコマンド

### 基本コマンド
- `/chat [メッセージ]` - AIと対話
- `/help` - ヘルプメッセージ表示
- `/status` - ボットとシステムの状態確認

### 記憶管理
- `/memory show` - 会話履歴を表示
- `/memory clear` - 会話履歴をクリア
- `/memory export` - 会話履歴をエクスポート

### 管理者コマンド
- `/admin reload` - 設定リロード
- `/admin train` - AIモデルの追加学習
- `/admin backup` - データバックアップ
- `/admin stats` - 使用統計表示

## トラブルシューティング

### よくある問題

1. **OpenMP競合エラー**
   ```bash
   export KMP_DUPLICATE_LIB_OK=TRUE
   ```

2. **PyTorch/Transformersのインポートエラー**
   - ボットは自動的にデバッグモード（ダミーAI）に切り替わります
   - 実際のAIモデルを使用したい場合は、依存関係を確認してください

3. **Discord Token エラー**
   - `.env`ファイルのDISCORD_TOKENが正しく設定されているか確認

## AIモデルについて

### 🤖 実際のAI会話機能
- **モデル**: `rinna/japanese-gpt2-medium` （軽量な日本語特化モデル）
- **特徴**: 自然な日本語会話、適度なメモリ使用量
- **応答品質**: コンテキストを考慮した一貫性のある会話

### 💡 フォールバック機能
PyTorchが利用できない環境では、自動的にダミーモードに切り替わります：
- 高速な起動
- メモリ使用量の削減
- 基本機能のテスト

## プロジェクト構造

```
discord_bot/
├── main.py                 # メインファイル
├── config.py              # 設定管理
├── commands/              # コマンド実装
├── models/                # AIモデル関連
├── utils/                 # ユーティリティ
├── data/                  # データ保存用
└── requirements.txt       # 依存関係
```

## 注意事項

- 初回起動時はDiscordのAPI制限により、スラッシュコマンドの同期に時間がかかる場合があります
- 大容量のAIモデル使用時は十分なメモリ（8GB以上推奨）が必要です
- 本番環境では適切なセキュリティ設定を行ってください