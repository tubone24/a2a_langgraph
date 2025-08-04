# A2A Multi-Agent System - シーケンス図

このドキュメントは、A2A Multi-Agent Systemにおけるユーザーの入力「1+1」がorchestratorを通じてmath_agentで処理され、正しい計算結果「2」が返されるまでの詳細な処理フローを示しています。

## システム概要

- **Client**: ユーザーインターフェース（インタラクティブモード）
- **A2AServer**: A2Aプロトコルを使用したメッセージングサーバー
- **OrchestratorAgent**: マルチエージェントの調整を行うオーケストレーター
- **MathAgent**: 数学計算専門エージェント
- **LangGraph**: ワークフロー管理フレームワーク
- **BedrockClaudeClient**: AWS Bedrock Claudeクライアント

## 処理フロー

```mermaid
sequenceDiagram
    participant User as ユーザー
    participant Client as MultiAgentClient
    participant Server as A2AServer
    participant Orchestrator as OrchestratorAgent
    participant LangGraph as LangGraph Workflow
    participant MathAgent as MathAgent
    participant MathGraph as Math LangGraph
    participant BedrockClient as BedrockClaudeClient

    Note over User,BedrockClient: インタラクティブモード: "1+1" 入力、orchestrator選択

    %% 1. ユーザー入力とクライアント処理
    User->>Client: input("1+1")
    User->>Client: select_agent("orchestrator")
    Client->>Client: send_message_to_agent("orchestrator", "1+1")

    %% 2. A2Aプロトコルでのメッセージ送信
    Client->>Client: Message(role="user", parts=[MessagePart("1+1")])
    Client->>Client: SendMessageRequest(params=MessageSendParams(message))
    Client->>Server: POST /messages (A2A protocol)

    %% 3. サーバー側でのメッセージ処理
    Server->>Server: handle_message(request)
    Server->>Orchestrator: process_new_message(message)

    %% 4. Orchestratorでのメッセージ処理開始
    Orchestrator->>Orchestrator: extract text_content from message.parts
    Note right of Orchestrator: text_content = "1+1"

    %% 5. LangGraphワークフローの実行
    Orchestrator->>LangGraph: graph.ainvoke({"user_input": "1+1", "message_id": uuid})
    
    %% 6. analyze_user_request ノード
    LangGraph->>LangGraph: analyze_user_request(state)
    Note right of LangGraph: analysis_prompt = "以下のユーザーリクエストを分析..."
    
    LangGraph->>BedrockClient: invoke([HumanMessage(analysis_prompt)])
    Note right of BedrockClient: AWS認証エラーが発生
    BedrockClient-->>LangGraph: Exception: Unable to locate credentials
    
    LangGraph->>LangGraph: _extract_required_agents("分析エラーが発生しました")
    Note right of LangGraph: デフォルトで["math_agent"]を返す
    LangGraph->>LangGraph: state["required_agents"] = ["math_agent"]

    %% 7. coordinate_agents ノード
    LangGraph->>LangGraph: coordinate_agents(state)
    LangGraph->>Orchestrator: _delegate_to_agent("math_agent", "1+1")
    
    %% 8. Math Agentへの委譲
    Orchestrator->>Orchestrator: _call_math_agent("1+1")
    Orchestrator->>Orchestrator: Message(role="user", parts=[MessagePart("1+1")])
    
    %% 9. Math Agentの非同期実行
    Note right of Orchestrator: asyncio.run を使用して同期的に呼び出し
    Orchestrator->>MathAgent: process_new_message(message)
    
    %% 10. Math Agentでのメッセージ処理
    MathAgent->>MathAgent: extract text_content = "1+1"
    MathAgent->>MathGraph: graph.ainvoke({"user_input": "1+1", "message_id": uuid})
    
    %% 11. Math Agent の analyze_request ノード
    MathGraph->>MathGraph: analyze_request(state)
    Note right of MathGraph: "1+1" → task_type = "calculate"
    MathGraph->>MathGraph: state["task_type"] = "calculate"

    %% 12. Math Agent の execute_calculation ノード
    MathGraph->>MathGraph: execute_calculation(state)
    MathGraph->>MathAgent: _handle_calculation("1+1")
    
    %% 13. 安全な計算処理
    MathAgent->>MathAgent: clean_expression = "1+1"
    MathAgent->>MathAgent: re.match(r'^[\d\s+\-*/().,x×÷]+$', "1+1") → True
    MathAgent->>MathAgent: ast.parse("1+1", mode='eval')
    MathAgent->>MathAgent: safe_eval(ast_tree)
    Note right of MathAgent: AST評価: 1 + 1 = 2
    MathAgent->>MathAgent: return "1+1 = 2"
    
    MathGraph->>MathGraph: state["result"] = "1+1 = 2"
    MathGraph->>MathGraph: state["status"] = "completed"

    %% 14. Math Agent の generate_response ノード
    MathGraph->>MathGraph: generate_response(state)
    Note right of MathGraph: prompt = "数学的タスク: calculate\n計算結果: 1+1 = 2"
    
    MathGraph->>BedrockClient: invoke([HumanMessage(prompt)])
    Note right of BedrockClient: AWS認証エラーが発生
    BedrockClient-->>MathGraph: Exception: Unable to locate credentials
    
    MathGraph->>MathGraph: state["final_response"] = "計算結果: 1+1 = 2"
    MathGraph-->>MathAgent: return {"final_response": "計算結果: 1+1 = 2"}
    
    %% 15. Math Agentからの応答
    MathAgent-->>Orchestrator: return "計算結果: 1+1 = 2"
    Orchestrator->>LangGraph: agent_responses["math_agent"] = "計算結果: 1+1 = 2"

    %% 16. synthesize_results ノード
    LangGraph->>LangGraph: synthesize_results(state)
    Note right of LangGraph: synthesis_prompt = "ユーザーの質問: 1+1\n各エージェント: math_agent: 計算結果: 1+1 = 2"
    
    LangGraph->>BedrockClient: invoke([HumanMessage(synthesis_prompt)])
    Note right of BedrockClient: AWS認証エラーが発生
    BedrockClient-->>LangGraph: Exception: Unable to locate credentials
    
    %% 17. フォールバック応答の生成
    LangGraph->>LangGraph: combined_response = "**math_agentからの回答:**\n計算結果: 1+1 = 2"
    LangGraph->>LangGraph: state["final_response"] = combined_response
    
    %% 18. 最終応答の返却
    LangGraph-->>Orchestrator: return {"final_response": "**math_agentからの回答:**\n計算結果: 1+1 = 2"}
    Orchestrator-->>Server: return "**math_agentからの回答:**\n計算結果: 1+1 = 2"
    Server-->>Client: SendMessageResponse(result={"content": "**math_agentからの回答:**\n計算結果: 1+1 = 2"})
    Client-->>User: print("回答: **math_agentからの回答:**\n計算結果: 1+1 = 2")

    Note over User,BedrockClient: 結果: ユーザーは "1+1 = 2" の正しい計算結果を受け取る
```

