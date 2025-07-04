import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Discord設定
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    GUILD_ID = os.getenv('GUILD_ID')  # スラッシュコマンド即時適用用のサーバーID
    
    # AI設定
    AI_MODEL_NAME = os.getenv('AI_MODEL_NAME', 'rinna/japanese-gpt2-medium')
    AI_MAX_TOKENS = int(os.getenv('AI_MAX_TOKENS', '100'))
    AI_TEMPERATURE = float(os.getenv('AI_TEMPERATURE', '0.8'))
    
    # データベース設定
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/bot.db')
    
    # ログ設定
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/bot.log')
    
    # 管理者設定
    ADMIN_IDS = os.getenv('ADMIN_IDS', '').split(',')