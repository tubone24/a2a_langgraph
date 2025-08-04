import asyncio
import logging
from typing import Dict, Any, List
from uuid import uuid4
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

from ..utils.bedrock_client import BedrockClaudeClient
from ..a2a.protocol import (
    A2AMessageHandler, Message, AgentCard, AgentSkill,
    SendMessageRequest, SendMessageResponse
)
from ..mcp.research_tools import research_mcp_server

logger = logging.getLogger(__name__)


class ResearchAgentState:
    """Research Agentの状態"""
    def __init__(self):
        self.messages: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}
        self.research_topic: str = ""
        self.search_results: List[Dict[str, Any]] = []
        self.analysis_results: List[str] = []
        self.final_report: str = ""


class ResearchAgent(A2AMessageHandler):
    """研究・調査専門のLangGraphエージェント"""
    
    def __init__(self):
        super().__init__()
        self.llm_client = BedrockClaudeClient.from_env()
        self.mcp_server = research_mcp_server.get_server()
        self.agent_card = self._create_agent_card()
        self.graph = self._create_langgraph()
        
        logger.info("Research Agent initialized")
    
    def _create_agent_card(self) -> AgentCard:
        """エージェントカードを作成"""
        return AgentCard(
            name="Research Agent",
            description="情報収集・分析・研究を実行するエージェント",
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="web_research",
                    description="Web検索と情報収集",
                    examples=["最新のAI技術について調べて", "量子コンピュータの現状は？"],
                    tags=["research", "web", "information"]
                ),
                AgentSkill(
                    name="text_analysis",
                    description="テキスト分析と要約",
                    examples=["この文書を要約して", "キーワードを抽出して"],
                    tags=["analysis", "text", "nlp"]
                ),
                AgentSkill(
                    name="fact_checking",
                    description="情報の事実確認",
                    examples=["この情報は正確ですか？", "事実確認をお願いします"],
                    tags=["fact-check", "verification", "accuracy"]
                ),
                AgentSkill(
                    name="research_synthesis",
                    description="研究結果の統合と報告書作成",
                    examples=["研究結果をまとめて", "総合的な報告書を作成"],
                    tags=["synthesis", "report", "integration"]
                )
            ],
            supportsAuthenticatedExtendedCard=True
        )
    
    def _create_langgraph(self) -> StateGraph:
        """LangGraphワークフローを作成"""
        
        def analyze_research_request(state: Dict[str, Any]) -> Dict[str, Any]:
            """研究リクエストを分析"""
            user_input = state.get("user_input", "")
            
            # 研究タスクの分類
            if any(keyword in user_input.lower() for keyword in ["検索", "調べて", "情報", "search"]):
                state["research_type"] = "web_search"
            elif any(keyword in user_input.lower() for keyword in ["分析", "要約", "analyze", "summary"]):
                state["research_type"] = "text_analysis"
            elif any(keyword in user_input.lower() for keyword in ["事実確認", "fact", "check", "正確"]):
                state["research_type"] = "fact_check"
            elif any(keyword in user_input.lower() for keyword in ["統合", "報告", "まとめ", "synthesis"]):
                state["research_type"] = "research_synthesis"
            else:
                state["research_type"] = "general_research"
            
            # 研究トピックを抽出
            state["research_topic"] = self._extract_topic(user_input)
            
            logger.info(f"Research type: {state['research_type']}, Topic: {state['research_topic']}")
            return state
        
        def execute_research(state: Dict[str, Any]) -> Dict[str, Any]:
            """研究を実行"""
            research_type = state.get("research_type")
            research_topic = state.get("research_topic", "")
            user_input = state.get("user_input", "")
            
            try:
                if research_type == "web_search":
                    state["research_results"] = self._perform_web_search(research_topic)
                elif research_type == "text_analysis":
                    state["research_results"] = self._perform_text_analysis(user_input)
                elif research_type == "fact_check":
                    state["research_results"] = self._perform_fact_check(research_topic)
                elif research_type == "research_synthesis":
                    state["research_results"] = self._perform_research_synthesis(user_input)
                else:
                    state["research_results"] = self._perform_general_research(research_topic)
                
                state["status"] = "completed"
            except Exception as e:
                logger.error(f"Research error: {e}")
                state["research_results"] = f"研究エラー: {str(e)}"
                state["status"] = "error"
            
            return state
        
        def synthesize_findings(state: Dict[str, Any]) -> Dict[str, Any]:
            """研究結果を統合"""
            research_results = state.get("research_results", "")
            research_topic = state.get("research_topic", "")
            research_type = state.get("research_type", "")
            
            # LLMを使用して研究結果を統合
            prompt = f"""
            研究タイプ: {research_type}
            研究トピック: {research_topic}
            研究結果: {research_results}
            
            上記の研究結果を基に、包括的で構造化された報告書を日本語で作成してください。
            以下の構成で報告書を作成してください：
            1. 概要
            2. 主要な発見事項
            3. 詳細な分析
            4. 結論と推奨事項
            """
            
            try:
                messages = [HumanMessage(content=prompt)]
                response = self.llm_client.invoke(messages)
                state["final_report"] = response
            except Exception as e:
                logger.error(f"LLM synthesis error: {e}")
                state["final_report"] = f"研究結果: {research_results}"
            
            return state
        
        # グラフの構築
        workflow = StateGraph(dict)
        
        workflow.add_node("analyze", analyze_research_request)
        workflow.add_node("research", execute_research)
        workflow.add_node("synthesize", synthesize_findings)
        
        workflow.set_entry_point("analyze")
        workflow.add_edge("analyze", "research")
        workflow.add_edge("research", "synthesize")
        workflow.add_edge("synthesize", END)
        
        return workflow.compile()
    
    def _extract_topic(self, user_input: str) -> str:
        """ユーザー入力から研究トピックを抽出"""
        # 簡単なトピック抽出ロジック
        # 実際の実装では、より高度なNLP処理を行う
        keywords = user_input.split()
        return " ".join(keywords[:5])  # 最初の5単語をトピックとする
    
    def _perform_web_search(self, topic: str) -> str:
        """Web検索を実行"""
        # 実際のMCPツールを使用したWeb検索をここで実装
        return f"'{topic}' に関するWeb検索結果"
    
    def _perform_text_analysis(self, text: str) -> str:
        """テキスト分析を実行"""
        # 実際のMCPツールを使用したテキスト分析をここで実装
        return f"テキスト分析結果: {text[:100]}..."
    
    def _perform_fact_check(self, statement: str) -> str:
        """事実確認を実行"""
        # 実際のMCPツールを使用した事実確認をここで実装
        return f"'{statement}' の事実確認結果"
    
    def _perform_research_synthesis(self, input_data: str) -> str:
        """研究統合を実行"""
        # 実際のMCPツールを使用した研究統合をここで実装
        return f"研究統合結果: {input_data[:100]}..."
    
    def _perform_general_research(self, topic: str) -> str:
        """一般的な研究を実行"""
        # 複数の研究手法を組み合わせた包括的な研究
        web_results = self._perform_web_search(topic)
        return f"'{topic}' に関する包括的な研究結果"
    
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
            return result.get("final_report", "研究を完了しました。")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"メッセージ処理エラー: {str(e)}"
    
    async def process_with_context(self, message: Message, context: Dict[str, Any]) -> str:
        """コンテキスト付きでメッセージを処理"""
        try:
            # 過去の研究結果を含めた処理
            previous_research = context.get("research_history", [])
            
            # 新しいメッセージを処理
            result = await self.process_new_message(message)
            
            # コンテキストを更新
            context["research_history"] = previous_research + [result]
            await self.save_context(message.contextId or str(uuid4()), context)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing message with context: {e}")
            return f"コンテキスト処理エラー: {str(e)}"
    
    def get_agent_card(self) -> AgentCard:
        """エージェントカードを取得"""
        return self.agent_card


# グローバルエージェントインスタンス
research_agent = ResearchAgent()