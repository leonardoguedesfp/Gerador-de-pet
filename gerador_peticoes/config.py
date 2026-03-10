"""Configurações padrão e dataclass de configuração."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    """Configurações para o gerador de petições."""

    dir_entrada: Path = Path("entrada")
    dir_saida: Path = Path("saida")
    nome_execucao: str = ""
    coluna_genero: str = "Genero"
    coluna_nome: str = "Nome"
    prefixo_arquivo: str = "Peticao"
    formato_data: str = "%d/%m/%Y"
    colunas_monetarias: list[str] = field(default_factory=list)
    colunas_relatorio: list[str] = field(default_factory=list)
    dry_run: bool = False
    workers: int = 1

    @property
    def planilha_path(self) -> Path:
        return self.dir_entrada / "dados_clientes.xlsx"

    @property
    def modelo_m_path(self) -> Path:
        return self.dir_entrada / "modelo_masculino.docx"

    @property
    def modelo_f_path(self) -> Path:
        return self.dir_entrada / "modelo_feminino.docx"
