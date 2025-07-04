import discord
from discord import app_commands
from discord.ext import commands


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="ヘルプメッセージを表示します")
    async def help(self, interaction: discord.Interaction):
        # 即座に応答を返す（重要！）
        await interaction.response.defer()

        embed = discord.Embed(
            title="🤖 AI Discord Bot ヘルプ",
            description="このボットは、ローカルAIを使用した日本語対応のDiscord botです。",
            color=discord.Color.green()
        )

        # 基本コマンド
        embed.add_field(
            name="📝 基本コマンド",
            value=(
                "`/chat [メッセージ]` - AIと対話\n"
                "`/help` - このヘルプを表示\n"
                "`/status` - ボットとAIの状態確認\n"
                "`/memory [action]` - 記憶管理"
            ),
            inline=False
        )

        # 記憶管理コマンド
        embed.add_field(
            name="🧠 記憶管理",
            value=(
                "`/memory show` - 会話履歴を表示\n"
                "`/memory clear` - 会話履歴をクリア\n"
                "`/memory export` - 会話履歴をエクスポート"
            ),
            inline=False
        )

        # 管理者コマンド
        # 自動応答コマンド
        embed.add_field(
            name="🤖 自動応答",
            value=(
                "`/auto enable` - 自動応答を有効化\n"
                "`/auto disable` - 自動応答を無効化\n"
                "`/auto status` - 自動応答状態確認\n"
                "`/auto list` - 自動応答チャンネル一覧"
            ),
            inline=False
        )
        
        # 管理者コマンド
        embed.add_field(
            name="⚙️ 管理者コマンド",
            value=(
                "`/admin reload` - 設定リロード\n"
                "`/admin train` - AIモデルの追加学習\n"
                "`/admin backup` - データバックアップ\n"
                "`/admin stats` - 使用統計表示"
            ),
            inline=False
        )

        embed.set_footer(
            text="AI Discord Bot v1.0 - ローカルAI駆動 | 自動応答: サーバー別会話履歴管理"
        )

        if self.bot.user and self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)

        # followupで実際のメッセージを送信
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(HelpCog(bot))