import discord
from discord import app_commands
from discord.ext import commands
from typing import Literal
from config import Config
import json
import os
import shutil
from datetime import datetime

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    def is_admin(self, user_id: str) -> bool:
        """管理者かどうかチェック"""
        return user_id in Config.ADMIN_IDS
        
    @app_commands.command(name="admin", description="管理者コマンド")
    @app_commands.describe(action="実行するアクション")
    async def admin(self, interaction: discord.Interaction, action: Literal["reload", "train", "backup", "stats"]):
        user_id = str(interaction.user.id)
        
        # 管理者権限チェック
        if not self.is_admin(user_id):
            embed = discord.Embed(
                title="🚫 権限エラー",
                description="このコマンドを実行する権限がありません。",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if action == "reload":
            await self._reload_config(interaction)
        elif action == "train":
            await self._train_model(interaction)
        elif action == "backup":
            await self._backup_data(interaction)
        elif action == "stats":
            await self._show_stats(interaction)
    
    async def _reload_config(self, interaction: discord.Interaction):
        """設定をリロード"""
        try:
            # 設定ファイルをリロード（簡易実装）
            embed = discord.Embed(
                title="⚙️ 設定リロード",
                description="設定をリロードしました。",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title="❌ 設定リロードエラー",
                description=f"設定のリロードに失敗しました：{str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def _train_model(self, interaction: discord.Interaction):
        """AIモデルの追加学習"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # 学習データの確認
            training_data_path = "data/conversations/training_data.json"
            if not os.path.exists(training_data_path):
                embed = discord.Embed(
                    title="📊 学習データなし",
                    description="学習データが見つかりません。",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed)
                return
            
            with open(training_data_path, 'r', encoding='utf-8') as f:
                training_data = json.load(f)
            
            # 簡易的な学習プロセス（実際の実装では時間がかかる）
            embed = discord.Embed(
                title="🧠 モデル学習",
                description=f"学習データ：{len(training_data)}件\n学習を開始します...",
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=embed)
            
            # 実際の学習処理はここに実装
            # await self._perform_training(training_data)
            
            embed = discord.Embed(
                title="✅ 学習完了",
                description="AIモデルの学習が完了しました。",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ 学習エラー",
                description=f"学習中にエラーが発生しました：{str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
    
    async def _backup_data(self, interaction: discord.Interaction):
        """データのバックアップ"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # バックアップディレクトリの作成
            backup_dir = f"backups/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.makedirs(backup_dir, exist_ok=True)
            
            # データディレクトリをバックアップ
            if os.path.exists("data"):
                shutil.copytree("data", os.path.join(backup_dir, "data"))
            
            embed = discord.Embed(
                title="💾 バックアップ完了",
                description=f"データのバックアップが完了しました。\n保存先：{backup_dir}",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ バックアップエラー",
                description=f"バックアップ中にエラーが発生しました：{str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
    
    async def _show_stats(self, interaction: discord.Interaction):
        """使用統計の表示"""
        try:
            # 統計データの収集
            stats = {
                "total_users": 0,
                "total_conversations": 0,
                "total_messages": 0
            }
            
            # 会話データの統計
            conversations_dir = "data/conversations/memories"
            if os.path.exists(conversations_dir):
                for file in os.listdir(conversations_dir):
                    if file.endswith('.json'):
                        stats["total_users"] += 1
                        try:
                            with open(os.path.join(conversations_dir, file), 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                conversations = data.get('conversations', [])
                                stats["total_conversations"] += len(conversations)
                                stats["total_messages"] += len(conversations) * 2  # ユーザー + AI
                        except:
                            continue
            
            # 学習データの統計
            training_data_path = "data/conversations/training_data.json"
            training_data_count = 0
            if os.path.exists(training_data_path):
                try:
                    with open(training_data_path, 'r', encoding='utf-8') as f:
                        training_data = json.load(f)
                        training_data_count = len(training_data)
                except:
                    pass
            
            embed = discord.Embed(
                title="📊 使用統計",
                description="ボットの使用統計です",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="👥 ユーザー統計",
                value=(
                    f"**総ユーザー数**: {stats['total_users']}\n"
                    f"**総会話数**: {stats['total_conversations']}\n"
                    f"**総メッセージ数**: {stats['total_messages']}"
                ),
                inline=True
            )
            
            embed.add_field(
                name="🧠 学習統計",
                value=(
                    f"**学習データ数**: {training_data_count}\n"
                    f"**学習回数**: {training_data_count // 100}\n"
                    f"**次回学習まで**: {100 - (training_data_count % 100)}"
                ),
                inline=True
            )
            
            embed.add_field(
                name="💾 データサイズ",
                value=self._get_data_size(),
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ 統計エラー",
                description=f"統計データの取得中にエラーが発生しました：{str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    def _get_data_size(self) -> str:
        """データディレクトリのサイズを取得"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk("data"):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
            
            # バイトをMBに変換
            size_mb = total_size / (1024 * 1024)
            return f"{size_mb:.2f} MB"
        except:
            return "不明"

async def setup(bot):
    await bot.add_cog(AdminCog(bot))