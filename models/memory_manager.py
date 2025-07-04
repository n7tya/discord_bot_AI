"""
記憶管理 - サーバー別会話履歴管理

ユーザーとサーバーごとに会話履歴を管理する改善版
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional


class MemoryManager:
    """サーバー別会話履歴管理クラス"""
    
    def __init__(self):
        self.memory_path = "data/conversations/memories/"
        os.makedirs(self.memory_path, exist_ok=True)
        
    def _get_file_path(self, user_id: str, guild_id: Optional[str] = None) -> str:
        """ファイルパスを取得（サーバー別）"""
        if guild_id:
            # サーバー別の履歴
            server_dir = os.path.join(self.memory_path, f"guild_{guild_id}")
            os.makedirs(server_dir, exist_ok=True)
            return os.path.join(server_dir, f"{user_id}.json")
        else:
            # DM用の履歴
            dm_dir = os.path.join(self.memory_path, "direct_messages")
            os.makedirs(dm_dir, exist_ok=True)
            return os.path.join(dm_dir, f"{user_id}.json")
        
    def get_context(self, user_id: str, guild_id: Optional[str] = None) -> List[Dict]:
        """ユーザーの会話履歴を取得"""
        file_path = self._get_file_path(user_id, guild_id)
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('conversations', [])
        except Exception as e:
            print(f"会話履歴読み込みエラー: {e}")
        
        return []
        
    def add_conversation(
        self, 
        user_id: str, 
        user_message: str, 
        ai_response: str,
        guild_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        message_type: str = "command"
    ):
        """会話を記録（改善版）"""
        file_path = self._get_file_path(user_id, guild_id)
        
        try:
            # 既存のデータを読み込み
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {
                    "user_id": user_id,
                    "guild_id": guild_id,
                    "created_at": datetime.now().isoformat(),
                    "conversations": []
                }
                
            # 新しい会話を追加
            conversation = {
                "timestamp": datetime.now().isoformat(),
                "user": user_message[:500],  # 長さ制限
                "assistant": ai_response[:500],  # 長さ制限
                "channel_id": channel_id,
                "type": message_type  # "command" or "auto_response"
            }
            
            data['conversations'].append(conversation)
            
            # 最新の30件のみ保持（サーバー別で効率化）
            if len(data['conversations']) > 30:
                data['conversations'] = data['conversations'][-30:]
                
            # 保存
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"会話履歴保存エラー: {e}")
            
    def clear_memory(self, user_id: str, guild_id: Optional[str] = None):
        """ユーザーの会話履歴をクリア"""
        file_path = self._get_file_path(user_id, guild_id)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"会話履歴削除エラー: {e}")
            
    def export_memory(self, user_id: str, guild_id: Optional[str] = None) -> str:
        """会話履歴をエクスポート"""
        conversations = self.get_context(user_id, guild_id)
        if not conversations:
            return "会話履歴がありません。"
            
        guild_name = f"サーバー{guild_id}" if guild_id else "DM"
        export_text = f"=== {guild_name} - {user_id} の会話履歴 ===\n\n"
        
        for conv in conversations:
            timestamp = conv.get('timestamp', '不明')
            msg_type = conv.get('type', 'command')
            channel = conv.get('channel_id', '不明')
            
            export_text += f"[{timestamp}] ({msg_type}) チャンネル: {channel}\n"
            export_text += f"ユーザー: {conv.get('user', '')}\n"
            export_text += f"AI: {conv.get('assistant', '')}\n\n"
            
        return export_text
    
    def get_server_stats(self, guild_id: str) -> Dict:
        """サーバーの統計情報を取得"""
        server_dir = os.path.join(self.memory_path, f"guild_{guild_id}")
        
        if not os.path.exists(server_dir):
            return {"total_users": 0, "total_conversations": 0}
        
        total_users = 0
        total_conversations = 0
        
        try:
            for file in os.listdir(server_dir):
                if file.endswith('.json'):
                    total_users += 1
                    file_path = os.path.join(server_dir, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        total_conversations += len(data.get('conversations', []))
        except Exception as e:
            print(f"統計取得エラー: {e}")
        
        return {
            "total_users": total_users,
            "total_conversations": total_conversations
        }