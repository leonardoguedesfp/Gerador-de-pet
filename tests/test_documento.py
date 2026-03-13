"""Testes para o módulo de documento."""

import pytest

from gerador_peticoes.documento import (
    nome_arquivo_seguro,
    gerar_peticao,
    processar_blocos_condicionais,
)

from docx import Document


class TestNomeArquivoSeguro:
    def test_remove_caracteres_proibidos(self):
        assert nome_arquivo_seguro('João <Silva>') == "João Silva"

    def test_remove_aspas_e_barras(self):
        assert nome_arquivo_seguro('Maria "Ana" S/A') == "Maria Ana SA"

    def test_strip(self):
        assert nome_arquivo_seguro("  José  ") == "José"

    def test_nome_limpo(self):
        assert nome_arquivo_seguro("Carlos Santos") == "Carlos Santos"


class TestGerarPeticao:
    def test_substituicao_basica(self, tmp_path):
        # Cria modelo
        modelo = tmp_path / "modelo.docx"
        doc = Document()
        doc.add_paragraph("Eu, {Nome}, portador do CPF {CPF}.")
        doc.save(str(modelo))

        saida = tmp_path / "saida" / "peticao.docx"
        gerar_peticao(modelo, {"Nome": "João Silva", "CPF": "123.456.789-00"}, saida)

        assert saida.exists()
        doc_resultado = Document(str(saida))
        texto = doc_resultado.paragraphs[0].text
        assert "João Silva" in texto
        assert "123.456.789-00" in texto
        assert "{Nome}" not in texto

    def test_variavel_nao_encontrada_permanece(self, tmp_path):
        modelo = tmp_path / "modelo.docx"
        doc = Document()
        doc.add_paragraph("Valor: {ValorInexistente}")
        doc.save(str(modelo))

        saida = tmp_path / "peticao.docx"
        gerar_peticao(modelo, {"Nome": "Test"}, saida)

        doc_resultado = Document(str(saida))
        assert "{ValorInexistente}" in doc_resultado.paragraphs[0].text


