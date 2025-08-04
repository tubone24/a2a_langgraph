# A2A LangGraph Multi-Agent System

LangGraphとAgent-to-Agent (A2A) プロトコルを使用したマルチエージェントシステムです。Amazon Bedrock Claude 3.5 Sonnetを使用しています。

## 🏗️ アーキテクチャ

このシステムは以下の主要コンポーネントで構成されています：

### エージェント
- **Math Agent**: 数学計算・微分積分・方程式解法・統計計算
- **Research Agent**: Web検索・情報分析・事実確認・研究統合
- **Orchestrator Agent**: マルチエージェント間の協調作業を調整

### 技術スタック
- **LangGraph**: エージェントワークフローの構築とオーケストレーション
- **A2A Protocol**: エージェント間の標準化された通信
- **Amazon Bedrock Claude 3.5 Sonnet**: 大規模言語モデル
- **MCP (Model Context Protocol)**: ツールとの統合
- **FastAPI**: REST APIサーバー

## 📋 前提条件

- Python 3.11+
- AWS アカウント（Bedrock Claude 3.5 Sonnet へのアクセス）
- uv (Pythonパッケージマネージャー)

## 🚀 セットアップ

### 1. リポジトリのクローンと依存関係のインストール

```bash
git clone <repository-url>
cd a2a_langgraph

# uvのインストール（まだインストールしていない場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 依存関係のインストール
uv sync

# 開発依存関係も含めてインストール
uv sync --dev
```

### 2. 環境変数の設定

`.env.example`を参考に`.env`ファイルを作成：

```bash
cp .env.example .env
```

`.env`ファイルを編集し、AWS認証情報を設定：

```bash
# AWS Bedrock Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here

# A2A Configuration
A2A_SERVER_PORT=8000
A2A_MATH_AGENT_PORT=8001
A2A_RESEARCH_AGENT_PORT=8002
A2A_ORCHESTRATOR_PORT=8003

# MCP Configuration
MCP_SERVER_PORT=9000

# Logging
LOG_LEVEL=INFO
```

### 3. サーバーの起動

#### 自動起動（推奨）

```bash
uv run python scripts/start_servers.py
```

#### 手動起動

各エージェントを個別のターミナルで起動：

```bash
# Math Agent
uv run python -m src.a2a.server math

# Research Agent  
uv run python -m src.a2a.server research

# Orchestrator
uv run python -m src.a2a.server orchestrator
```

## 💻 使用方法

### クライアント例の実行

```bash
uv run python examples/client_example.py
```

### エージェントカードの確認

各エージェントのエージェントカードは以下のエンドポイントで確認できます：

```bash
# Math Agent
curl http://localhost:8001/.well-known/agent.json

# Research Agent
curl http://localhost:8002/.well-known/agent.json

# Orchestrator
curl http://localhost:8003/.well-known/agent.json
```

### API使用例

#### Math Agentへの直接リクエスト

```bash
curl -X POST http://localhost:8001/a2a/sendMessage \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "sendMessage",
    "id": "1",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "x^2 + 3x + 2 の微分を計算してください"}],
        "messageId": "test-123"
      }
    }
  }'
```

#### Orchestrator経由の複合タスク

```bash
curl -X POST http://localhost:8003/a2a/sendMessage \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "sendMessage",
    "id": "1",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "sin(x)の微分を計算して、その結果について詳しく調べてください"}],
        "messageId": "complex-task-123"
      }
    }
  }'
```

## 🧪 テスト

テストの実行：

```bash
# 全テストの実行
uv run pytest tests/ -v

# 特定のテストファイルの実行
uv run python tests/test_agents.py
```

## 📁 プロジェクト構造

```
a2a_langgraph/
├── src/
│   ├── agents/           # エージェント実装
│   │   ├── math_agent.py
│   │   ├── research_agent.py
│   │   └── orchestrator.py
│   ├── a2a/             # A2Aプロトコル実装
│   │   ├── protocol.py
│   │   └── server.py
│   ├── mcp/             # MCPツール実装
│   │   ├── math_tools.py
│   │   └── research_tools.py
│   └── utils/           # ユーティリティ
│       ├── bedrock_client.py
│       ├── config.py
│       └── logging_config.py
├── examples/            # 使用例
│   └── client_example.py
├── tests/              # テストコード
│   └── test_agents.py
├── scripts/            # ユーティリティスクリプト
│   └── start_servers.py
├── config/             # 設定ファイル
├── pyproject.toml      # プロジェクト設定（uv対応）
├── uv.lock            # uvロックファイル
├── .python-version    # Pythonバージョン指定
└── README.md
```

## 🔧 設定

### LangGraphワークフロー

各エージェントはLangGraphを使用してワークフローを定義しています：

- **分析フェーズ**: ユーザーリクエストの分析
- **実行フェーズ**: タスクの実行（MCPツールの使用）
- **統合フェーズ**: 結果の統合とレスポンス生成

### A2Aプロトコル

エージェント間の通信は標準化されたA2Aプロトコルを使用：

- エージェントカードによる能力の公開
- JSON-RPCベースのメッセージ交換
- マルチターン会話のサポート
- コンテキストの保持

### Amazon Bedrock Claude 3.5 Sonnet

高度な推論能力を提供するLLMとして使用：

- 温度設定: 0.1（決定論的な応答）
- 最大トークン数: 4096
- リージョン: us-east-1（デフォルト）

## 🚨 トラブルシューティング

### よくある問題

1. **AWS認証エラー**
   - `.env`ファイルでAWS認証情報が正しく設定されているか確認
   - AWS Bedrockサービスへのアクセス権限があるか確認

2. **ポート競合エラー**
   - 他のアプリケーションが同じポートを使用していないか確認
   - `.env`ファイルでポート番号を変更

3. **エージェント接続エラー**
   - 全てのエージェントサーバーが起動しているか確認
   - ファイアウォール設定を確認

### ログの確認

ログレベルを調整してデバッグ情報を確認：

```bash
export LOG_LEVEL=DEBUG
uv run python scripts/start_servers.py
```

## 🤝 貢献

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📄 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。

## 🙏 謝辞

- [LangGraph](https://github.com/langchain-ai/langgraph) - エージェントワークフローフレームワーク
- [A2A Protocol](https://a2a.ai/) - エージェント間通信プロトコル
- [Amazon Bedrock](https://aws.amazon.com/bedrock/) - 大規模言語モデルサービス
- [Model Context Protocol](https://modelcontextprotocol.io/) - ツール統合プロトコル