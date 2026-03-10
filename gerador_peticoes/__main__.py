"""Ponto de entrada CLI: python -m gerador_peticoes"""

import argparse
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog

from . import __version__
from .config import Config
from .gerador import executar


def _selecionar_pasta() -> Path | None:
    """Abre diálogo para o usuário selecionar a pasta de entrada."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    pasta = filedialog.askdirectory(
        title="Selecione a pasta com os arquivos de entrada "
              "(dados_clientes.xlsx, modelo_masculino.docx, modelo_feminino.docx)",
    )

    root.destroy()

    if not pasta:
        return None
    return Path(pasta)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gerador_peticoes",
        description="Gerador Automático de Petições Personalizadas",
    )
    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "-e", "--entrada", type=Path, default=None,
        help="Diretório com planilha e modelos (se omitido, abre caixa de seleção)",
    )
    parser.add_argument(
        "-s", "--saida", type=Path, default=Path("saida"),
        help="Diretório-base de saída (padrão: saida/)",
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

    # Selecionar pasta de entrada
    dir_entrada = args.entrada
    if dir_entrada is None:
        dir_entrada = _selecionar_pasta()
        if dir_entrada is None:
            print("Nenhuma pasta selecionada. Encerrando.")
            return 1

    # Criar subpasta de saída com timestamp
    timestamp = datetime.now().strftime("%d-%m-%Y_%Hh%Mm%Ss")
    nome_subpasta = f"saida_{timestamp}"
    dir_saida = args.saida / nome_subpasta

    cfg = Config(
        dir_entrada=dir_entrada,
        dir_saida=dir_saida,
        nome_execucao=nome_subpasta,
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
