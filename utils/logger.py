import logging
import os
from datetime import datetime
from config import Config


class BotLogger:
    """Discord Bot用ロガークラス"""
    
    def __init__(self):
        """ロガーの初期化"""
        self.logger = logging.getLogger('discord_bot')
        self.setup_logger()
    
    def setup_logger(self):
        """ロガーの設定"""
        # ログレベルの設定
        level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # フォーマッターの設定
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # ファイルハンドラー
        if Config.LOG_FILE:
            # ログディレクトリの作成
            log_dir = os.path.dirname(Config.LOG_FILE)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            file_handler = logging.FileHandler(Config.LOG_FILE, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def info(self, message: str):
        """情報ログ"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """警告ログ"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """エラーログ"""
        self.logger.error(message)
    
    def debug(self, message: str):
        """デバッグログ"""
        self.logger.debug(message)
    
    def log_command(self, user_id: str, command: str, success: bool = True):
        """コマンド実行ログ"""
        status = "SUCCESS" if success else "FAILED"
        self.info(f"Command {command} by user {user_id}: {status}")
    
    def log_ai_response(self, user_id: str, message_length: int, response_length: int, duration: float):
        """AI応答ログ"""
        self.info(f"AI response for user {user_id}: {message_length} -> {response_length} chars in {duration:.2f}s")
    
    def log_error_with_traceback(self, error: Exception, context: str = ""):
        """エラーとトレースバックをログ"""
        import traceback
        error_msg = f"Error in {context}: {str(error)}\n{traceback.format_exc()}"
        self.error(error_msg)


# グローバルロガーインスタンス
bot_logger = BotLogger()