"""Funções de formatação de valores (datas, moeda, etc.)."""

from datetime import datetime, date, timedelta

FORMATO_DATA = "%d/%m/%Y"

_TERMOS_DATA = frozenset([
    "data", "date", "nascimento", "admissao", "admissão",
    "demissao", "demissão", "aposentadoria", "desligamento",
    "contratacao", "contratação", "inicio", "início",
    "fim", "termino", "término", "vencimento", "protocolo",
    "ajuizamento", "distribuicao", "distribuição", "publicacao",
    "publicação", "trânsito", "transito", "adesao", "adesão",
])


_MESES_PT = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]


def gerar_data_peticao(dt: date | None = None) -> str:
    """Retorna a data no formato 'Brasília, 13 de março de 2026.'."""
    if dt is None:
        dt = date.today()
    mes = _MESES_PT[dt.month - 1]
    return f"Brasília, {dt.day} de {mes} de {dt.year}."


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
