"""CLI entry point for GJF Editor"""

import sys
from pathlib import Path

from .backup import BackupSystem
from .interface import CLIInterface
from .keywords import KeywordManager
from .parser import GJFParser


def main() -> None:
    """Função principal"""
    try:
        # Inicializa componentes
        parser = GJFParser()

        # Usa dados do pacote
        data_dir = Path(__file__).parent / "data"
        keyword_manager = KeywordManager(data_dir)

        backup_system = BackupSystem()

        # Cria interface
        interface = CLIInterface(parser, keyword_manager, backup_system)

        # Executa wizard
        interface.run_wizard()

    except FileNotFoundError as e:
        print(f"Erro: {e}")
        print("Certifique-se de que o arquivo keywords.json está no pacote")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nPrograma interrompido pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"Erro inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
