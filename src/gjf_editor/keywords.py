import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class KeywordInfo:
    """Informações sobre uma keyword Gaussian"""

    name: str
    description: str
    category: str
    requires_parameters: bool = False
    compatible_with: Optional[List[str]] = None
    common_parameters: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.compatible_with is None:
            self.compatible_with = []
        if self.common_parameters is None:
            self.common_parameters = {}


@dataclass
class ParameterTemplate:
    """Template para keywords que requerem parâmetros"""

    keyword: str
    template: str
    description: str
    defaults: Dict[str, Any]
    options: Optional[Dict[str, List[str]]] = None

    def __post_init__(self) -> None:
        if self.options is None:
            self.options = {}


class KeywordManager:
    """Gerenciador de keywords Gaussian com estrutura hierárquica"""

    def __init__(self, data_dir: Path = Path("data")):
        self.data_dir = data_dir
        self.keywords: Dict[str, KeywordInfo] = {}
        self.categories: Dict[str, Dict] = {}
        self.parameter_templates: Dict[str, ParameterTemplate] = {}
        self.compatibility_rules: Dict[str, Any] = {}

        self._load_data()

    def _load_data(self) -> None:
        """Carrega dados de keywords do arquivo JSON"""
        keywords_file = self.data_dir / "keywords.json"

        if not keywords_file.exists():
            raise FileNotFoundError(
                f"Arquivo de keywords não encontrado: {keywords_file}"
            )

        with open(keywords_file, "r") as f:
            data = json.load(f)

        # Carrega categorias e keywords
        self.categories = data.get("categories", {})

        # Constrói dicionário de keywords
        for category_id, category_data in self.categories.items():
            category_name = category_data.get("name", category_id)

            for kw_data in category_data.get("keywords", []):
                kw_name = kw_data.get("name")
                if kw_name:
                    self.keywords[kw_name] = KeywordInfo(
                        name=kw_name,
                        description=kw_data.get("description", ""),
                        category=category_name,
                        requires_parameters=kw_data.get("requires_parameters", False),
                        compatible_with=kw_data.get("compatible_with", []),
                        common_parameters=kw_data.get("common_parameters", {}),
                    )

        # Carrega templates de parâmetros
        common_params = data.get("common_parameters", {})
        for kw_name, param_data in common_params.items():
            self.parameter_templates[kw_name] = ParameterTemplate(
                keyword=kw_name,
                template=param_data.get("template", ""),
                description=param_data.get("description", ""),
                defaults=param_data.get("defaults", {}),
                options=param_data.get("options", {}),
            )

        # Carrega regras de compatibilidade
        self.compatibility_rules = data.get("compatibility_rules", {})

    def get_keyword(self, name: str) -> Optional[KeywordInfo]:
        """Obtém informações sobre uma keyword específica"""
        return self.keywords.get(name)

    def get_keywords_by_category(self, category_id: str) -> List[KeywordInfo]:
        """Obtém todas as keywords de uma categoria"""
        category_data = self.categories.get(category_id, {})
        keywords = []

        for kw_data in category_data.get("keywords", []):
            kw_name = kw_data.get("name")
            if kw_name in self.keywords:
                keywords.append(self.keywords[kw_name])

        return keywords

    def get_all_categories(self) -> List[Tuple[str, str]]:
        """Retorna lista de todas as categorias (id, nome)"""
        return [
            (cat_id, cat_data.get("name", cat_id))
            for cat_id, cat_data in self.categories.items()
        ]

    def search_keywords(
        self, query: str, category_filter: Optional[str] = None
    ) -> List[KeywordInfo]:
        """Busca keywords por nome ou descrição"""
        query = query.lower()
        results = []

        for kw_info in self.keywords.values():
            if category_filter and kw_info.category != category_filter:
                continue

            if query in kw_info.name.lower() or query in kw_info.description.lower():
                results.append(kw_info)

        return results

    def get_parameter_template(self, keyword: str) -> Optional[ParameterTemplate]:
        """Obtém template de parâmetros para uma keyword"""
        return self.parameter_templates.get(keyword)

    def generate_parameter_string(self, keyword: str, **kwargs: Any) -> str:
        """
        Gera string de parâmetros para uma keyword

        Args:
            keyword: Nome da keyword
            **kwargs: Valores para substituir no template

        Returns:
            String formatada com parâmetros
        """
        template = self.get_parameter_template(keyword)
        if not template:
            return keyword

        # Usa defaults se não fornecidos
        params = template.defaults.copy()
        params.update(kwargs)

        # Substitui no template
        result = template.template

        # Primeiro, substitui parâmetros com valores
        for key, value in params.items():
            if value is not None and value != "":
                placeholder = "{" + key + "}"
                result = result.replace(placeholder, str(value))

        # Remove placeholders vazios (parâmetros sem valor como "smd")
        import re

        result = re.sub(
            r",\s*\{[^}]+\}", "", result
        )  # Remove placeholders precedidos por vírgula
        result = re.sub(
            r"\{[^}]+\},\s*", "", result
        )  # Remove placeholders seguidos por vírgula
        result = re.sub(
            r"\(\s*\{[^}]+\}\s*\)", "()", result
        )  # Remove placeholders únicos entre parênteses

        # Limpa vírgulas extras
        result = result.replace("(,", "(").replace(",)", ")").replace(",,", ",")

        return result

    def get_parameter_defaults(self, keyword: str) -> Dict[str, Any]:
        """
        Obtém valores padrão para os parâmetros de uma keyword

        Args:
            keyword: Nome da keyword

        Returns:
            Dicionário com valores padrão ou vazio se não houver template
        """
        template = self.get_parameter_template(keyword)
        if not template:
            return {}
        return template.defaults.copy()

    def check_compatibility(
        self, existing_keywords: List[str], new_keyword: str
    ) -> Tuple[bool, List[str]]:
        """
        Verifica compatibilidade de uma nova keyword com as existentes

        Args:
            existing_keywords: Lista de keywords já presentes
            new_keyword: Nova keyword a ser adicionada

        Returns:
            Tuple (é_compatível, lista_de_avisos)
        """
        warnings = []

        # Verifica exclusividade mútua
        mutually_exclusive = self.compatibility_rules.get("mutually_exclusive", [])
        for group in mutually_exclusive:
            if new_keyword in group:
                conflicting = [
                    kw for kw in existing_keywords if kw in group and kw != new_keyword
                ]
                if conflicting:
                    warnings.append(
                        f"{new_keyword} é mutuamente exclusivo com: {', '.join(conflicting)}"
                    )

        # Verifica requisitos
        requires = self.compatibility_rules.get("requires", {})
        if new_keyword in requires:
            required = requires[new_keyword]
            missing = []

            for req in required:
                if isinstance(req, str) and req not in existing_keywords:
                    # Verifica se é uma categoria
                    if req in self.categories:
                        # Precisa de pelo menos uma keyword da categoria
                        category_keywords = [
                            kw.name for kw in self.get_keywords_by_category(req)
                        ]
                        if not any(kw in existing_keywords for kw in category_keywords):
                            missing.append(f"alguma keyword da categoria '{req}'")
                    else:
                        missing.append(req)

            if missing:
                warnings.append(f"{new_keyword} requer: {', '.join(missing)}")

        # Sugere recomendações
        recommended = self.compatibility_rules.get("recommended_with", {})
        if new_keyword in recommended:
            for rec in recommended[new_keyword]:
                if rec not in existing_keywords:
                    warnings.append(f"Recomendado com {new_keyword}: {rec}")

        is_compatible = len(warnings) == 0 or all("Recomendado" in w for w in warnings)
        return is_compatible, warnings

    def parse_keyword_string(self, keyword_string: str) -> Tuple[str, Dict[str, str]]:
        """
        Parseia uma string de keyword com parâmetros

        Args:
            keyword_string: String completa (ex: "td=(nstates=50,root=1)")

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
            # Processa parâmetros separados por vírgula, considerando parênteses aninhados
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

    def extract_current_parameters(self, keyword_string: str) -> Dict[str, str]:
        """
        Extrai parâmetros atuais de uma string de keyword

        Args:
            keyword_string: String da keyword com parâmetros

        Returns:
            Dicionário com parâmetros atuais
        """
        _, params = self.parse_keyword_string(keyword_string)
        return params

    def update_parameter_string(
        self, keyword_string: str, new_params: Dict[str, str]
    ) -> str:
        """
        Atualiza parâmetros em uma string de keyword

        Args:
            keyword_string: String original da keyword
            new_params: Novos valores para os parâmetros

        Returns:
            String atualizada da keyword
        """
        keyword_name, current_params = self.parse_keyword_string(keyword_string)

        # Atualiza parâmetros com novos valores
        updated_params = current_params.copy()
        updated_params.update(new_params)

        # Gera nova string
        if not updated_params:
            return keyword_name

        # Verifica se é um template conhecido
        template = self.get_parameter_template(keyword_name)
        if template:
            # Remove parâmetros vazios (como "smd" que não tem valor)
            filtered_params = {
                k: v for k, v in updated_params.items() if v is not None and v != ""
            }
            return self.generate_parameter_string(keyword_name, **filtered_params)

        # Formato genérico
        if len(updated_params) == 1 and "value" in updated_params:
            return f"{keyword_name}={updated_params['value']}"
        else:
            # Filtra parâmetros vazios
            filtered_params = {
                k: v for k, v in updated_params.items() if v is not None and v != ""
            }
            if not filtered_params:
                return keyword_name
            params_str = ",".join(f"{k}={v}" for k, v in filtered_params.items())
            return f"{keyword_name}=({params_str})"

    def get_parameter_options(self, keyword: str, param_name: str) -> List[str]:
        """
        Obtém opções disponíveis para um parâmetro específico

        Args:
            keyword: Nome da keyword
            param_name: Nome do parâmetro

        Returns:
            Lista de opções disponíveis ou lista vazia se não houver restrições
        """
        template = self.get_parameter_template(keyword)
        if not template or not template.options:
            return []

        # Verifica se há opções específicas para este parâmetro
        if param_name in template.options:
            return template.options[param_name]

        # Verifica opções comuns (ex: common_solvents, common_types)
        if param_name == "solvent" and "common_solvents" in template.options:
            return template.options["common_solvents"]
        elif param_name == "type" and "common_types" in template.options:
            return template.options["common_types"]
        elif param_name == "option" and "common_options" in template.options:
            return template.options["common_options"]

        return []

    def format_keyword_for_display(self, keyword_string: str) -> str:
        """
        Formata uma keyword para exibição amigável

        Args:
            keyword_string: String da keyword

        Returns:
            String formatada para exibição
        """
        name, params = self.parse_keyword_string(keyword_string)
        kw_info = self.get_keyword(name)

        if kw_info:
            display = f"{name} - {kw_info.description}"
            if params:
                display += f" ({', '.join(f'{k}={v}' for k, v in params.items())})"
            return display

        return keyword_string

    def get_keyword_choices(
        self, category_id: Optional[str] = None
    ) -> List[Tuple[str, str]]:
        """
        Retorna lista de choices para menus de seleção

        Args:
            category_id: ID da categoria para filtrar (opcional)

        Returns:
            Lista de tuples (value, display_text)
        """
        choices = []

        if category_id:
            keywords = self.get_keywords_by_category(category_id)
        else:
            keywords = list(self.keywords.values())

        for kw_info in keywords:
            display = self.format_keyword_for_display(kw_info.name)
            choices.append((kw_info.name, display))

        return choices
