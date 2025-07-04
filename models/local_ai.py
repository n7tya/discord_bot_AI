"""
ローカルAIモデル - 日本語会話AI

安全で軽量な日本語会話AIの実装
"""

import asyncio
import json
import os
import random
from datetime import datetime
from typing import List, Dict, Optional

# PyTorchとTransformersのインポートを安全に行う
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class LocalAI:
    """ローカル日本語AIモデル"""
    
    def __init__(self):
        """AIモデルの初期化"""
        from config import Config
        self.model_name = Config.AI_MODEL_NAME
        self.device = None
        self.tokenizer = None
        self.model = None
        self.use_real_model = False
        
        # 学習データのパス
        self.training_data_path = "data/conversations/training_data.json"
        
        # モデルの初期化を試行
        self._initialize_model()

    def _initialize_model(self):
        """モデルの初期化処理"""
        if not TORCH_AVAILABLE:
            print("❌ PyTorchが利用できません。ダミーAIを使用します")
            return

        try:
            # Mac Apple Silicon (M1/M2)の場合はMPS、それ以外はCPU
            from config import Config
            if torch.backends.mps.is_available() and Config.AI_USE_MPS:
                self.device = torch.device("mps")
                print("🍎 Apple Silicon (MPS) を使用します")
            elif torch.cuda.is_available():
                self.device = torch.device("cuda")
                print("🚀 CUDA GPU を使用します")
            else:
                self.device = torch.device("cpu")
                print("💻 CPU を使用します")
                
            print(f"日本語モデル {self.model_name} をロード中...")
            
            # トークナイザーのロード
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                use_fast=True
            )
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # モデルのロード（Apple Silicon最適化）
            model_kwargs = {
                "low_cpu_mem_usage": True,
                "use_cache": True
            }
            
            # Apple Silicon (MPS)の場合の最適化
            if self.device.type == "mps":
                model_kwargs["torch_dtype"] = torch.float32  # MPSはfloat16をサポートしない場合があるため
            elif self.device.type == "cuda":
                model_kwargs["torch_dtype"] = torch.float16
            else:
                model_kwargs["torch_dtype"] = torch.float32
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_kwargs
            )
            
            # モデルをデバイスに移動
            self.model = self.model.to(self.device)
            self.model.eval()
            self.use_real_model = True
            
            print("✅ 日本語モデルのロードが完了しました")
            print(f"   デバイス: {self.device}")
            print(f"   メモリ使用量: {torch.cuda.memory_allocated() / 1024**2:.1f}MB" if self.device.type == "cuda" else "")
            
        except Exception as e:
            print(f"❌ モデルロードエラー: {e}")
            print("🔄 ダミーモードに切り替えます")
            self._reset_to_dummy_mode()
    def _reset_to_dummy_mode(self):
        """ダミーモードにリセット"""
        self.use_real_model = False
        self.tokenizer = None
        self.model = None

    async def generate_response(self, message: str, context: List[Dict]) -> str:
        """メッセージに対する応答を生成"""
        return await asyncio.to_thread(self._generate_sync, message, context)
        
    def _generate_sync(self, message: str, context: List[Dict]) -> str:
        """同期的な応答生成"""
        # 入力の検証
        if not message or len(message.strip()) == 0:
            return "何かメッセージをお聞かせください。"
        
        # 長すぎるメッセージの制限
        if len(message) > 500:
            return "メッセージが長すぎます。もう少し短くしてください。"
        
        # ダミーモードの場合
        if not self.use_real_model:
            return self._generate_dummy_response(message, context)
        
        # 実際のAIモデルでの生成
        try:
            return self._generate_real_response(message, context)
        except Exception as e:
            print(f"AI生成エラー: {e}")
            return self._generate_dummy_response(message, context)

    def _generate_dummy_response(self, message: str, context: List[Dict]) -> str:
        """ダミー応答の生成"""
        responses = [
            f"「{message}」について考えてみますね。",
            f"なるほど、「{message}」ですね。",
            f"「{message}」に関してお答えします。",
            f"「{message}」について一緒に考えてみましょう。"
        ]
        
        # コンテキストを考慮
        if context and len(context) > 0:
            last_conv = context[-1]
            if 'user' in last_conv:
                responses.append(f"先ほどの話も踏まえて、「{message}」についてお答えしますね。")
        
        return random.choice(responses)

    def _generate_real_response(self, message: str, context: List[Dict]) -> str:
        """実際のAIモデルでの応答生成"""
        # プロンプトの作成
        prompt = self._build_prompt(message, context)
        
        # トークナイズ
        inputs = self.tokenizer(
            prompt, 
            return_tensors="pt", 
            max_length=400,  # より短い制限で安全性向上
            truncation=True
        ).to(self.device)
        
        # より安全で制御された生成パラメータ（設定ファイルから読み込み）
        from config import Config
        with torch.no_grad():
            outputs = self.model.generate(
                inputs.input_ids,
                max_new_tokens=Config.AI_MAX_TOKENS,     # 設定ファイルから読み込み
                min_new_tokens=5,                        # 最低限の長さ
                temperature=Config.AI_TEMPERATURE,       # 設定ファイルから読み込み
                do_sample=True,
                top_p=0.8,               # より制限的
                top_k=20,                # 語彙を制限
                repetition_penalty=1.2,   # 繰り返し強く抑制
                no_repeat_ngram_size=3,   # より長いn-gramの繰り返し防止
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                bad_words_ids=[[self.tokenizer.unk_token_id]] if hasattr(self.tokenizer, 'unk_token_id') else None
            )
        
        # デコードと後処理
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = response.replace(prompt, "").strip()
        
        # 応答のクリーニング
        response = self._clean_response(response)
        
        return response if response else "申し訳ございません。うまく応答できませんでした。"
    def _build_prompt(self, message: str, context: List[Dict]) -> str:
        """対話プロンプトの構築（改善版）"""
        # より制御しやすいシンプルなプロンプト
        prompt = ""
        
        # コンテキストは最新の1つのみ（混乱を避ける）
        if context and len(context) > 0:
            last_conv = context[-1]
            if 'user' in last_conv and 'assistant' in last_conv:
                prompt += f"前回: {last_conv['user']} → {last_conv['assistant']}\n"
        
        prompt += f"質問: {message}\n回答:"
        return prompt
    
    def _clean_response(self, response: str) -> str:
        """応答のクリーニング（強化版）"""
        if not response:
            return ""
        
        # 基本的なクリーニング
        response = response.strip()
        
        # 改行を除去
        response = response.replace('\n', ' ')
        
        # 連続する空白を単一の空白に
        import re
        response = re.sub(r'\s+', ' ', response)
        
        # 短すぎる場合は除外
        if len(response) < 3:
            return ""
        
        # 長すぎる場合は最初の文のみ
        sentences = response.split('。')
        if len(sentences) > 0 and sentences[0].strip():
            response = sentences[0].strip()
            # 文の終わりに句点を追加（ない場合）
            if not response.endswith(('。', '！', '？')):
                response += '。'
        
        # 異常なパターンを検出して除外
        if any(pattern in response.lower() for pattern in [
            'http', 'www.', 'chatroom', 'website', 'translation', 
            'contact me', 'support', 'blog', 'english'
        ]):
            return ""
        
        # 100文字を超える場合は切り詰め
        if len(response) > 100:
            response = response[:100] + "..."
        
        return response
        
    async def update_learning_data(self, user_id: str, message: str, response: str):
        """学習データの更新（簡略版）"""
        try:
            # データの保存（シンプル版）
            data = {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "message": message[:100],  # 長さ制限
                "response": response[:200]  # 長さ制限
            }
            
            os.makedirs(os.path.dirname(self.training_data_path), exist_ok=True)
            
            # 既存データの読み込み
            training_data = []
            if os.path.exists(self.training_data_path):
                with open(self.training_data_path, 'r', encoding='utf-8') as f:
                    training_data = json.load(f)
            
            # 新しいデータを追加
            training_data.append(data)
            
            # 最新の1000件のみ保持
            if len(training_data) > 1000:
                training_data = training_data[-1000:]
            
            # データを保存
            with open(self.training_data_path, 'w', encoding='utf-8') as f:
                json.dump(training_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"学習データ保存エラー: {e}")