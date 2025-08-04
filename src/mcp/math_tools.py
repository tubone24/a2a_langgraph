import asyncio
import json
import logging
from typing import Any, Dict, List
import numpy as np
import sympy as sp
from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class MathMCPServer:
    """数学計算用MCPサーバー"""
    
    def __init__(self):
        self.server = Server("math-mcp-server")
        self._setup_tools()
    
    def _setup_tools(self):
        """MCPツールのセットアップ"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="calculate_expression",
                    description="数学的表現を安全に評価します",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "評価する数学表現"
                            }
                        },
                        "required": ["expression"]
                    }
                ),
                Tool(
                    name="solve_equation",
                    description="代数方程式を解きます",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "equation": {
                                "type": "string",
                                "description": "解く方程式 (例: x**2 - 4 = 0)"
                            },
                            "variable": {
                                "type": "string",
                                "description": "解く変数 (デフォルト: x)",
                                "default": "x"
                            }
                        },
                        "required": ["equation"]
                    }
                ),
                Tool(
                    name="differentiate",
                    description="数学関数の微分を計算します",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "微分する関数"
                            },
                            "variable": {
                                "type": "string",
                                "description": "微分する変数 (デフォルト: x)",
                                "default": "x"
                            }
                        },
                        "required": ["expression"]
                    }
                ),
                Tool(
                    name="integrate",
                    description="数学関数の積分を計算します",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "積分する関数"
                            },
                            "variable": {
                                "type": "string",
                                "description": "積分する変数 (デフォルト: x)",
                                "default": "x"
                            }
                        },
                        "required": ["expression"]
                    }
                ),
                Tool(
                    name="statistics_calculator",
                    description="統計計算を実行します",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "operation": {
                                "type": "string",
                                "enum": ["mean", "median", "std", "variance"],
                                "description": "実行する統計操作"
                            },
                            "data": {
                                "type": "array",
                                "items": {"type": "number"},
                                "description": "計算対象のデータ"
                            }
                        },
                        "required": ["operation", "data"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            try:
                if name == "calculate_expression":
                    return await self._handle_calculate_expression(arguments)
                elif name == "solve_equation":
                    return await self._handle_solve_equation(arguments)
                elif name == "differentiate":
                    return await self._handle_differentiate(arguments)
                elif name == "integrate":
                    return await self._handle_integrate(arguments)
                elif name == "statistics_calculator":
                    return await self._handle_statistics_calculator(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return [TextContent(type="text", text=f"エラー: {str(e)}")]
    
    async def _handle_calculate_expression(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """数学表現の計算"""
        expression = arguments["expression"]
        try:
            # sympyを使用して安全に計算
            result = sp.sympify(expression)
            result_value = float(result.evalf())
            return [TextContent(
                type="text",
                text=f"計算結果: {expression} = {result_value}"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"計算エラー: {str(e)}"
            )]
    
    async def _handle_solve_equation(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """方程式の解"""
        equation = arguments["equation"]
        variable = arguments.get("variable", "x")
        
        try:
            # 方程式を解析
            var = sp.Symbol(variable)
            eq = sp.sympify(equation)
            solutions = sp.solve(eq, var)
            
            if not solutions:
                return [TextContent(
                    type="text",
                    text=f"方程式 {equation} に解が見つかりませんでした"
                )]
            
            solutions_str = ", ".join([str(sol) for sol in solutions])
            return [TextContent(
                type="text",
                text=f"方程式 {equation} の解: {variable} = {solutions_str}"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"方程式解エラー: {str(e)}"
            )]
    
    async def _handle_differentiate(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """微分計算"""
        expression = arguments["expression"]
        variable = arguments.get("variable", "x")
        
        try:
            var = sp.Symbol(variable)
            expr = sp.sympify(expression)
            derivative = sp.diff(expr, var)
            
            return [TextContent(
                type="text",
                text=f"{expression} の {variable} に関する微分: {derivative}"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"微分エラー: {str(e)}"
            )]
    
    async def _handle_integrate(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """積分計算"""
        expression = arguments["expression"]
        variable = arguments.get("variable", "x")
        
        try:
            var = sp.Symbol(variable)
            expr = sp.sympify(expression)
            integral = sp.integrate(expr, var)
            
            return [TextContent(
                type="text",
                text=f"{expression} の {variable} に関する積分: {integral}"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"積分エラー: {str(e)}"
            )]
    
    async def _handle_statistics_calculator(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """統計計算"""
        operation = arguments["operation"]
        data = arguments["data"]
        
        try:
            data_array = np.array(data)
            
            if operation == "mean":
                result = np.mean(data_array)
            elif operation == "median":
                result = np.median(data_array)
            elif operation == "std":
                result = np.std(data_array)
            elif operation == "variance":
                result = np.var(data_array)
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            return [TextContent(
                type="text",
                text=f"データ {data} の {operation}: {result}"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"統計計算エラー: {str(e)}"
            )]
    
    def get_server(self) -> Server:
        """MCPサーバーインスタンスを取得"""
        return self.server


# グローバルサーバーインスタンス
math_mcp_server = MathMCPServer()