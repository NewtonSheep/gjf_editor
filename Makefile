# Makefile para GJF Editor
# Comandos úteis para desenvolvimento e manutenção

.PHONY: help install dev-install clean lint format typecheck test run build venv setup

# Variáveis
PYTHON = .venv/bin/python
UV = uv
PROJECT_NAME = gjf_editor
SRC_DIR = src/$(PROJECT_NAME)
TEST_DIR = tests

# Cores para output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

# Ajuda - comando padrão
help:
	@echo "$(GREEN)=== GJF Editor - Comandos Disponíveis ===$(NC)"
	@echo ""
	@echo "$(YELLOW)Desenvolvimento:$(NC)"
	@echo "  $(GREEN)make setup$(NC)        - Configura ambiente do zero (venv + dependências)"
	@echo "  $(GREEN)make venv$(NC)         - Cria ambiente virtual com uv"
	@echo "  $(GREEN)make install$(NC)      - Instala dependências básicas"
	@echo "  $(GREEN)make dev-install$(NC)  - Instala dependências de desenvolvimento"
	@echo "  $(GREEN)make run$(NC)          - Executa o editor"
	@echo ""
	@echo "$(YELLOW)Qualidade de Código:$(NC)"
	@echo "  $(GREEN)make lint$(NC)         - Executa ruff para verificação de estilo"
	@echo "  $(GREEN)make format$(NC)       - Formata código com ruff format"
	@echo "  $(GREEN)make typecheck$(NC)    - Verifica tipos com mypy"
	@echo "  $(GREEN)make check$(NC)        - Executa todas as verificações (lint + typecheck)"
	@echo ""
	@echo "$(YELLOW)Testes:$(NC)"
	@echo "  $(GREEN)make test$(NC)         - Executa testes com pytest"
	@echo "  $(GREEN)make test-cov$(NC)     - Executa testes com cobertura"
	@echo ""
	@echo "$(YELLOW)Limpeza:$(NC)"
	@echo "  $(GREEN)make clean$(NC)        - Remove arquivos gerados"
	@echo "  $(GREEN)make clean-all$(NC)    - Remove tudo (incluindo venv)"
	@echo ""
	@echo "$(YELLOW)Build:$(NC)"
	@echo "  $(GREEN)make build$(NC)        - Cria distribuição do pacote"
	@echo ""

# Configuração inicial
setup: venv install dev-install
	@echo "$(GREEN)✓ Ambiente configurado com sucesso!$(NC)"
	@echo "$(YELLOW)Execute 'make run' para iniciar o editor.$(NC)"

# Ambiente virtual
venv:
	@echo "$(YELLOW)Criando ambiente virtual...$(NC)"
	@$(UV) venv
	@echo "$(GREEN)✓ Ambiente virtual criado em .venv$(NC)"

# Instalação de dependências básicas
install:
	@echo "$(YELLOW)Instalando dependências básicas...$(NC)"
	@$(UV) pip install -e .
	@echo "$(GREEN)✓ Dependências básicas instaladas$(NC)"

# Instalação de dependências de desenvolvimento
dev-install:
	@echo "$(YELLOW)Instalando dependências de desenvolvimento...$(NC)"
	@$(UV) pip install -e ".[dev]"
	@echo "$(GREEN)✓ Dependências de desenvolvimento instaladas$(NC)"

# Executar o editor
run:
	@echo "$(YELLOW)Iniciando GJF Editor...$(NC)"
	@$(PYTHON) -m $(PROJECT_NAME).cli

# Linting
lint:
	@echo "$(YELLOW)Executando linting com ruff...$(NC)"
	@$(PYTHON) -m ruff check $(SRC_DIR)
	@echo "$(GREEN)✓ Linting concluído$(NC)"

# Formatação
format:
	@echo "$(YELLOW)Formatando código com ruff...$(NC)"
	@$(PYTHON) -m ruff format $(SRC_DIR)
	@echo "$(GREEN)✓ Formatação concluída$(NC)"

# Verificação de tipos
typecheck:
	@echo "$(YELLOW)Verificando tipos com mypy...$(NC)"
	@$(PYTHON) -m mypy $(SRC_DIR)
	@echo "$(GREEN)✓ Verificação de tipos concluída$(NC)"

# Todas as verificações
check: lint typecheck
	@echo "$(GREEN)✓ Todas as verificações concluídas$(NC)"

# Testes
test:
	@echo "$(YELLOW)Executando testes...$(NC)"
	@$(PYTHON) -m pytest $(TEST_DIR) -v
	@echo "$(GREEN)✓ Testes concluídos$(NC)"

# Testes com cobertura
test-cov:
	@echo "$(YELLOW)Executando testes com cobertura...$(NC)"
	@$(PYTHON) -m pytest $(TEST_DIR) -v --cov=$(SRC_DIR) --cov-report=term-missing
	@echo "$(GREEN)✓ Testes com cobertura concluídos$(NC)"

# Build do pacote
build:
	@echo "$(YELLOW)Construindo pacote...$(NC)"
	@$(PYTHON) -m build
	@echo "$(GREEN)✓ Pacote construído em dist/$(NC)"

# Limpeza básica
clean:
	@echo "$(YELLOW)Limpando arquivos gerados...$(NC)"
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg-info/
	@rm -rf __pycache__/
	@rm -rf $(SRC_DIR)/__pycache__/
	@rm -rf $(TEST_DIR)/__pycache__/
	@rm -rf .pytest_cache/
	@rm -rf .mypy_cache/
	@rm -rf .ruff_cache/
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "$(GREEN)✓ Limpeza concluída$(NC)"

# Limpeza completa (incluindo venv)
clean-all: clean
	@echo "$(YELLOW)Removendo ambiente virtual...$(NC)"
	@rm -rf .venv/
	@echo "$(GREEN)✓ Ambiente virtual removido$(NC)"

# Comando para desenvolvimento rápido (formata + verifica + testa)
dev: format check test
	@echo "$(GREEN)✓ Desenvolvimento: todas as etapas concluídas$(NC)"