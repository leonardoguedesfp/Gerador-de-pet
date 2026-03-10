"""Ponto de entrada CLI: python -m gerador_peticoes"""

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import Config
from .gerador import executar


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gerador_peticoes",
        description="Gerador Automático de Petições Personalizadas",
    )
    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "-e", "--entrada", type=Path, default=Path("entrada"),
        help="Diretório com planilha e modelos (padrão: entrada/)",
    )
    parser.add_argument(
        "-s", "--saida", type=Path, default=Path("saida"),
        help="Diretório de saída (padrão: saida/)",
    )
    parser.add_argument(
        "-p", "--planilha", default="dados_clientes.xlsx",
        help="Nome do arquivo de planilha (padrão: dados_clientes.xlsx)",
    )
    parser.add_argument(
        "--modelo-masculino", default="modelo_masculino.docx",
        help="Nome do modelo masculino (padrão: modelo_masculino.docx)",
    )
    parser.add_argument(
        "--modelo-feminino", default="modelo_feminino.docx",
        help="Nome do modelo feminino (padrão: modelo_feminino.docx)",
    )
    parser.add_argument(
        "--coluna-genero", default="Genero",
        help="Nome da coluna de gênero (padrão: Genero)",
    )
    parser.add_argument(
        "--coluna-nome", default="Nome",
        help="Nome da coluna de nome (padrão: Nome)",
    )
    parser.add_argument(
        "--prefixo", default="Peticao",
        help="Prefixo dos arquivos gerados (padrão: Peticao)",
    )
    parser.add_argument(
        "--formato-data", default="%d/%m/%Y",
        help="Formato de data (padrão: %%d/%%m/%%Y)",
    )
    parser.add_argument(
        "--colunas-monetarias", nargs="*", default=[],
        help="Nomes de colunas com valores monetários",
    )
    parser.add_argument(
        "--colunas-relatorio", nargs="*", default=[],
        help="Colunas extras a incluir no relatório de conferência",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Simula a geração sem criar arquivos .docx",
    )
    parser.add_argument(
        "-w", "--workers", type=int, default=1,
        help="Número de threads para geração paralela (padrão: 1)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    cfg = Config(
        dir_entrada=args.entrada,
        dir_saida=args.saida,
        arquivo_planilha=args.planilha,
        modelo_masculino=args.modelo_masculino,
        modelo_feminino=args.modelo_feminino,
        coluna_genero=args.coluna_genero,
        coluna_nome=args.coluna_nome,
        prefixo_arquivo=args.prefixo,
        formato_data=args.formato_data,
        colunas_monetarias=args.colunas_monetarias,
        colunas_relatorio=args.colunas_relatorio,
        dry_run=args.dry_run,
        workers=args.workers,
    )

    return executar(cfg)


if __name__ == "__main__":
    sys.exit(main())
