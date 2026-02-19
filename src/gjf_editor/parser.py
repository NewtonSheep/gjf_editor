import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class KeywordSection:
    """Representa uma seção de keywords em um arquivo .gjf"""

    line_number: int
    original_line: str
    section_type: str  # 'opt', 'td', 'unknown'
    keywords: List[str]
    parameters: Dict[str, str]  # Parâmetros como td=(nstates=50,root=1)


@dataclass
class GJFSection:
    """Representa uma seção completa de cálculo em um arquivo .gjf"""

    section_number: int
    start_line: int
    end_line: int
    keyword_section: Optional[KeywordSection]
    lines: List[str]
    is_link_section: bool


class GJFParser:
    """Parser para arquivos de entrada Gaussian (.gjf)"""

    def __init__(self) -> None:
        self.link_pattern = re.compile(r"^--Link(\d+)--$")
        self.keyword_line_pattern = re.compile(r"^#p\s+(.+)$")
        self.opt_pattern = re.compile(r"\bopt\b")
        self.td_pattern = re.compile(r"\btd=\([^)]+\)")

    def parse_file(self, file_path: Path) -> List[GJFSection]:
        """Parseia um arquivo .gjf e retorna suas seções"""
        with open(file_path, "r") as f:
            lines = f.readlines()

        sections = []
        current_section_start = 0
        section_number = 0

        for i, line in enumerate(lines):
            # Verifica se é início de nova seção (--LinkX--)
            if self.link_pattern.match(line.strip()):
                # Finaliza seção atual
                if current_section_start < i:
                    section = self._create_section(
                        section_number, current_section_start, i, lines
                    )
                    sections.append(section)
                    section_number += 1

                # Inicia nova seção (a partir da próxima linha)
                current_section_start = i + 1

        # Adiciona última seção (se houver)
        if current_section_start < len(lines):
            section = self._create_section(
                section_number, current_section_start, len(lines), lines
            )
            sections.append(section)

        # Se não encontrou seções Link, trata o arquivo inteiro como uma seção
        if not sections:
            section = self._create_section(0, 0, len(lines), lines)
            sections.append(section)

        return sections

    def _create_section(
        self, section_num: int, start: int, end: int, lines: List[str]
    ) -> GJFSection:
        """Cria um objeto GJFSection a partir do intervalo de linhas"""
        section_lines = lines[start:end]
        keyword_section = self._find_keyword_section(section_lines, start)

        return GJFSection(
            section_number=section_num,
            start_line=start,
            end_line=end,
            keyword_section=keyword_section,
            lines=section_lines,
            is_link_section=(section_num > 0),  # Primeira seção não é Link
        )

    def _find_keyword_section(
        self, lines: List[str], start_offset: int
    ) -> Optional[KeywordSection]:
        """Encontra a linha de keywords dentro de uma seção"""
        for i, line in enumerate(lines):
            match = self.keyword_line_pattern.match(line.strip())
            if match:
                keyword_line = match.group(1)
                line_number = start_offset + i + 1  # +1 porque linhas começam em 1

                # Determina tipo de seção
                section_type = "unknown"
                if self.opt_pattern.search(keyword_line):
                    section_type = "opt"
                elif self.td_pattern.search(keyword_line):
                    section_type = "td"

                # Parseia keywords e parâmetros
                keywords, parameters = self._parse_keywords(keyword_line)

                return KeywordSection(
                    line_number=line_number,
                    original_line=line.strip(),
                    section_type=section_type,
                    keywords=keywords,
                    parameters=parameters,
                )

        return None

    def _parse_keywords(self, keyword_line: str) -> Tuple[List[str], Dict[str, str]]:
        """Parseia uma linha de keywords em lista de keywords e parâmetros"""
        keywords = []
        parameters = {}

        # Divide por espaços, mas preserva parênteses
        tokens = []
        current_token = ""
        paren_depth = 0

        for char in keyword_line:
            if char == "(":
                paren_depth += 1
                current_token += char
            elif char == ")":
                paren_depth -= 1
                current_token += char
            elif char == " " and paren_depth == 0:
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
            else:
                current_token += char

        if current_token:
            tokens.append(current_token)

        # Processa tokens
        for token in tokens:
            # Verifica se é parâmetro com = (ex: td=(nstates=50,root=1))
            if "=" in token and "(" in token and ")" in token:
                # Extrai nome do parâmetro (antes do =)
                param_name = token.split("=", 1)[0]
                parameters[param_name] = token
                keywords.append(param_name)
            elif "=" in token:
                # Parâmetro simples (ex: empiricaldispersion=gd3)
                param_name = token.split("=", 1)[0]
                param_value = token.split("=", 1)[1]
                parameters[param_name] = param_value
                keywords.append(param_name)
            else:
                # Keyword simples (ex: opt, freq)
                keywords.append(token)

        return keywords, parameters

    def parse_keyword_with_params(
        self, keyword_string: str
    ) -> Tuple[str, Dict[str, str]]:
        """
        Parseia uma string de keyword com parâmetros de forma mais robusta

        Args:
            keyword_string: String da keyword (ex: "scrf=(smd,solvent=water)")

        Returns:
            Tuple (nome_da_keyword, parâmetros)
        """
        if "=" not in keyword_string:
            return keyword_string, {}

        # Separa nome e parâmetros
        if "(" in keyword_string and ")" in keyword_string:
            # Formato: keyword=(param1=value1,param2=value2)
            name_end = keyword_string.find("=")
            name = keyword_string[:name_end]

            params_start = keyword_string.find("(") + 1
            params_end = keyword_string.find(")")
            params_str = keyword_string[params_start:params_end]

            params = {}
            # Processa parâmetros separados por vírgula
            param_parts = []
            current_part = ""
            in_quotes = False
            paren_depth = 0

            for char in params_str:
                if char == '"' or char == "'":
                    in_quotes = not in_quotes
                    current_part += char
                elif char == "(":
                    paren_depth += 1
                    current_part += char
                elif char == ")":
                    paren_depth -= 1
                    current_part += char
                elif char == "," and not in_quotes and paren_depth == 0:
                    param_parts.append(current_part.strip())
                    current_part = ""
                else:
                    current_part += char

            if current_part:
                param_parts.append(current_part.strip())

            # Processa cada parte do parâmetro
            for part in param_parts:
                if "=" in part:
                    key, value = part.split("=", 1)
                    params[key.strip()] = value.strip()
                else:
                    # Parâmetro sem valor (ex: "smd" em "scrf=(smd,solvent=water)")
                    params[part] = ""

            return name, params
        else:
            # Formato simples: keyword=value
            name, value = keyword_string.split("=", 1)
            return name, {"value": value}

    def update_keyword_section(
        self, section: GJFSection, new_keywords: List[str]
    ) -> List[str]:
        """Atualiza a linha de keywords em uma seção com novas keywords"""
        if not section.keyword_section:
            return section.lines.copy()

        # Reconstroi a linha de keywords
        keyword_line_parts = []

        for keyword in new_keywords:
            if keyword in section.keyword_section.parameters:
                # Adiciona parâmetro completo
                keyword_line_parts.append(section.keyword_section.parameters[keyword])
            else:
                # Adiciona keyword simples
                keyword_line_parts.append(keyword)

        new_keyword_line = f"#p {' '.join(keyword_line_parts)}"

        # Atualiza a linha na seção
        updated_lines = section.lines.copy()
        keyword_line_index = (
            section.keyword_section.line_number - section.start_line - 1
        )

        if 0 <= keyword_line_index < len(updated_lines):
            updated_lines[keyword_line_index] = new_keyword_line + "\n"

        return updated_lines

    def update_keyword_parameter(
        self, section: GJFSection, keyword_name: str, new_parameter_string: str
    ) -> List[str]:
        """
        Atualiza o parâmetro de uma keyword específica em uma seção

        Args:
            section: Seção a ser atualizada
            keyword_name: Nome da keyword
            new_parameter_string: Nova string de parâmetro (ex: "td=(nstates=30,root=2)")

        Returns:
            Lista de linhas atualizadas
        """
        if not section.keyword_section:
            return section.lines.copy()

        # Atualiza o parâmetro no dicionário
        section.keyword_section.parameters[keyword_name] = new_parameter_string

        # Reconstroi a linha de keywords
        keyword_line_parts = []
        for kw in section.keyword_section.keywords:
            if kw in section.keyword_section.parameters:
                keyword_line_parts.append(section.keyword_section.parameters[kw])
            else:
                keyword_line_parts.append(kw)

        new_keyword_line = f"#p {' '.join(keyword_line_parts)}"

        # Atualiza a linha na seção
        updated_lines = section.lines.copy()
        keyword_line_index = (
            section.keyword_section.line_number - section.start_line - 1
        )

        if 0 <= keyword_line_index < len(updated_lines):
            updated_lines[keyword_line_index] = new_keyword_line + "\n"

        return updated_lines

    def find_all_gjf_files(self, directory: Path) -> List[Path]:
        """Encontra todos os arquivos .gjf em um diretório"""
        return list(directory.glob("*.gjf"))
