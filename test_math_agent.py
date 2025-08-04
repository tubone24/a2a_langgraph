#!/usr/bin/env python3
"""
Math Agent のテスト用スクリプト
"""

import asyncio
import sys
import os
from uuid import uuid4

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents.math_agent import math_agent
from src.a2a.protocol import Message, MessagePart


async def test_math_agent():
    """Math Agentをテスト"""
    
    test_cases = [
        "2*3",
        "10+5", 
        "100/4",
        "2*3+5",
        "x^2の微分",
        "[1,2,3,4,5]の平均値"
    ]
    
    print("=== Math Agent テスト ===\n")
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"テスト {i}: {test_input}")
        
        # Messageオブジェクトを作成
        message = Message(
            role="user",
            messageId=str(uuid4()),
            parts=[MessagePart(kind="text", text=test_input)],
            contextId=None
        )
        
        try:
            # Math Agentを呼び出し
            result = await math_agent.process_new_message(message)
            print(f"結果: {result}")
        except Exception as e:
            print(f"エラー: {e}")
        
        print("-" * 40)


if __name__ == "__main__":
    asyncio.run(test_math_agent())