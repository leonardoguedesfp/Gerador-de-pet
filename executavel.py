"""Ponto de entrada para o executável (.exe) gerado pelo PyInstaller."""

import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from gerador_peticoes.__main__ import main


def _diretorio_executavel() -> Path:
    """Retorna o diretório onde o .exe está localizado."""
    if getattr(sys, "frozen", False):
        # Executando como .exe (PyInstaller)
        return Path(sys.executable).parent
    # Executando como script Python normal
    return Path.cwd()


def executar_gui():
    """Executa o gerador e exibe resultado em caixa de diálogo."""
    # Mudar para o diretório do executável para que caminhos relativos funcionem
    dir_exe = _diretorio_executavel()
    os.chdir(dir_exe)

    try:
        codigo = main()
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Erro", f"Ocorreu um erro inesperado:\n\n{e}")
        root.destroy()
        sys.exit(1)

    if codigo == 0:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(
            "Concluído",
            "Petições geradas com sucesso!\n\n"
            f"Verifique a pasta:\n{dir_exe / 'saida'}",
        )
        root.destroy()

    sys.exit(codigo)


if __name__ == "__main__":
    executar_gui()
