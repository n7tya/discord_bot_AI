import discord
from discord import app_commands
from discord.ext import commands
import psutil
import os
from datetime import datetime

# PyTorchのインポートを安全に行う
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

class StatusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="status", description="ボットとAIの状態を確認します")
    async def status(self, interaction: discord.Interaction):
        # システム情報を取得
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # GPU情報を取得
        if TORCH_AVAILABLE:
            gpu_available = torch.cuda.is_available()
            gpu_name = torch.cuda.get_device_name(0) if gpu_available else "なし"
            gpu_memory = torch.cuda.get_device_properties(0).total_memory // 1024**3 if gpu_available else 0
        else:
            gpu_available = False
            gpu_name = "PyTorch未インストール"
            gpu_memory = 0
        
        # 会話データの統計
        conversations_dir = "data/conversations/memories"
        total_conversations = 0
        if os.path.exists(conversations_dir):
            for file in os.listdir(conversations_dir):
                if file.endswith('.json'):
                    total_conversations += 1
        
        embed = discord.Embed(
            title="🔍 ボット状態",
            description="現在のボットとAIシステムの状態です",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # ボット情報
        embed.add_field(
            name="🤖 ボット情報",
            value=(
                f"**稼働時間**: {self._get_uptime()}\n"
                f"**サーバー数**: {len(self.bot.guilds)}\n"
                f"**ユーザー数**: {len(self.bot.users)}\n"
                f"**Ping**: {round(self.bot.latency * 1000)}ms"
            ),
            inline=True
        )
        
        # AI情報
        embed.add_field(
            name="🧠 AI情報",
            value=(
                f"**モデル**: rinna/japanese-gpt-neox-3.6b\n"
                f"**GPU**: {gpu_name}\n"
                f"**GPU メモリ**: {gpu_memory}GB\n"
                f"**学習データ**: {total_conversations} ユーザー"
            ),
            inline=True
        )
        
        # システム情報
        embed.add_field(
            name="⚙️ システム情報",
            value=(
                f"**CPU使用率**: {cpu_percent}%\n"
                f"**メモリ**: {memory.percent}% ({memory.used//1024**3}GB/{memory.total//1024**3}GB)\n"
                f"**ディスク**: {disk.percent}% ({disk.used//1024**3}GB/{disk.total//1024**3}GB)\n"
                f"**Python**: {torch.__version__}"
            ),
            inline=False
        )
        
        # 状態インジケーター
        if cpu_percent < 50 and memory.percent < 80:
            embed.color = discord.Color.green()
            status_text = "🟢 正常"
        elif cpu_percent < 80 and memory.percent < 90:
            embed.color = discord.Color.yellow()
            status_text = "🟡 注意"
        else:
            embed.color = discord.Color.red()
            status_text = "🔴 負荷高"
            
        embed.add_field(
            name="📊 システム状態",
            value=status_text,
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    def _get_uptime(self):
        """ボットの稼働時間を取得"""
        # 簡易的な実装
        return "稼働中"

async def setup(bot):
    await bot.add_cog(StatusCog(bot))