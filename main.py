import discord
from discord.ext import commands
import asyncio
import logging
from config import Config
from commands import ai_chat, help, status, memory, admin

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='/', intents=intents)
        
    async def setup_hook(self):
        try:
            # コマンドの登録
            print("コマンドを登録中...")
            await self.add_cog(ai_chat.AIChatCog(self))
            print("AI chat コマンドを登録しました")
            await self.add_cog(help.HelpCog(self))
            print("Help コマンドを登録しました")
            await self.add_cog(status.StatusCog(self))
            print("Status コマンドを登録しました")
            await self.add_cog(memory.MemoryCog(self))
            print("Memory コマンドを登録しました")
            await self.add_cog(admin.AdminCog(self))
            print("Admin コマンドを登録しました")
            
            # スラッシュコマンドの同期（GUILD_ID指定で即時適用）
            print("スラッシュコマンドを同期中...")
            
            if Config.GUILD_ID:
                # 特定のサーバーに即時同期
                guild = discord.Object(id=int(Config.GUILD_ID))
                await self.tree.sync(guild=guild)
                print(f"✅ サーバー {Config.GUILD_ID} にスラッシュコマンドを即時同期しました")
            else:
                # グローバル同期（最大1時間かかる場合があります）
                await self.tree.sync()
                print("✅ グローバルにスラッシュコマンドを同期しました（反映まで最大1時間）")
            
        except Exception as e:
            print(f"セットアップエラー: {e}")
            raise
        
    async def on_ready(self):
        print(f'{self.user} として起動しました！')
        print(f"接続サーバー数: {len(self.guilds)}")
        await self.change_presence(activity=discord.Game(name="/help でヘルプ"))

def main():
    if not Config.DISCORD_TOKEN:
        print("エラー: DISCORD_TOKENが設定されていません。")
        print(".envファイルを作成してDISCORD_TOKENを設定してください。")
        return
    
    try:
        bot = DiscordBot()
        print("ボットを起動中...")
        bot.run(Config.DISCORD_TOKEN)
    except Exception as e:
        print(f"ボット起動エラー: {e}")

if __name__ == "__main__":
    main()