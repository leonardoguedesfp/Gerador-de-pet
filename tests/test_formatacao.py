"""Testes para o módulo de formatação."""

from datetime import datetime, date

import pytest

from gerador_peticoes.formatacao import (
    formatar_data,
    formatar_monetario,
    detectar_coluna_data,
    formatar_valor_celula,
)


class TestFormatarData:
    def test_datetime(self):
        assert formatar_data(datetime(2024, 3, 15)) == "15/03/2024"

    def test_date(self):
        assert formatar_data(date(2024, 1, 1)) == "01/01/2024"

    def test_serial_excel(self):
        # 45292 = 01/01/2024 no Excel
        assert formatar_data(45292) == "01/01/2024"

    def test_none(self):
        assert formatar_data(None) == ""

    def test_string_passthrough(self):
        assert formatar_data("01/03/2024") == "01/03/2024"

    def test_formato_custom(self):
        assert formatar_data(datetime(2024, 3, 15), "%Y-%m-%d") == "2024-03-15"


class TestFormatarMonetario:
    def test_inteiro(self):
        assert formatar_monetario(50000) == "R$ 50.000,00"

    def test_decimal(self):
        assert formatar_monetario(1234.56) == "R$ 1.234,56"

    def test_negativo(self):
        assert formatar_monetario(-100) == "-R$ 100,00"

    def test_zero(self):
        assert formatar_monetario(0) == "R$ 0,00"

    def test_none(self):
        assert formatar_monetario(None) == ""

    def test_string_passthrough(self):
        assert formatar_monetario("R$ 50.000,00") == "R$ 50.000,00"


class TestDetectarColunaData:
    @pytest.mark.parametrize("nome", [
        "DataNascimento", "data_admissao", "DataAposentadoria",
        "data", "Data_Inicio",
    ])
    def test_positivos(self, nome):
        assert detectar_coluna_data(nome) is True

    @pytest.mark.parametrize("nome", [
        "Nome", "CPF", "Valor", "Endereco",
    ])
    def test_negativos(self, nome):
        assert detectar_coluna_data(nome) is False


class TestFormatarValorCelula:
    def test_coluna_monetaria(self):
        assert formatar_valor_celula("Salario", 5000, ["Salario"]) == "R$ 5.000,00"

    def test_datetime(self):
        assert formatar_valor_celula("Qualquer", datetime(2024, 1, 1)) == "01/01/2024"

    def test_data_serial(self):
        assert formatar_valor_celula("DataNascimento", 45292) == "01/01/2024"

    def test_string_normal(self):
        assert formatar_valor_celula("Nome", "João") == "João"

    def test_none(self):
        assert formatar_valor_celula("Nome", None) == ""
