"""Exceções customizadas do gerador de petições."""


class GeradorError(Exception):
    """Erro base do gerador de petições."""


class ArquivoNaoEncontradoError(GeradorError):
    """Arquivo de entrada obrigatório não encontrado."""


class PlanilhaInvalidaError(GeradorError):
    """Planilha com estrutura inválida (colunas ausentes, sem dados, etc.)."""


class GeracaoPeticaoError(GeradorError):
    """Erro ao gerar uma petição individual."""
