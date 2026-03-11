# Tutorial — Gerador de Petições Personalizadas

## O que é este programa?

O **Gerador de Petições** é uma ferramenta em Python que automatiza a criação de documentos jurídicos (petições) personalizados. Ele lê os dados de clientes a partir de uma planilha Excel, preenche modelos Word (.docx) com essas informações e gera um arquivo individual para cada cliente.

---

## Pré-requisitos

- **Python 3.10** ou superior
- Bibliotecas: `python-docx` e `openpyxl`

Para instalar as dependências:

```bash
pip install -r requirements.txt
```

---

## Estrutura do Projeto

```
Gerador-de-pet/
├── gerador_peticoes/        # Pacote principal
│   ├── __init__.py          # Versão do pacote (2.0.0)
│   ├── __main__.py          # Ponto de entrada (CLI)
│   ├── config.py            # Configurações
│   ├── gerador.py           # Lógica principal de execução
│   ├── documento.py         # Geração e substituição nos documentos Word
│   ├── formatacao.py        # Formatação de datas e valores monetários
│   ├── planilha.py          # Leitura da planilha Excel
│   ├── relatorio.py         # Geração do relatório de conferência
│   ├── logger.py            # Sistema de log (terminal + arquivo)
│   └── exceptions.py        # Exceções personalizadas
├── entrada/                 # Pasta de entrada (planilha + modelos)
├── tests/                   # Testes automatizados
├── pyproject.toml           # Metadados do projeto
└── requirements.txt         # Dependências
```

---

## Como Preparar os Arquivos de Entrada

Antes de rodar o programa, coloque três arquivos dentro da pasta `entrada/`:

### 1. Planilha de clientes (`dados_clientes.xlsx`)

Uma planilha Excel onde cada linha é um cliente. As colunas obrigatórias são:

| Coluna   | Descrição                              |
|----------|----------------------------------------|
| **Nome** | Nome completo do cliente               |
| **Genero** | Gênero do cliente: `M` ou `F`       |

Você pode adicionar quantas colunas extras quiser (CPF, data de nascimento, endereço, valor, etc.). Cada coluna vira uma variável disponível no modelo.

### 2. Modelo masculino (`modelo_masculino.docx`)

Documento Word usado para clientes com gênero **M**.

### 3. Modelo feminino (`modelo_feminino.docx`)

Documento Word usado para clientes com gênero **F**.

### Como funcionam as variáveis nos modelos

Nos modelos Word, use o nome da coluna entre chaves `{}` para inserir o valor do cliente. Por exemplo, se a planilha tem as colunas `Nome`, `CPF` e `Data_Nascimento`, escreva no modelo:

```
Eu, {Nome}, portador(a) do CPF {CPF}, nascido(a) em {Data_Nascimento}, venho...
```

O programa substituirá automaticamente cada `{Variável}` pelo valor correspondente da planilha.

---

## Como Executar

### Modo básico (com diálogo gráfico)

```bash
python -m gerador_peticoes
```

Uma janela aparecerá para você selecionar a pasta de entrada.

### Modo com argumentos (linha de comando)

```bash
python -m gerador_peticoes --entrada ./entrada --saida ./saida
```

### Opções disponíveis

| Argumento               | Descrição                                      | Padrão        |
|-------------------------|-------------------------------------------------|---------------|
| `--entrada`             | Pasta com a planilha e os modelos               | `entrada/`    |
| `--saida`               | Pasta base para os arquivos gerados             | `saida/`      |
| `--coluna-genero`       | Nome da coluna de gênero na planilha            | `Genero`      |
| `--coluna-nome`         | Nome da coluna de nome na planilha              | `Nome`        |
| `--prefixo`             | Prefixo do nome dos arquivos gerados            | `Peticao`     |
| `--formato-data`        | Formato de saída das datas                      | `%d/%m/%Y`    |
| `--colunas-monetarias`  | Colunas que devem ser formatadas como moeda     | —             |
| `--colunas-relatorio`   | Colunas extras para incluir no relatório        | —             |
| `--dry-run`             | Simula a execução sem criar arquivos            | desativado    |
| `--workers`             | Número de threads para processamento paralelo   | `1`           |

