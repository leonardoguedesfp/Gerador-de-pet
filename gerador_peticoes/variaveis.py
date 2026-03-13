"""Pré-processamento de variáveis derivadas para petições."""

import re


def _extrair_preservacoes(registro: dict[str, str]) -> list[tuple[str, str]]:
    """
    Extrai pares (data, valor) de colunas de preservação do registro.

    Detecta colunas com padrões como:
      - Preservacao_Data_1 / Preservacao_Valor_1
      - PreservacaoData1 / PreservacaoValor1
      - Preservacao_1_Data / Preservacao_1_Valor

    Retorna lista de (data, valor) ordenada pelo índice numérico.
    """
    # Mapear índice → {tipo: valor}
    pares: dict[int, dict[str, str]] = {}

    padrao_data = re.compile(
        r"[Pp]reserva[cç][aã]o[_]?[Dd]ata[_]?(\d+)"
        r"|[Pp]reserva[cç][aã]o[_]?(\d+)[_]?[Dd]ata",
    )
    padrao_valor = re.compile(
        r"[Pp]reserva[cç][aã]o[_]?[Vv]alor[_]?(\d+)"
        r"|[Pp]reserva[cç][aã]o[_]?(\d+)[_]?[Vv]alor",
    )

    for coluna, valor in registro.items():
        if not valor:
            continue

        m = padrao_data.search(coluna)
        if m:
            idx = int(m.group(1) or m.group(2))
            pares.setdefault(idx, {})["data"] = valor
            continue

        m = padrao_valor.search(coluna)
        if m:
            idx = int(m.group(1) or m.group(2))
            pares.setdefault(idx, {})["valor"] = valor

    resultado = []
    for idx in sorted(pares):
        data = pares[idx].get("data", "")
        valor = pares[idx].get("valor", "")
        if data and valor:
            resultado.append((data, valor))

    return resultado


def _formatar_preservacoes(preservacoes: list[tuple[str, str]]) -> str:
    """
    Formata lista de preservações no padrão esperado.

    Exemplo: "em 6/2017, no importe de R$9.729,16"
    Múltiplas: "em 6/2017, no importe de R$9.729,16; em 12/2018, ..."
    """
    partes = []
    for data, valor in preservacoes:
        partes.append(f"em {data}, no importe de {valor}")
    return "; ".join(partes)


def computar_variaveis_derivadas(registro: dict[str, str]) -> dict[str, str]:
    """
    Cria variáveis derivadas a partir dos dados brutos da planilha.

    Mapeamentos:
      - RT_VerbasTrabalhistas → {ListaRTs}, {ListaRTsComDoc}
      - RT_Indenizatoria → {RTAnterior}
      - Colunas de preservação → {ListaPreservacoes}
    """
    variaveis = dict(registro)

    rt_verbas = registro.get("RT_VerbasTrabalhistas", "")
    rt_indenizatoria = registro.get("RT_Indenizatoria", "")

    # Problema 1: ListaRTs e ListaRTsComDoc devem vir de RT_VerbasTrabalhistas
    if rt_verbas:
        variaveis["ListaRTs"] = rt_verbas
        variaveis["ListaRTsComDoc"] = rt_verbas

    # Problema 2: RTAnterior deve vir de RT_Indenizatoria
    if rt_indenizatoria:
        variaveis["RTAnterior"] = rt_indenizatoria

    # Problema 3: ListaPreservacoes a partir de colunas de preservação
    preservacoes = _extrair_preservacoes(registro)
    if preservacoes:
        variaveis["ListaPreservacoes"] = _formatar_preservacoes(preservacoes)

    return variaveis
