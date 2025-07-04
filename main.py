"""
AI Discord Bot - メインファイル

ローカルAIを使用した日本語対応のDiscord botのメインエントリーポイント
"""

import os
import traceback
import asyncio
import logging

import discord
from discord.ext import commands

from config import Config


class DiscordBot(commands.Bot):
    """AI機能付きDiscordボット"""
    
    def __init__(self):
        """ボットの初期化"""
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='/', intents=intents)

    async def setup_hook(self):
        """ボット起動時のセットアップ処理"""
        try:
            print("コマンドを登録中...")
            
            # 各Cogを個別にインポートして登録
            from commands import ai_chat, help, status, memory, admin, auto_response

            cogs = [
                (ai_chat.AIChatCog, "AI chat"),
                (help.HelpCog, "Help"),
                (status.StatusCog, "Status"),
                (memory.MemoryCog, "Memory"),
                (admin.AdminCog, "Admin"),
                (auto_response.AutoResponseCog, "Auto Response")
            ]
            
            for cog_class, name in cogs:
                await self.add_cog(cog_class(self))
                print(f"✅ {name} コマンドを登録しました")

            # 登録されたコマンドの確認
            print("\n登録されたスラッシュコマンド:")
            for command in self.tree.get_commands():
                print(f"  - /{command.name}: {command.description}")

            # スラッシュコマンドの同期
            await self._sync_commands()

        except Exception as e:
            print(f"❌ セットアップエラー: {e}")
            traceback.print_exc()
            raise

    async def _sync_commands(self):
        """スラッシュコマンドの同期処理"""
        print("\nスラッシュコマンドを同期中...")

        if Config.GUILD_ID and Config.GUILD_ID.strip():
            try:
                guild_id = int(Config.GUILD_ID.strip())
                guild = discord.Object(id=guild_id)

                # ギルドコマンドをクリアしてから同期
                self.tree.clear_commands(guild=guild)
                await self.tree.sync(guild=guild)

                print(f"✅ サーバー {guild_id} にスラッシュコマンドを即時同期しました")
                print("   コマンドは即座に利用可能です！")
                
            except ValueError:
                print(f"⚠️ GUILD_ID '{Config.GUILD_ID}' が無効です。グローバル同期を行います。")
                await self._global_sync()
        else:
            await self._global_sync()

    async def _global_sync(self):
        """グローバルコマンド同期"""
        await self.tree.sync()
        print("✅ グローバルにスラッシュコマンドを同期しました（反映まで最大1時間）")
        print("💡 ヒント: .envファイルにGUILD_IDを設定すると、即座にコマンドが使えます")

    async def on_ready(self):
        """ボット準備完了時の処理"""
        print(f"\n🤖 {self.user} として起動しました！")
        print(f"📊 接続サーバー数: {len(self.guilds)}")

        # 接続しているサーバーの一覧を表示
        if self.guilds:
            print("\n接続中のサーバー:")
            for guild in self.guilds:
                print(f"  - {guild.name} (ID: {guild.id})")

        await self.change_presence(activity=discord.Game(name="/help でヘルプ"))
        await self._display_available_commands()

    async def on_message(self, message):
        """メッセージイベントハンドラー（自動応答用）"""
        # ボット自身のメッセージは無視
        if message.author.bot:
            return
        
        # DMの場合は処理しない
        if isinstance(message.channel, discord.DMChannel):
            return
        
        # 自動応答が有効なチャンネルかチェック
        from utils.auto_response_manager import auto_response_manager
        if not auto_response_manager.is_active_channel(message.channel.id):
            return
        
        # 空のメッセージや短すぎるメッセージは無視
        if not message.content or len(message.content.strip()) < 2:
            return
        
        # 長すぎるメッセージは無視
        if len(message.content) > 500:
            return
        
        try:
            # AIによる自動応答
            await self._process_auto_response(message)
        except Exception as e:
            print(f"自動応答エラー: {e}")

    async def _process_auto_response(self, message):
        """自動応答の処理"""
        from models.local_ai import LocalAI
        from models.memory_manager import MemoryManager
        import time
        
        # AIとメモリマネージャーの初期化
        ai = LocalAI()
        memory = MemoryManager()
        
        # 会話履歴を取得（サーバー別）
        user_id = str(message.author.id)
        guild_id = str(message.guild.id) if message.guild else None
        context = memory.get_context(user_id, guild_id)
        
        # typing表示
        async with message.channel.typing():
            # AI応答生成
            start_time = time.time()
            response = await ai.generate_response(message.content, context)
            generation_time = time.time() - start_time
        
        # 応答が有効かチェック
        if not response or len(response.strip()) < 3:
            return  # 無効な応答の場合は送信しない
        
        # 会話履歴を保存（サーバー別、自動応答として）
        memory.add_conversation(
            user_id=user_id,
            user_message=message.content,
            ai_response=response,
            guild_id=guild_id,
            channel_id=str(message.channel.id),
            message_type="auto_response"
        )
        
        # 学習データの更新
        await ai.update_learning_data(user_id, message.content, response)
        
        # 応答を送信
        embed = discord.Embed(
            description=response,
            color=discord.Color.from_rgb(135, 206, 235)  # スカイブルー
        )
        embed.set_footer(
            text=f"応答時間: {generation_time:.2f}秒 | 自動応答",
            icon_url=message.author.display_avatar.url
        )
        
        await message.reply(embed=embed, mention_author=False)

    async def _display_available_commands(self):
        """利用可能なコマンドの表示"""
        print("\n📝 利用可能なコマンドを確認中...")
        
        # グローバルコマンド
        commands = await self.tree.fetch_commands()
        if commands:
            print("グローバルコマンド:")
            for cmd in commands:
                print(f"  - /{cmd.name}")

        # ギルドコマンド
        if Config.GUILD_ID and Config.GUILD_ID.strip():
            try:
                guild_id = int(Config.GUILD_ID.strip())
                guild_commands = await self.tree.fetch_commands(
                    guild=discord.Object(id=guild_id)
                )
                if guild_commands:
                    print(f"\nサーバー {guild_id} のコマンド:")
                    for cmd in guild_commands:
                        print(f"  - /{cmd.name}")
            except Exception:
                pass


def check_environment():
    """環境変数のチェック"""
    if not Config.DISCORD_TOKEN:
        print("❌ エラー: DISCORD_TOKENが設定されていません。")
        print("📝 .envファイルを作成してDISCORD_TOKENを設定してください。")
        print("\n例:")
        print("DISCORD_TOKEN=your_bot_token_here")
        print("GUILD_ID=your_server_id_here  # オプション：即座にコマンドを使いたい場合")
        return False
    return True


def setup_environment():
    """環境設定"""
    # OpenMP競合回避の環境変数設定
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'


def main():
    """メイン処理"""
    if not check_environment():
        return

    setup_environment()

    try:
        bot = DiscordBot()
        print("🚀 ボットを起動中...")
        print("=" * 50)
        bot.run(Config.DISCORD_TOKEN)
        
    except discord.LoginFailure:
        print("❌ ログインエラー: Discord Tokenが無効です。")
        print("   .envファイルのDISCORD_TOKENを確認してください。")
        
    except Exception as e:
        print(f"❌ ボット起動エラー: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()