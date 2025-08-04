import asyncio
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .protocol import SendMessageRequest, SendMessageResponse, AgentCard
from ..agents.math_agent import math_agent
from ..agents.research_agent import research_agent
from ..agents.orchestrator import orchestrator_agent
from ..utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


class A2AServer:
    """A2Aサーバー"""
    
    def __init__(self, agent_handler, agent_card: AgentCard, port: int = 8000):
        self.agent_handler = agent_handler
        self.agent_card = agent_card
        self.port = port
        self.app = self._create_app()
        
        setup_logging()
        logger.info(f"A2A Server initialized for {agent_card.name} on port {port}")
    
    def _create_app(self) -> FastAPI:
        """FastAPIアプリケーションを作成"""
        app = FastAPI(
            title=f"{self.agent_card.name} A2A Server",
            description=self.agent_card.description,
            version=self.agent_card.version
        )
        
        # CORS設定
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # エージェントカードエンドポイント
        @app.get("/.well-known/agent.json")
        async def get_agent_card() -> Dict[str, Any]:
            """公開エージェントカードを返す"""
            return self.agent_card.model_dump(exclude_none=True)
        
        @app.get("/agent/authenticatedExtendedCard")
        async def get_extended_agent_card() -> Dict[str, Any]:
            """認証済み拡張エージェントカードを返す"""
            # 実際の実装では認証チェックを行う
            return self.agent_card.model_dump(exclude_none=True)
        
        # A2Aメッセージングエンドポイント
        @app.post("/a2a/sendMessage")
        async def send_message(request: SendMessageRequest) -> SendMessageResponse:
            """メッセージを送信"""
            try:
                response = await self.agent_handler.handle_message(request)
                return response
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # ヘルスチェックエンドポイント
        @app.get("/health")
        async def health_check() -> Dict[str, str]:
            """ヘルスチェック"""
            return {"status": "healthy", "agent": self.agent_card.name}
        
        return app
    
    async def start(self):
        """サーバーを開始"""
        import uvicorn
        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()


async def start_math_agent_server():
    """Math Agentサーバーを開始"""
    server = A2AServer(
        agent_handler=math_agent,
        agent_card=math_agent.get_agent_card(),
        port=8001
    )
    await server.start()


async def start_research_agent_server():
    """Research Agentサーバーを開始"""
    server = A2AServer(
        agent_handler=research_agent,
        agent_card=research_agent.get_agent_card(),
        port=8002
    )
    await server.start()


async def start_orchestrator_server():
    """Orchestratorサーバーを開始"""
    # オーケストレーターの初期化
    await orchestrator_agent.initialize_agent_connections()
    
    server = A2AServer(
        agent_handler=orchestrator_agent,
        agent_card=orchestrator_agent.get_agent_card(),
        port=8003
    )
    await server.start()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python -m src.a2a.server [math|research|orchestrator]")
        sys.exit(1)
    
    agent_type = sys.argv[1]
    
    if agent_type == "math":
        asyncio.run(start_math_agent_server())
    elif agent_type == "research":
        asyncio.run(start_research_agent_server())
    elif agent_type == "orchestrator":
        asyncio.run(start_orchestrator_server())
    else:
        print("Invalid agent type. Use: math, research, or orchestrator")
        sys.exit(1)