# CLAUDE.md - Discord Bot開発ガイド

## 概要
このドキュメントは、AI対話機能を持つDiscord botの開発ガイドラインです。各開発セッションの開始時に必ず読み上げてください。

## プロジェクト構造
```
discord-bot/
├── main.py                 # メインファイル（bot起動）
├── config.py              # 設定ファイル
├── requirements.txt       # 依存関係
├── commands/              # コマンドフォルダ
│   ├── __init__.py
│   ├── ai_chat.py        # AI対話コマンド
│   ├── help.py           # ヘルプコマンド
│   ├── status.py         # ステータス確認コマンド
│   ├── memory.py         # 記憶管理コマンド
│   └── admin.py          # 管理者用コマンド
├── models/                # AIモデル関連
│   ├── __init__.py
│   ├── local_ai.py       # ローカルAIモデル
│   └── memory_manager.py # 記憶管理システム
├── utils/                 # ユーティリティ
│   ├── __init__.py
│   ├── logger.py         # ログ管理
│   └── database.py       # データベース管理
└── data/                  # データ保存用
    ├── conversations/     # 会話履歴
    ├── models/           # モデルファイル
    └── config/           # 設定ファイル
```

## 開発要件

### 1. 基本要件
- **言語**: Python 3.9以上
- **フレームワーク**: discord.py 2.0以上
- **AI対話**: ローカルで動作する日本語特化型モデル
- **コマンド形式**: スラッシュコマンド（/command）

### 2. 必須機能
- **AI対話機能**: ローカルAIによる自然な日本語会話
- **学習・成長機能**: 会話履歴を基にした継続的な最適化
- **記憶システム**: ユーザーごとの会話履歴と文脈の保持
- **スラッシュコマンド**: 全コマンドのスラッシュコマンド対応

### 3. ローカルAI仕様
- **モデル**: Japanese-optimized GPT/BERT系モデル（例: rinna/japanese-gpt-neox）
- **実装**: Hugging Face Transformersを使用
- **最適化**: 量子化技術による軽量化（INT8/INT4）
- **学習**: Fine-tuningによる継続的改善

## コマンド一覧

### 基本コマンド
1. **/chat [メッセージ]** - AIと対話
2. **/help** - ヘルプメッセージ表示
3. **/status** - botとAIの状態確認
4. **/memory [action]** - 記憶管理（表示/クリア/エクスポート）

### 管理者コマンド
1. **/admin reload** - 設定リロード
2. **/admin train** - AIモデルの追加学習
3. **/admin backup** - データバックアップ
4. **/admin stats** - 使用統計表示

### 便利機能コマンド
1. **/translate [言語] [テキスト]** - 翻訳機能
2. **/summary [チャンネル]** - チャンネルの会話要約
3. **/remind [時間] [内容]** - リマインダー設定
4. **/poll [質問] [選択肢...]** - 投票作成

## 実装詳細

### main.py
```python
import discord
from discord.ext import commands
import asyncio
import logging
from config import Config
from commands import ai_chat, help, status, memory, admin

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='/', intents=intents)
        
    async def setup_hook(self):
        # コマンドの登録
        await self.add_cog(ai_chat.AIChatCog(self))
        await self.add_cog(help.HelpCog(self))
        await self.add_cog(status.StatusCog(self))
        await self.add_cog(memory.MemoryCog(self))
        await self.add_cog(admin.AdminCog(self))
        
        # スラッシュコマンドの同期
        await self.tree.sync()
        
    async def on_ready(self):
        print(f'{self.user} として起動しました！')
        await self.change_presence(activity=discord.Game(name="/help でヘルプ"))

def main():
    bot = DiscordBot()
    bot.run(Config.DISCORD_TOKEN)

if __name__ == "__main__":
    main()
```

### commands/ai_chat.py
```python
import discord
from discord import app_commands
from discord.ext import commands
from models.local_ai import LocalAI
from models.memory_manager import MemoryManager
import asyncio

class AIChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ai = LocalAI()
        self.memory = MemoryManager()
        
    @app_commands.command(name="chat", description="AIと対話します")
    @app_commands.describe(message="AIに送るメッセージ")
    async def chat(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer()
        
        # ユーザーの会話履歴を取得
        user_id = str(interaction.user.id)
        context = self.memory.get_context(user_id)
        
        # AI応答生成
        response = await self.ai.generate_response(message, context)
        
        # 会話履歴を更新
        self.memory.add_conversation(user_id, message, response)
        
        # 応答送信
        embed = discord.Embed(
            title="AI Assistant",
            description=response,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"返信先: {interaction.user.name}")
        
        await interaction.followup.send(embed=embed)
        
        # 非同期で学習データを更新
        asyncio.create_task(self.ai.update_learning_data(user_id, message, response))

async def setup(bot):
    await bot.add_cog(AIChatCog(bot))
```

