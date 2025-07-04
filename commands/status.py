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
        self.start_time = datetime.now()

    @app_commands.command(name="status", description="ボットとAIの状態を確認します")
    async def status(self, interaction: discord.Interaction):
        # 即座に応答を返す（3秒のタイムアウトを防ぐ）
        await interaction.response.defer()

        try:
            # システム情報を取得
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # GPU情報を取得
            if TORCH_AVAILABLE and torch.cuda.is_available():
                gpu_available = True
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory // 1024 ** 3
            else:
                gpu_available = False
                gpu_name = "PyTorch未インストール" if not TORCH_AVAILABLE else "なし"
                gpu_memory = 0

            # 会話データの統計（サーバー別に対応）
            conversations_dir = "data/conversations/memories"
            total_conversations = 0
            total_servers = 0
            
            if os.path.exists(conversations_dir):
                for item in os.listdir(conversations_dir):
                    item_path = os.path.join(conversations_dir, item)
                    if os.path.isdir(item_path) and item.startswith("guild_"):
                        total_servers += 1
                        for file in os.listdir(item_path):
                            if file.endswith('.json'):
                                total_conversations += 1
                    elif item.endswith('.json'):
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
            from config import Config
            embed.add_field(
                name="🧠 AI情報",
                value=(
                    f"**モデル**: {Config.AI_MODEL_NAME}\n"
                    f"**GPU**: {gpu_name}\n"
                    f"**GPU メモリ**: {gpu_memory}GB\n"
                    f"**学習データ**: {total_conversations} ユーザー\n"
                    f"**MPS**: {'有効' if Config.AI_USE_MPS else '無効'}"
                ),
                inline=True
            )
            
            # サーバー統計
            embed.add_field(
                name="🌐 サーバー統計",
                value=(
                    f"**サーバー数**: {total_servers}\n"
                    f"**会話履歴あり**: {total_conversations}ユーザー\n"
                    f"**データ管理**: サーバー別分離"
                ),
                inline=True
            )

            # システム情報
            embed.add_field(
                name="⚙️ システム情報",
                value=(
                    f"**CPU使用率**: {cpu_percent}%\n"
                    f"**メモリ**: {memory.percent}% ({memory.used // 1024 ** 3}GB/{memory.total // 1024 ** 3}GB)\n"
                    f"**ディスク**: {disk.percent}% ({disk.used // 1024 ** 3}GB/{disk.total // 1024 ** 3}GB)\n"
                    f"**PyTorch**: {'利用可能' if TORCH_AVAILABLE else '未インストール'}"
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

            # followupで実際のメッセージを送信
            await interaction.followup.send(embed=embed)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ エラー",
                description=f"状態の取得中にエラーが発生しました: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed)

    def _get_uptime(self):
        """ボットの稼働時間を取得"""
        uptime = datetime.now() - self.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if days > 0:
            return f"{days}日 {hours}時間 {minutes}分"
        elif hours > 0:
            return f"{hours}時間 {minutes}分"
        else:
            return f"{minutes}分 {seconds}秒"


async def setup(bot):
    await bot.add_cog(StatusCog(bot))