class TestBlocosCondicionais:
    def test_bloco_removido_quando_campo_vazio(self, tmp_path):
        """Bloco {SE:Campo}...{FIM_SE:Campo} é removido se Campo está vazio."""
        modelo = tmp_path / "modelo.docx"
        doc = Document()
        doc.add_paragraph("Parágrafo 1 - antes do bloco.")
        doc.add_paragraph("{SE:PreservacaoSP}")
        doc.add_paragraph("4.2. Texto sobre preservação com {ListaPreservacoes}.")
        doc.add_paragraph("{FIM_SE:PreservacaoSP}")
        doc.add_paragraph("Parágrafo final - depois do bloco.")
        doc.save(str(modelo))

        saida = tmp_path / "saida.docx"
        variaveis = {
            "PreservacaoSP": "",
            "ListaPreservacoes": "",
        }
        gerar_peticao(modelo, variaveis, saida)

        doc_resultado = Document(str(saida))
        textos = [p.text for p in doc_resultado.paragraphs]
        assert "Parágrafo 1 - antes do bloco." in textos
        assert "Parágrafo final - depois do bloco." in textos
        assert not any("4.2" in t for t in textos)
        assert not any("SE:" in t for t in textos)

    def test_bloco_mantido_quando_campo_com_valor(self, tmp_path):
        """Bloco é mantido e marcadores são limpos se Campo tem valor."""
        modelo = tmp_path / "modelo.docx"
        doc = Document()
        doc.add_paragraph("Parágrafo 1.")
        doc.add_paragraph("{SE:PreservacaoSP}")
        doc.add_paragraph("4.2. Preservação: {ListaPreservacoes}.")
        doc.add_paragraph("{FIM_SE:PreservacaoSP}")
        doc.add_paragraph("Parágrafo final.")
        doc.save(str(modelo))

        saida = tmp_path / "saida.docx"
        variaveis = {
            "PreservacaoSP": "07/2012,R$7.487,54",
            "ListaPreservacoes": "em julho de 2012, no valor de R$ 7.487,54",
        }
        gerar_peticao(modelo, variaveis, saida)

        doc_resultado = Document(str(saida))
        textos = [p.text for p in doc_resultado.paragraphs]
        assert "Parágrafo 1." in textos
        assert "Parágrafo final." in textos
        # Conteúdo do bloco presente com variável substituída
        texto_preservacao = [t for t in textos if "4.2" in t]
        assert len(texto_preservacao) == 1
        assert "julho de 2012" in texto_preservacao[0]
        # Marcadores foram limpos
        assert not any("{SE:" in t for t in textos)
        assert not any("{FIM_SE:" in t for t in textos)

    def test_multiplos_blocos_condicionais(self, tmp_path):
        """Múltiplos blocos condicionais independentes."""
        modelo = tmp_path / "modelo.docx"
        doc = Document()
        doc.add_paragraph("Início.")
        doc.add_paragraph("{SE:CampoA}")
        doc.add_paragraph("Conteúdo A.")
        doc.add_paragraph("{FIM_SE:CampoA}")
        doc.add_paragraph("Meio.")
        doc.add_paragraph("{SE:CampoB}")
        doc.add_paragraph("Conteúdo B.")
        doc.add_paragraph("{FIM_SE:CampoB}")
        doc.add_paragraph("Fim.")
        doc.save(str(modelo))

        saida = tmp_path / "saida.docx"
        # CampoA tem valor (mantém), CampoB vazio (remove)
        variaveis = {"CampoA": "sim", "CampoB": ""}
        gerar_peticao(modelo, variaveis, saida)

        doc_resultado = Document(str(saida))
        textos = [p.text for p in doc_resultado.paragraphs]
        assert "Início." in textos
        assert "Conteúdo A." in textos
        assert "Meio." in textos
        assert "Conteúdo B." not in textos
        assert "Fim." in textos

    def test_bloco_com_multiplos_paragrafos(self, tmp_path):
        """Bloco condicional com vários parágrafos internos."""
        modelo = tmp_path / "modelo.docx"
        doc = Document()
        doc.add_paragraph("Antes.")
        doc.add_paragraph("{SE:Campo}")
        doc.add_paragraph("Linha 1 do bloco.")
        doc.add_paragraph("Linha 2 do bloco.")
        doc.add_paragraph("Linha 3 do bloco.")
        doc.add_paragraph("{FIM_SE:Campo}")
        doc.add_paragraph("Depois.")
        doc.save(str(modelo))

        saida = tmp_path / "saida.docx"
        variaveis = {"Campo": ""}
        gerar_peticao(modelo, variaveis, saida)

        doc_resultado = Document(str(saida))
        textos = [p.text for p in doc_resultado.paragraphs]
        assert "Antes." in textos
        assert "Depois." in textos
        assert not any("Linha" in t for t in textos)

    def test_bloco_condicional_nao_afeta_outros_paragrafos(self, tmp_path):
        """Remoção de bloco condicional não afeta parágrafos fora do bloco."""
        modelo = tmp_path / "modelo.docx"
        doc = Document()
        doc.add_paragraph("Item 1.")
        doc.add_paragraph("Item 2.")
        doc.add_paragraph("Item 3.")
        doc.add_paragraph("{SE:CampoVazio}")
        doc.add_paragraph("Item 4.2 condicional.")
        doc.add_paragraph("{FIM_SE:CampoVazio}")
        doc.add_paragraph("Item 5.")
        doc.add_paragraph("Item 6.")
        doc.save(str(modelo))

        saida = tmp_path / "saida.docx"
        variaveis = {"CampoVazio": ""}
        gerar_peticao(modelo, variaveis, saida)

        doc_resultado = Document(str(saida))
        textos = [p.text for p in doc_resultado.paragraphs]
        assert "Item 1." in textos
        assert "Item 2." in textos
        assert "Item 3." in textos
        assert "Item 5." in textos
        assert "Item 6." in textos
        assert "Item 4.2 condicional." not in textos


