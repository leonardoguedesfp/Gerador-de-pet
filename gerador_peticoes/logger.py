"""Logger que grava no terminal e em arquivo simultaneamente."""

from datetime import datetime
from pathlib import Path


class Logger:
    """Escreve mensagens no terminal e num arquivo de log simultaneamente."""

    def __init__(self, caminho_log: Path | None = None):
        self.caminho_log = caminho_log
        self._arquivo = None

    def abrir(self) -> None:
        if self.caminho_log is None:
            return
        self.caminho_log.parent.mkdir(parents=True, exist_ok=True)
        self._arquivo = open(self.caminho_log, "w", encoding="utf-8")
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self._escrever_log(f"Log de execução iniciado em {timestamp}")
        self._escrever_log("=" * 65)

    def fechar(self) -> None:
        if self._arquivo:
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            self._escrever_log(f"\nLog encerrado em {timestamp}")
            self._arquivo.close()
            self._arquivo = None

    def info(self, mensagem: str) -> None:
        print(mensagem)
        self._escrever_log(mensagem)

    def erro(self, mensagem: str) -> None:
        print(mensagem)
        self._escrever_log(f"[ERRO] {mensagem}")

    def aviso(self, mensagem: str) -> None:
        print(mensagem)
        self._escrever_log(f"[AVISO] {mensagem}")

    def _escrever_log(self, mensagem: str) -> None:
        if self._arquivo:
            self._arquivo.write(mensagem + "\n")
            self._arquivo.flush()

    def __enter__(self):
        self.abrir()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.fechar()
        return False
