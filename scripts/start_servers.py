#!/usr/bin/env python3
"""
Multi-Agent System Server Launcher

複数のエージェントサーバーを同時に起動するスクリプト
"""

import asyncio
import logging
import signal
import sys
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Process
import subprocess
import time

from src.utils.logging_config import setup_logging

# ログ設定
setup_logging()
logger = logging.getLogger(__name__)


class ServerManager:
    """サーバー管理クラス"""
    
    def __init__(self):
        self.processes = []
        self.running = True
    
    def start_agent_server(self, agent_type: str, port: int):
        """エージェントサーバーを起動"""
        try:
            cmd = [
                sys.executable, "-m", "src.a2a.server", agent_type
            ]
            
            logger.info(f"Starting {agent_type} server on port {port}")
            print(f"🚀 {agent_type} サーバーをポート {port} で起動中...")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes.append({
                'name': agent_type,
                'port': port,
                'process': process
            })
            
            return process
            
        except Exception as e:
            logger.error(f"Failed to start {agent_type} server: {e}")
            print(f"❌ {agent_type} サーバーの起動に失敗しました: {e}")
            return None
    
    def start_all_servers(self):
        """全てのサーバーを起動"""
        servers = [
            ("math", 8001),
            ("research", 8002),
            ("orchestrator", 8003)
        ]
        
        print("=== A2A Multi-Agent System Server Launcher ===\n")
        
        for agent_type, port in servers:
            process = self.start_agent_server(agent_type, port)
            if process:
                time.sleep(2)  # サーバー起動の間隔
        
        print(f"\n✅ {len(self.processes)} 個のサーバーを起動しました")
        print("\nサーバー状態:")
        for server in self.processes:
            print(f"  - {server['name']}: http://localhost:{server['port']}")
        
        print("\n📋 利用可能なエンドポイント:")
        print("  - Math Agent: http://localhost:8001/.well-known/agent.json")
        print("  - Research Agent: http://localhost:8002/.well-known/agent.json")
        print("  - Orchestrator: http://localhost:8003/.well-known/agent.json")
        
        print("\n⚡ クライアント例を実行するには:")
        print("  python examples/client_example.py")
        
        print("\n🛑 停止するには Ctrl+C を押してください")
    
    def monitor_servers(self):
        """サーバーの状態を監視"""
        try:
            while self.running:
                time.sleep(5)
                
                for server in self.processes:
                    process = server['process']
                    if process.poll() is not None:
                        # プロセスが終了している
                        logger.warning(f"{server['name']} server has stopped")
                        print(f"⚠️  {server['name']} サーバーが停止しました")
                        
                        # 再起動を試みる
                        if self.running:
                            print(f"🔄 {server['name']} サーバーを再起動中...")
                            new_process = self.start_agent_server(
                                server['name'], 
                                server['port']
                            )
                            if new_process:
                                server['process'] = new_process
                
        except KeyboardInterrupt:
            self.shutdown()
    
    def shutdown(self):
        """全てのサーバーを停止"""
        print("\n🛑 サーバーを停止中...")
        self.running = False
        
        for server in self.processes:
            try:
                process = server['process']
                if process.poll() is None:
                    logger.info(f"Stopping {server['name']} server")
                    process.terminate()
                    
                    # 5秒待って強制終了
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        logger.warning(f"Force killing {server['name']} server")
                        process.kill()
                        process.wait()
                
                print(f"✅ {server['name']} サーバーを停止しました")
                
            except Exception as e:
                logger.error(f"Error stopping {server['name']} server: {e}")
        
        print("🏁 全てのサーバーを停止しました")
    
    def check_dependencies(self):
        """依存関係をチェック"""
        print("🔍 依存関係をチェック中...")
        
        try:
            # 環境変数のチェック
            import os
            required_env_vars = [
                "AWS_REGION",
                "AWS_ACCESS_KEY_ID", 
                "AWS_SECRET_ACCESS_KEY"
            ]
            
            missing_vars = []
            for var in required_env_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                print(f"⚠️  以下の環境変数が設定されていません: {', '.join(missing_vars)}")
                print("   .env ファイルを確認してください")
                return False
            
            # パッケージのインポートテスト
            packages_to_test = [
                "boto3",
                "langchain", 
                "langgraph",
                "fastapi",
                "httpx",
                "mcp"
            ]
            
            for package in packages_to_test:
                try:
                    __import__(package)
                except ImportError as e:
                    print(f"❌ パッケージ {package} がインストールされていません")
                    print(f"   pip install {package} を実行してください")
                    return False
            
            print("✅ 依存関係のチェックが完了しました")
            return True
            
        except Exception as e:
            print(f"❌ 依存関係のチェックでエラーが発生しました: {e}")
            return False


def signal_handler(signum, frame):
    """シグナルハンドラー"""
    print("\n🛑 停止シグナルを受信しました...")
    sys.exit(0)


async def run_health_checks():
    """ヘルスチェックを実行"""
    import httpx
    
    print("\n🏥 ヘルスチェックを実行中...")
    
    endpoints = [
        ("Math Agent", "http://localhost:8001/health"),
        ("Research Agent", "http://localhost:8002/health"),
        ("Orchestrator", "http://localhost:8003/health")
    ]
    
    async with httpx.AsyncClient() as client:
        for name, url in endpoints:
            try:
                response = await client.get(url, timeout=10.0)
                if response.status_code == 200:
                    print(f"✅ {name}: 正常")
                else:
                    print(f"⚠️  {name}: 応答コード {response.status_code}")
            except Exception as e:
                print(f"❌ {name}: 接続エラー - {e}")


def main():
    """メイン関数"""
    # シグナルハンドラーの設定
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    manager = ServerManager()
    
    try:
        # 依存関係チェック
        if not manager.check_dependencies():
            print("❌ 依存関係のチェックに失敗しました。修正後に再実行してください。")
            return
        
        # サーバー起動
        manager.start_all_servers()
        
        # 起動待機
        print("\n⏳ サーバーの起動を待機中...")
        time.sleep(10)
        
        # ヘルスチェック
        asyncio.run(run_health_checks())
        
        # 監視開始
        manager.monitor_servers()
        
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ 予期しないエラーが発生しました: {e}")
    finally:
        manager.shutdown()


if __name__ == "__main__":
    main()