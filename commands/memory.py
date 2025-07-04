import discord
from discord import app_commands
from discord.ext import commands
from models.memory_manager import MemoryManager
from typing import Literal

class MemoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.memory = MemoryManager()
        
    @app_commands.command(name="memory", description="記憶管理を行います")
    @app_commands.describe(action="実行するアクション")
    async def memory(self, interaction: discord.Interaction, action: Literal["show", "clear", "export"]):
        user_id = str(interaction.user.id)
        
        if action == "show":
            await self._show_memory(interaction, user_id)
        elif action == "clear":
            await self._clear_memory(interaction, user_id)
        elif action == "export":
            await self._export_memory(interaction, user_id)
    
    async def _show_memory(self, interaction: discord.Interaction, user_id: str):
        """会話履歴を表示（サーバー別）"""
        guild_id = str(interaction.guild.id) if interaction.guild else None
        conversations = self.memory.get_context(user_id, guild_id)
        
        if not conversations:
            embed = discord.Embed(
                title="🧠 記憶",
                description="まだ会話履歴がありません。",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # 最新の5件を表示
        recent_conversations = conversations[-5:]
        
        server_name = interaction.guild.name if interaction.guild else "DM"
        embed = discord.Embed(
            title="🧠 記憶",
            description=f"**サーバー**: {server_name}\n"
                       f"最新の{len(recent_conversations)}件の会話履歴（全{len(conversations)}件）",
            color=discord.Color.blue()
        )
        
        for i, conv in enumerate(recent_conversations, 1):
            timestamp = conv.get('timestamp', '不明')
            msg_type = conv.get('type', 'command')
            type_emoji = "💬" if msg_type == "command" else "🤖"
            
            user_msg = conv.get('user', '')[:80] + ('...' if len(conv.get('user', '')) > 80 else '')
            ai_msg = conv.get('assistant', '')[:80] + ('...' if len(conv.get('assistant', '')) > 80 else '')
            
            embed.add_field(
                name=f"{type_emoji} 会話 {i} ({msg_type})",
                value=f"**時刻**: {timestamp}\n**あなた**: {user_msg}\n**AI**: {ai_msg}",
                inline=False
            )
        
        embed.set_footer(text=f"ユーザーID: {user_id} | サーバー別履歴")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def _clear_memory(self, interaction: discord.Interaction, user_id: str):
        """会話履歴をクリア（サーバー別）"""
        guild_id = str(interaction.guild.id) if interaction.guild else None
        conversations = self.memory.get_context(user_id, guild_id)
        
        if not conversations:
            embed = discord.Embed(
                title="🧠 記憶クリア",
                description="クリアする会話履歴がありません。",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        server_name = interaction.guild.name if interaction.guild else "DM"
        # 確認メッセージを表示
        embed = discord.Embed(
            title="🧠 記憶クリア",
            description=f"**サーバー**: {server_name}\n"
                       f"本当に{len(conversations)}件の会話履歴をクリアしますか？",
            color=discord.Color.red()
        )
        
        class ConfirmView(discord.ui.View):
            def __init__(self, memory_manager, user_id, guild_id):
                super().__init__(timeout=30)
                self.memory_manager = memory_manager
                self.user_id = user_id
                self.guild_id = guild_id
                
            @discord.ui.button(label="はい", style=discord.ButtonStyle.danger)
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.memory_manager.clear_memory(self.user_id, self.guild_id)
                
                embed = discord.Embed(
                    title="🧠 記憶クリア完了",
                    description=f"**{server_name}** の会話履歴をクリアしました。",
                    color=discord.Color.green()
                )
                await interaction.response.edit_message(embed=embed, view=None)
                
            @discord.ui.button(label="いいえ", style=discord.ButtonStyle.secondary)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                embed = discord.Embed(
                    title="🧠 記憶クリア",
                    description="キャンセルしました。",
                    color=discord.Color.blue()
                )
                await interaction.response.edit_message(embed=embed, view=None)
        
        view = ConfirmView(self.memory, user_id, guild_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def _export_memory(self, interaction: discord.Interaction, user_id: str):
        """会話履歴をエクスポート（サーバー別）"""
        guild_id = str(interaction.guild.id) if interaction.guild else None
        export_text = self.memory.export_memory(user_id, guild_id)
        
        if export_text == "会話履歴がありません。":
            embed = discord.Embed(
                title="🧠 記憶エクスポート",
                description="エクスポートする会話履歴がありません。",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # ファイルとして送信
        import io
        from datetime import datetime
        
        buffer = io.BytesIO()
        buffer.write(export_text.encode('utf-8'))
        buffer.seek(0)
        
        server_suffix = f"_guild{guild_id}" if guild_id else "_dm"
        filename = f"conversation_history_{user_id}{server_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file = discord.File(buffer, filename=filename)
        
        server_name = interaction.guild.name if interaction.guild else "DM"
        embed = discord.Embed(
            title="🧠 記憶エクスポート",
            description=f"**{server_name}** の会話履歴をエクスポートしました。",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, file=file, ephemeral=True)

async def setup(bot):
    await bot.add_cog(MemoryCog(bot))