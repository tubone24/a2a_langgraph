#!/usr/bin/env python3
"""
A2A Multi-Agent System Tests

マルチエージェントシステムのテストコード
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from uuid import uuid4

from src.agents.math_agent import MathAgent
from src.agents.research_agent import ResearchAgent
from src.agents.orchestrator import OrchestratorAgent
from src.a2a.protocol import Message, MessagePart, SendMessageRequest, MessageSendParams


class TestMathAgent:
    """Math Agentのテスト"""
    
    @pytest.fixture
    def math_agent(self):
        """Math Agentのフィクスチャ"""
        return MathAgent()
    
    @pytest.mark.asyncio
    async def test_process_simple_calculation(self, math_agent):
        """簡単な計算のテスト"""
        message = Message(
            role="user",
            parts=[MessagePart(kind="text", text="2 + 2 を計算してください")]
        )
        
        result = await math_agent.process_new_message(message)
        
        assert isinstance(result, str)
        assert len(result) > 0
        print(f"Math Agent result: {result}")
    
    @pytest.mark.asyncio
    async def test_process_differentiation(self, math_agent):
        """微分計算のテスト"""
        message = Message(
            role="user",
            parts=[MessagePart(kind="text", text="x^2の微分を計算してください")]
        )
        
        result = await math_agent.process_new_message(message)
        
        assert isinstance(result, str)
        assert len(result) > 0
        print(f"Differentiation result: {result}")
    
    def test_agent_card_creation(self, math_agent):
        """エージェントカードの作成テスト"""
        agent_card = math_agent.get_agent_card()
        
        assert agent_card.name == "Math Agent"
        assert len(agent_card.skills) > 0
        assert any(skill.name == "arithmetic" for skill in agent_card.skills)


class TestResearchAgent:
    """Research Agentのテスト"""
    
    @pytest.fixture
    def research_agent(self):
        """Research Agentのフィクスチャ"""
        return ResearchAgent()
    
    @pytest.mark.asyncio
    async def test_process_research_request(self, research_agent):
        """研究リクエストのテスト"""
        message = Message(
            role="user",
            parts=[MessagePart(kind="text", text="人工知能について調べてください")]
        )
        
        result = await research_agent.process_new_message(message)
        
        assert isinstance(result, str)
        assert len(result) > 0
        print(f"Research result: {result}")
    
    @pytest.mark.asyncio
    async def test_process_text_analysis(self, research_agent):
        """テキスト分析のテスト"""
        message = Message(
            role="user",
            parts=[MessagePart(kind="text", text="この文章を分析してください: AIは重要です")]
        )
        
        result = await research_agent.process_new_message(message)
        
        assert isinstance(result, str)
        assert len(result) > 0
        print(f"Text analysis result: {result}")
    
    def test_agent_card_creation(self, research_agent):
        """エージェントカードの作成テスト"""
        agent_card = research_agent.get_agent_card()
        
        assert agent_card.name == "Research Agent"
        assert len(agent_card.skills) > 0
        assert any(skill.name == "web_research" for skill in agent_card.skills)


class TestOrchestratorAgent:
    """Orchestrator Agentのテスト"""
    
    @pytest.fixture
    def orchestrator_agent(self):
        """Orchestrator Agentのフィクスチャ"""
        return OrchestratorAgent()
    
    @pytest.mark.asyncio
    async def test_process_complex_request(self, orchestrator_agent):
        """複合リクエストのテスト"""
        message = Message(
            role="user",
            parts=[MessagePart(kind="text", text="微分を計算してその結果について研究してください")]
        )
        
        result = await orchestrator_agent.process_new_message(message)
        
        assert isinstance(result, str)
        assert len(result) > 0
        print(f"Orchestrator result: {result}")
    
    @pytest.mark.asyncio
    async def test_agent_selection(self, orchestrator_agent):
        """エージェント選択のテスト"""
        # Math Agentが必要なリクエスト
        math_request = "2 + 2 を計算してください"
        required_agents = orchestrator_agent._extract_required_agents(f"Math Agent が必要: {math_request}")
        assert "math_agent" in required_agents
        
        # Research Agentが必要なリクエスト
        research_request = "AIについて調べてください"
        required_agents = orchestrator_agent._extract_required_agents(f"Research Agent が必要: {research_request}")
        assert "research_agent" in required_agents
    
    def test_agent_card_creation(self, orchestrator_agent):
        """エージェントカードの作成テスト"""
        agent_card = orchestrator_agent.get_agent_card()
        
        assert agent_card.name == "Orchestrator Agent"
        assert len(agent_card.skills) > 0
        assert any(skill.name == "multi_agent_coordination" for skill in agent_card.skills)


class TestA2AProtocol:
    """A2Aプロトコルのテスト"""
    
    def test_message_creation(self):
        """メッセージ作成のテスト"""
        message = Message(
            role="user",
            parts=[MessagePart(kind="text", text="テストメッセージ")]
        )
        
        assert message.role == "user"
        assert len(message.parts) == 1
        assert message.parts[0].text == "テストメッセージ"
        assert message.messageId is not None
    
    def test_send_message_request_creation(self):
        """SendMessageRequestの作成テスト"""
        message = Message(
            role="user",
            parts=[MessagePart(kind="text", text="テストメッセージ")]
        )
        
        request = SendMessageRequest(
            params=MessageSendParams(message=message)
        )
        
        assert request.jsonrpc == "2.0"
        assert request.method == "sendMessage"
        assert request.id is not None
        assert request.params.message == message


@pytest.mark.asyncio
async def test_integration_workflow():
    """統合ワークフローのテスト"""
    print("\n=== Integration Workflow Test ===")
    
    # 各エージェントのインスタンスを作成
    math_agent = MathAgent()
    research_agent = ResearchAgent()
    orchestrator = OrchestratorAgent()
    
    # Math Agentテスト
    math_message = Message(
        role="user",
        parts=[MessagePart(kind="text", text="3 * 4 を計算してください")]
    )
    math_result = await math_agent.process_new_message(math_message)
    print(f"Math Agent Result: {math_result}")
    
    # Research Agentテスト
    research_message = Message(
        role="user", 
        parts=[MessagePart(kind="text", text="機械学習について要約してください")]
    )
    research_result = await research_agent.process_new_message(research_message)
    print(f"Research Agent Result: {research_result}")
    
    # Orchestratorテスト
    complex_message = Message(
        role="user",
        parts=[MessagePart(kind="text", text="統計学の平均値について計算例と説明をお願いします")]
    )
    orchestrator_result = await orchestrator.process_new_message(complex_message)
    print(f"Orchestrator Result: {orchestrator_result}")
    
    # 全てのテストが成功したことを確認
    assert all([
        isinstance(math_result, str) and len(math_result) > 0,
        isinstance(research_result, str) and len(research_result) > 0,
        isinstance(orchestrator_result, str) and len(orchestrator_result) > 0
    ])
    
    print("✓ All integration tests passed!")


if __name__ == "__main__":
    # テストを実行
    pytest.main([__file__, "-v", "--tb=short"])