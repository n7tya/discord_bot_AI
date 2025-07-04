"""
自動応答管理 - チャンネル指定での自動AI応答機能

指定されたチャンネルでのメッセージに自動的にAIが応答する機能を管理
"""

import json
import os
from typing import Set


class AutoResponseManager:
    """自動応答チャンネル管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.config_path = "data/config/auto_response_channels.json"
        self.active_channels: Set[int] = set()
        self._load_config()

    def _load_config(self):
        """設定ファイルの読み込み"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.active_channels = set(data.get('channels', []))
        except Exception as e:
            print(f"自動応答設定の読み込みエラー: {e}")
            self.active_channels = set()

    def _save_config(self):
        """設定ファイルの保存"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            data = {
                'channels': list(self.active_channels)
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"自動応答設定の保存エラー: {e}")

    def add_channel(self, channel_id: int) -> bool:
        """チャンネルを自動応答リストに追加"""
        if channel_id not in self.active_channels:
            self.active_channels.add(channel_id)
            self._save_config()
            return True
        return False

    def remove_channel(self, channel_id: int) -> bool:
        """チャンネルを自動応答リストから削除"""
        if channel_id in self.active_channels:
            self.active_channels.remove(channel_id)
            self._save_config()
            return True
        return False

    def is_active_channel(self, channel_id: int) -> bool:
        """指定チャンネルが自動応答対象かチェック"""
        return channel_id in self.active_channels

    def get_active_channels(self) -> Set[int]:
        """アクティブなチャンネル一覧を取得"""
        return self.active_channels.copy()

    def clear_all_channels(self):
        """全ての自動応答チャンネルをクリア"""
        self.active_channels.clear()
        self._save_config()


# グローバルインスタンス
auto_response_manager = AutoResponseManager()