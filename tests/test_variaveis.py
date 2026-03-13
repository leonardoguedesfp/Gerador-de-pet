"""Testes para o módulo de variáveis derivadas."""

from gerador_peticoes.variaveis import (
    computar_variaveis_derivadas,
    _extrair_preservacoes,
    _formatar_preservacoes,
)


class TestComputarVariaveisDerivadas:
    def test_lista_rts_vem_de_verbas_trabalhistas(self):
        registro = {
            "Nome": "Sérgio de Paula Souza",
            "RT_VerbasTrabalhistas": "0001604-98.2014.5.10.0002",
            "RT_Indenizatoria": "0000002-28.2021.5.10.0002",
        }
        resultado = computar_variaveis_derivadas(registro)
        assert resultado["ListaRTs"] == "0001604-98.2014.5.10.0002"
        assert resultado["ListaRTsComDoc"] == "0001604-98.2014.5.10.0002"

    def test_rt_anterior_vem_de_indenizatoria(self):
        registro = {
            "Nome": "Sérgio de Paula Souza",
            "RT_VerbasTrabalhistas": "0001604-98.2014.5.10.0002",
            "RT_Indenizatoria": "0000002-28.2021.5.10.0002",
        }
        resultado = computar_variaveis_derivadas(registro)
        assert resultado["RTAnterior"] == "0000002-28.2021.5.10.0002"

    def test_rts_nao_trocadas(self):
        """Verifica que ListaRTs != RT_Indenizatoria (bug original)."""
        registro = {
            "RT_VerbasTrabalhistas": "0001604-98.2014.5.10.0002",
            "RT_Indenizatoria": "0000002-28.2021.5.10.0002",
        }
        resultado = computar_variaveis_derivadas(registro)
        assert resultado["ListaRTs"] != resultado["RTAnterior"]
        assert resultado["ListaRTs"] == "0001604-98.2014.5.10.0002"
        assert resultado["RTAnterior"] == "0000002-28.2021.5.10.0002"

    def test_sem_colunas_rt(self):
        registro = {"Nome": "João", "Genero": "M"}
        resultado = computar_variaveis_derivadas(registro)
        assert "ListaRTs" not in resultado
        assert "RTAnterior" not in resultado

    def test_preserva_dados_originais(self):
        registro = {"Nome": "João", "CPF": "123.456.789-00"}
        resultado = computar_variaveis_derivadas(registro)
        assert resultado["Nome"] == "João"
        assert resultado["CPF"] == "123.456.789-00"

    def test_preservacoes_padrao_data_valor(self):
        registro = {
            "Nome": "Genebaldo",
            "PreservacaoData1": "6/2017",
            "PreservacaoValor1": "R$9.729,16",
        }
        resultado = computar_variaveis_derivadas(registro)
        assert resultado["ListaPreservacoes"] == "em 6/2017, no importe de R$9.729,16"

    def test_preservacoes_multiplas(self):
        registro = {
            "PreservacaoData1": "6/2017",
            "PreservacaoValor1": "R$9.729,16",
            "PreservacaoData2": "12/2018",
            "PreservacaoValor2": "R$5.000,00",
        }
        resultado = computar_variaveis_derivadas(registro)
        esperado = (
            "em 6/2017, no importe de R$9.729,16; "
            "em 12/2018, no importe de R$5.000,00"
        )
        assert resultado["ListaPreservacoes"] == esperado

    def test_sem_preservacoes(self):
        registro = {"Nome": "João"}
        resultado = computar_variaveis_derivadas(registro)
        assert "ListaPreservacoes" not in resultado


class TestExtrairPreservacoes:
    def test_padrao_com_underscore(self):
        registro = {
            "Preservacao_Data_1": "6/2017",
            "Preservacao_Valor_1": "R$9.729,16",
        }
        resultado = _extrair_preservacoes(registro)
        assert resultado == [("6/2017", "R$9.729,16")]

    def test_padrao_sem_underscore(self):
        registro = {
            "PreservacaoData1": "6/2017",
            "PreservacaoValor1": "R$9.729,16",
        }
        resultado = _extrair_preservacoes(registro)
        assert resultado == [("6/2017", "R$9.729,16")]

    def test_padrao_numero_no_meio(self):
        registro = {
            "Preservacao_1_Data": "6/2017",
            "Preservacao_1_Valor": "R$9.729,16",
        }
        resultado = _extrair_preservacoes(registro)
        assert resultado == [("6/2017", "R$9.729,16")]

    def test_ordena_por_indice(self):
        registro = {
            "PreservacaoData3": "1/2020",
            "PreservacaoValor3": "R$1.000,00",
            "PreservacaoData1": "6/2017",
            "PreservacaoValor1": "R$9.729,16",
        }
        resultado = _extrair_preservacoes(registro)
        assert resultado[0] == ("6/2017", "R$9.729,16")
        assert resultado[1] == ("1/2020", "R$1.000,00")

    def test_ignora_par_incompleto(self):
        registro = {
            "PreservacaoData1": "6/2017",
            # Falta PreservacaoValor1
        }
        resultado = _extrair_preservacoes(registro)
        assert resultado == []

    def test_ignora_valores_vazios(self):
        registro = {
            "PreservacaoData1": "",
            "PreservacaoValor1": "R$9.729,16",
        }
        resultado = _extrair_preservacoes(registro)
        assert resultado == []

    def test_preservacao_com_cedilha(self):
        registro = {
            "PreservaçãoData1": "6/2017",
            "PreservaçãoValor1": "R$9.729,16",
        }
        resultado = _extrair_preservacoes(registro)
        assert resultado == [("6/2017", "R$9.729,16")]


class TestFormatarPreservacoes:
    def test_uma_preservacao(self):
        assert _formatar_preservacoes([("6/2017", "R$9.729,16")]) == (
            "em 6/2017, no importe de R$9.729,16"
        )

    def test_multiplas(self):
        resultado = _formatar_preservacoes([
            ("6/2017", "R$9.729,16"),
            ("12/2018", "R$5.000,00"),
        ])
        assert resultado == (
            "em 6/2017, no importe de R$9.729,16; "
            "em 12/2018, no importe de R$5.000,00"
        )

    def test_lista_vazia(self):
        assert _formatar_preservacoes([]) == ""