### models/local_ai.py
```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
import os
from datetime import datetime
import asyncio

class LocalAI:
    def __init__(self):
        self.model_name = "rinna/japanese-gpt-neox-3.6b"
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # モデルとトークナイザーの初期化
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto"
        )
        
        # 学習データのパス
        self.training_data_path = "data/conversations/training_data.json"
        
    async def generate_response(self, message: str, context: list) -> str:
        # 非同期でCPU集約的なタスクを実行
        return await asyncio.to_thread(self._generate_sync, message, context)
        
    def _generate_sync(self, message: str, context: list) -> str:
        # コンテキストを含むプロンプトを作成
        prompt = self._build_prompt(message, context)
        
        # トークナイズ
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        # 生成
        with torch.no_grad():
            outputs = self.model.generate(
                inputs.input_ids,
                max_new_tokens=200,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
        
        # デコード
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = response.replace(prompt, "").strip()
        
        return response
        
    def _build_prompt(self, message: str, context: list) -> str:
        prompt = "以下は親切で知識豊富なAIアシスタントとユーザーの会話です。\n\n"
        
        # 最新の5つの会話を含める
        for conv in context[-5:]:
            prompt += f"ユーザー: {conv['user']}\n"
            prompt += f"アシスタント: {conv['assistant']}\n"
            
        prompt += f"ユーザー: {message}\nアシスタント: "
        
        return prompt
        
    async def update_learning_data(self, user_id: str, message: str, response: str):
        # 学習データに追加
        data = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "response": response
        }
        
        # 既存のデータを読み込み
        if os.path.exists(self.training_data_path):
            with open(self.training_data_path, 'r', encoding='utf-8') as f:
                training_data = json.load(f)
        else:
            training_data = []
            
        training_data.append(data)
        
        # データを保存
        os.makedirs(os.path.dirname(self.training_data_path), exist_ok=True)
        with open(self.training_data_path, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, ensure_ascii=False, indent=2)
            
        # 一定量のデータが溜まったら自動的にファインチューニング
        if len(training_data) % 100 == 0:
            asyncio.create_task(self._fine_tune_model())
            
    async def _fine_tune_model(self):
        # ファインチューニングの実装（簡略版）
        print("モデルのファインチューニングを開始します...")
        # 実際の実装では、LoRAやQLoRAなどの効率的な手法を使用
        pass
```

### models/memory_manager.py
```python
import json
import os
from datetime import datetime
from typing import List, Dict

class MemoryManager:
    def __init__(self):
        self.memory_path = "data/conversations/memories/"
        os.makedirs(self.memory_path, exist_ok=True)
        
    def get_context(self, user_id: str) -> List[Dict]:
        """ユーザーの会話履歴を取得"""
        file_path = os.path.join(self.memory_path, f"{user_id}.json")
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('conversations', [])
        
        return []
        
    def add_conversation(self, user_id: str, user_message: str, ai_response: str):
        """会話を記録"""
        file_path = os.path.join(self.memory_path, f"{user_id}.json")
        
        # 既存のデータを読み込み
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
                "conversations": []
            }
            
        # 新しい会話を追加
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "user": user_message,
            "assistant": ai_response
        }
        
        data['conversations'].append(conversation)
        
        # 最新の50件のみ保持（メモリ管理）
        if len(data['conversations']) > 50:
            data['conversations'] = data['conversations'][-50:]
            
        # 保存
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def clear_memory(self, user_id: str):
        """ユーザーの会話履歴をクリア"""
        file_path = os.path.join(self.memory_path, f"{user_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            
    def export_memory(self, user_id: str) -> str:
        """会話履歴をエクスポート"""
        conversations = self.get_context(user_id)
        if not conversations:
            return "会話履歴がありません。"
            
        export_text = f"=== {user_id} の会話履歴 ===\n\n"
        for conv in conversations:
            export_text += f"[{conv['timestamp']}]\n"
            export_text += f"ユーザー: {conv['user']}\n"
            export_text += f"AI: {conv['assistant']}\n\n"
            
        return export_text
```

### config.py
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Discord設定
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    
    # AI設定
    AI_MODEL_NAME = os.getenv('AI_MODEL_NAME', 'rinna/japanese-gpt-neox-3.6b')
    AI_MAX_TOKENS = int(os.getenv('AI_MAX_TOKENS', '200'))
    AI_TEMPERATURE = float(os.getenv('AI_TEMPERATURE', '0.7'))
    
    # データベース設定
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/bot.db')
    
    # ログ設定
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/bot.log')
    
    # 管理者設定
    ADMIN_IDS = os.getenv('ADMIN_IDS', '').split(',')
```

### requirements.txt
```
discord.py>=2.3.0
transformers>=4.35.0
torch>=2.0.0
accelerate>=0.24.0
sentencepiece>=0.1.99
python-dotenv>=1.0.0
aiosqlite>=0.19.0
numpy>=1.24.0
scipy>=1.10.0
```

## セットアップ手順

1. **環境構築**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **.envファイルの作成**
   ```
   DISCORD_TOKEN=your_discord_bot_token
   AI_MODEL_NAME=rinna/japanese-gpt-neox-3.6b
   ADMIN_IDS=your_discord_id,other_admin_id
   ```

3. **初回起動**
   ```bash
   python main.py
   ```

## 開発時の注意事項

### 必ず守ること
1. **このCLAUDE.mdを毎回読み上げる**
2. **mainと各コマンドのファイルを分離する**
3. **全てPythonで実装する**
4. **全コマンドをスラッシュコマンドで実装**
5. **AIはローカルで動作させる（API不使用）**
6. **日本語に特化した実装**
7. **会話履歴による学習・成長機能の実装**

### パフォーマンス最適化
- モデルの量子化（INT8/INT4）を活用
- 非同期処理を徹底
- キャッシュの適切な利用
- バッチ処理での学習データ更新

### セキュリティ
- ユーザーデータの適切な管理
- 管理者コマンドの権限チェック
- エラーハンドリングの徹底
- ログの適切な記録

## トラブルシューティング

### よくある問題
1. **メモリ不足**: モデルサイズを小さくするか、量子化を適用
2. **応答が遅い**: GPUの使用、またはより小さいモデルへの変更
3. **文字化け**: エンコーディングをUTF-8に統一
4. **スラッシュコマンドが表示されない**: tree.sync()の実行確認

## 今後の拡張案
- 音声認識・合成機能
- 画像生成・認識機能
- より高度な記憶システム
- マルチモーダル対応
- プラグインシステム

---
最終更新: 2025年7月4日