import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class AppConfig(BaseSettings):
    """アプリケーション設定"""
    
    # AWS Bedrock設定
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    aws_access_key_id: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    
    # A2Aサーバー設定
    a2a_server_port: int = Field(default=8000, env="A2A_SERVER_PORT")
    a2a_math_agent_port: int = Field(default=8001, env="A2A_MATH_AGENT_PORT")
    a2a_research_agent_port: int = Field(default=8002, env="A2A_RESEARCH_AGENT_PORT")
    a2a_orchestrator_port: int = Field(default=8003, env="A2A_ORCHESTRATOR_PORT")
    
    # MCPサーバー設定
    mcp_server_port: int = Field(default=9000, env="MCP_SERVER_PORT")
    
    # ログ設定
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


# グローバル設定インスタンス
config = AppConfig()