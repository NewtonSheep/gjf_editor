import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class BackupSystem:
    """Sistema de backup para arquivos .gjf"""

    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self._ensure_backup_dir()

    def _ensure_backup_dir(self) -> None:
        """Garante que o diretório de backup existe"""
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self, gjf_path: Path) -> Path:
        """
        Cria um backup do arquivo .gjf

        Args:
            gjf_path: Caminho para o arquivo .gjf original

        Returns:
            Caminho para o arquivo de backup criado
        """
        if not gjf_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {gjf_path}")

        # Gera nome único para o backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{gjf_path.stem}_{timestamp}.gjf.bak"
        backup_path = self.backup_dir / backup_name

        # Copia o arquivo
        shutil.copy2(gjf_path, backup_path)

        return backup_path

    def get_backup_files(self, original_name: Optional[str] = None) -> List[Path]:
        """
        Lista arquivos de backup

        Args:
            original_name: Nome base do arquivo original (opcional)

        Returns:
            Lista de caminhos para arquivos de backup
        """
        if original_name:
            # Filtra por nome base
            pattern = f"*{original_name}*.gjf.bak"
            return sorted(self.backup_dir.glob(pattern))
        else:
            # Todos os backups
            return sorted(self.backup_dir.glob("*.gjf.bak"))

    def get_latest_backup(self, original_name: str) -> Optional[Path]:
        """
        Obtém o backup mais recente para um arquivo específico

        Args:
            original_name: Nome base do arquivo original

        Returns:
            Caminho para o backup mais recente ou None
        """
        backups = self.get_backup_files(original_name)
        return backups[-1] if backups else None

    def restore_backup(
        self, backup_path: Path, target_path: Path, overwrite: bool = False
    ) -> bool:
        """
        Restaura um backup para o local original

        Args:
            backup_path: Caminho para o arquivo de backup
            target_path: Caminho de destino (normalmente o original)
            overwrite: Se True, sobrescreve o arquivo de destino

        Returns:
            True se restaurado com sucesso, False caso contrário
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup não encontrado: {backup_path}")

        if target_path.exists() and not overwrite:
            return False

        shutil.copy2(backup_path, target_path)
        return True

    def cleanup_old_backups(self, keep_last_n: int = 10) -> List[Path]:
        """
        Remove backups antigos, mantendo apenas os N mais recentes

        Args:
            keep_last_n: Número de backups mais recentes para manter

        Returns:
            Lista de backups removidos
        """
        all_backups = self.get_backup_files()

        if len(all_backups) <= keep_last_n:
            return []

        # Ordena por data de modificação (mais antigos primeiro)
        backups_by_mtime = sorted(all_backups, key=lambda p: p.stat().st_mtime)

        # Mantém os N mais recentes
        to_keep = backups_by_mtime[-keep_last_n:]
        to_remove = [b for b in all_backups if b not in to_keep]

        # Remove os antigos
        removed = []
        for backup in to_remove:
            try:
                backup.unlink()
                removed.append(backup)
            except Exception as e:
                print(f"Erro ao remover backup {backup}: {e}")

        return removed

    def get_backup_info(self) -> Dict[str, object]:
        """Retorna informações sobre o sistema de backup"""
        all_backups = self.get_backup_files()

        # Agrupa por arquivo original
        backups_by_file: dict[str, list[Path]] = {}
        for backup in all_backups:
            # Extrai nome base (remove timestamp e extensão)
            parts = backup.stem.split("_")
            if len(parts) >= 2:
                # Tenta reconstruir nome original (pode não ser perfeito)
                original_parts = parts[:-6]  # Remove timestamp (YYYYMMDD_HHMMSS)
                original_name = "_".join(original_parts)
            else:
                original_name = backup.stem

            if original_name not in backups_by_file:
                backups_by_file[original_name] = []
            backups_by_file[original_name].append(backup)

        return {
            "backup_dir": str(self.backup_dir),
            "total_backups": len(all_backups),
            "backups_by_file": {k: len(v) for k, v in backups_by_file.items()},
            "disk_usage_mb": sum(b.stat().st_size for b in all_backups) / (1024 * 1024),
        }
