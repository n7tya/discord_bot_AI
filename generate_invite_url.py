#!/usr/bin/env python3
"""
Discord Bot 招待URL生成スクリプト
「不明な連携」エラーを解決するための正しい招待URLを生成します。
"""

import os
from config import Config

def generate_invite_url():
    """正しいスコープと権限を持つ招待URLを生成"""
    
    print("🤖 Discord Bot 招待URL生成ツール")
    print("=" * 50)
    
    # Client IDの取得
    client_id = input("Bot の Client ID を入力してください: ").strip()
    
    if not client_id:
        print("❌ Client ID が入力されていません。")
        return
    
    # 必要なスコープ
    scopes = ["bot", "applications.commands"]
    scope_string = "%20".join(scopes)
    
    # 推奨権限の計算
    permissions = {
        "Send Messages": 2048,
        "Use Slash Commands": 2147483648,  # これが重要！
        "Embed Links": 16384,
        "Attach Files": 32768,
        "Read Message History": 65536,
        "Add Reactions": 64,
        "View Channels": 1024
    }
    
    # 権限値の合計
    total_permissions = sum(permissions.values())
    
    # 招待URL生成
    invite_url = f"https://discord.com/api/oauth2/authorize?client_id={client_id}&permissions={total_permissions}&scope={scope_string}"
    
    print("\n✅ 生成された招待URL:")
    print(f"{invite_url}")
    
    print("\n📋 含まれるスコープ:")
    for scope in scopes:
        print(f"  ✅ {scope}")
    
    print("\n🔐 含まれる権限:")
    for perm_name, perm_value in permissions.items():
        print(f"  ✅ {perm_name}")
    
    print("\n🚀 使用方法:")
    print("1. 上記のURLをコピーしてブラウザで開く")
    print("2. ボットを招待したいサーバーを選択")
    print("3. 権限を確認して「認証」をクリック")
    
    print("\n⚠️  既存ボットがいる場合:")
    print("1. 先に古いボットをサーバーから削除")
    print("2. この新しいURLで再招待")
    
    # URLをファイルに保存
    with open("invite_url.txt", "w") as f:
        f.write(invite_url)
    
    print(f"\n💾 招待URLは 'invite_url.txt' にも保存されました。")

if __name__ == "__main__":
    try:
        generate_invite_url()
    except KeyboardInterrupt:
        print("\n\n👋 中断されました。")
    except Exception as e:
        print(f"\n❌ エラー: {e}")