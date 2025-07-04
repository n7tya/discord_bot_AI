import discord
from discord import app_commands
from discord.ext import commands
from models.local_ai import LocalAI
from models.memory_manager import MemoryManager
import asyncio

class AIChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ai = LocalAI()
        self.memory = MemoryManager()
        
    @app_commands.command(name="chat", description="AIと対話します")
    @app_commands.describe(message="AIに送るメッセージ")
    async def chat(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer(thinking=True)
        
        try:
            # ユーザーの会話履歴を取得（サーバー別）
            user_id = str(interaction.user.id)
            guild_id = str(interaction.guild.id) if interaction.guild else None
            context = self.memory.get_context(user_id, guild_id)
            
            # AI応答生成（時間測定）
            import time
            start_time = time.time()
            response = await self.ai.generate_response(message, context)
            generation_time = time.time() - start_time
            
            # 会話履歴を更新（サーバー別、コマンドとして）
            self.memory.add_conversation(
                user_id=user_id,
                user_message=message,
                ai_response=response,
                guild_id=guild_id,
                channel_id=str(interaction.channel.id),
                message_type="command"
            )
            
            # 応答の品質チェック
            if not response or len(response.strip()) < 5:
                response = "申し訳ございません。うまく応答を生成できませんでした。もう一度お試しください。"
            
            # 応答送信（より魅力的なEmbed）
            embed = discord.Embed(
                title="🤖 AI アシスタント",
                description=response,
                color=discord.Color.from_rgb(100, 149, 237)  # コーンフラワーブルー
            )
            
            # 応答時間とモデル情報を追加
            model_info = "rinna/japanese-gpt2-medium" if self.ai.use_real_model else "ダミーモード"
            embed.set_footer(
                text=f"応答時間: {generation_time:.2f}秒 | モデル: {model_info} | {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.followup.send(embed=embed)
            
            # 非同期で学習データを更新
            asyncio.create_task(self.ai.update_learning_data(user_id, message, response))
            
        except Exception as e:
            print(f"Chat command error: {e}")
            error_embed = discord.Embed(
                title="❌ エラー",
                description="申し訳ございません。処理中にエラーが発生しました。",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AIChatCog(bot))