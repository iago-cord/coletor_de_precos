import pandas as pd
import numpy as np
import sqlite3
import time

# Função pra o tratamento do preço da RAW_PRECOS
# Retirando todos os elmentos que nao correspondem aos filtos aplicados 
# e com os elementos restantes aplicados outro tratamento para retirar os cifroes e trocando , pelo .
# em razao do padrao de moeda
def tratar_preco(df):
    
    df = df[
    df["PRECO"].notna() &
    (df["PRECO"] != "R$0,00") &
    (df["PRECO"] != "--")
].copy()
    
    df['PRECO'] = (
    df['PRECO']
    .astype(str)
    .str.strip()
    .str.replace("R$", "", regex=False)
    .str.replace(",",".", regex=False)
    )   
    return df

# Função pra o tratamento do preço da PRECOS_ROLEMAR
# Retirando todos os elmentos que nao correspondem aos filtos aplicados 
# e com os elementos restantes aplicados outro tratamento para retirar os cifroes e trocando , pelo .
# em razao do padrao de moeda
def tratar_preco_rolemar(df):
    
    df = df[
    df["PRECO_FINAL"].notna() &
    (df["PRECO_FINAL"] != "R$0,00") &
    (df["PRECO_FINAL"] != "--")
].copy()
    
    df[['PRECO_FINAL','PRECO_TOP_MASTER']] = (
    df[['PRECO_FINAL','PRECO_TOP_MASTER']]
    .apply(lambda x: x.astype(str).str.strip().str.replace("R$", "", regex=False).str.replace(",",".", regex=False))
    )   
    return df

# retirando os elementos duplicados que se enquandram nas condições aplicadas
def tratar_duplicados (df):
    df = df.drop_duplicates(
    subset=[
        "ID_COLETA",
        "COD_FABRICANTE",
        "CONCORRENTE",
        "ID_FILIAL_CONCORRENTE"
    ]
)
    return df


# retirando os elementos duplicados que se enquandram nas condições aplicadas
def tratar_duplicados_rolemar (df):
    df = df.drop_duplicates(
    subset=[
        "FILIAL",
        "REF_FORN"
    ]
)
    return df

# faz um merge da FILIAIS_CONCORRENTES com RAW_PRECOS para enriquecer a tabela com o ESTADO de cada filial
def adicionar_dados_filiais(df, filiais):
    df = df.merge(
    filiais[['id_filial', 'nome_filial', 'Estado']],
    left_on='filial',
    right_on='nome_filial',
    how='left'
)

    df = df.drop(columns='nome_filial')
    
    return df

# faz um merge da FILIAIS_ROLEMAR com PRECOS_ROLEMAR para enriquecer a tabela com o ESTADO de cada filial
def adicionar_filiais_rolemar(df, filiais):
    df = df.merge(
        filiais[['Filial', 'Estado']],
        left_on='CODEMP',
        right_on='Filial',
        how='left'
    )
    
    df = df.drop(columns='Filial')
    
    return df

# Renomeia as colunas para um padrao, onde sejam mais descritivas do dado inserido nela
def renomear_colunas(df):
    df = df.rename(columns={
    'fornecedor': 'CONCORRENTE',
    'cod_buscado': 'COD_BUSCADO',
    'cod_fabricante': 'COD_FABRICANTE',
    'descricao': 'DESCRICAO',
    'preco': 'PRECO',
    'fabricante': 'FABRICANTE',
    'status': 'STATUS',
    'prazo': 'PRAZO',
    'filial': 'FILIAL_CONCORRENTE',
    'data coleta': 'DATA_COLETA',
    'id_filial' : 'ID_FILIAL_CONCORRENTE',
    'Estado': 'ESTADO'
})
    return df

# Renomeia as colunas para um padrao, onde sejam mais descritivas do dado inserido nela
def renomear_colunas_rolemar(df):
    df = df.rename(columns={
        'CODEMP': 'FILIAL',
        'ESTADO': 'ESTADO',
        'CODPROD': 'COD_PRODUTO',
        'CODGRUPOPROD': 'COD_GRUPO_PRODUTO',
        'REFFORN': 'REF_FORN',
        'CARACTERISTICAS': 'CARACTERISTICAS',
        'PRECO_PRINCIPAL': 'PRECO_PRINCIPAL',
        'TABELA_PRI': 'TABELA_DESCONTO',
        'PERC_DESCONTO_TABELA_PRI': 'PERC_DESCONTO_TABELA',
        'PERC_DESCONTO_QUANT_PRI': 'PERC_DESCONTO_QUANT',
        'PRECO_PRI_COM_DESCONTOS': 'PRECO_FINAL',
        'MARCA': 'MARCA',
        'DESCRGRUPOPRODPRI': 'DESCRICAO_GRUPO',
        'PRECO_PRI_COM_TOP_MASTER': 'PRECO_TOP_MASTER'
    })
    
    return df

