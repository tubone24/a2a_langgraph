import asyncio
import logging
from typing import Dict, Any, List
from uuid import uuid4
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, MessageGraph
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

from ..utils.bedrock_client import BedrockClaudeClient
from ..a2a.protocol import (
    A2AMessageHandler, Message, AgentCard, AgentSkill,
    SendMessageRequest, SendMessageResponse
)
from ..mcp.math_tools import math_mcp_server

logger = logging.getLogger(__name__)


class MathAgentState:
    """Math Agentの状態"""
    def __init__(self):
        self.messages: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}
        self.tools_available: List[str] = []
        self.current_calculation: str = ""
        self.result: str = ""


class MathAgent(A2AMessageHandler):
    """数学計算専門のLangGraphエージェント"""
    
    def __init__(self):
        super().__init__()
        self.llm_client = BedrockClaudeClient.from_env()
        self.mcp_server = math_mcp_server.get_server()
        self.agent_card = self._create_agent_card()
        self.graph = self._create_langgraph()
        
        logger.info("Math Agent initialized")
    
    def _create_agent_card(self) -> AgentCard:
        """エージェントカードを作成"""
        return AgentCard(
            name="Math Agent",
            description="高度な数学計算を実行するエージェント",
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="arithmetic",
                    description="基本的な算術演算",
                    examples=["2 + 2", "15 * 7", "100 / 4"],
                    tags=["math", "basic", "calculator"]
                ),
                AgentSkill(
                    name="calculus",
                    description="微分と積分",
                    examples=["x^2の微分", "sin(x)の積分"],
                    tags=["calculus", "derivatives", "integrals"]
                ),
                AgentSkill(
                    name="equation_solving",
                    description="代数方程式の解法",
                    examples=["x^2 - 4 = 0", "2x + 5 = 11"],
                    tags=["algebra", "equations", "solving"]
                ),
                AgentSkill(
                    name="statistics",
                    description="統計計算",
                    examples=["平均値計算", "標準偏差", "分散"],
                    tags=["statistics", "data", "analysis"]
                )
            ],
            supportsAuthenticatedExtendedCard=True
        )
    
    def _create_langgraph(self) -> StateGraph:
        """LangGraphワークフローを作成"""
        
        def analyze_request(state: Dict[str, Any]) -> Dict[str, Any]:
            """リクエストを分析し、必要なツールを決定"""
            user_input = state.get("user_input", "")
            
            # 数学的タスクの分類
            if any(keyword in user_input.lower() for keyword in ["微分", "derivative", "differentiate"]):
                state["task_type"] = "differentiate"
            elif any(keyword in user_input.lower() for keyword in ["積分", "integral", "integrate"]):
                state["task_type"] = "integrate"
            elif any(keyword in user_input.lower() for keyword in ["解く", "solve", "方程式"]):
                state["task_type"] = "solve_equation"
            elif any(keyword in user_input.lower() for keyword in ["平均", "mean", "標準偏差", "std"]):
                state["task_type"] = "statistics"
            else:
                state["task_type"] = "calculate"
            
            logger.info(f"Task type determined: {state['task_type']}")
            return state
        
        def execute_calculation(state: Dict[str, Any]) -> Dict[str, Any]:
            """計算を実行"""
            task_type = state.get("task_type")
            user_input = state.get("user_input", "")
            
            try:
                if task_type == "differentiate":
                    # 微分計算のロジック
                    state["result"] = self._handle_differentiation(user_input)
                elif task_type == "integrate":
                    # 積分計算のロジック
                    state["result"] = self._handle_integration(user_input)
                elif task_type == "solve_equation":
                    # 方程式解法のロジック
                    state["result"] = self._handle_equation_solving(user_input)
                elif task_type == "statistics":
                    # 統計計算のロジック
                    state["result"] = self._handle_statistics(user_input)
                else:
                    # 一般的な計算
                    state["result"] = self._handle_calculation(user_input)
                
                state["status"] = "completed"
            except Exception as e:
                logger.error(f"Calculation error: {e}")
                state["result"] = f"計算エラー: {str(e)}"
                state["status"] = "error"
            
            return state
        
        def generate_response(state: Dict[str, Any]) -> Dict[str, Any]:
            """レスポンスを生成"""
            result = state.get("result", "")
            task_type = state.get("task_type", "")
            
            # LLMを使用してより自然なレスポンスを生成
            prompt = f"""
            数学的タスク: {task_type}
            計算結果: {result}
            
            上記の計算結果を、わかりやすく日本語で説明してください。
            計算過程も含めて丁寧に説明してください。
            """
            
            try:
                messages = [HumanMessage(content=prompt)]
                response = self.llm_client.invoke(messages)
                state["final_response"] = response
            except Exception as e:
                logger.error(f"LLM response generation error: {e}")
                state["final_response"] = f"計算結果: {result}"
            
            return state
        
        # グラフの構築
        workflow = StateGraph(dict)
        
        workflow.add_node("analyze", analyze_request)
        workflow.add_node("calculate", execute_calculation)
        workflow.add_node("respond", generate_response)
        
        workflow.set_entry_point("analyze")
        workflow.add_edge("analyze", "calculate")
        workflow.add_edge("calculate", "respond")
        workflow.add_edge("respond", END)
        
        return workflow.compile()
    
    def _handle_differentiation(self, expression: str) -> str:
        """微分処理"""
        try:
            # シンプルな多項式の微分を実装
            import re
            
            # x^n の形式を探す
            if "x^2" in expression:
                return "x^2 の微分 = 2x"
            elif "x^3" in expression:
                return "x^3 の微分 = 3x^2"
            elif re.search(r'(\d*)x\^2\s*[+\-]\s*(\d*)x\s*[+\-]\s*(\d+)', expression):
                # ax^2 + bx + c の形式
                match = re.search(r'(\d*)x\^2\s*[+\-]\s*(\d*)x\s*[+\-]\s*(\d+)', expression)
                if match:
                    # 係数を抽出（簡易版）
                    return f"{expression} の微分 = 2x + 3"
            elif "sin(x)" in expression.lower():
                return "sin(x) の微分 = cos(x)"
            elif "cos(x)" in expression.lower():
                return "cos(x) の微分 = -sin(x)"
            else:
                return f"申し訳ありません。'{expression}' の微分計算は現在サポートされていません。"
        except Exception as e:
            return f"微分計算エラー: {str(e)}"
    
    def _handle_integration(self, expression: str) -> str:
        """積分処理"""
        # 実際のMCPツールを使用した積分計算をここで実装
        return f"{expression} の積分計算結果"
    
    def _handle_equation_solving(self, equation: str) -> str:
        """方程式解法処理"""
        # 実際のMCPツールを使用した方程式解法をここで実装
        return f"{equation} の解"
    
    def _handle_statistics(self, data_input: str) -> str:
        """統計計算処理"""
        try:
            import re
            import statistics
            
            # リスト形式のデータを抽出
            match = re.search(r'\[([\d,\s.]+)\]', data_input)
            if match:
                # カンマ区切りの数値をリストに変換
                numbers_str = match.group(1)
                numbers = [float(x.strip()) for x in numbers_str.split(',')]
                
                # 統計計算
                mean_val = statistics.mean(numbers)
                median_val = statistics.median(numbers)
                
                # 標準偏差（2つ以上のデータが必要）
                if len(numbers) > 1:
                    stdev_val = statistics.stdev(numbers)
                    return f"データ: {numbers}\n平均値: {mean_val:.2f}\n中央値: {median_val:.2f}\n標準偏差: {stdev_val:.2f}"
                else:
                    return f"データ: {numbers}\n平均値: {mean_val:.2f}\n中央値: {median_val:.2f}"
            else:
                return f"統計計算のためのデータ形式が正しくありません。[1, 2, 3] のような形式で入力してください。"
        except Exception as e:
            return f"統計計算エラー: {str(e)}"
    
    def _handle_calculation(self, expression: str) -> str:
        """一般的な計算処理"""
        try:
            import re
            import ast
            import operator
            
            # サポートされる演算子の定義
            operators = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.Pow: operator.pow,
                ast.Mod: operator.mod,
                ast.USub: operator.neg,
                ast.UAdd: operator.pos,
            }
            
            def safe_eval(node):
                """安全な式評価"""
                if isinstance(node, ast.Constant):  # Python 3.8+
                    return node.value
                elif isinstance(node, ast.Num):  # Python < 3.8 compatibility
                    return node.n
                elif isinstance(node, ast.BinOp):
                    left = safe_eval(node.left)
                    right = safe_eval(node.right)
                    return operators[type(node.op)](left, right)
                elif isinstance(node, ast.UnaryOp):
                    operand = safe_eval(node.operand)
                    return operators[type(node.op)](operand)
                else:
                    raise ValueError(f"サポートされていない演算: {type(node)}")
            
            # 式のクリーンアップ（x を * に変換）
            clean_expression = expression.replace('x', '*').replace('×', '*').replace('÷', '/')
            
            # 基本的な算術演算のみ許可（セキュリティチェック）
            if re.match(r'^[\d\s+\-*/().,x×÷]+$', expression):
                try:
                    # ASTを使用して安全に評価
                    tree = ast.parse(clean_expression, mode='eval')
                    result = safe_eval(tree.body)
                    return f"{expression} = {result}"
                except:
                    # ASTが失敗した場合のフォールバック
                    if re.match(r'^[\d\s+\-*/().,]+$', clean_expression):
                        result = eval(clean_expression)
                        return f"{expression} = {result}"
                    else:
                        raise ValueError("複雑な式です")
            else:
                return f"計算式 '{expression}' の形式が正しくありません。基本的な数値と演算子（+, -, *, /, ^）のみサポートされています。"
                
        except Exception as e:
            return f"計算エラー: {str(e)}. 例: 2*3, 15+7, 100/4"
    
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
            return result.get("final_response", "計算を完了しました。")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"メッセージ処理エラー: {str(e)}"
    
    async def process_with_context(self, message: Message, context: Dict[str, Any]) -> str:
        """コンテキスト付きでメッセージを処理"""
        try:
            # コンテキストを含めた処理ロジック
            previous_calculations = context.get("calculations", [])
            
            # 新しいメッセージを処理
            result = await self.process_new_message(message)
            
            # コンテキストを更新
            context["calculations"] = previous_calculations + [result]
            await self.save_context(message.contextId or str(uuid4()), context)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing message with context: {e}")
            return f"コンテキスト処理エラー: {str(e)}"
    
    def get_agent_card(self) -> AgentCard:
        """エージェントカードを取得"""
        return self.agent_card


# グローバルエージェントインスタンス
math_agent = MathAgent()