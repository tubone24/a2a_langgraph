from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from uuid import uuid4
import httpx
import logging

logger = logging.getLogger(__name__)


class AgentSkill(BaseModel):
    """エージェントのスキル定義"""
    name: str
    description: str
    examples: List[str] = []
    tags: List[str] = []


class AgentCard(BaseModel):
    """A2Aエージェントカード"""
    name: str
    description: str
    version: str = "1.0.0"
    skills: List[AgentSkill] = []
    supportsAuthenticatedExtendedCard: bool = True
    endpoint: Optional[str] = None


class MessagePart(BaseModel):
    """メッセージの一部"""
    kind: str  # "text", "image", etc.
    text: Optional[str] = None
    data: Optional[Any] = None


class Message(BaseModel):
    """A2Aメッセージ"""
    role: str  # "user", "assistant", "system"
    parts: List[MessagePart]
    messageId: str = Field(default_factory=lambda: uuid4().hex)
    taskId: Optional[str] = None
    contextId: Optional[str] = None


class MessageSendParams(BaseModel):
    """メッセージ送信パラメータ"""
    message: Message


class SendMessageRequest(BaseModel):
    """メッセージ送信リクエスト"""
    jsonrpc: str = "2.0"
    method: str = "sendMessage"
    id: str = Field(default_factory=lambda: str(uuid4()))
    params: MessageSendParams


class MessageResult(BaseModel):
    """メッセージ結果"""
    id: str
    status: str  # "completed", "processing", "failed"
    contextId: Optional[str] = None
    artifacts: List[Dict[str, Any]] = []
    content: Optional[str] = None


class SendMessageResponse(BaseModel):
    """メッセージ送信レスポンス"""
    jsonrpc: str = "2.0"
    id: str
    result: Optional[MessageResult] = None
    error: Optional[Dict[str, Any]] = None


class A2ACardResolver:
    """A2Aエージェントカードリゾルバー"""
    
    def __init__(self, httpx_client: httpx.AsyncClient, base_url: str):
        self.client = httpx_client
        self.base_url = base_url.rstrip('/')
    
    async def get_agent_card(
        self,
        relative_card_path: str = "/.well-known/agent.json",
        http_kwargs: Optional[Dict[str, Any]] = None
    ) -> AgentCard:
        """エージェントカードを取得"""
        url = f"{self.base_url}{relative_card_path}"
        kwargs = http_kwargs or {}
        
        try:
            response = await self.client.get(url, **kwargs)
            response.raise_for_status()
            card_data = response.json()
            return AgentCard(**card_data)
        except Exception as e:
            logger.error(f"Failed to fetch agent card from {url}: {e}")
            raise


class A2AClient:
    """A2Aクライアント"""
    
    def __init__(self, httpx_client: httpx.AsyncClient, agent_card: AgentCard, base_url: str = ""):
        self.client = httpx_client
        self.agent_card = agent_card
        self.base_url = base_url or agent_card.endpoint or ""
    
    async def send_message(self, request: SendMessageRequest) -> SendMessageResponse:
        """メッセージを送信"""
        url = f"{self.base_url}/a2a/sendMessage"
        
        try:
            response = await self.client.post(
                url,
                json=request.model_dump(exclude_none=True),
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            response_data = response.json()
            return SendMessageResponse(**response_data)
        except Exception as e:
            logger.error(f"Failed to send message to {url}: {e}")
            raise
    
    async def send_message_streaming(self, request: SendMessageRequest):
        """ストリーミングメッセージを送信"""
        url = f"{self.base_url}/a2a/sendMessageStreaming"
        
        try:
            async with self.client.stream(
                "POST",
                url,
                json=request.model_dump(exclude_none=True),
                headers={"Content-Type": "application/json"}
            ) as response:
                response.raise_for_status()
                async for chunk in response.aiter_lines():
                    if chunk:
                        yield chunk
        except Exception as e:
            logger.error(f"Failed to send streaming message to {url}: {e}")
            raise


class A2AMessageHandler:
    """A2Aメッセージハンドラー"""
    
    def __init__(self):
        self.contexts: Dict[str, Dict[str, Any]] = {}
    
    async def handle_message(self, request: SendMessageRequest) -> SendMessageResponse:
        """メッセージを処理"""
        try:
            message = request.params.message
            task_id = message.taskId
            context_id = message.contextId
            
            # コンテキストの復元または作成
            if task_id and context_id:
                context = await self.restore_context(context_id)
                response_content = await self.process_with_context(message, context)
            else:
                context_id = str(uuid4())
                response_content = await self.process_new_message(message)
            
            # レスポンスの作成
            result = MessageResult(
                id=str(uuid4()),
                status="completed",
                contextId=context_id,
                content=response_content,
                artifacts=[]
            )
            
            return SendMessageResponse(
                jsonrpc="2.0",
                id=request.id,
                result=result
            )
        
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return SendMessageResponse(
                jsonrpc="2.0",
                id=request.id,
                error={
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            )
    
    async def restore_context(self, context_id: str) -> Dict[str, Any]:
        """コンテキストを復元"""
        return self.contexts.get(context_id, {})
    
    async def save_context(self, context_id: str, context: Dict[str, Any]):
        """コンテキストを保存"""
        self.contexts[context_id] = context
    
    async def process_with_context(self, message: Message, context: Dict[str, Any]) -> str:
        """コンテキスト付きでメッセージを処理（サブクラスでオーバーライド）"""
        raise NotImplementedError
    
    async def process_new_message(self, message: Message) -> str:
        """新しいメッセージを処理（サブクラスでオーバーライド）"""
        raise NotImplementedError