import os
import boto3
from typing import Optional
from langchain_aws import ChatBedrockConverse
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel
import logging

logger = logging.getLogger(__name__)


class BedrockClaudeClient:
    """Amazon Bedrock Claude 3.5 Sonnetクライアント"""
    
    def __init__(
        self,
        region: str = "us-east-1",
        model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
        temperature: float = 0.1,
        max_tokens: int = 4096,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None
    ):
        self.region = region
        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # AWS認証情報の設定
        session_kwargs = {"region_name": region}
        if aws_access_key_id and aws_secret_access_key:
            session_kwargs.update({
                "aws_access_key_id": aws_access_key_id,
                "aws_secret_access_key": aws_secret_access_key
            })
        
        self.session = boto3.Session(**session_kwargs)
        self.bedrock_client = self.session.client("bedrock-runtime")
        
        # LangChain BedrockChatモデルの初期化
        self.llm = ChatBedrockConverse(
            region_name=self.region,
            model_id=self.model_id,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        
        logger.info(f"Bedrock Claude client initialized with model: {self.model_id}")
    
    def get_llm(self) -> BaseChatModel:
        """LangChainのChatModelインスタンスを取得"""
        return self.llm
    
    async def ainvoke(self, messages: list[BaseMessage]) -> str:
        """非同期でメッセージを送信し、レスポンスを取得"""
        try:
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error invoking Bedrock Claude: {e}")
            raise
    
    def invoke(self, messages: list[BaseMessage]) -> str:
        """同期でメッセージを送信し、レスポンスを取得"""
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error invoking Bedrock Claude: {e}")
            raise
    
    @classmethod
    def from_env(cls) -> "BedrockClaudeClient":
        """環境変数から設定を読み込んでインスタンスを作成"""
        return cls(
            region=os.getenv("AWS_REGION", "us-east-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )


def create_bedrock_llm(
    temperature: float = 0.1,
    max_tokens: int = 4096
) -> BaseChatModel:
    """環境変数から設定を読み込んでBedrock Claude LLMを作成"""
    client = BedrockClaudeClient.from_env()
    return client.get_llm()