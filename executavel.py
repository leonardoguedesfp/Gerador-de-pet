"""Ponto de entrada para o executável (.exe) gerado pelo PyInstaller."""

import sys
import tkinter as tk
from tkinter import messagebox

from gerador_peticoes.__main__ import main


def executar_gui():
    """Executa o gerador e exibe resultado em caixa de diálogo."""
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
            "Verifique a pasta 'saida' para os arquivos gerados.",
        )
        root.destroy()

    sys.exit(codigo)


if __name__ == "__main__":
    executar_gui()
