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