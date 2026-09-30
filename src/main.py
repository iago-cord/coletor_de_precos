from src.Coletores import coleta_preco_DS
from src.Coletores import coleta_preco_R
from src.Coletores import coleta_preco_S
from src.Coletores import coleta_preco_P
from src.Coletores import coleta_preco_A
from src.Coletores import coleta_preco_SSP
from src.Coletores import coleta_preco_SPR
from src.Coletores import coleta_preco_D
import pandas as pd
import logging
import datetime as dt
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.functions import tratar_preco_sem_estoque
from src.load_db import carregar_coleta
from src.transforms import buscar_comparativo
import time

# Cria a pasta checkpoints caso nao exista para salvar os arquivos RAW após o fim da coleta de cada concorrente
os.makedirs("checkpoints", exist_ok=True)

# Configuraçao dos logs de busca
logging.basicConfig(
    filename="coletor_precos.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8"
)

# Executa o modulo do concorrente passado como parametro, se o modulo terminar sem lançar exceção
# salva o dataframa na pasta checkpoints e registra o log de salvo com sucesso
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
def executar(codigos, ds=True, r=True, s=True, p=True, a = True,ssp = True ,spr = True , d= True,
             filiais_ds = None, filiais_r = None, filiais_s = None, filiais_a = None, filiais_ssp = None, 
             filiais_spr = None, filiais_d= None, callback = None):
    resultados = []

    # se true adiciona a etapa a lista nome / modulo
    etapas = []
    if r: etapas.append(("R", coleta_preco_R, filiais_r))
    if ds: etapas.append(("Ds", coleta_preco_DS, filiais_ds))
    if s: etapas.append(("S", coleta_preco_S, filiais_s))
    if p: etapas.append(("P", coleta_preco_P, None))
    if a: etapas.append(("A",coleta_preco_A, filiais_a ))
    if ssp: etapas.append(("SSP",coleta_preco_SSP, filiais_ssp))
    if spr: etapas.append(("SPR", coleta_preco_SPR, filiais_spr))
    if d: etapas.append(("D", coleta_preco_D, filiais_d))

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
    
    # se o campo preco vier 'None' retornar na coluna status "Sem Estoque"
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
    # Ajusta a coluna status
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
    
    arquivo = rf'CAMINHO PARA SALVAR ARQUIVO COM DADOS COLETADOS{id_coleta}.xlsx'
    
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