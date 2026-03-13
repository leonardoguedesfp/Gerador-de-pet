"""Geração de petições a partir de modelos Word (.docx)."""

import re
from pathlib import Path

from docx import Document

_NS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
_PADRAO_SE = re.compile(r'\{SE:(\w+)\}')
_PADRAO_FIM_SE = re.compile(r'\{FIM_SE:(\w+)\}')


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


# ---------------------------------------------------------------------------
# Blocos condicionais: {SE:Campo} ... {FIM_SE:Campo}
# ---------------------------------------------------------------------------

def _get_text_from_element(elem):
    """Extrai texto completo de um elemento XML, concatenando todos os <w:t>."""
    return ''.join(t.text or '' for t in elem.iter(f'{_NS}t'))


def _processar_condicionais_em_container(container, variaveis: dict[str, str]) -> None:
    """
    Remove blocos {SE:Campo}...{FIM_SE:Campo} do container XML quando
    o campo está vazio. Se o campo tem valor, os marcadores são mantidos
    (serão limpos depois pela substituição de variáveis).

    Opera sobre TODOS os filhos diretos do container (parágrafos e tabelas),
    permitindo que blocos condicionais contenham tabelas inteiras.
    """
    filhos = list(container)
    remover = []
    dentro_bloco = None

    for filho in filhos:
        texto = _get_text_from_element(filho)

        if dentro_bloco is None:
            match = _PADRAO_SE.search(texto)
            if match:
                campo = match.group(1)
                valor = variaveis.get(campo, '').strip()
                if not valor:
                    # Campo vazio: marcar para remoção
                    dentro_bloco = campo
                    remover.append(filho)
        else:
            # Dentro de um bloco condicional vazio: marcar para remoção
            remover.append(filho)
            if _PADRAO_FIM_SE.search(texto):
                match_fim = _PADRAO_FIM_SE.search(texto)
                if match_fim and match_fim.group(1) == dentro_bloco:
                    dentro_bloco = None

    for elem in remover:
        container.remove(elem)


def _coletar_marcadores_condicionais(doc: Document) -> dict[str, str]:
    """
    Varre o documento em busca de marcadores {SE:X} e {FIM_SE:X}
    remanescentes (de blocos que foram MANTIDOS) e retorna um dict
    mapeando cada marcador para string vazia, para que a substituição
    de variáveis os limpe.
    """
    marcadores = {}

    def _varrer_paragrafos(paragrafos):
        for para in paragrafos:
            texto = "".join(run.text for run in para.runs)
            for m in re.finditer(r'((?:SE|FIM_SE):\w+)', texto):
                marcadores[m.group(1)] = ""

    # Corpo
    _varrer_paragrafos(doc.paragraphs)

    # Tabelas
    for tabela in doc.tables:
        for linha in tabela.rows:
            for celula in linha.cells:
                _varrer_paragrafos(celula.paragraphs)

    # Cabeçalhos e rodapés
    for secao in doc.sections:
        for hf in [
            secao.header, secao.footer,
            secao.first_page_header, secao.first_page_footer,
            secao.even_page_header, secao.even_page_footer,
        ]:
            if hf is None:
                continue
            _varrer_paragrafos(hf.paragraphs)
            for tabela in hf.tables:
                for linha in tabela.rows:
                    for celula in linha.cells:
                        _varrer_paragrafos(celula.paragraphs)

    return marcadores


def processar_blocos_condicionais(doc: Document, variaveis: dict[str, str]) -> None:
    """
    Processa todos os blocos condicionais {SE:Campo}...{FIM_SE:Campo}
    no documento.

    - Se 'Campo' estiver vazio em variaveis: remove o bloco inteiro
      (parágrafos, tabelas e qualquer elemento entre os marcadores).
    - Se 'Campo' tiver valor: mantém o bloco e limpa os marcadores.
    """
    # Processar corpo do documento
    _processar_condicionais_em_container(doc._element.body, variaveis)

    # Processar tabelas no corpo (condicionais dentro de células)
    for tabela in doc.tables:
        for linha in tabela.rows:
            for celula in linha.cells:
                _processar_condicionais_em_container(celula._tc, variaveis)

    # Processar cabeçalhos e rodapés
    for secao in doc.sections:
        for hf in [
            secao.header, secao.footer,
            secao.first_page_header, secao.first_page_footer,
            secao.even_page_header, secao.even_page_footer,
        ]:
            if hf is None:
                continue
            _processar_condicionais_em_container(hf._element, variaveis)


def gerar_peticao(
    modelo_path: Path,
    variaveis: dict[str, str],
    saida_path: Path,
) -> None:
    """
    Gera uma petição personalizada a partir de um modelo .docx.

    Fluxo:
    1. Processa blocos condicionais (remove seções de campos vazios)
    2. Coleta marcadores remanescentes e os adiciona como variáveis vazias
    3. Substitui todas as variáveis {Chave} pelos valores
    """
    doc = Document(str(modelo_path))

    # 1. Remover blocos condicionais de campos vazios
    processar_blocos_condicionais(doc, variaveis)

    # 2. Coletar marcadores {SE:X}/{FIM_SE:X} restantes para limpeza
    marcadores = _coletar_marcadores_condicionais(doc)
    variaveis_completas = dict(variaveis)
    variaveis_completas.update(marcadores)

    # 3. Substituir variáveis
    substituir_variaveis_no_documento(doc, variaveis_completas)

    saida_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(saida_path))


def nome_arquivo_seguro(nome: str) -> str:
    """Remove caracteres não permitidos em nomes de arquivo."""
    return re.sub(r'[<>:"/\\|?*]', '', nome).strip()
