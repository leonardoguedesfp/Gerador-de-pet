"""Funções de formatação de valores (datas, moeda, etc.)."""

import re
from datetime import datetime, date, timedelta

FORMATO_DATA = "%d/%m/%Y"

MESES_PT = {
    1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
    5: "maio", 6: "junho", 7: "julho", 8: "agosto",
    9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
}

# Padrão: MM/AAAA,R$X.XXX,XX (uma ou mais entradas separadas por ;)
_PADRAO_PRESERVACAO = re.compile(
    r'^\d{1,2}/\d{4},\s*R\$\s*[\d.,]+'
    r'(?:;\s*\d{1,2}/\d{4},\s*R\$\s*[\d.,]+)*$'
)

_PADRAO_ENTRADA_PRESERVACAO = re.compile(
    r'(\d{1,2})/(\d{4}),\s*(R\$\s*[\d.,]+)'
)

# Padrão CNJ: NNNNNNN-DD.AAAA.J.TT.OOOO
_PADRAO_CNJ = re.compile(
    r'^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$'
)

_TERMOS_DATA = frozenset([
    "data", "date", "nascimento", "admissao", "admissão",
    "demissao", "demissão", "aposentadoria", "desligamento",
    "contratacao", "contratação", "inicio", "início",
    "fim", "termino", "término", "vencimento", "protocolo",
    "ajuizamento", "distribuicao", "distribuição", "publicacao",
    "publicação", "trânsito", "transito", "adesao", "adesão",
])


def formatar_data(valor, formato: str = FORMATO_DATA) -> str:
    """
    Converte datas do Excel para o formato dd/mm/aaaa.

    Aceita datetime, date, número serial do Excel ou string.
    """
    if valor is None:
        return ""

    if isinstance(valor, datetime):
        return valor.strftime(formato)
    if isinstance(valor, date):
        return valor.strftime(formato)

    if isinstance(valor, (int, float)):
        try:
            base = datetime(1899, 12, 30)
            data = base + timedelta(days=int(valor))
            if 1900 <= data.year <= 2100:
                return data.strftime(formato)
        except (ValueError, OverflowError):
            pass

    return str(valor).strip()


def formatar_monetario(valor) -> str:
    """Formata valor numérico como moeda brasileira: R$ 50.000,00."""
    if valor is None:
        return ""
    if isinstance(valor, str):
        return valor.strip()
    if isinstance(valor, (int, float)):
        negativo = valor < 0
        valor_abs = abs(valor)
        parte_inteira = int(valor_abs)
        parte_decimal = round((valor_abs - parte_inteira) * 100)
        str_inteira = f"{parte_inteira:,}".replace(",", ".")
        resultado = f"R$ {str_inteira},{parte_decimal:02d}"
        return f"-{resultado}" if negativo else resultado
    return str(valor).strip()


def detectar_coluna_data(nome_coluna: str) -> bool:
    """Heurística: retorna True se o nome da coluna sugere conteúdo de data."""
    nome_lower = nome_coluna.lower()
    return any(termo in nome_lower for termo in _TERMOS_DATA)


def formatar_valor_celula(
    nome_coluna: str,
    valor,
    colunas_monetarias: list[str] | None = None,
    formato_data: str = FORMATO_DATA,
) -> str:
    """
    Decide a formatação de um valor com base no nome da coluna.

    Prioridade:
      1. Colunas em colunas_monetarias → monetário
      2. Valores datetime/date → data
      3. Nome sugere data + valor numérico → data serial
      4. Demais → string
    """
    colunas_monetarias = colunas_monetarias or []

    if nome_coluna in colunas_monetarias:
        return formatar_monetario(valor)

    if isinstance(valor, (datetime, date)):
        return formatar_data(valor, formato_data)

    if detectar_coluna_data(nome_coluna) and isinstance(valor, (int, float)):
        return formatar_data(valor, formato_data)

    if valor is None:
        return ""
    return str(valor).strip()


# ---------------------------------------------------------------------------
# Formatação jurídica (humanização de dados brutos)
# ---------------------------------------------------------------------------

def _juntar_com_e(itens: list[str]) -> str:
    """Junta itens com vírgula e 'e' antes do último."""
    if not itens:
        return ""
    if len(itens) == 1:
        return itens[0]
    return ", ".join(itens[:-1]) + " e " + itens[-1]