class TestIntegracaoCompleta:
    def test_peticao_com_preservacao(self, tmp_path):
        """Cenário real: cliente com preservação — item 4.2 mantido."""
        modelo = tmp_path / "modelo.docx"
        doc = Document()
        doc.add_paragraph("Eu, {Nome}, venho requerer:")
        doc.add_paragraph("4.1. A condenação da ré.")
        doc.add_paragraph("{SE:PreservacaoSP}")
        doc.add_paragraph("4.2. Preservou salário de participação {ListaPreservacoes}.")
        doc.add_paragraph("{FIM_SE:PreservacaoSP}")
        doc.add_paragraph("5. Pedidos finais.")
        doc.save(str(modelo))

        saida = tmp_path / "saida.docx"
        variaveis = {
            "Nome": "Almir",
            "PreservacaoSP": "07/2012,R$7.487,54",
            "ListaPreservacoes": "em julho de 2012, no valor de R$ 7.487,54",
        }
        gerar_peticao(modelo, variaveis, saida)

        doc_resultado = Document(str(saida))
        textos = [p.text for p in doc_resultado.paragraphs]
        assert "Eu, Almir, venho requerer:" in textos
        assert "4.1. A condenação da ré." in textos
        texto_42 = [t for t in textos if "4.2" in t]
        assert len(texto_42) == 1
        assert "julho de 2012" in texto_42[0]
        assert "R$ 7.487,54" in texto_42[0]
        assert "5. Pedidos finais." in textos

    def test_peticao_sem_preservacao(self, tmp_path):
        """Cenário real: cliente sem preservação — item 4.2 removido."""
        modelo = tmp_path / "modelo.docx"
        doc = Document()
        doc.add_paragraph("Eu, {Nome}, venho requerer:")
        doc.add_paragraph("4.1. A condenação da ré.")
        doc.add_paragraph("{SE:PreservacaoSP}")
        doc.add_paragraph("4.2. Preservou salário de participação {ListaPreservacoes}.")
        doc.add_paragraph("{FIM_SE:PreservacaoSP}")
        doc.add_paragraph("5. Pedidos finais.")
        doc.save(str(modelo))

        saida = tmp_path / "saida.docx"
        variaveis = {
            "Nome": "Roseli",
            "PreservacaoSP": "",
            "ListaPreservacoes": "",
        }
        gerar_peticao(modelo, variaveis, saida)

        doc_resultado = Document(str(saida))
        textos = [p.text for p in doc_resultado.paragraphs]
        assert "Eu, Roseli, venho requerer:" in textos
        assert "4.1. A condenação da ré." in textos
        assert not any("4.2" in t for t in textos)
        assert not any("ListaPreservacoes" in t for t in textos)
        assert "5. Pedidos finais." in textos

    def test_peticao_com_rts_multiplas(self, tmp_path):
        """Cenário Denilson: duas RTs indenizatórias formatadas."""
        modelo = tmp_path / "modelo.docx"
        doc = Document()
        doc.add_paragraph(
            "{Nome} ajuizou a reclamação trabalhista nº {ListaRTs}."
        )
        doc.add_paragraph(
            "Requer suspensão até trânsito em julgado da RT {ListaRTsComDoc}."
        )
        doc.save(str(modelo))

        saida = tmp_path / "saida.docx"
        variaveis = {
            "Nome": "Denilson",
            "ListaRTs": (
                "0000001-61.2022.5.10.0017 e nº 0000443-05.2023.5.10.0013"
            ),
            "ListaRTsComDoc": (
                "0000001-61.2022.5.10.0017 e nº 0000443-05.2023.5.10.0013"
            ),
        }
        gerar_peticao(modelo, variaveis, saida)

        doc_resultado = Document(str(saida))
        textos = [p.text for p in doc_resultado.paragraphs]
        assert "e nº" in textos[0]
        assert "{ListaRTs}" not in textos[0]
        assert "{ListaRTsComDoc}" not in textos[1]

    def test_peticao_genebaldo_4_preservacoes(self, tmp_path):
        """Cenário Genebaldo: 4 preservações formatadas corretamente."""
        modelo = tmp_path / "modelo.docx"
        doc = Document()
        doc.add_paragraph("{SE:PreservacaoSP}")
        doc.add_paragraph(
            "4.2. O reclamante preservou seu salário de participação "
            "{ListaPreservacoes}."
        )
        doc.add_paragraph("{FIM_SE:PreservacaoSP}")
        doc.save(str(modelo))

        saida = tmp_path / "saida.docx"
        variaveis = {
            "PreservacaoSP": (
                "3/2013,R$6.622,33;5/2013,R$8.419,03;"
                "8/2013,R$8.631,77;8/2014,R$9.418,28"
            ),
            "ListaPreservacoes": (
                "em março de 2013, no valor de R$ 6.622,33, "
                "em maio de 2013, no valor de R$ 8.419,03, "
                "em agosto de 2013, no valor de R$ 8.631,77 e "
                "em agosto de 2014, no valor de R$ 9.418,28"
            ),
        }
        gerar_peticao(modelo, variaveis, saida)

        doc_resultado = Document(str(saida))
        textos = [p.text for p in doc_resultado.paragraphs]
        texto_42 = [t for t in textos if "4.2" in t]
        assert len(texto_42) == 1
        assert "março de 2013" in texto_42[0]
        assert "maio de 2013" in texto_42[0]
        assert "agosto de 2013" in texto_42[0]
        assert "agosto de 2014" in texto_42[0]
        assert "R$ 9.418,28" in texto_42[0]
        assert "{ListaPreservacoes}" not in texto_42[0]
