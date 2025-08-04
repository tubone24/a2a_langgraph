.PHONY: install install-dev sync format lint test clean run-servers run-math run-research run-orchestrator run-client

# デフォルトターゲット
all: install

# uvのインストール確認
check-uv:
	@command -v uv >/dev/null 2>&1 || { echo "uvがインストールされていません。https://github.com/astral-sh/uv からインストールしてください。"; exit 1; }

# 依存関係のインストール
install: check-uv
	uv sync

# 開発依存関係を含めてインストール
install-dev: check-uv
	uv sync --dev

# 依存関係の同期
sync: check-uv
	uv sync

# コードフォーマット
format: check-uv
	uv run black src/ tests/ examples/ scripts/
	uv run ruff check --fix src/ tests/ examples/ scripts/

# Lintチェック
lint: check-uv
	uv run ruff check src/ tests/ examples/ scripts/
	uv run black --check src/ tests/ examples/ scripts/

# テスト実行
test: check-uv
	uv run pytest tests/ -v

# 単体テスト
test-unit: check-uv
	uv run python tests/test_agents.py

# クリーンアップ
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

# 全サーバーの起動
run-servers: check-uv
	uv run python scripts/start_servers.py

# 個別サーバーの起動
run-math: check-uv
	uv run python -m src.a2a.server math

run-research: check-uv
	uv run python -m src.a2a.server research

run-orchestrator: check-uv
	uv run python -m src.a2a.server orchestrator

# クライアントの実行
run-client: check-uv
	uv run python examples/client_example.py

# 環境変数の設定確認
check-env:
	@if [ ! -f .env ]; then \
		echo ".envファイルが見つかりません。.env.exampleをコピーして作成してください。"; \
		echo "cp .env.example .env"; \
		exit 1; \
	fi
	@echo ".envファイルが見つかりました。"
	@grep -E "^AWS_REGION|^AWS_ACCESS_KEY_ID|^AWS_SECRET_ACCESS_KEY" .env || echo "警告: AWS認証情報が設定されていない可能性があります。"

# ヘルプ
help:
	@echo "利用可能なコマンド:"
	@echo "  make install        - 依存関係のインストール"
	@echo "  make install-dev    - 開発依存関係を含めてインストール"
	@echo "  make sync          - 依存関係の同期"
	@echo "  make format        - コードのフォーマット"
	@echo "  make lint          - Lintチェック"
	@echo "  make test          - 全テストの実行"
	@echo "  make test-unit     - 単体テストの実行"
	@echo "  make clean         - キャッシュファイルの削除"
	@echo "  make run-servers   - 全サーバーの起動"
	@echo "  make run-math      - Math Agentサーバーの起動"
	@echo "  make run-research  - Research Agentサーバーの起動"
	@echo "  make run-orchestrator - Orchestratorサーバーの起動"
	@echo "  make run-client    - クライアントの実行"
	@echo "  make check-env     - 環境変数の確認"
	@echo "  make help          - このヘルプを表示"