from Coletores import coleta_preco_DISAPE
from Coletores import coleta_preco_RMP
from Coletores import coleta_preco_SKY
from Coletores import coleta_preco_PELLEGRINO
from Coletores import coleta_preco_AUTONORTE
from Coletores import coleta_preco_SKY_SP
from Coletores import coleta_preco_SKY_PR
from Coletores import coleta_preco_DPK
import pandas as pd
import logging
import datetime as dt
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from functions import tratar_preco_sem_estoque
from load_db import carregar_coleta
from transforms import buscar_comparativo
import time

os.makedirs("checkpoints", exist_ok=True)

# Configuraçao dos logs de busca
logging.basicConfig(
    filename="coletor_precos.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8"
)

def executar_concorrente(nome, modulo, codigos, filiais):
    try:
        if filiais:
            resultado = modulo.executar(codigos,filiais)
        else:
            resultado = modulo.executar(codigos)
        
        resultado.to_excel(f"checkpoints/checkpoint_{nome}.xlsx", index=False)
        
        logging.info(f"{nome}: checkpoint salvo com sucesso")
        
        return nome, resultado, None
    except Exception:
        logging.exception(f"{nome}: falhou")
        return nome, None, True


# funcao orquestradora recebendo uma lista de codigos como parametro e um valor boolean que vem 
# dos checkbox de concorrentes selecionados no app.py
def executar(codigos, disape=True, rmp=True, sky=True, pellegrino=True, autonorte = True,sky_sp = True ,sky_pr = True , dpk= True,
             filiais_disape = None, filiais_rmp = None, filiais_sky = None, filiais_autonorte = None, filiais_sky_sp = None, 
             filiais_sky_pr = None, filiais_dpk= None, callback = None):
    #codigos = ["ECO1651","VC-232"]
    resultados = []

    # se true adiciona a etapa a lista nome / modulo
    etapas = []
    if rmp: etapas.append(("RMP", coleta_preco_RMP, filiais_rmp))
    if disape: etapas.append(("Disape", coleta_preco_DISAPE, filiais_disape))
    if sky: etapas.append(("SkyPecas", coleta_preco_SKY, filiais_sky))
    if pellegrino: etapas.append(("Pellegrino", coleta_preco_PELLEGRINO, None))
    if autonorte: etapas.append(("Auto Norte",coleta_preco_AUTONORTE, filiais_autonorte ))
    if sky_sp: etapas.append(("SKY SP",coleta_preco_SKY_SP, filiais_sky_sp))
    if sky_pr: etapas.append(("SKY PR", coleta_preco_SKY_PR, filiais_sky_pr))
    if dpk: etapas.append(("DPK", coleta_preco_DPK, filiais_dpk))

    # total de etapas é igual ao tamanho da lista definida anteriormente
    total = len(etapas)
    logging.info(f"Iniciando busca de {len(codigos)} códigos em {total} concorrente(s)")

    # paralelização da execução - todos os navegadores abrem simultaneamente com um intervalo de 30s para evitar sobrecarga de rede e memoria
    with ThreadPoolExecutor(max_workers=len(etapas)) as executor:
        tarefas = {}
        
        for nome, modulo, filiais in etapas:
            tarefa = executor.submit(
                executar_concorrente,
                nome,
                modulo,
                codigos,
                filiais
            )
            
            tarefas[tarefa] = nome
            
            time.sleep(30)
        
        for tarefa in as_completed(tarefas):
            nome, resultado, erro = tarefa.result()
            
            if erro:
                logging.error(f"{nome}: coleta falhou")
                
                if callback:
                    callback(
                        len(resultados),
                        total,
                        nome,
                        "Coleta Falhou"
                    )
                    
                continue
            
            resultados.append(resultado)
            
            if callback:
                callback(
                    len(resultados),
                    total,
                    nome,
                    "Coleta Concluida"
                )
            
            logging.info(f"{nome}: busca concluida com sucesso")
    if not resultados:
        return pd.DataFrame()

    # concatenando os dataframes com os resultados
    precos_concorrentes = pd.concat(resultados)
    
    if callback:
        callback(0,0,"","✅ Coletas Concluidas")

    # adicionando coluna com a data da coleta
    precos_concorrentes["data coleta"] = dt.datetime.now()
    
    # se o campo preco vier '--' retornar na coluna status "Sem Estoque"
    precos_concorrentes.loc[precos_concorrentes['preco'] == None, 'status'] = "Sem Estoque"
    
    # removendo hifens e pontos do campo cod_buscado
    precos_concorrentes['cod_buscado'] = precos_concorrentes['cod_buscado'].astype(str).str.strip().str.replace("-","",regex=False).str.replace(".","",regex=False).str.replace(" ","", regex=False)
    precos_concorrentes['cod_fabricante'] = (
    precos_concorrentes['cod_fabricante']
    .astype(str)
    .str.strip()
    .str.replace("-", "", regex=False)
    .str.replace(".", "", regex=False)
    .str.replace(" ", "", regex=False)
    )
    # salvando os registros que atendem as condicionais aplicadas
    valida_similar = (
    (precos_concorrentes['cod_buscado'] != precos_concorrentes['cod_fabricante'])
    & (precos_concorrentes['status'] == 'OK')
    )
    
    # pegando a lista e alterando o valor da coluna status para "Similar"
    precos_concorrentes.loc[valida_similar,'status'] = "Similar"
    
    # Ajusta a coluna status
    precos_concorrentes.loc[
    precos_concorrentes['cod_buscado'] == precos_concorrentes['cod_fabricante'],
    'status'
    ] = 'OK'

    precos_concorrentes.loc[
    (precos_concorrentes['cod_buscado'] != precos_concorrentes['cod_fabricante']) &
    (precos_concorrentes['status'] == 'OK'),
    'status'
    ] = 'Similar'
    
   
    # retirando duplicados com base no subset informado 
    precos_concorrentes = precos_concorrentes.drop_duplicates(
    subset=['fornecedor', 'cod_buscado', 'cod_fabricante', 'filial']
    )
    
    # Removendo linhas vazias da busca
    precos_concorrentes = precos_concorrentes[
        ~(
            precos_concorrentes[['fornecedor', 'cod_buscado', 'cod_fabricante','filial']].isna().all(axis=1)
            &
            (precos_concorrentes['status'] != "NÃO ENCONTRADO")
        )
    ]
    
    # tratamento de preços 
    precos_concorrentes = tratar_preco_sem_estoque(precos_concorrentes)
    
    precos_concorrentes = precos_concorrentes.replace(r"^\s*$", pd.NA, regex=True)
    
    # retirando linhas vazias
    precos_concorrentes = precos_concorrentes.dropna(
        subset = ["cod_fabricante", "descricao", "preco", "fabricante"],
        how="all"
    )
    
    id_coleta = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if callback:
        callback(0,0,"","⏳ Gravando Dados no Banco")
    
    id_coletas = carregar_coleta(precos_concorrentes)
    
    arquivo = rf'C:\Users\imercado2\OneDrive - GIRANDO COMERCIO DE PECAS LTDA\iMercado - Eder Iago\Coletor Precos\Coletas\coleta_{id_coleta}.xlsx'
    
    if callback:
        callback(0,0,"","⏳ Salvando Arquivo em Excel")
    # transformando o dataframe em uma planilha excel
    precos_concorrentes.to_excel(arquivo, index=False)
    
    if callback:
            callback(0,0,"","⏳ Gerando Comparativo")
            
    comparativo_precos = buscar_comparativo(id_coletas)
    if callback:
                callback(0,0,"","✅ Processo Concluido")
                
    # retornando a planilha com os resultados da busca
    return comparativo_precos