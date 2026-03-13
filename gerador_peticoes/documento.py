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
        # Limpa chaves órfãs (ex.: '{' solto sem '}' correspondente)
        if '{' in texto_completo or '}' in texto_completo:
            texto_limpo = texto_completo.replace('{', '').replace('}', '')
            if texto_limpo != texto_completo and paragrafo.runs:
                paragrafo.runs[0].text = texto_limpo
                for run in paragrafo.runs[1:]:
                    run.text = ""
        return

    texto_substituido = texto_completo
    for chave, valor in variaveis.items():
        texto_substituido = texto_substituido.replace("{" + chave + "}", valor)

    # Limpa placeholders que sobraram (não mapeados)
    texto_substituido = re.sub(r'\{[^}]+\}', '', texto_substituido)
    # Limpa chaves órfãs residuais
    texto_substituido = texto_substituido.replace('{', '').replace('}', '')

    if texto_substituido == texto_completo:
        return

    if paragrafo.runs:
        paragrafo.runs[0].text = texto_substituido
        for run in paragrafo.runs[1:]:
            run.text = ""


def _remover_paragrafo(paragrafo) -> None:
    """Remove um parágrafo do documento XML."""
    elemento = paragrafo._element
    elemento.getparent().remove(elemento)


def _remover_secao_42(doc: Document) -> None:
    """
    Remove toda a seção 4.2 da petição (parágrafos do '4.2' até o próximo
    item de mesmo nível ou superior, ex.: '4.3', '5', etc.).
    """
    paragrafos = doc.paragraphs
    inicio = None
    a_remover = []

    for i, p in enumerate(paragrafos):
        texto = p.text.strip()
        if inicio is None:
            # Procura o início da seção 4.2
            if re.match(r'^4\.2[\s.\-–—]', texto) or texto == "4.2":
                inicio = i
                a_remover.append(p)
        else:
            # Verifica se chegamos na próxima seção (4.3, 5, etc.)
            match = re.match(r'^(\d+(?:\.\d+)*)[\s.\-–—]', texto)
            if match:
                secao_encontrada = match.group(1)
                # Se é uma seção diferente de 4.2 e suas subseções
                if (secao_encontrada != "4.2"
                        and not secao_encontrada.startswith("4.2.")):
                    break
            a_remover.append(p)

    for p in reversed(a_remover):
        _remover_paragrafo(p)


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


def gerar_peticao(
    modelo_path: Path,
    variaveis: dict[str, str],
    saida_path: Path,
    remover_secao_preservacao: bool = False,
) -> None:
    """Gera uma petição personalizada a partir de um modelo .docx."""
    doc = Document(str(modelo_path))
    if remover_secao_preservacao:
        _remover_secao_42(doc)
    substituir_variaveis_no_documento(doc, variaveis)
    saida_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(saida_path))


def nome_arquivo_seguro(nome: str) -> str:
    """Remove caracteres não permitidos em nomes de arquivo."""
    return re.sub(r'[<>:"/\\|?*]', '', nome).strip()
