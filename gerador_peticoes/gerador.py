"""Lógica principal de geração de petições."""

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .config import Config
from .documento import gerar_peticao, nome_arquivo_seguro
from .exceptions import ArquivoNaoEncontradoError, PlanilhaInvalidaError
from .formatacao import detectar_coluna_data
from .logger import Logger
from .planilha import ler_planilha
from .relatorio import gerar_relatorio_conferencia


def _verificar_entrada(cfg: Config) -> None:
    """Verifica se os arquivos de entrada existem."""
    faltando = []
    for path, desc in [
        (cfg.planilha_path, "Planilha"),
        (cfg.modelo_m_path, "Modelo masculino"),
        (cfg.modelo_f_path, "Modelo feminino"),
    ]:
        if not path.exists():
            faltando.append(f"  {desc} não encontrado: {path}")

    if faltando:
        raise ArquivoNaoEncontradoError(
            "Arquivos de entrada não encontrados:\n" + "\n".join(faltando)
        )


def _processar_registro(
    i: int,
    registro: dict[str, str],
    cfg: Config,
    log: Logger,
) -> dict:
    """Processa um único registro e retorna o resultado para o relatório."""
    nome = registro.get(cfg.coluna_nome, "").strip()
    genero = registro.get(cfg.coluna_genero, "").strip().upper()

    resultado = {
        "numero": i,
        "nome": nome,
        "genero": genero,
        "arquivo": "",
        "status": "",
        "observacao": "",
    }
    for col in cfg.colunas_relatorio:
        resultado[col] = registro.get(col, "")

    if not nome:
        log.aviso(f"  [{i:03d}] Registro sem nome. Pulando...")
        resultado["status"] = "AVISO"
        resultado["observacao"] = "Registro sem nome na planilha"
        return resultado

    if genero == "M":
        modelo = cfg.modelo_m_path
    elif genero == "F":
        modelo = cfg.modelo_f_path
    else:
        log.aviso(f"  [{i:03d}] Gênero inválido '{genero}' para {nome}. Pulando...")
        resultado["status"] = "AVISO"
        resultado["observacao"] = f"Gênero inválido: '{genero}' (esperado M ou F)"
        return resultado

    nome_arq = f"{cfg.prefixo_arquivo} - {nome_arquivo_seguro(nome)}.docx"
    caminho_saida = cfg.dir_saida / nome_arq
    resultado["arquivo"] = nome_arq

    if cfg.dry_run:
        log.info(f"  [{i:03d}] SIMULAÇÃO: {nome_arq}")
        resultado["status"] = "OK"
        resultado["observacao"] = "Simulação (dry-run)"
        return resultado

    try:
        gerar_peticao(modelo, registro, caminho_saida)
        log.info(f"  [{i:03d}] OK: {nome_arq}")
        resultado["status"] = "OK"
    except Exception as e:
        log.erro(f"  [{i:03d}] ERRO ao gerar petição para {nome}: {e}")
        resultado["status"] = "ERRO"
        resultado["observacao"] = str(e)

    return resultado


def executar(cfg: Config) -> int:
    """
    Executa o fluxo completo de geração de petições.

    Retorna 0 em caso de sucesso, 1 em caso de erro fatal.
    """
    cfg.dir_saida.mkdir(parents=True, exist_ok=True)
    caminho_log = cfg.dir_saida / "log_execucao.txt"

    with Logger(caminho_log) as log:
        log.info("=" * 65)
        log.info("  GERADOR AUTOMÁTICO DE PETIÇÕES PERSONALIZADAS")
        if cfg.dry_run:
            log.info("  ** MODO SIMULAÇÃO (dry-run) — nenhum arquivo será gerado **")
        log.info("=" * 65)
        log.info("")

        if cfg.nome_execucao:
            log.info(f"Execução: {cfg.nome_execucao}")
        log.info(f"Pasta de entrada: {cfg.dir_entrada.resolve()}")
        log.info(f"Pasta de saída:   {cfg.dir_saida.resolve()}")
        log.info("")

        try:
            _verificar_entrada(cfg)
        except ArquivoNaoEncontradoError as e:
            log.erro(str(e))
            log.info(
                "\nCertifique-se de que os arquivos 'dados_clientes.xlsx', "
                "'modelo_masculino.docx' e 'modelo_feminino.docx' "
                f"estão na pasta '{cfg.dir_entrada}'"
            )
            return 1

        log.info(f"Lendo planilha: {cfg.planilha_path.name}")
        cabecalhos, dados = ler_planilha(
            cfg.planilha_path, cfg.colunas_monetarias, cfg.formato_data,
        )
        log.info(f"  Colunas encontradas: {', '.join(cabecalhos)}")
        log.info(f"  Total de registros:  {len(dados)}")

        colunas_data = [c for c in cabecalhos if detectar_coluna_data(c)]
        if colunas_data:
            log.info(f"  Colunas de data detectadas: {', '.join(colunas_data)}")
        monetarias = [c for c in cfg.colunas_monetarias if c in cabecalhos]
        if monetarias:
            log.info(f"  Colunas monetárias: {', '.join(monetarias)}")
        log.info("")

        if cfg.coluna_genero not in cabecalhos:
            log.erro(f"Coluna '{cfg.coluna_genero}' não encontrada na planilha.")
            log.info(f"  Colunas disponíveis: {', '.join(cabecalhos)}")
            return 1

        if cfg.coluna_nome not in cabecalhos:
            log.erro(f"Coluna '{cfg.coluna_nome}' não encontrada na planilha.")
            log.info(f"  Colunas disponíveis: {', '.join(cabecalhos)}")
            return 1

        if not dados:
            log.aviso("A planilha não contém dados (apenas cabeçalho).")
            return 0

        log.info("Gerando petições...")
        log.info("-" * 65)

        resultados: list[dict] = []

        if cfg.workers > 1 and len(dados) > 1:
            with ThreadPoolExecutor(max_workers=cfg.workers) as pool:
                futures = {
                    pool.submit(_processar_registro, i, reg, cfg, log): i
                    for i, reg in enumerate(dados, start=1)
                }
                for future in as_completed(futures):
                    resultados.append(future.result())
            resultados.sort(key=lambda r: r["numero"])
        else:
            for i, registro in enumerate(dados, start=1):
                resultados.append(_processar_registro(i, registro, cfg, log))

        total_ok = sum(1 for r in resultados if r["status"] == "OK")
        total_erros = sum(1 for r in resultados if r["status"] != "OK")

        log.info("-" * 65)
        log.info("")
        log.info(f"  Petições geradas com sucesso: {total_ok}")
        if total_erros > 0:
            log.info(f"  Registros com erro/aviso:     {total_erros}")
        log.info(f"  Total de registros:            {len(dados)}")
        log.info(f"  Pasta de saída: {cfg.dir_saida.resolve()}")
        log.info("")

        caminho_relatorio = cfg.dir_saida / "relatorio_conferencia.xlsx"
        try:
            gerar_relatorio_conferencia(
                resultados, caminho_relatorio, log,
                cfg.colunas_relatorio, cfg.nome_execucao,
            )
        except Exception as e:
            log.erro(f"Erro ao gerar relatório de conferência: {e}")

        log.info(f"  Log de execução: {caminho_log.name}")
        log.info("")
        log.info("Concluído!")

    return 0