### Exemplo completo

```bash
python -m gerador_peticoes \
  --entrada ./entrada \
  --saida ./saida \
  --coluna-genero Sexo \
  --coluna-nome "Nome Completo" \
  --prefixo Recurso \
  --colunas-monetarias Salario "Valor Causa" \
  --workers 4
```

---

## Fluxo de Execução

O programa segue estes passos:

```
1. Lê os argumentos ou abre diálogo para selecionar a pasta
         │
2. Valida se os 3 arquivos obrigatórios existem na pasta de entrada
         │
3. Lê a planilha Excel e formata os dados
   ├── Datas → formato DD/MM/AAAA
   └── Valores monetários → formato R$ X.XXX,XX
         │
4. Para cada cliente na planilha:
   ├── Identifica o gênero (M ou F)
   ├── Seleciona o modelo Word correspondente
   ├── Substitui todas as {Variáveis} pelos dados do cliente
   └── Salva o documento na pasta de saída
         │
5. Gera um relatório Excel de conferência com:
   ├── Status de cada documento (OK / ERRO / AVISO)
   ├── Cores para facilitar a leitura
   └── Estatísticas resumidas
         │
6. Salva o arquivo de log com todo o histórico da execução
```

---

## Saída Gerada

Todos os arquivos ficam em uma subpasta com data e hora, por exemplo:

```
saida/saida_11-03-2026_14h30m00s/
├── Peticao_Joao_Silva.docx
├── Peticao_Maria_Santos.docx
├── Peticao_Carlos_Oliveira.docx
├── relatorio_conferencia.xlsx
└── log_execucao.txt
```

### Relatório de conferência

O relatório Excel gerado inclui:

- **Número**: ordem de processamento
- **Nome**: nome do cliente
- **Gênero**: M ou F
- **Arquivo Gerado**: nome do arquivo .docx criado
- **Status**: OK (verde), ERRO (vermelho) ou AVISO (laranja)
- **Observação**: detalhes em caso de erro ou aviso
- **Resumo**: total de documentos gerados, erros e avisos

---

## Formatação Automática de Dados

O programa formata automaticamente certos tipos de dados:

### Datas

Colunas com nomes que contenham palavras como `data`, `nascimento`, `admissao`, `vencimento`, etc. são detectadas automaticamente e formatadas como `DD/MM/AAAA`.

### Valores monetários

Colunas indicadas com `--colunas-monetarias` são formatadas no padrão brasileiro:

```
1500.50   →  R$ 1.500,50
250000    →  R$ 250.000,00
```

---

## Modo Simulação (Dry Run)

Para testar sem gerar documentos reais:

```bash
python -m gerador_peticoes --dry-run
```

O programa percorre todos os registros e gera o relatório, mas não cria os arquivos .docx. Útil para validar a planilha antes de gerar os documentos.

---

## Processamento Paralelo

Para planilhas grandes, use múltiplas threads:

```bash
python -m gerador_peticoes --workers 4
```

Isso processa 4 clientes simultaneamente, acelerando a geração.

---

## Criando um Executável (.exe)

No Windows, é possível gerar um executável usando o script incluído:

```bat
criar_executavel.bat
```

Isso usa o PyInstaller para criar um `.exe` que pode ser distribuído para usuários que não têm Python instalado.

---

## Executando os Testes

```bash
pip install -r requirements-dev.txt
pytest tests/
```

Os testes cobrem:

- Substituição de variáveis nos documentos
- Formatação de datas e valores monetários
- Sanitização de nomes de arquivo
- Fluxo completo de geração (integração)
- Modo dry-run e processamento paralelo

---

## Resumo Rápido

| Etapa | O que fazer |
|-------|-------------|
| 1     | Instalar dependências: `pip install -r requirements.txt` |
| 2     | Colocar `dados_clientes.xlsx`, `modelo_masculino.docx` e `modelo_feminino.docx` na pasta `entrada/` |
| 3     | Usar `{NomeColuna}` nos modelos Word para marcar onde os dados serão inseridos |
| 4     | Executar: `python -m gerador_peticoes` |
| 5     | Conferir os documentos gerados na pasta `saida/` |
