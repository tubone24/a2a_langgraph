import asyncio
import json
import logging
from typing import Any, Dict, List
import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent

logger = logging.getLogger(__name__)


class ResearchMCPServer:
    """研究・調査用MCPサーバー"""
    
    def __init__(self):
        self.server = Server("research-mcp-server")
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self._setup_tools()
    
    def _setup_tools(self):
        """MCPツールのセットアップ"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="web_search",
                    description="Web検索を実行します",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "検索クエリ"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "最大結果数 (デフォルト: 5)",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="analyze_text",
                    description="テキストを分析し、要約や洞察を提供します",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "分析するテキスト"
                            },
                            "analysis_type": {
                                "type": "string",
                                "enum": ["summary", "keywords", "sentiment", "structure"],
                                "description": "分析タイプ",
                                "default": "summary"
                            }
                        },
                        "required": ["text"]
                    }
                ),
                Tool(
                    name="fact_check",
                    description="情報の事実確認を行います",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "statement": {
                                "type": "string",
                                "description": "確認する情報・ステートメント"
                            }
                        },
                        "required": ["statement"]
                    }
                ),
                Tool(
                    name="research_synthesis",
                    description="複数の情報源から総合的な研究結果を作成します",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sources": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "研究対象の情報源リスト"
                            },
                            "topic": {
                                "type": "string",
                                "description": "研究トピック"
                            }
                        },
                        "required": ["sources", "topic"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            try:
                if name == "web_search":
                    return await self._handle_web_search(arguments)
                elif name == "analyze_text":
                    return await self._handle_analyze_text(arguments)
                elif name == "fact_check":
                    return await self._handle_fact_check(arguments)
                elif name == "research_synthesis":
                    return await self._handle_research_synthesis(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return [TextContent(type="text", text=f"エラー: {str(e)}")]
    
    async def _handle_web_search(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Web検索の実行"""
        query = arguments["query"]
        max_results = arguments.get("max_results", 5)
        
        try:
            # 実際のWeb検索APIの代わりにモックレスポンスを返す
            # 本番環境では実際の検索APIを使用する
            mock_results = [
                {
                    "title": f"検索結果 {i+1}: {query}",
                    "url": f"https://example.com/result-{i+1}",
                    "snippet": f"これは'{query}'に関する検索結果 {i+1} のスニペットです。"
                }
                for i in range(min(max_results, 3))
            ]
            
            results_text = "Web検索結果:\n"
            for result in mock_results:
                results_text += f"- {result['title']}\n"
                results_text += f"  URL: {result['url']}\n"
                results_text += f"  概要: {result['snippet']}\n\n"
            
            return [TextContent(type="text", text=results_text)]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Web検索エラー: {str(e)}"
            )]
    
    async def _handle_analyze_text(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """テキスト分析"""
        text = arguments["text"]
        analysis_type = arguments.get("analysis_type", "summary")
        
        try:
            if analysis_type == "summary":
                # 簡単な要約ロジック（実際にはより高度な処理を行う）
                sentences = text.split('。')
                summary = '。'.join(sentences[:3]) + '。'
                result = f"要約:\n{summary}"
            
            elif analysis_type == "keywords":
                # キーワード抽出の簡単な実装
                words = text.split()
                keywords = list(set([word for word in words if len(word) > 3]))[:10]
                result = f"キーワード: {', '.join(keywords)}"
            
            elif analysis_type == "sentiment":
                # 感情分析の簡単な実装
                positive_words = ["良い", "素晴らしい", "優秀", "成功"]
                negative_words = ["悪い", "問題", "失敗", "困難"]
                
                pos_count = sum(1 for word in positive_words if word in text)
                neg_count = sum(1 for word in negative_words if word in text)
                
                if pos_count > neg_count:
                    sentiment = "ポジティブ"
                elif neg_count > pos_count:
                    sentiment = "ネガティブ"
                else:
                    sentiment = "中立"
                
                result = f"感情分析: {sentiment} (ポジティブ: {pos_count}, ネガティブ: {neg_count})"
            
            elif analysis_type == "structure":
                # 文書構造分析
                char_count = len(text)
                word_count = len(text.split())
                sentence_count = len([s for s in text.split('。') if s.strip()])
                
                result = f"文書構造:\n- 文字数: {char_count}\n- 単語数: {word_count}\n- 文数: {sentence_count}"
            
            else:
                result = f"未知の分析タイプ: {analysis_type}"
            
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"テキスト分析エラー: {str(e)}"
            )]
    
    async def _handle_fact_check(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """事実確認"""
        statement = arguments["statement"]
        
        try:
            # 実際の事実確認システムの代わりにモック実装
            result = f"事実確認結果:\n"
            result += f"ステートメント: '{statement}'\n"
            result += f"信頼度: 中程度\n"
            result += f"注意: これはモック実装です。実際の事実確認が必要です。"
            
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"事実確認エラー: {str(e)}"
            )]
    
    async def _handle_research_synthesis(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """研究統合"""
        sources = arguments["sources"]
        topic = arguments["topic"]
        
        try:
            result = f"研究統合結果: {topic}\n\n"
            result += f"情報源数: {len(sources)}\n"
            result += f"分析した情報源:\n"
            
            for i, source in enumerate(sources, 1):
                result += f"{i}. {source}\n"
            
            result += f"\n総合的な結論:\n"
            result += f"'{topic}'に関する研究から、以下の知見が得られました：\n"
            result += f"- 複数の情報源から一貫した傾向が確認されました\n"
            result += f"- さらなる研究が推奨される領域も特定されました\n"
            result += f"- 実践的な応用可能性が示唆されています"
            
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"研究統合エラー: {str(e)}"
            )]
    
    def get_server(self) -> Server:
        """MCPサーバーインスタンスを取得"""
        return self.server
    
    async def close(self):
        """リソースのクリーンアップ"""
        await self.http_client.aclose()


# グローバルサーバーインスタンス
research_mcp_server = ResearchMCPServer()