## 重要な修正ポイント

### 1. Message オブジェクトの修正

**修正前の問題:**
```python
# role フィールドが不足していた
message = Message(
    messageId=str(uuid4()),
    parts=[MessagePart(kind="text", text=user_input)],
    contextId=None
)
```

**修正後:**
```python
# orchestrator.py の _call_math_agent メソッド
message = Message(
    role="user",  # ← これを追加
    messageId=str(uuid4()),
    parts=[MessagePart(kind="text", text=user_input)],
    contextId=None
)
```

### 2. 安全な計算処理の実装

**`math_agent.py` の `_handle_calculation` メソッド:**
```python
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
```

### 3. サポートされる演算子

```python
operators = {
    ast.Add: operator.add,      # +
    ast.Sub: operator.sub,      # -
    ast.Mult: operator.mul,     # *
    ast.Div: operator.truediv,  # /
    ast.Pow: operator.pow,      # **
    ast.Mod: operator.mod,      # %
    ast.USub: operator.neg,     # -x
    ast.UAdd: operator.pos,     # +x
}
```

### 4. エラーハンドリング

**AWS認証エラーへの対応:**
- BedrockClaudeClientの認証が失敗してもシステムは動作継続
- フォールバック機能により基本的な計算結果は返される
- LLMが使用できない場合でも数学計算機能は正常動作

**非同期処理の処理:**
```python
# orchestrator.py の _call_math_agent メソッド
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
```

## テスト結果

以下の計算が正常に動作することを確認済み：

- `2*3 = 6`
- `10+5 = 15`
- `100/4 = 25.0`
- `2*3+5 = 11`
- 微分計算（`x^2 の微分 = 2x`）
- 統計計算（平均値、中央値、標準偏差）

## システムアーキテクチャの利点

1. **モジュラー設計**: 各エージェントが独立して動作
2. **セキュアな計算**: ASTベースの安全な式評価
3. **エラー耐性**: AWS認証エラーが発生してもシステム継続動作
4. **拡張可能性**: 新しいエージェントの追加が容易
5. **A2Aプロトコル**: 標準化されたエージェント間通信

## 今後の改善点

1. **AWS認証の設定**: 環境変数の正しい設定でLLM機能を有効化
2. **エラーログの改善**: より詳細なエラー情報の提供
3. **パフォーマンス最適化**: 非同期処理の改善
4. **テストカバレッジ**: より多くの計算パターンのテスト追加