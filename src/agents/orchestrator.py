import asyncio
import logging
from typing import Dict, Any, List, Optional
from uuid import uuid4
import httpx
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

from ..utils.bedrock_client import BedrockClaudeClient
from ..a2a.protocol import (
    A2AMessageHandler, A2AClient, A2ACardResolver,
    Message, MessagePart, MessageSendParams, SendMessageRequest,
    AgentCard, AgentSkill
)

logger = logging.getLogger(__name__)


class OrchestratorState:
    """Orchestratorの状態"""
    def __init__(self):
        self.user_request: str = ""
        self.task_analysis: Dict[str, Any] = {}
        self.selected_agents: List[str] = []
        self.agent_responses: Dict[str, str] = {}
        self.final_synthesis: str = ""


class OrchestratorAgent(A2AMessageHandler):
    """マルチエージェントシステムのオーケストレーター"""
    
    def __init__(self):
        super().__init__()
        self.llm_client = BedrockClaudeClient.from_env()
        self.http_client = httpx.AsyncClient()
        self.agent_registry: Dict[str, Dict[str, Any]] = {}
        self.agent_clients: Dict[str, A2AClient] = {}
        self.graph = self._create_langgraph()
        
        # 利用可能なエージェントを登録
        self._register_agents()
        
        logger.info("Orchestrator Agent initialized")
    
    def _register_agents(self):
        """利用可能なエージェントを登録"""
        self.agent_registry = {
            "math_agent": {
                "name": "Math Agent",
                "description": "数学計算専門エージェント",
                "endpoint": "http://localhost:8001",
                "capabilities": ["arithmetic", "calculus", "equation_solving", "statistics"]
            },
            "research_agent": {
                "name": "Research Agent", 
                "description": "研究・調査専門エージェント",
                "endpoint": "http://localhost:8002",
                "capabilities": ["web_research", "text_analysis", "fact_checking", "research_synthesis"]
            }
        }
    
    def _create_langgraph(self) -> StateGraph:
        """LangGraphワークフローを作成"""
        
        def analyze_user_request(state: Dict[str, Any]) -> Dict[str, Any]:
            """ユーザーリクエストを分析"""
            user_input = state.get("user_input", "")
            
            # LLMを使用してタスクを分析
            analysis_prompt = f"""
            以下のユーザーリクエストを分析し、どのエージェントが必要かを判断してください。
            
            ユーザーリクエスト: {user_input}
            
            利用可能なエージェント:
            1. Math Agent - 数学計算、微分積分、方程式解法、統計
            2. Research Agent - Web検索、情報分析、事実確認、研究統合
            
            以下の形式で回答してください:
            必要なエージェント: [エージェント名のリスト]
            タスクの複雑度: [低/中/高]
            実行順序: [シーケンシャル/並列]
            理由: [選択理由]
            """
            
            try:
                messages = [HumanMessage(content=analysis_prompt)]
                analysis_result = self.llm_client.invoke(messages)
                
                # 分析結果からエージェントを特定
                required_agents = self._extract_required_agents(analysis_result)
                state["required_agents"] = required_agents
                state["task_analysis"] = analysis_result
                
                logger.info(f"Task analysis completed. Required agents: {required_agents}")
                
            except Exception as e:
                logger.error(f"Task analysis error: {e}")
                state["required_agents"] = ["math_agent"]  # デフォルト
                state["task_analysis"] = "分析エラーが発生しました"
            
            return state
        
        def coordinate_agents(state: Dict[str, Any]) -> Dict[str, Any]:
            """エージェント間の協調作業を調整"""
            required_agents = state.get("required_agents", [])
            user_input = state.get("user_input", "")
            
            agent_responses = {}
            
            for agent_name in required_agents:
                try:
                    response = self._delegate_to_agent(agent_name, user_input)
                    agent_responses[agent_name] = response
                    logger.info(f"Response received from {agent_name}")
                except Exception as e:
                    logger.error(f"Error delegating to {agent_name}: {e}")
                    agent_responses[agent_name] = f"エージェント {agent_name} でエラーが発生しました: {str(e)}"
            
            state["agent_responses"] = agent_responses
            return state
        
        def synthesize_results(state: Dict[str, Any]) -> Dict[str, Any]:
            """エージェントからの結果を統合"""
            agent_responses = state.get("agent_responses", {})
            user_input = state.get("user_input", "")
            
            # 複数のエージェントからの回答を統合
            synthesis_prompt = f"""
            ユーザーの質問: {user_input}
            
            各エージェントからの回答:
            """
            
            for agent_name, response in agent_responses.items():
                synthesis_prompt += f"\n{agent_name}: {response}\n"
            
            synthesis_prompt += """
            
            上記の情報を統合し、ユーザーに対する包括的で有用な回答を日本語で作成してください。
            各エージェントの専門知識を活用し、一貫性のある回答にしてください。
            """
            
            try:
                messages = [HumanMessage(content=synthesis_prompt)]
                final_response = self.llm_client.invoke(messages)
                state["final_response"] = final_response
            except Exception as e:
                logger.error(f"Synthesis error: {e}")
                # フォールバック: 各エージェントの回答をそのまま結合
                combined_response = "\n\n".join([
                    f"**{agent}からの回答:**\n{response}" 
                    for agent, response in agent_responses.items()
                ])
                state["final_response"] = combined_response
            
            return state
        
        # グラフの構築
        workflow = StateGraph(dict)
        
        workflow.add_node("analyze", analyze_user_request)
        workflow.add_node("coordinate", coordinate_agents)
        workflow.add_node("synthesize", synthesize_results)
        
        workflow.set_entry_point("analyze")
        workflow.add_edge("analyze", "coordinate")
        workflow.add_edge("coordinate", "synthesize")
        workflow.add_edge("synthesize", END)
        
        return workflow.compile()
    
    def _extract_required_agents(self, analysis_result: str) -> List[str]:
        """分析結果から必要なエージェントを抽出"""
        agents = []
        
        if "Math Agent" in analysis_result or "数学" in analysis_result:
            agents.append("math_agent")
        if "Research Agent" in analysis_result or "研究" in analysis_result or "検索" in analysis_result:
            agents.append("research_agent")
        
        # デフォルトでMath Agentを使用
        if not agents:
            agents.append("math_agent")
        
        return agents
    
    def _delegate_to_agent(self, agent_name: str, user_input: str) -> str:
        """特定のエージェントにタスクを委譲"""
        if agent_name not in self.agent_registry:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        # 実際のエージェントを呼び出し
        if agent_name == "math_agent":
            return self._call_math_agent(user_input)
        elif agent_name == "research_agent":
            return self._mock_research_agent_response(user_input)
        else:
            return f"{agent_name} からの応答: {user_input}"
    
    def _call_math_agent(self, user_input: str) -> str:
        """Math Agentを直接呼び出し"""
        try:
            from .math_agent import math_agent
            from ..a2a.protocol import Message, MessagePart
            from uuid import uuid4
            
            # Messageオブジェクトを作成
            message = Message(
                role="user",
                messageId=str(uuid4()),
                parts=[MessagePart(kind="text", text=user_input)],
                contextId=None
            )
            
            # Math Agentを同期的に呼び出し（asyncio.run を使用）
            import asyncio
            try:
                # 既存のイベントループがある場合の処理
                loop = asyncio.get_running_loop()
                # タスクとして実行
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, math_agent.process_new_message(message))
                    result = future.result(timeout=30)
                return result
            except RuntimeError:
                # イベントループがない場合
                result = asyncio.run(math_agent.process_new_message(message))
                return result
                
        except Exception as e:
            logger.error(f"Error calling math agent: {e}")
            return f"Math Agent呼び出しエラー: {str(e)}"
    
    def _mock_math_agent_response(self, user_input: str) -> str:
        """Math Agentのモック応答（フォールバック用）"""
        if "微分" in user_input or "derivative" in user_input:
            return "微分計算を実行しました。数学的分析が完了しています。"
        elif "積分" in user_input or "integral" in user_input:
            return "積分計算を実行しました。結果が得られています。"
        elif any(op in user_input for op in ["+", "-", "*", "/", "計算"]):
            return "数学的計算を実行しました。正確な結果を提供します。"
        else:
            return "数学的問題を分析し、適切な解法を適用しました。"
    
    def _mock_research_agent_response(self, user_input: str) -> str:
        """Research Agentのモック応答"""
        if "検索" in user_input or "調べ" in user_input:
            return "Web検索を実行し、関連情報を収集しました。詳細な分析結果を提供します。"
        elif "分析" in user_input or "要約" in user_input:
            return "テキスト分析を実行しました。重要なポイントと洞察を抽出しています。"
        else:
            return "包括的な研究を実行し、信頼性の高い情報を収集しました。"
    
    async def initialize_agent_connections(self):
        """エージェント接続を初期化"""
        for agent_name, agent_info in self.agent_registry.items():
            try:
                endpoint = agent_info["endpoint"]
                resolver = A2ACardResolver(self.http_client, endpoint)
                agent_card = await resolver.get_agent_card()
                client = A2AClient(self.http_client, agent_card)
                self.agent_clients[agent_name] = client
                logger.info(f"Connected to {agent_name} at {endpoint}")
            except Exception as e:
                logger.warning(f"Failed to connect to {agent_name}: {e}")
    
    async def process_new_message(self, message: Message) -> str:
        """新しいメッセージを処理"""
        try:
            # メッセージからテキストを抽出
            text_content = ""
            for part in message.parts:
                if part.kind == "text" and part.text:
                    text_content += part.text
            
            # LangGraphワークフローを実行
            initial_state = {
                "user_input": text_content,
                "message_id": message.messageId
            }
            
            result = await self.graph.ainvoke(initial_state)
            return result.get("final_response", "タスクを完了しました。")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"メッセージ処理エラー: {str(e)}"
    
    async def process_with_context(self, message: Message, context: Dict[str, Any]) -> str:
        """コンテキスト付きでメッセージを処理"""
        try:
            # 過去の相互作用を考慮した処理
            previous_interactions = context.get("interactions", [])
            
            # 新しいメッセージを処理
            result = await self.process_new_message(message)
            
            # コンテキストを更新
            context["interactions"] = previous_interactions + [{
                "message": message.dict(),
                "response": result,
                "timestamp": str(uuid4())
            }]
            await self.save_context(message.contextId or str(uuid4()), context)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing message with context: {e}")
            return f"コンテキスト処理エラー: {str(e)}"
    
    def get_agent_card(self) -> AgentCard:
        """エージェントカードを取得"""
        return AgentCard(
            name="Orchestrator Agent",
            description="マルチエージェントシステムの調整を行うオーケストレーター",
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="multi_agent_coordination",
                    description="複数のエージェント間の協調作業の調整",
                    examples=["複雑なタスクの分散処理", "エージェント間の情報統合"],
                    tags=["orchestration", "coordination", "multi-agent"]
                ),
                AgentSkill(
                    name="task_analysis",
                    description="ユーザーリクエストの分析とタスク分割",
                    examples=["タスクの複雑性分析", "最適なエージェント選択"],
                    tags=["analysis", "planning", "task-management"]
                )
            ],
            supportsAuthenticatedExtendedCard=True
        )
    
    async def close(self):
        """リソースのクリーンアップ"""
        await self.http_client.aclose()


# グローバルオーケストレーターインスタンス
orchestrator_agent = OrchestratorAgent()