# Renomeia as colunas para um padrao, onde sejam mais descritivas do dado inserido nela
def renomear_colunas_curated(df):
    df = df.rename(columns={
        'fornecedor': 'CONCORRENTE',
        'cod_buscado': 'COD_BUSCADO',
        'cod_fabricante': 'COD_FABRICANTE',
        'descricao': 'DESCRICAO',
        'preco': 'PRECO',
        'fabricante': 'FABRICANTE',
        'status': 'STATUS',
        'prazo': 'PRAZO',
        'filial': 'FILIAL_CONCORRENTE',
        'data coleta': 'DATA_COLETA',
        'Estado': 'ESTADO',
        'CODPROD': 'COD_PRODUTO',
        'REFFORN': 'REF_FORN',
        'PRECO_PRI_COM_DESCONTOS': 'PRECO_FINAL',
        'TABELA_PRI': 'TABELA_DESCONTO',
        'Descrição': 'DESCRICAO_TABELA',
        'Diferença Preço': 'DIF_PRECO',
        'Diferença %': 'PERC_DIF_PRECO',
        'Situacao': 'SITUACAO',
        'DESCRGRUPOPRODPRI': 'DESCRICAO_GRUPO',
        'PRECO_PRI_COM_TOP_MASTER': 'PRECO_TOP_MASTER',
        'Diferença Preço Top Master': 'DIF_PRECO_TOP_MASTER',
        'Diferença % Top Master': 'PERC_DIF_PRECO_TOP_MASTER'
        
    })
    
    return df


# Filtra a base de dados da rolemar para manter somente os itens com correspondencia na coleta de preços
def filtro_base_rolemar(precos_concorrentes, precos_rolemar):
    chaves = precos_concorrentes[
        ['COD_FABRICANTE', 'ESTADO']
    ].drop_duplicates()
    
    precos_rolemar = precos_rolemar.merge(
        chaves,
        left_on=['REF_FORN', 'ESTADO'],
        right_on=['COD_FABRICANTE', 'ESTADO'],
        how='inner'
    )
    
    return precos_rolemar

