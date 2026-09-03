import pandas as pd
import sqlite3
from transforms import (tratar_preco, tratar_duplicados, adicionar_dados_filiais, renomear_colunas, 
                        adicionar_filiais_rolemar, renomear_colunas_rolemar, tratar_preco_rolemar, 
                        filtro_base_rolemar, precos_comparativo, renomear_colunas_curated, tratar_duplicados_rolemar)
from INSERT import (iniciar_coleta, preparar_dados, insert_raw_precos, finalizar_coleta,preparar_dados_rolemar,
                    insert_precos_rolemar, preparar_dados_curated, insert_precos_curated)
from pathlib import Path

def carregar_coleta(precos_raw):
    print("ENTROU NO CARREGAR_COLETA")
    
    BASE_DIR = Path(__file__).resolve().parent
    
    # Armazena o caminho do arquivo SQLite referente ao banco de dados
    DB_PATH = BASE_DIR / "Precos-db" / "precos.db" 
    
    # Armazena o caminho do arquivo e faz a leitura de FILIAIS_CONCORRENTES
    FILIAIS_CONC_PATH = BASE_DIR / "Auxiliares" / "Filiais Concorrentes x Estado.xlsx"
    filiais_conc = pd.read_excel(FILIAIS_CONC_PATH, engine='openpyxl')
    
    # Armazena o caminho do arquivo e faz a leitura de FILIAIS_ROLEMAR
    FILIAIS_ROLEMAR_PATH = BASE_DIR / "Auxiliares" / "Filiais Rolemar x Estado.xlsx"
    filiais_rolemar = pd.read_excel(FILIAIS_ROLEMAR_PATH)
    
    # Armazena o caminho do arquivo e faz a leitura de PRECOS_ROLEMAR
    PRECOS_ROLEMAR_PATH = BASE_DIR / "Auxiliares" / "Precos Rolemar.xlsx"
    precos_rolemar = pd.read_excel(PRECOS_ROLEMAR_PATH)
    
    # Armazena o caminho do arquivo e faz a leitura de TABELAS_DESCONTO
    TAB_DESCONTOS_PATH = BASE_DIR / "Auxiliares" / "Tabelas de Desconto.xlsx"
    tab_desconto = pd.read_excel(TAB_DESCONTOS_PATH)

    # Inicia a conexao com o Banco de Dados passando o caminho do arquivo precos.db
    conexao = sqlite3.connect(DB_PATH)

    # Criando o cursor para executar as funçoes no Banco de Dados
    cursor = conexao.cursor()

    # Executa a funcao precos_comprativo que todo o processo e devolve um df com o comparativo
    precos_curated = precos_comparativo(tab_desconto,filiais_conc, filiais_rolemar, precos_raw, precos_rolemar)

    # Executa a função que renomeia e padroniza a nomenclatura das colunas
    precos_curated = renomear_colunas_curated(precos_curated)

    # Executa a funcao adicionar_dados_filiais para enriquecer a RAW_PRECOS
    precos_raw = adicionar_dados_filiais(precos_raw, filiais_conc)

    # Executa a funcao adicionar_dados_filiais para enriquecer a PRECOS_ROLEMAR
    precos_rolemar = adicionar_filiais_rolemar(precos_rolemar, filiais_rolemar)

    # Executa a função que renomeia e padroniza a nomenclatura das colunas
    precos_raw = renomear_colunas(precos_raw)

    # Executa a função que renomeia e padroniza a nomenclatura das colunas
    precos_rolemar = renomear_colunas_rolemar(precos_rolemar)

    # Executa a função iniciar_coleta para criar uma nova coleta, representando um novo INSERT de preços e captura o 
    # ultimo ID_COLETA adicionado na tabela
    id_coleta = iniciar_coleta(cursor)

    # Insere na RAW_PRECOS o ID_COLETA capturado anteriormente para identificar as informações da coleta
    precos_raw['ID_COLETA'] = id_coleta

    # Insere na PRECOS_ROLEMAR o ID_COLETA capturado anteriormente para identificar as informações da coleta
    precos_rolemar['ID_COLETA'] = id_coleta

    # Insere na CURATED o ID_COLETA capturado anteriormente para identificar as informações da coleta
    precos_curated['ID_COLETA'] = id_coleta

    # Convertendo a coluna de data para string pois o SQLite nao aceita TIMESTAMP
    precos_raw['DATA_COLETA'] = precos_raw['DATA_COLETA'].astype(str)

    # Convertendo a coluna de data para string pois o SQLite nao aceita TIMESTAMP
    precos_curated['DATA_COLETA'] = precos_curated['DATA_COLETA'].astype(str)
    
    # Executa a função tratar_duplicados que retira os dados duplicados do df passado como parametro
    precos_raw = tratar_duplicados(precos_raw)

    # Executa a função tratar_preco que faz o tratamento da coluna PRECO do df passado como parametro
    precos_raw = tratar_preco(precos_raw)

    # Executa a função tratar_preco que faz o tratamento da coluna PRECO do df passado como parametro
    precos_rolemar = tratar_preco_rolemar(precos_rolemar)

    # Filtra a base da rolemar para deixar somente o que correspondencia na RAW_PRECOS
    precos_rolemar = filtro_base_rolemar(precos_raw, precos_rolemar)
    
    # Faz o tratamento de valores no df especificado
    precos_raw = precos_raw.astype(object).where(pd.notna(precos_raw), None)
    
    # Executa a função tratar_duplicados_rolemar para retirar os dados duplicados do df passado como parametro
    precos_rolemar = tratar_duplicados_rolemar(precos_rolemar)

    # Executa a função preparar_dados que faz a transformacao de cada linha do DF em tuplas do df passado como parametro
    dados = preparar_dados(precos_raw)

    # Executa a função preparar_dados que faz a transformacao de cada linha do DF em tuplas do df passado como parametro
    dados_rolemar = preparar_dados_rolemar(precos_rolemar)

    # Transformando valores NaN e NA em None por que o SQLite nao aceita esses tipos
    precos_curated = precos_curated.astype(object).where(pd.notna(precos_curated), None)

    # Executa a função preparar_dados que faz a transformacao de cada linha do DF em tuplas do df passado como parametro
    dados_curated = preparar_dados_curated(precos_curated)
    
    # Executa a função insert_raw_precos que faz o INSERT do df preparado na tabela RAW_PRECOS
    insert_raw_precos(cursor, dados)

    # Executa a função insert_raw_precos que faz o INSERT do df preparado na tabela PRECOS_ROLEMAR
    insert_precos_rolemar(cursor, dados_rolemar)

    # Executa a função insert_precos_curated que faz o INSERT do df preparado na tabela CURATED
    insert_precos_curated(cursor, dados_curated)

    # Faz a contagem que quantas linhas existem no dataframe passado como parametro
    qtd_raw = len(precos_raw)

    # Faz a contagem que quantas linhas existem no dataframe passado como parametro
    qtd_rolemar = len(precos_rolemar)

    # Faz o UPDATE na tabela COLETAS sinalizando o fim do INSERT e inserindo a quantidade de linhas adicionadas
    # recebe como parametro o id_coleta a ser utilizado no WHERE e qtd_raw para inserir na contagem de linhas da RAW_PRECOS 
    finalizar_coleta(cursor, id_coleta, qtd_raw, qtd_rolemar)

    # Aplica as alterações no Banco de dados de forma definitiva (Nao chamar esse metodo faz com que as alterações sejam
    # desfeitas apos fechar a conexao)
    conexao.commit()

    # Encerrando a conexao com o Banco de Dados
    conexao.close()
    
    return id_coleta
