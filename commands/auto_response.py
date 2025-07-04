"""
自動応答コマンド - チャンネル指定での自動AI応答設定

特定のチャンネルでの自動応答機能を設定・管理するコマンド
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Literal

from utils.auto_response_manager import auto_response_manager
from config import Config


class AutoResponseCog(commands.Cog):
    """自動応答管理コマンド"""
    
    def __init__(self, bot):
        self.bot = bot

    def _is_admin(self, user_id: int) -> bool:
        """管理者権限チェック"""
        return str(user_id) in Config.ADMIN_IDS

    @app_commands.command(name="auto", description="チャンネルでの自動応答を設定します")
    @app_commands.describe(
        action="実行するアクション",
        channel="対象チャンネル（省略時は現在のチャンネル）"
    )
    async def auto_response(
        self, 
        interaction: discord.Interaction, 
        action: Literal["enable", "disable", "status", "list"],
        channel: discord.TextChannel = None
    ):
        """自動応答設定コマンド"""
        # 管理者権限チェック
        if not self._is_admin(interaction.user.id):
            embed = discord.Embed(
                title="❌ 権限エラー",
                description="このコマンドは管理者のみ使用できます。",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # チャンネルが指定されていない場合は現在のチャンネル
        target_channel = channel or interaction.channel
        
        if action == "enable":
            await self._enable_auto_response(interaction, target_channel)
        elif action == "disable":
            await self._disable_auto_response(interaction, target_channel)
        elif action == "status":
            await self._show_status(interaction, target_channel)
        elif action == "list":
            await self._show_list(interaction)

    async def _enable_auto_response(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """自動応答を有効化"""
        success = auto_response_manager.add_channel(channel.id)
        
        if success:
            embed = discord.Embed(
                title="✅ 自動応答を有効化",
                description=f"チャンネル {channel.mention} で自動応答が有効になりました。\n"
                           f"このチャンネルでのメッセージにAIが自動的に応答します。",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="ℹ️ 既に有効",
                description=f"チャンネル {channel.mention} は既に自動応答が有効です。",
                color=discord.Color.blue()
            )
        
        await interaction.response.send_message(embed=embed)

    async def _disable_auto_response(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """自動応答を無効化"""
        success = auto_response_manager.remove_channel(channel.id)
        
        if success:
            embed = discord.Embed(
                title="🔕 自動応答を無効化",
                description=f"チャンネル {channel.mention} の自動応答を無効にしました。",
                color=discord.Color.orange()
            )
        else:
            embed = discord.Embed(
                title="ℹ️ 既に無効",
                description=f"チャンネル {channel.mention} は既に自動応答が無効です。",
                color=discord.Color.blue()
            )
        
        await interaction.response.send_message(embed=embed)

    async def _show_status(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """特定チャンネルの状態表示"""
        is_active = auto_response_manager.is_active_channel(channel.id)
        
        embed = discord.Embed(
            title="📊 自動応答ステータス",
            description=f"チャンネル: {channel.mention}",
            color=discord.Color.green() if is_active else discord.Color.red()
        )
        
        embed.add_field(
            name="状態",
            value="🟢 有効" if is_active else "🔴 無効",
            inline=True
        )
        
        embed.add_field(
            name="説明",
            value="このチャンネルでのメッセージにAIが自動応答します" if is_active 
                  else "このチャンネルでは `/chat` コマンドが必要です",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

    async def _show_list(self, interaction: discord.Interaction):
        """全自動応答チャンネル一覧表示"""
        active_channels = auto_response_manager.get_active_channels()
        
        embed = discord.Embed(
            title="📋 自動応答チャンネル一覧",
            color=discord.Color.blue()
        )
        
        if not active_channels:
            embed.description = "現在、自動応答が有効なチャンネルはありません。"
        else:
            channel_list = []
            for channel_id in active_channels:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    channel_list.append(f"• {channel.mention} (`{channel.name}`)")
                else:
                    channel_list.append(f"• チャンネルID: {channel_id} (削除済み?)")
            
            embed.description = f"**有効なチャンネル数**: {len(active_channels)}\n\n" + \
                               "\n".join(channel_list)
        
        embed.set_footer(text="管理者のみがこの設定を変更できます")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(AutoResponseCog(bot))