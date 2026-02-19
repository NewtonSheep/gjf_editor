# GJF Editor

Editor de Keywords Gaussian com interface wizard interativa.

## 📋 Funcionalidades

- **Edição interativa de keywords**: Adicione, remova ou edite keywords em arquivos .gjf
- **Compatibilidade automática**: Verifica compatibilidade entre keywords
- **Edição de parâmetros**: Edite parâmetros de keywords como `td=(nstates=50,root=1)`
- **Sistema de backup**: Cria backups automáticos antes de salvar alterações
- **Interface wizard**: Navegação intuitiva com opções de "voltar" em todos os menus
- **Estrutura Hierárquica**: Keywords organizadas por categorias (DFT, bases, solventes, etc.)
- **Suporte a Múltiplas Seções**: Detecta automaticamente seções `--LinkX--`

## Instalação

1. Clone o repositório ou copie os arquivos
2. Crie e ative o ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou venv\Scripts\activate  # Windows
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## Estrutura do Projeto

```
gjf_editor/
├── src/                    # Código fonte
│   ├── parser.py          # Parser de arquivos .gjf
│   ├── keywords.py        # Gerenciador de keywords
│   ├── interface.py       # Interface CLI wizard
│   └── backup.py          # Sistema de backup
├── data/                  # Dados de keywords
│   └── keywords.json      # Lista completa de keywords Gaussian
├── backups/               # Backups automáticos
├── main.py               # Ponto de entrada
├── requirements.txt      # Dependências
└── README.md            # Esta documentação
```

## Uso

### Modo Interativo (Recomendado)
```bash
python main.py
```

O wizard guiará você através dos passos:
1. **Selecionar arquivo** - Escolha um arquivo `.gjf` no diretório atual
2. **Editar keywords** - Para cada seção (OPT/TD):
   - Visualize keywords atuais
   - Adicione novas keywords (seleção por categoria)
   - Remova keywords existentes
   - Navegue pela lista completa
3. **Salvar alterações** - Confirme e crie backup automático
4. **Ver backups** - Gerencie cópias de segurança

### Teste dos Componentes
```bash
python test_components.py
```

## Formatos Suportados

### Arquivos .gjf
- Múltiplas seções com `--LinkX--`
- Linhas de keywords começando com `#p`
- Keywords com parâmetros: `td=(nstates=50,root=1)`
- Métodos com bases: `b3lyp/6-311g(d,p)`

### Keywords Reconhecidas
- **Métodos DFT**: `b3lyp`, `pbe0`, `m06-2x`, `wb97xd`, etc.
- **Bases**: `6-31g`, `6-311g(d,p)`, `cc-pvdz`, `def2-svp`, etc.
- **Semi-empíricos**: `pm3`, `am1`, `pm6`, `pm7`
- **Cálculos**: `opt`, `freq`, `td`, `cis`, `mp2`
- **Solventes**: `scrf`, `pcm`, `smd`
- **Opções**: `nosymm`, `empiricaldispersion`, `pop`, etc.

## Sistema de Backup

- Backups automáticos na pasta `backups/`
- Nomeação: `{arquivo}_{timestamp}.gjf.bak`
- Mantém todos os backups (sem limitação)
- Visualização via menu "Ver backups"

## Validação de Compatibilidade

O sistema verifica:
- **Exclusividade mútua**: `opt` e `td` não podem estar juntos
- **Requisitos**: `td` requer método DFT ou HF
- **Recomendações**: `opt` recomenda `freq` após otimização

## Exemplo de Uso

1. Execute `python main.py`
2. Selecione `Teste.gjf`
3. Escolha "Editar keywords"
4. Selecione a seção OPT
5. Adicione `freq` e `nosymm`
6. Remova `empiricaldispersion`
7. Salve as alterações
8. Verifique o backup criado

## Personalização

### Adicionar Novas Keywords
Edite `data/keywords.json` para adicionar:
- Novas categorias
- Keywords personalizadas
- Regras de compatibilidade

### Modificar Comportamento
- `src/parser.py`: Algoritmo de parsing
- `src/keywords.py`: Gerenciamento de keywords
- `src/interface.py`: Fluxo do wizard

## Limitações Conhecidas

1. **Interface**: Requer terminal interativo (não funciona em modo batch)
2. **Parsing**: `método/base` tratado como keyword única
3. **Compatibilidade**: Regras básicas implementadas

## Próximas Melhorias

- [ ] Modo batch com arquivo de configuração YAML
- [ ] Separação de método e base no parsing
- [ ] Interface web opcional
- [ ] Mais regras de compatibilidade
- [ ] Export/import de configurações

## Licença

Projeto para uso acadêmico e de pesquisa.

## Contribuição

1. Reporte issues no repositório
2. Sugira novas keywords ou categorias
3. Melhore a validação de compatibilidade