def formatar_preservacoes(valor: str) -> str:
    """
    Converte 'MM/AAAA,R$X.XXX,XX;...' em texto jurídico.

    Exemplo:
      '3/2013,R$6.622,33;5/2013,R$8.419,03'
      → 'em março de 2013, no valor de R$ 6.622,33 e em maio de 2013,
         no valor de R$ 8.419,03'
    """
    if not valor:
        return valor

    entradas = [e.strip() for e in valor.split(";") if e.strip()]
    partes = []
    for entrada in entradas:
        match = _PADRAO_ENTRADA_PRESERVACAO.match(entrada)
        if match:
            mes = int(match.group(1))
            ano = match.group(2)
            val_mon = re.sub(r'R\$\s*', 'R$ ', match.group(3))
            nome_mes = MESES_PT.get(mes, str(mes))
            partes.append(f"em {nome_mes} de {ano}, no valor de {val_mon}")
        else:
            partes.append(entrada)

    return _juntar_com_e(partes)


def formatar_lista_processos(valor: str) -> str:
    """
    Converte números de processo separados por ';' em texto com conjunção.

    Exemplo:
      '0000001-61.2022.5.10.0017;0000443-05.2023.5.10.0013'
      → '0000001-61.2022.5.10.0017 e nº 0000443-05.2023.5.10.0013'
    """
    if not valor or ";" not in valor:
        return valor

    partes = [p.strip() for p in valor.split(";") if p.strip()]

    if not all(_PADRAO_CNJ.match(p) for p in partes):
        return valor

    if len(partes) == 1:
        return partes[0]
    if len(partes) == 2:
        return f"{partes[0]} e nº {partes[1]}"

    return ", nº ".join(partes[:-1]) + " e nº " + partes[-1]


def humanizar_registro(registro: dict[str, str]) -> dict[str, str]:
    """
    Aplica formatação humanizada aos valores do registro para uso
    em petições jurídicas.

    Detecta automaticamente:
    - Preservações no formato MM/AAAA,R$X.XXX,XX
    - Números de processo CNJ separados por ;
    """
    resultado = {}
    for chave, valor in registro.items():
        if not isinstance(valor, str) or not valor.strip():
            resultado[chave] = valor
            continue

        valor_strip = valor.strip()

        # Preservações: MM/AAAA,R$X.XXX,XX;...
        if _PADRAO_PRESERVACAO.match(valor_strip):
            resultado[chave] = formatar_preservacoes(valor_strip)
            continue

        # Múltiplos números de processo CNJ separados por ;
        if ";" in valor_strip:
            partes = [p.strip() for p in valor_strip.split(";") if p.strip()]
            if all(_PADRAO_CNJ.match(p) for p in partes):
                resultado[chave] = formatar_lista_processos(valor_strip)
                continue

        resultado[chave] = valor

    return resultado


# ---------------------------------------------------------------------------
# Derivação de variáveis (colunas da planilha → variáveis do modelo Word)
# ---------------------------------------------------------------------------

def derivar_variaveis(
    registro: dict[str, str],
    formato_data: str = FORMATO_DATA,
) -> dict[str, str]:
    """
    Cria variáveis derivadas a partir das colunas brutas da planilha
    e aplica formatação humanizada em todos os valores.

    Variáveis geradas automaticamente:
    - {DataPeticao}         ← data atual
    - {ListaPreservacoes}   ← PreservacaoSP formatado por extenso
    - {ListaRTs}            ← RT_Indenizatoria com conjunção
    - {ListaRTsComDoc}      ← RT_Indenizatoria com conjunção (para contexto documental)
    - {RTAnterior}          ← RT_Anterior ou RTAnterior

    O registro original é preservado; as variáveis derivadas são ADICIONADAS.
    """
    resultado = dict(registro)

    # {DataPeticao}: data atual formatada
    resultado.setdefault("DataPeticao", datetime.now().strftime(formato_data))

    # {ListaPreservacoes}: de PreservacaoSP, humanizado
    preservacao = registro.get("PreservacaoSP", "").strip()
    resultado["ListaPreservacoes"] = (
        formatar_preservacoes(preservacao) if preservacao else ""
    )

    # {ListaRTs} e {ListaRTsComDoc}: de RT_Indenizatoria, com conjunção
    rt_ind = registro.get("RT_Indenizatoria", "").strip()
    resultado["ListaRTs"] = formatar_lista_processos(rt_ind) if rt_ind else ""
    resultado["ListaRTsComDoc"] = formatar_lista_processos(rt_ind) if rt_ind else ""

    # {RTAnterior}: busca em variantes comuns de nome de coluna
    if not resultado.get("RTAnterior", "").strip():
        for col in ("RT_Anterior", "RtAnterior", "Rt_Anterior"):
            val = registro.get(col, "").strip()
            if val:
                resultado["RTAnterior"] = val
                break
        else:
            resultado.setdefault("RTAnterior", "")

    # Humanizar todos os valores (formata padrões brutos restantes)
    return humanizar_registro(resultado)
