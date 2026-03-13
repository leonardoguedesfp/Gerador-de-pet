"""Testes para o módulo de formatação."""

from datetime import datetime, date

import pytest

from gerador_peticoes.formatacao import (
    formatar_data,
    formatar_monetario,
    detectar_coluna_data,
    formatar_valor_celula,
    formatar_preservacoes,
    formatar_lista_processos,
    humanizar_registro,
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


class TestFormatarPreservacoes:
    def test_unica(self):
        assert formatar_preservacoes("07/2012,R$7.487,54") == (
            "em julho de 2012, no valor de R$ 7.487,54"
        )

    def test_multiplas(self):
        entrada = "3/2013,R$6.622,33;5/2013,R$8.419,03;8/2013,R$8.631,77;8/2014,R$9.418,28"
        resultado = formatar_preservacoes(entrada)
        assert resultado == (
            "em março de 2013, no valor de R$ 6.622,33, "
            "em maio de 2013, no valor de R$ 8.419,03, "
            "em agosto de 2013, no valor de R$ 8.631,77 e "
            "em agosto de 2014, no valor de R$ 9.418,28"
        )

    def test_duas(self):
        assert formatar_preservacoes("1/2020,R$5.000,00;12/2020,R$6.000,00") == (
            "em janeiro de 2020, no valor de R$ 5.000,00 e "
            "em dezembro de 2020, no valor de R$ 6.000,00"
        )

    def test_vazio(self):
        assert formatar_preservacoes("") == ""

    def test_texto_normal_nao_altera(self):
        assert formatar_preservacoes("texto qualquer") == "texto qualquer"


class TestFormatarListaProcessos:
    def test_unico(self):
        assert formatar_lista_processos("0000001-61.2022.5.10.0017") == (
            "0000001-61.2022.5.10.0017"
        )

    def test_dois(self):
        entrada = "0000001-61.2022.5.10.0017;0000443-05.2023.5.10.0013"
        assert formatar_lista_processos(entrada) == (
            "0000001-61.2022.5.10.0017 e nº 0000443-05.2023.5.10.0013"
        )

    def test_tres(self):
        entrada = "0000001-61.2022.5.10.0017;0000443-05.2023.5.10.0013;0000999-88.2024.5.10.0001"
        assert formatar_lista_processos(entrada) == (
            "0000001-61.2022.5.10.0017, nº 0000443-05.2023.5.10.0013 e "
            "nº 0000999-88.2024.5.10.0001"
        )

    def test_sem_ponto_virgula(self):
        assert formatar_lista_processos("texto sem separador") == "texto sem separador"

    def test_nao_cnj_nao_altera(self):
        assert formatar_lista_processos("abc;def") == "abc;def"


class TestHumanizarRegistro:
    def test_preservacao(self):
        reg = {"Nome": "João", "PreservacaoSP": "07/2012,R$7.487,54"}
        resultado = humanizar_registro(reg)
        assert resultado["Nome"] == "João"
        assert resultado["PreservacaoSP"] == "em julho de 2012, no valor de R$ 7.487,54"

    def test_rt_multipla(self):
        reg = {"RT_Indenizatoria": "0000001-61.2022.5.10.0017;0000443-05.2023.5.10.0013"}
        resultado = humanizar_registro(reg)
        assert resultado["RT_Indenizatoria"] == (
            "0000001-61.2022.5.10.0017 e nº 0000443-05.2023.5.10.0013"
        )

    def test_valores_normais_nao_alterados(self):
        reg = {"Nome": "Maria", "CPF": "123.456.789-00", "Genero": "F"}
        resultado = humanizar_registro(reg)
        assert resultado == reg

    def test_valor_vazio(self):
        reg = {"Campo": "", "Outro": "  "}
        resultado = humanizar_registro(reg)
        assert resultado["Campo"] == ""
        assert resultado["Outro"] == "  "