def tratar_refforn(df):
    df['REFFORN'] = (
        df['REFFORN']
        .astype(str)
        .str.strip()
        .str.replace("-", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace("/", "", regex=False)
        )
    return df

# faz todos os tratamentos e merges necessarios para retornar a curated ja na forma do comparativo
def precos_comparativo(tabela_desconto, filiais_concorrentes, filiais_rolemar, precos_concorrentes,
                       precos_rolemar):

    precos_concorrentes['cod_fabricante'] = (
    precos_concorrentes['cod_fabricante']
    .astype(str)
    .str.strip()
    .str.replace("-", "", regex=False)
    .str.replace(".", "", regex=False)
    .str.replace(" ", "", regex=False)
    .str.replace("/", "", regex=False)
    )

    precos_rolemar[['REFFORN']] = (
    precos_rolemar[['REFFORN']]
    .apply(
        lambda col:
            col.astype('string')
            .str.strip()
            .str.replace("-","", regex=False)
            .str.replace(".","", regex=False)
            .str.replace("/","", regex=False)
            .str.replace(" ","", regex=False)
        ))
    
    precos_concorrentes['preco'] = (
    precos_concorrentes['preco']
    .astype(str)
    .str.strip()
    .str.replace("R$", "", regex=False)
    .str.replace(".", "", regex=False)
    .str.replace(",",".", regex=False)
    .str.replace("\xa0", "", regex=False)
    )
    
    precos_rolemar[['PRECO_PRI_COM_DESCONTOS','PRECO_PRI_COM_TOP_MASTER']] = (
    precos_rolemar[['PRECO_PRI_COM_DESCONTOS','PRECO_PRI_COM_TOP_MASTER']]
    .apply(lambda x: x.astype(str).str.strip().str.replace("R$", "", regex=False).str.replace(",",".", regex=False))
    ) 
       
    precos_concorrentes = precos_concorrentes[
            precos_concorrentes["preco"].notna() &
            precos_concorrentes["preco"].str.strip().ne("") &
            (precos_concorrentes["preco"] != "R$0,00") &
            (precos_concorrentes["preco"] != "--")]
    
    precos_concorrentes_estado = precos_concorrentes.merge(
    filiais_concorrentes,
    left_on='filial',
    right_on='nome_filial',
    how='left'
    )

    precos_concorrentes_estado = precos_concorrentes_estado.drop(columns='nome_filial')
    precos_concorrentes_estado = precos_concorrentes_estado.drop(columns='id_filial')
    
    precos_rolemar_tabela = precos_rolemar.merge(
        tabela_desconto,
        left_on='TABELA_PRI',
        right_on='Tab.',
        how='left'
    )
    
    precos_comparativo = precos_concorrentes_estado.merge(
    precos_rolemar_tabela[
        ['ESTADO', 'CODPROD', 'REFFORN', 'PRECO_PRI_COM_DESCONTOS','TABELA_PRI','Descrição','DESCRGRUPOPRODPRI','PRECO_PRI_COM_TOP_MASTER']
    ],
    left_on=['cod_fabricante', 'Estado'],
    right_on=['REFFORN', 'ESTADO'],
    how='left'
    )

    precos_comparativo = precos_comparativo[
        ~(
            (precos_comparativo['fornecedor'] == "PELLEGRINO") &
            (precos_comparativo['Estado'] != "PR")
        )
    ]
    
    precos_comparativo = precos_comparativo.drop_duplicates(
        subset=['cod_buscado', 'Estado','cod_fabricante', 'fornecedor', 'filial']
    )
    
    precos_comparativo = precos_comparativo.drop(columns='ESTADO')
    
    if precos_comparativo.empty:
            return precos_comparativo
        
    print(precos_comparativo.loc[
    precos_comparativo['fornecedor'] == 'DPK',
    'preco'
    ].map(repr).head())

    print(precos_comparativo.loc[
    precos_comparativo['fornecedor'] == 'DPK',
    'preco'
    ].dtype)
    

    precos_comparativo[['preco','PRECO_PRI_COM_DESCONTOS','PRECO_PRI_COM_TOP_MASTER']]=(
    precos_comparativo[['preco','PRECO_PRI_COM_DESCONTOS','PRECO_PRI_COM_TOP_MASTER']].apply(
        lambda col: pd.to_numeric(col, errors = 'coerce')
        #col.astype(float)
    ))
    
    print("DEPOIS DO TO_NUMERIC:")
    print(precos_comparativo[
    precos_comparativo['fornecedor'] == 'DPK'
    ][['fornecedor', 'preco']])

    #if precos_comparativo.empty:
    #    return precos_comparativo
    
    precos_comparativo['Diferença Preço'] = (
        precos_comparativo['preco'] - precos_comparativo['PRECO_PRI_COM_DESCONTOS']
    )

    precos_comparativo['Diferença %'] = (
        precos_comparativo['preco'] / precos_comparativo['PRECO_PRI_COM_DESCONTOS'] -1
    )
    
    precos_comparativo['Diferença Preço Top Master'] = (
    precos_comparativo['preco'] - precos_comparativo['PRECO_PRI_COM_TOP_MASTER']
    )
    
    precos_comparativo['Diferença % Top Master'] = (
        precos_comparativo['preco'] / precos_comparativo['PRECO_PRI_COM_TOP_MASTER'] -1
    )

    precos_comparativo['Situacao'] = np.select(
        [
            precos_comparativo['Diferença %'] < 0,
            precos_comparativo['Diferença %'] == 0,
            precos_comparativo['Diferença %'] > 0
        ],
        
        [
            "Concorrente mais barato",
            "Mesmo Preço",
            "Rolemar mais barato"
        ],
        default = "Sem Comparação"
    )
    
    return precos_comparativo

def buscar_comparativo(id_coleta):
    
    # Armazena o caminho do arquivo SQLite referente ao banco de dados
    arquivo_db = r'C:\Users\imercado2\OneDrive - GIRANDO COMERCIO DE PECAS LTDA\iMercado - Eder Iago\Coletor Precos\Precos-db\precos.db'
    
    conexao = sqlite3.connect(arquivo_db)
    
    query = """
        SELECT
            COD_BUSCADO,
            COD_FABRICANTE,
            DESCRICAO,
            STATUS,
            CONCORRENTE,
            FILIAL_CONCORRENTE,
            ESTADO,
            PRECO AS "PRECO CONCORRENTE",
            PRECO_FINAL AS "PRECO ROLEMAR",
            ROUND(DIF_PRECO,2) AS "DIFERENÇA PREÇO",
            ROUND(PERC_DIF_PRECO,2) AS "DIFERENÇA %",
            PRECO_TOP_MASTER AS "PRECO TOP MASTER",
            DIF_PRECO_TOP_MASTER,
            ROUND(PERC_DIF_PRECO_TOP_MASTER,2) AS "DIFERENCA % TOP MASTER",
            SITUACAO,
            DESCRICAO_GRUPO
            FROM CURATED
            WHERE ID_COLETA = ?
        """
    df = pd.read_sql_query(
        query, conexao, params=(id_coleta,)
        )
    
    conexao.close()
    
    return df
    
