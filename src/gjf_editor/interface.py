from pathlib import Path
from typing import List, Optional

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .backup import BackupSystem
from .keywords import KeywordManager
from .parser import GJFParser, GJFSection

console = Console()


class CLIInterface:
    """Interface CLI wizard para edição de keywords Gaussian"""

    def __init__(
        self,
        parser: GJFParser,
        keyword_manager: KeywordManager,
        backup_system: BackupSystem,
    ):
        self.parser = parser
        self.keyword_manager = keyword_manager
        self.backup_system = backup_system
        self.current_file: Optional[Path] = None
        self.current_sections: List[GJFSection] = []

    def run_wizard(self) -> None:
        """Executa o wizard passo-a-passo"""
        self._show_welcome()

        while True:
            choice = self._main_menu()

            if choice == "select_file":
                self._select_file()
            elif choice == "edit_keywords":
                if not self.current_file:
                    self._show_error("Selecione um arquivo primeiro!")
                    continue
                self._edit_keywords_wizard()
            elif choice == "save_changes":
                if not self.current_file:
                    self._show_error("Nenhum arquivo carregado!")
                    continue
                self._save_changes()
            elif choice == "view_backups":
                self._view_backups()
            elif choice == "exit":
                if self._confirm_exit():
                    break

    def _show_welcome(self) -> None:
        """Exibe mensagem de boas-vindas"""
        console.clear()
        console.print(
            Panel.fit(
                "[bold cyan]GJF Editor - Editor de Keywords Gaussian[/bold cyan]\n"
                "Ferramenta para adicionar/remover keywords em arquivos .gjf",
                border_style="cyan",
            )
        )

    def _main_menu(self) -> str:
        """Menu principal"""
        choices = [
            questionary.Choice("Selecionar arquivo .gjf", value="select_file"),
            questionary.Choice(
                "Editar keywords",
                value="edit_keywords",
                disabled="Nenhum arquivo carregado" if not self.current_file else None,
            ),
            questionary.Choice(
                "Salvar alterações",
                value="save_changes",
                disabled="Nenhum arquivo carregado" if not self.current_file else None,
            ),
            questionary.Choice("Ver backups", value="view_backups"),
            questionary.Choice("Sair", value="exit"),
        ]

        answer = questionary.select(
            "Menu Principal:",
            choices=choices,
            instruction="(Use ↑↓ para navegar, Enter para selecionar)",
        ).ask()

        return answer or "exit"  # Fallback para sair se None

    def _select_file(self) -> None:
        """Seleção de arquivo .gjf"""
        # Encontra arquivos .gjf no diretório atual
        gjf_files = self.parser.find_all_gjf_files(Path.cwd())

        if not gjf_files:
            self._show_error("Nenhum arquivo .gjf encontrado no diretório atual!")
            return

        # Adiciona opção para voltar
        file_choices = [
            questionary.Choice(str(file.name), value=file) for file in gjf_files
        ]
        file_choices.append(questionary.Choice("← Voltar", value=None))

        selected = questionary.select(
            "Selecione um arquivo .gjf:",
            choices=file_choices,
            instruction="(Use ↑↓ para navegar, Enter para selecionar)",
        ).ask()

        if selected:
            self.current_file = selected
            self._load_file()
            self._show_success(f"Arquivo carregado: {selected.name}")

    def _load_file(self) -> None:
        """Carrega e analisa o arquivo atual"""
        try:
            if not self.current_file:
                return

            self.current_sections = self.parser.parse_file(self.current_file)

            # Exibe resumo
            table = Table(title=f"Análise: {self.current_file.name}")
            table.add_column("Seção", style="cyan")
            table.add_column("Tipo", style="magenta")
            table.add_column("Linhas", style="green")
            table.add_column("Keywords", style="yellow")

            for section in self.current_sections:
                section_type = (
                    section.keyword_section.section_type
                    if section.keyword_section
                    else "N/A"
                )
                keywords = (
                    section.keyword_section.keywords if section.keyword_section else []
                )

                table.add_row(
                    f"{section.section_number + 1}",
                    section_type,
                    f"{len(section.lines)}",
                    ", ".join(keywords) if keywords else "Nenhuma",
                )

            console.print(table)

        except Exception as e:
            self._show_error(f"Erro ao carregar arquivo: {e}")
            self.current_file = None
            self.current_sections = []

    def _edit_keywords_wizard(self) -> None:
        """Wizard para edição de keywords"""
        if not self.current_sections:
            self._show_error("Nenhuma seção encontrada no arquivo!")
            return

        # Seleciona seção para editar
        section_choices = []
        for i, section in enumerate(self.current_sections):
            if section.keyword_section:
                desc = f"Seção {i + 1}: {section.keyword_section.section_type.upper()}"
                keywords = ", ".join(section.keyword_section.keywords[:3])
                if len(section.keyword_section.keywords) > 3:
                    keywords += "..."
                desc += f" ({keywords})"
            else:
                desc = f"Seção {i + 1}: Sem keywords"

            section_choices.append(questionary.Choice(desc, value=section))

        section_choices.append(questionary.Choice("← Voltar", value=None))

        selected_section = questionary.select(
            "Selecione uma seção para editar:",
            choices=section_choices,
            instruction="(Use ↑↓ para navegar, Enter para selecionar)",
        ).ask()

        if not selected_section:
            return

        # Menu de edição da seção
        while True:
            self._show_section_details(selected_section)

            edit_choices = [
                questionary.Choice("Adicionar keywords", value="add"),
                questionary.Choice("Remover keywords", value="remove"),
                questionary.Choice(
                    "Editar parâmetros de keywords", value="edit_params"
                ),
                questionary.Choice("Ver todas keywords disponíveis", value="browse"),
                questionary.Choice("← Voltar ao menu anterior", value="back"),
            ]

            action = questionary.select(
                "O que deseja fazer?", choices=edit_choices
            ).ask()

            if action == "back":
                break
            elif action == "add":
                self._add_keywords(selected_section)
            elif action == "remove":
                self._remove_keywords(selected_section)
            elif action == "edit_params":
                self._edit_parameters(selected_section)
            elif action == "browse":
                self._browse_keywords(selected_section)

    def _show_section_details(self, section: GJFSection) -> None:
        """Exibe detalhes de uma seção"""
        console.clear()

        if section.keyword_section:
            table = Table(
                title=f"Seção {section.section_number + 1} - {section.keyword_section.section_type.upper()}"
            )
            table.add_column("Keyword", style="cyan")
            table.add_column("Descrição", style="white")
            table.add_column("Parâmetros", style="yellow")

            for kw in section.keyword_section.keywords:
                kw_info = self.keyword_manager.get_keyword(kw)
                if kw_info:
                    desc = kw_info.description
                    params = section.keyword_section.parameters.get(kw, "")
                else:
                    desc = "Desconhecida"
                    params = section.keyword_section.parameters.get(kw, "")

                table.add_row(kw, desc, str(params))

            console.print(table)
        else:
            console.print("[yellow]Esta seção não contém keywords.[/yellow]")

    def _add_keywords(self, section: GJFSection) -> None:
        """Adiciona keywords a uma seção"""
        if not section.keyword_section:
            self._show_error("Esta seção não tem linha de keywords!")
            return

        # Menu hierárquico de categorias
        categories = self.keyword_manager.get_all_categories()
        category_choices = [
            questionary.Choice(name, value=cat_id) for cat_id, name in categories
        ]
        category_choices.append(questionary.Choice("← Voltar", value=None))

        selected_category = questionary.select(
            "Selecione uma categoria:", choices=category_choices
        ).ask()

        if not selected_category:
            return

        # Filtra keywords já presentes
        existing_keywords = section.keyword_section.keywords
        available_keywords = self.keyword_manager.get_keywords_by_category(
            selected_category
        )

        # Remove keywords já presentes
        available_keywords = [
            kw for kw in available_keywords if kw.name not in existing_keywords
        ]

        if not available_keywords:
            self._show_info("Todas as keywords desta categoria já estão presentes!")
            return

        # Cria choices para seleção múltipla com opção de voltar
        keyword_choices = []
        for kw_info in available_keywords:
            # Verifica compatibilidade
            is_compatible, warnings = self.keyword_manager.check_compatibility(
                existing_keywords, kw_info.name
            )

            # Formata display com ícone de compatibilidade
            icon = "✅" if is_compatible else "⚠️"
            display = f"{icon} {kw_info.name} - {kw_info.description}"

            if warnings and "Recomendado" not in warnings[0]:
                display += f" [red]({warnings[0]})[/red]"

            keyword_choices.append(
                questionary.Choice(
                    display,
                    value=kw_info.name,
                    disabled="Incompatível" if not is_compatible else None,
                )
            )

        # Adiciona opção de voltar à seleção de categoria
        keyword_choices.append(
            questionary.Choice("← Voltar à seleção de categoria", value=None)
        )

        selected_keywords = questionary.checkbox(
            "Selecione keywords para adicionar:",
            choices=keyword_choices,
            instruction="(Use ↑↓ para navegar, Espaço para selecionar, Enter para confirmar)",
        ).ask()

        if selected_keywords:
            # Remove None da lista se presente (opção de voltar)
            selected_keywords = [kw for kw in selected_keywords if kw is not None]

            if not selected_keywords:
                # Usuário selecionou apenas a opção de voltar
                return

            # Adiciona keywords selecionadas
            new_keywords = existing_keywords + selected_keywords

            # Atualiza seção
            updated_lines = self.parser.update_keyword_section(section, new_keywords)
            section.lines = updated_lines

            # Atualiza keyword_section
            section.keyword_section.keywords = new_keywords

            self._show_success(f"Keywords adicionadas: {', '.join(selected_keywords)}")

    def _remove_keywords(self, section: GJFSection) -> None:
        """Remove keywords de uma seção"""
        if not section.keyword_section or not section.keyword_section.keywords:
            self._show_error("Não há keywords para remover!")
            return

        # Cria choices para seleção múltipla com opção de cancelar
        keyword_choices = []
        for kw in section.keyword_section.keywords:
            kw_info = self.keyword_manager.get_keyword(kw)
            if kw_info:
                display = f"{kw} - {kw_info.description}"
            else:
                display = kw

            keyword_choices.append(questionary.Choice(display, value=kw))

        # Adiciona opção de cancelar
        keyword_choices.append(questionary.Choice("← Cancelar e voltar", value=None))

        selected_keywords = questionary.checkbox(
            "Selecione keywords para remover:",
            choices=keyword_choices,
            instruction="(Use ↑↓ para navegar, Espaço para selecionar, Enter para confirmar)",
        ).ask()

        if selected_keywords is None:
            # Usuário cancelou
            return

        if selected_keywords:
            # Remove None da lista se presente
            selected_keywords = [kw for kw in selected_keywords if kw is not None]

            if not selected_keywords:
                # Usuário selecionou apenas a opção de cancelar
                return

            # Remove keywords selecionadas
            new_keywords = [
                kw
                for kw in section.keyword_section.keywords
                if kw not in selected_keywords
            ]

            # Atualiza seção
            updated_lines = self.parser.update_keyword_section(section, new_keywords)
            section.lines = updated_lines

            # Atualiza keyword_section
            section.keyword_section.keywords = new_keywords

            self._show_success(f"Keywords removidas: {', '.join(selected_keywords)}")

    def _edit_parameters(self, section: GJFSection) -> None:
        """Edita parâmetros de keywords em uma seção"""
        if not section.keyword_section or not section.keyword_section.keywords:
            self._show_error("Não há keywords para editar!")
            return

        # Filtra keywords que têm parâmetros
        keywords_with_params = []
        for kw in section.keyword_section.keywords:
            kw_info = self.keyword_manager.get_keyword(kw)
            if kw_info and (
                kw_info.requires_parameters or kw in section.keyword_section.parameters
            ):
                keywords_with_params.append(kw)

        if not keywords_with_params:
            self._show_info("Nenhuma keyword com parâmetros para editar!")
            return

        # Menu para selecionar qual keyword editar
        keyword_choices = []
        for kw in keywords_with_params:
            kw_info = self.keyword_manager.get_keyword(kw)
            param_str = section.keyword_section.parameters.get(kw, "sem parâmetros")
            if kw_info:
                display = f"{kw} - {kw_info.description} ({param_str})"
            else:
                display = f"{kw} ({param_str})"
            keyword_choices.append(questionary.Choice(display, value=kw))

        keyword_choices.append(questionary.Choice("← Voltar", value=None))

        selected_keyword = questionary.select(
            "Selecione uma keyword para editar parâmetros:",
            choices=keyword_choices,
            instruction="(Use ↑↓ para navegar, Enter para selecionar)",
        ).ask()

        if not selected_keyword:
            return

        # Obtém parâmetros atuais
        current_param_str = section.keyword_section.parameters.get(selected_keyword)
        if current_param_str is None:
            current_param_str = selected_keyword
        current_params = self.keyword_manager.extract_current_parameters(
            str(current_param_str)
        )

        # Obtém template da keyword (não usado diretamente, mas mantido para consistência)
        _ = self.keyword_manager.get_parameter_template(selected_keyword)

        console.clear()
        console.print(
            f"[bold cyan]Editando parâmetros de '{selected_keyword}':[/bold cyan]"
        )
        console.print(f"[yellow]Formato atual: {current_param_str}[/yellow]")
        console.print()

        # Coleta novos valores para cada parâmetro
        new_params = {}
        for param_name, current_value in current_params.items():
            # Obtém opções disponíveis para este parâmetro
            options = self.keyword_manager.get_parameter_options(
                selected_keyword, param_name
            )

            if options:
                # Menu de seleção para parâmetros com opções pré-definidas
                option_choices = [
                    questionary.Choice(str(opt), value=str(opt)) for opt in options
                ]
                option_choices.append(
                    questionary.Choice("← Cancelar edição", value=None)
                )

                new_value = questionary.select(
                    f"Parâmetro '{param_name}' (atual: {current_value}):",
                    choices=option_choices,
                    instruction="(Use ↑↓ para navegar, Enter para selecionar)",
                ).ask()

                if new_value is None:
                    # Usuário cancelou a edição
                    self._show_info("Edição cancelada.")
                    return
            else:
                # Entrada de texto livre para parâmetros sem opções pré-definidas
                # com opção clara de cancelar
                new_value = questionary.text(
                    f"Parâmetro '{param_name}' (atual: {current_value}):",
                    default=str(current_value),
                    instruction="(Deixe em branco e pressione Enter para cancelar a edição deste parâmetro)",
                ).ask()

                if new_value is None or new_value.strip() == "":
                    # Usuário cancelou a edição deste parâmetro
                    # Pergunta se quer cancelar toda a edição ou apenas este parâmetro
                    cancel_choice = questionary.select(
                        f"Deseja cancelar a edição do parâmetro '{param_name}' ou toda a operação?",
                        choices=[
                            questionary.Choice(
                                f"Cancelar apenas '{param_name}' (manter valor atual)",
                                value="param_only",
                            ),
                            questionary.Choice(
                                "Cancelar toda a edição da keyword", value="all"
                            ),
                            questionary.Choice(
                                "Voltar a editar este parâmetro", value="retry"
                            ),
                        ],
                        default="param_only",
                    ).ask()

                    if cancel_choice == "all":
                        self._show_info("Edição cancelada.")
                        return
                    elif cancel_choice == "retry":
                        # Volta a editar este parâmetro
                        continue
                    else:
                        # Mantém valor atual e continua com próximo parâmetro
                        new_params[param_name] = current_value
                        continue

            new_params[param_name] = new_value

        # Gera nova string de parâmetro
        new_param_str = self.keyword_manager.update_parameter_string(
            str(current_param_str), new_params
        )

        console.print()
        console.print("[bold green]Preview da alteração:[/bold green]")
        console.print(f"  Antes: {current_param_str}")
        console.print(f"  Depois: {new_param_str}")
        console.print()

        # Confirmação
        confirm = questionary.confirm(
            "Deseja aplicar estas alterações?", default=True
        ).ask()

        if confirm:
            # Atualiza a seção
            updated_lines = self.parser.update_keyword_parameter(
                section, selected_keyword, new_param_str
            )
            section.lines = updated_lines

            # Atualiza o dicionário de parâmetros
            section.keyword_section.parameters[selected_keyword] = new_param_str

            self._show_success(f"Parâmetros de '{selected_keyword}' atualizados!")
        else:
            self._show_info("Alterações descartadas.")

    def _browse_keywords(self, section: GJFSection) -> None:
        """Navega por todas as keywords disponíveis"""
        console.clear()

        table = Table(title="Todas as Keywords Disponíveis")
        table.add_column("Categoria", style="cyan")
        table.add_column("Keyword", style="magenta")
        table.add_column("Descrição", style="white")
        table.add_column("Status", style="yellow")

        categories = self.keyword_manager.get_all_categories()
        existing_keywords = (
            section.keyword_section.keywords if section.keyword_section else []
        )

        for cat_id, cat_name in categories:
            keywords = self.keyword_manager.get_keywords_by_category(cat_id)

            for kw_info in keywords:
                if kw_info.name in existing_keywords:
                    status = "[green]✓ Presente[/green]"
                else:
                    is_compatible, _ = self.keyword_manager.check_compatibility(
                        existing_keywords, kw_info.name
                    )
                    status = (
                        "[yellow]Disponível[/yellow]"
                        if is_compatible
                        else "[red]Incompatível[/red]"
                    )

                table.add_row(cat_name, kw_info.name, kw_info.description, status)

        console.print(table)
        console.print()

        # Adiciona opção de voltar
        back_choice = questionary.select(
            "O que deseja fazer?",
            choices=[
                questionary.Choice("← Voltar ao menu anterior", value="back"),
                questionary.Choice("Continuar visualizando", value="continue"),
            ],
            default="back",
        ).ask()

        if back_choice == "back":
            return

    def _save_changes(self) -> None:
        """Salva alterações no arquivo"""
        if not self.current_sections:
            return

        # Mostra preview das alterações
        console.clear()
        console.print("[bold cyan]Preview das Alterações:[/bold cyan]")

        for section in self.current_sections:
            if section.keyword_section:
                console.print(f"\n[bold]Seção {section.section_number + 1}:[/bold]")
                console.print(f"  Original: {section.keyword_section.original_line}")

                # Reconstroi linha atual
                updated_lines = self.parser.update_keyword_section(
                    section, section.keyword_section.keywords
                )
                keyword_line_index = (
                    section.keyword_section.line_number - section.start_line - 1
                )
                if 0 <= keyword_line_index < len(updated_lines):
                    console.print(
                        f"  Atual:    {updated_lines[keyword_line_index].strip()}"
                    )

        # Confirmação
        confirm = questionary.confirm(
            "Deseja salvar as alterações?", default=False
        ).ask()

        if confirm:
            try:
                if not self.current_file:
                    self._show_error("Nenhum arquivo selecionado!")
                    return

                # Cria backup
                backup_path = self.backup_system.create_backup(self.current_file)

                # Salva arquivo
                all_lines = []
                for section in self.current_sections:
                    all_lines.extend(section.lines)

                with open(self.current_file, "w") as f:
                    f.writelines(all_lines)

                self._show_success(
                    f"Alterações salvas! Backup criado: {backup_path.name}"
                )

            except Exception as e:
                self._show_error(f"Erro ao salvar arquivo: {e}")
        else:
            self._show_info("Alterações descartadas.")

    def _view_backups(self) -> None:
        """Visualiza backups disponíveis"""
        console.clear()

        backup_info = self.backup_system.get_backup_info()

        table = Table(title="Sistema de Backup")
        table.add_column("Informação", style="cyan")
        table.add_column("Valor", style="white")

        table.add_row("Diretório", str(backup_info.get("backup_dir", "")))
        table.add_row("Total de backups", str(backup_info.get("total_backups", 0)))
        disk_usage = backup_info.get("disk_usage_mb", 0)
        disk_usage_float = (
            float(disk_usage) if isinstance(disk_usage, (int, float)) else 0.0
        )
        table.add_row("Uso de disco", f"{disk_usage_float:.2f} MB")

        console.print(table)

        backups_by_file = backup_info.get("backups_by_file", {})
        if backups_by_file and isinstance(backups_by_file, dict):
            console.print("\n[bold]Backups por arquivo:[/bold]")
            for file_name, count in backups_by_file.items():
                console.print(f"  {file_name}: {count} backup(s)")

        console.print()

        # Adiciona opção de voltar
        back_choice = questionary.select(
            "O que deseja fazer?",
            choices=[
                questionary.Choice("← Voltar ao menu principal", value="back"),
                questionary.Choice("Continuar visualizando", value="continue"),
            ],
            default="back",
        ).ask()

        if back_choice == "back":
            return

    def _confirm_exit(self) -> bool:
        """Confirma saída do programa"""
        if self.current_file and self._has_unsaved_changes():
            confirm = questionary.confirm(
                "Tem alterações não salvas. Deseja realmente sair?", default=False
            ).ask()
            return confirm or False  # Fallback para False se None
        return True

    def _has_unsaved_changes(self) -> bool:
        """Verifica se há alterações não salvas"""
        # Implementação simplificada - sempre retorna True se houver seções carregadas
        return bool(self.current_sections)

    def _show_error(self, message: str) -> None:
        """Exibe mensagem de erro"""
        console.print(f"[bold red]Erro:[/bold red] {message}")
        questionary.press_any_key_to_continue(
            "Pressione qualquer tecla para continuar..."
        ).ask()

    def _show_success(self, message: str) -> None:
        """Exibe mensagem de sucesso"""
        console.print(f"[bold green]✓[/bold green] {message}")
        questionary.press_any_key_to_continue(
            "Pressione qualquer tecla para continuar..."
        ).ask()

    def _show_info(self, message: str) -> None:
        """Exibe mensagem informativa"""
        console.print(f"[bold blue]ℹ[/bold blue] {message}")
        questionary.press_any_key_to_continue(
            "Pressione qualquer tecla para continuar..."
        ).ask()
