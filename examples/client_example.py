#!/usr/bin/env python3
"""
A2A Multi-Agent System Client Example

このスクリプトは、LangGraphとA2Aを使用したマルチエージェントシステムの
使用例を示します。
"""

import asyncio
import httpx
import logging
from uuid import uuid4
from typing import List, Dict, Any

from src.a2a.protocol import (
    A2ACardResolver, A2AClient,
    Message, MessagePart, MessageSendParams, SendMessageRequest
)
from src.utils.logging_config import setup_logging

# ログ設定
setup_logging()
logger = logging.getLogger(__name__)


class MultiAgentClient:
    """マルチエージェントシステムクライアント"""
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.agents: Dict[str, A2AClient] = {}
    
    async def initialize_agents(self):
        """エージェントとの接続を初期化"""
        agent_endpoints = {
            "math_agent": "http://localhost:8001",
            "research_agent": "http://localhost:8002", 
            "orchestrator": "http://localhost:8003"
        }
        
        for agent_name, endpoint in agent_endpoints.items():
            try:
                resolver = A2ACardResolver(self.http_client, endpoint)
                agent_card = await resolver.get_agent_card()
                client = A2AClient(self.http_client, agent_card, endpoint)
                self.agents[agent_name] = client
                
                logger.info(f"Connected to {agent_name}: {agent_card.name}")
                print(f"✓ {agent_card.name} に接続しました")
                
            except Exception as e:
                logger.warning(f"Failed to connect to {agent_name}: {e}")
                print(f"✗ {agent_name} への接続に失敗しました: {e}")
    
    async def send_message_to_agent(
        self, 
        agent_name: str, 
        message_text: str,
        context_id: str = None
    ) -> str:
        """特定のエージェントにメッセージを送信"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} is not connected")
        
        client = self.agents[agent_name]
        
        # メッセージを構築
        message = Message(
            role="user",
            parts=[MessagePart(kind="text", text=message_text)],
            messageId=uuid4().hex,
            contextId=context_id
        )
        
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(message=message)
        )
        
        # メッセージを送信
        response = await client.send_message(request)
        
        if response.result:
            return response.result.content or "応答がありませんでした"
        elif response.error:
            return f"エラー: {response.error.get('message', 'Unknown error')}"
        else:
            return "不明なレスポンス"
    
    async def run_examples(self):
        """使用例を実行"""
        print("\n=== A2A Multi-Agent System Examples ===\n")
        
        # 1. Math Agentへの直接リクエスト
        print("1. Math Agent - 数学計算の例")
        math_queries = [
            "x^2 + 3x + 2 の微分を計算してください",
            "2 + 2 * 3 を計算してください",
            "[1, 2, 3, 4, 5] の平均値を求めてください"
        ]
        
        for query in math_queries:
            print(f"質問: {query}")
            try:
                response = await self.send_message_to_agent("math_agent", query)
                print(f"回答: {response}\n")
            except Exception as e:
                print(f"エラー: {e}\n")
        
        # 2. Research Agentへの直接リクエスト
        print("2. Research Agent - 研究・調査の例")
        research_queries = [
            "人工知能の最新動向について調べてください",
            "この文章を要約してください: '人工知能は現代社会において重要な役割を果たしています。'",
            "量子コンピュータに関する事実確認をお願いします"
        ]
        
        for query in research_queries:
            print(f"質問: {query}")
            try:
                response = await self.send_message_to_agent("research_agent", query)
                print(f"回答: {response}\n")
            except Exception as e:
                print(f"エラー: {e}\n")
        
        # 3. Orchestratorを通じた複合タスク
        print("3. Orchestrator - 複合タスクの例")
        complex_queries = [
            "sin(x)の微分を計算して、その結果について詳しく調べてください",
            "統計学の基本概念を説明し、平均値の計算例も示してください",
            "AIと数学の関係について研究し、具体的な計算例も含めて説明してください"
        ]
        
        for query in complex_queries:
            print(f"質問: {query}")
            try:
                response = await self.send_message_to_agent("orchestrator", query)
                print(f"回答: {response}\n")
            except Exception as e:
                print(f"エラー: {e}\n")
    
    async def interactive_mode(self):
        """インタラクティブモード"""
        print("\n=== インタラクティブモード ===")
        print("利用可能なエージェント: math_agent, research_agent, orchestrator")
        print("終了するには 'quit' と入力してください\n")
        
        context_id = str(uuid4())
        
        while True:
            try:
                user_input = input("質問を入力してください: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not user_input:
                    continue
                
                # エージェント選択
                print("どのエージェントを使用しますか？")
                print("1. math_agent (数学計算)")
                print("2. research_agent (研究・調査)")
                print("3. orchestrator (自動選択・複合タスク)")
                
                agent_choice = input("選択 (1-3, デフォルト: 3): ").strip()
                
                agent_map = {
                    "1": "math_agent",
                    "2": "research_agent", 
                    "3": "orchestrator",
                    "": "orchestrator"
                }
                
                selected_agent = agent_map.get(agent_choice, "orchestrator")
                
                print(f"質問を {selected_agent} に送信中...")
                response = await self.send_message_to_agent(
                    selected_agent, 
                    user_input,
                    context_id
                )
                
                print(f"\n回答: {response}\n")
                print("-" * 50)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"エラーが発生しました: {e}")
    
    async def close(self):
        """リソースをクリーンアップ"""
        await self.http_client.aclose()


async def main():
    """メイン関数"""
    client = MultiAgentClient()
    
    try:
        # エージェントに接続
        await client.initialize_agents()
        
        if not client.agents:
            print("エージェントに接続できませんでした。サーバーが起動しているか確認してください。")
            return
        
        # 使用例を実行
        await client.run_examples()
        
        # インタラクティブモード
        await client.interactive_mode()
        
    except KeyboardInterrupt:
        print("\n終了しています...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"予期しないエラーが発生しました: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())