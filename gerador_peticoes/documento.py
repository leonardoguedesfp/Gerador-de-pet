"""Geração de petições a partir de modelos Word (.docx)."""

import re
from pathlib import Path

from docx import Document


def _substituir_em_paragrafo(paragrafo, variaveis: dict[str, str]) -> None:
    """
    Substitui variáveis {Chave} em um parágrafo, lidando com o caso
    em que o Word fragmenta o texto em múltiplos runs.
    """
    texto_completo = "".join(run.text for run in paragrafo.runs)
    if not re.search(r'\{[^}]+\}', texto_completo):
        return

    texto_substituido = texto_completo
    for chave, valor in variaveis.items():
        texto_substituido = texto_substituido.replace("{" + chave + "}", valor)

    if texto_substituido == texto_completo:
        return

    if paragrafo.runs:
        paragrafo.runs[0].text = texto_substituido
        for run in paragrafo.runs[1:]:
            run.text = ""


def substituir_variaveis_no_documento(
    doc: Document,
    variaveis: dict[str, str],
) -> None:
    """Substitui todas as variáveis {Chave} no documento Word."""
    # Corpo principal
    for paragrafo in doc.paragraphs:
        _substituir_em_paragrafo(paragrafo, variaveis)

    # Tabelas
    for tabela in doc.tables:
        for linha in tabela.rows:
            for celula in linha.cells:
                for paragrafo in celula.paragraphs:
                    _substituir_em_paragrafo(paragrafo, variaveis)

    # Cabeçalhos e rodapés
    for secao in doc.sections:
        for hf in [
            secao.header, secao.footer,
            secao.first_page_header, secao.first_page_footer,
            secao.even_page_header, secao.even_page_footer,
        ]:
            if hf is None:
                continue
            for paragrafo in hf.paragraphs:
                _substituir_em_paragrafo(paragrafo, variaveis)
            for tabela in hf.tables:
                for linha in tabela.rows:
                    for celula in linha.cells:
                        for paragrafo in celula.paragraphs:
                            _substituir_em_paragrafo(paragrafo, variaveis)


def _remover_paragrafo(paragrafo) -> None:
    """Remove um parágrafo do documento Word."""
    p = paragrafo._element
    p.getparent().remove(p)


def _remover_item_4_2(doc: Document) -> None:
    """Remove parágrafos pertencentes ao item 4.2 do documento."""
    dentro_item = False
    paragrafos_remover = []

    for paragrafo in doc.paragraphs:
        texto = paragrafo.text.strip()

        if re.match(r'^4\.2[\s.\-–—)]', texto):
            dentro_item = True
            paragrafos_remover.append(paragrafo)
            continue

        if dentro_item:
            if re.match(r'^[0-9]+(\.[0-9]+)*[\s.\-–—)]', texto):
                dentro_item = False
            else:
                paragrafos_remover.append(paragrafo)

    for p in paragrafos_remover:
        _remover_paragrafo(p)


def gerar_peticao(
    modelo_path: Path,
    variaveis: dict[str, str],
    saida_path: Path,
) -> None:
    """Gera uma petição personalizada a partir de um modelo .docx."""
    doc = Document(str(modelo_path))
    substituir_variaveis_no_documento(doc, variaveis)

    if not variaveis.get("PreservacaoSP", "").strip():
        _remover_item_4_2(doc)

    saida_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(saida_path))


def nome_arquivo_seguro(nome: str) -> str:
    """Remove caracteres não permitidos em nomes de arquivo."""
    return re.sub(r'[<>:"/\\|?*]', '', nome).strip()
