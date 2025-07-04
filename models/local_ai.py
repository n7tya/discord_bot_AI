import json
import os
from datetime import datetime
import asyncio
import random

# PyTorchとTransformersのインポートを安全に行う
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    TORCH_AVAILABLE = True
except ImportError as e:
    print(f"PyTorch/Transformersのインポートエラー: {e}")
    TORCH_AVAILABLE = False

class LocalAI:
    def __init__(self):
        # より軽量な日本語モデルを使用
        self.model_name = "rinna/japanese-gpt2-medium"
        
        if TORCH_AVAILABLE:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = None
        
        # 実際のAIモデルを有効化（PyTorchが利用できる場合）
        self.use_real_model = TORCH_AVAILABLE
        
        try:
            if self.use_real_model and TORCH_AVAILABLE:
                # モデルとトークナイザーの初期化
                print(f"日本語モデル {self.model_name} をロード中...")
                
                # トークナイザーのロード
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name,
                    use_fast=True
                )
                
                # pad_tokenの設定
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
                
                # モデルのロード（メモリ最適化）
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    device_map="auto" if torch.cuda.is_available() else None,
                    low_cpu_mem_usage=True,
                    trust_remote_code=True
                )
                
                # モデルをデバイスに移動
                if not torch.cuda.is_available():
                    self.model = self.model.to(self.device)
                
                # 評価モードに設定
                self.model.eval()
                
                print("✅ 日本語モデルのロードが完了しました")
                print(f"   デバイス: {self.device}")
                print(f"   モデルサイズ: {sum(p.numel() for p in self.model.parameters())/1e6:.1f}M parameters")
                
            else:
                # ダミーモデル
                if not TORCH_AVAILABLE:
                    print("❌ PyTorchが利用できません。ダミーAIを使用します")
                else:
                    print("🔧 デバッグモード: ダミーAIを使用します")
                self.tokenizer = None
                self.model = None
                
        except Exception as e:
            print(f"❌ モデルロードエラー: {e}")
            print("🔄 フォールバック: ダミーモードに切り替えます")
            self.use_real_model = False
            self.tokenizer = None
            self.model = None
        
        # 学習データのパス
        self.training_data_path = "data/conversations/training_data.json"
        
    async def generate_response(self, message: str, context: list) -> str:
        # 非同期でCPU集約的なタスクを実行
        return await asyncio.to_thread(self._generate_sync, message, context)
        
    def _generate_sync(self, message: str, context: list) -> str:
        if not self.use_real_model:
            # デバッグ用のダミー応答
            dummy_responses = [
                f"こんにちは！「{message}」について考えてみますね。",
                f"なるほど、「{message}」ですね。興味深いお話です。",
                f"「{message}」について、私なりに回答させていただきます。",
                f"ご質問の「{message}」に関して、お答えします。",
                f"「{message}」について、一緒に考えてみましょう。"
            ]
            
            # コンテキストを考慮したより自然な応答
            if context:
                last_conv = context[-1] if context else None
                if last_conv:
                    dummy_responses.append(f"先ほどの「{last_conv.get('user', '')}」の件も含めて、「{message}」について回答しますね。")
            
            return random.choice(dummy_responses)
        
        # 実際のモデルを使用する場合
        if not TORCH_AVAILABLE:
            return f"PyTorchが利用できないため、「{message}」にダミー応答でお答えします。"
            
        try:
            # コンテキストを含むプロンプトを作成
            prompt = self._build_prompt(message, context)
            
            # トークナイズ（最大長制限）
            inputs = self.tokenizer(
                prompt, 
                return_tensors="pt", 
                max_length=512, 
                truncation=True
            ).to(self.device)
            
            # 生成パラメータ（日本語会話最適化）
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_new_tokens=100,  # より短く、応答性を向上
                    min_new_tokens=10,   # 最低限の長さを保証
                    temperature=0.8,     # 適度な創造性
                    do_sample=True,
                    top_p=0.85,          # 自然な応答のバランス
                    top_k=40,            # 語彙の多様性制御
                    repetition_penalty=1.15,  # 繰り返し抑制強化
                    no_repeat_ngram_size=2,   # n-gram繰り返し防止
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    early_stopping=True
                )
            
            # デコードと後処理
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = response.replace(prompt, "").strip()
            
            # レスポンスのクリーニング
            response = self._clean_response(response)
            
            return response if response else "すみません、うまく応答を生成できませんでした。"
            
        except Exception as e:
            print(f"AI生成エラー: {e}")
            # エラー時もより自然なフォールバック
            fallback_responses = [
                f"「{message}」について考えてみますが、今は少し調子が悪いようです。",
                f"申し訳ありません。「{message}」に関して、今すぐお答えできません。",
                f"「{message}」についてお聞きいただきありがとうございます。少し時間をください。"
            ]
            return random.choice(fallback_responses)
        
    def _build_prompt(self, message: str, context: list) -> str:
        # 日本語会話に最適化されたプロンプト
        prompt = "あなたは親切で知識豊富な日本語AIアシスタントです。自然で親しみやすい会話を心がけてください。\n\n"
        
        # 最新の3つの会話を含める（メモリ効率化）
        recent_context = context[-3:] if context else []
        for conv in recent_context:
            prompt += f"ユーザー: {conv['user']}\n"
            prompt += f"アシスタント: {conv['assistant']}\n"
            
        prompt += f"ユーザー: {message}\nアシスタント: "
        
        return prompt
    
    def _clean_response(self, response: str) -> str:
        """応答のクリーニングと後処理"""
        if not response:
            return ""
        
        # 不要な改行や空白を除去
        response = response.strip()
        
        # 文の途中で切れている場合の処理
        sentences = response.split('。')
        if len(sentences) > 1 and sentences[-1].strip() and not sentences[-1].endswith(('！', '？', '♪')):
            # 最後の不完全な文を除去
            response = '。'.join(sentences[:-1]) + '。'
        
        # 短すぎる応答の除外
        if len(response.replace(' ', '').replace('\n', '')) < 5:
            return ""
        
        # 重複フレーズの除去
        lines = response.split('\n')
        unique_lines = []
        for line in lines:
            if line.strip() and line.strip() not in unique_lines:
                unique_lines.append(line.strip())
        
        return '\n'.join(unique_lines) if unique_lines else response
        
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