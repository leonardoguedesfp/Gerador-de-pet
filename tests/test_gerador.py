"""Testes de integração para o gerador."""

from pathlib import Path

from docx import Document
from openpyxl import Workbook

from gerador_peticoes.config import Config
from gerador_peticoes.gerador import executar


def _criar_modelo(path: Path, texto: str = "Eu, {Nome}, gênero {Genero}.") -> None:
    doc = Document()
    doc.add_paragraph(texto)
    doc.save(str(path))


def _criar_planilha(path: Path, registros: list[dict]) -> None:
    wb = Workbook()
    ws = wb.active
    if registros:
        headers = list(registros[0].keys())
        ws.append(headers)
        for reg in registros:
            ws.append([reg[h] for h in headers])
    wb.save(str(path))


class TestExecutar:
    def test_fluxo_basico(self, tmp_path):
        entrada = tmp_path / "entrada"
        saida = tmp_path / "saida"
        entrada.mkdir()

        _criar_modelo(entrada / "modelo_masculino.docx")
        _criar_modelo(entrada / "modelo_feminino.docx")
        _criar_planilha(entrada / "dados_clientes.xlsx", [
            {"Nome": "João", "Genero": "M"},
            {"Nome": "Maria", "Genero": "F"},
        ])

        cfg = Config(dir_entrada=entrada, dir_saida=saida)
        result = executar(cfg)

        assert result == 0
        assert (saida / "Peticao - João.docx").exists()
        assert (saida / "Peticao - Maria.docx").exists()
        assert (saida / "relatorio_conferencia.xlsx").exists()
        assert (saida / "log_execucao.txt").exists()

    def test_dry_run_nao_cria_docx(self, tmp_path):
        entrada = tmp_path / "entrada"
        saida = tmp_path / "saida"
        entrada.mkdir()

        _criar_modelo(entrada / "modelo_masculino.docx")
        _criar_modelo(entrada / "modelo_feminino.docx")
        _criar_planilha(entrada / "dados_clientes.xlsx", [
            {"Nome": "João", "Genero": "M"},
        ])

        cfg = Config(dir_entrada=entrada, dir_saida=saida, dry_run=True)
        result = executar(cfg)

        assert result == 0
        assert not (saida / "Peticao - João.docx").exists()

    def test_genero_invalido_gera_aviso(self, tmp_path):
        entrada = tmp_path / "entrada"
        saida = tmp_path / "saida"
        entrada.mkdir()

        _criar_modelo(entrada / "modelo_masculino.docx")
        _criar_modelo(entrada / "modelo_feminino.docx")
        _criar_planilha(entrada / "dados_clientes.xlsx", [
            {"Nome": "Alex", "Genero": "X"},
        ])

        cfg = Config(dir_entrada=entrada, dir_saida=saida)
        result = executar(cfg)

        assert result == 0
        assert not (saida / "Peticao - Alex.docx").exists()

    def test_arquivo_entrada_faltando(self, tmp_path):
        cfg = Config(dir_entrada=tmp_path / "nao_existe", dir_saida=tmp_path / "saida")
        result = executar(cfg)
        assert result == 1

    def test_workers_paralelo(self, tmp_path):
        entrada = tmp_path / "entrada"
        saida = tmp_path / "saida"
        entrada.mkdir()

        _criar_modelo(entrada / "modelo_masculino.docx")
        _criar_modelo(entrada / "modelo_feminino.docx")
        _criar_planilha(entrada / "dados_clientes.xlsx", [
            {"Nome": "João", "Genero": "M"},
            {"Nome": "Maria", "Genero": "F"},
            {"Nome": "Pedro", "Genero": "M"},
        ])

        cfg = Config(dir_entrada=entrada, dir_saida=saida, workers=2)
        result = executar(cfg)

        assert result == 0
        assert (saida / "Peticao - João.docx").exists()
        assert (saida / "Peticao - Maria.docx").exists()
        assert (saida / "Peticao - Pedro.docx").exists()
