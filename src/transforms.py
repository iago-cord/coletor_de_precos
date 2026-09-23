import pandas as pd
import numpy as np
import sqlite3


# Função pra o tratamento do preço da RAW_PRECOS
# Retirando todos os elementos que nao correspondem aos filtros aplicados 
# e com os elementos restantes aplicado outro tratamento para retirar os cifroes e trocando , pelo .
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

# Função pra o tratamento do preço da PRECOS_EMPRESA
# Retirando todos os elmentos que nao correspondem aos filtos aplicados 
# e com os elementos restantes aplicados outro tratamento para retirar os cifroes e trocando , pelo .
# em razao do padrao de moeda
def tratar_preco_empresa(df):
    
    df = df[
    df["PRECO_FINAL"].notna() &
    (df["PRECO_FINAL"] != "R$0,00") &
    (df["PRECO_FINAL"] != "--")
].copy()
    
    df[['PRECO_FINAL','PRECO_CLUBE']] = (
    df[['PRECO_FINAL','PRECO_CLUBE']]
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
def tratar_duplicados_empresa(df):
    df = df.drop_duplicates(
    subset=[
        "FILIAL",
        "COD_FORNECEDOR"
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

# faz um merge da FILIAIS_EMPRESA com PRECOS_EMPRESA para enriquecer a tabela com o ESTADO de cada filial
def adicionar_filiais_empresa(df, filiais):
    df = df.merge(
        filiais[['Filial', 'Estado']],
        left_on='COD_EMPRESA',
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
def renomear_colunas_empresa(df):
    df = df.rename(columns={
        'COD_EMPRESA': 'FILIAL',
        'ESTADO': 'ESTADO',
        'COD_PRODUTO': 'COD_PRODUTO',
        'COD_GRUPO': 'COD_GRUPO_PRODUTO',
        'COD_FORNECEDOR': 'COD_FORNECEDOR',
        'CARACTERISTICAS': 'CARACTERISTICAS',
        'PRECO_PRINCIPAL': 'PRECO_PRINCIPAL',
        'TABELA_PRINCIPAL': 'TABELA_DESCONTO',
        'PERC_DESCONTO_TABELA_PRINCIPAL': 'PERC_DESCONTO_TABELA',
        'PERC_DESCONTO_QUANT_PRINCIPAL': 'PERC_DESCONTO_QUANT',
        'PRECO_PRINCIPAL_COM_DESCONTOS': 'PRECO_FINAL',
        'MARCA': 'MARCA',
        'DESCRICAO_GRUPO': 'DESCRICAO_GRUPO',
        'PRECO_PRI_CLUBE': 'PRECO_CLUBE'
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
        'COD_FORNECEDOR': 'COD_FORNECEDOR',
        'PRECO_PRINCIPAL_COM_DESCONTOS': 'PRECO_FINAL',
        'TABELA_PRINCIPAL': 'TABELA_DESCONTO',
        'Descrição': 'DESCRICAO_TABELA',
        'Diferença Preço': 'DIF_PRECO',
        'Diferença %': 'PERC_DIF_PRECO',
        'Situacao': 'SITUACAO',
        'DESCRICAO_GRUPO': 'DESCRICAO_GRUPO',
        'PRECO_PRINCIPAL_CLUBE': 'PRECO_CLUBE',
        'Diferença Preço Clube': 'DIF_PRECO_CLUBE',
        'Diferença % Clube': 'PERC_DIF_PRECO_CLUBE'
    })
    return df

# Filtra a base de dados da EMPRESA para manter somente os itens com correspondencia na coleta de preços
def filtro_base_empresa(precos_concorrentes, precos_empresa):
    chaves = precos_concorrentes[
        ['COD_FABRICANTE', 'ESTADO']
    ].drop_duplicates()
    
    precos_empresa = precos_empresa.merge(
        chaves,
        left_on=['COD_FORNECEDOR', 'ESTADO'],
        right_on=['COD_FABRICANTE', 'ESTADO'],
        how='inner'
    )
    return precos_empresa

def tratar_cod_fornecedor(df):
    df['COD_FORNECEDOR'] = (
        df['COD_FORNECEDOR']
        .astype(str)
        .str.strip()
        .str.replace("-", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace("/", "", regex=False)
        )
    return df

# faz todos os tratamentos e merges necessarios para retornar a curated ja na forma do comparativo
def precos_comparativo(tabela_desconto, filiais_concorrentes, filiais_empresa, precos_concorrentes,
                       precos_empresa):

    precos_concorrentes['cod_fabricante'] = (
    precos_concorrentes['cod_fabricante']
    .astype(str)
    .str.strip()
    .str.replace("-", "", regex=False)
    .str.replace(".", "", regex=False)
    .str.replace(" ", "", regex=False)
    .str.replace("/", "", regex=False)
    )

    precos_empresa[['COD_FORNECEDOR']] = (
    precos_empresa[['COD_FORNECEDOR']]
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
    
    precos_empresa[['PRECO_PRINCIPAL_COM_DESCONTOS','PRECO_PRINCIPAL_CLUBE']] = (
    precos_empresa[['PRECO_PRINCIPAL_COM_DESCONTOS','PRECO_PRINCIPAL_CLUBE']]
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
    
    precos_empresa_tabela = precos_empresa.merge(
        tabela_desconto,
        left_on='TABELA_PRINCIPAL',
        right_on='Tab.',
        how='left'
    )
    
    precos_comparativo = precos_concorrentes_estado.merge(
    precos_empresa_tabela[
        ['ESTADO', 'COD_PRODUTO', 'COD_FORNECEDOR', 'PRECO_PRINCIPAL_COM_DESCONTOS','TABELA_PRINCIPAL','Descrição','DESCRICAO_GRUPO','PRECO_PRINCIPAL_CLUBE']
    ],
    left_on=['cod_fabricante', 'Estado'],
    right_on=['COD_FORNECEDOR', 'ESTADO'],
    how='left'
    )

    precos_comparativo = precos_comparativo[
        ~(
            (precos_comparativo['fornecedor'] == "CONCORRENTE_P") &
            (precos_comparativo['Estado'] != "PR")
        )
    ]
    
    precos_comparativo = precos_comparativo.drop_duplicates(
        subset=['cod_buscado', 'Estado','cod_fabricante', 'fornecedor', 'filial']
    )
    
    precos_comparativo = precos_comparativo.drop(columns='ESTADO')
    
    if precos_comparativo.empty:
            return precos_comparativo
        
    precos_comparativo[['preco','PRECO_PRINCIPAL_COM_DESCONTOS','PRECO_PRINCIPAL_CLUBE']]=(
    precos_comparativo[['preco','PRECO_PRINCIPAL_COM_DESCONTOS','PRECO_PRINCIPAL_CLUBE']].apply(
        lambda col: pd.to_numeric(col, errors = 'coerce')
    ))
    
    precos_comparativo['Diferença Preço'] = (
        precos_comparativo['preco'] - precos_comparativo['PRECO_PRINCIPAL_COM_DESCONTOS']
    )

    precos_comparativo['Diferença %'] = (
        precos_comparativo['preco'] / precos_comparativo['PRECO_PRINCIPAL_COM_DESCONTOS'] -1
    )
    
    precos_comparativo['Diferença Preço Clube'] = (
    precos_comparativo['preco'] - precos_comparativo['PRECO_PRINCIPAL_CLUBE']
    )
    
    precos_comparativo['Diferença % Clube'] = (
        precos_comparativo['preco'] / precos_comparativo['PRECO_PRINCIPAL_CLUBE'] -1
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
            "Empresa mais barato"
        ],
        default = "Sem Comparação"
    )
    
    return precos_comparativo

def buscar_comparativo(id_coleta):
    
    # Armazena o caminho do arquivo SQLite referente ao banco de dados
    arquivo_db = ('CAMINHO DO BANCO DE DADOS')
    
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
            PRECO_FINAL AS "PRECO EMPRESA",
            ROUND(DIF_PRECO,2) AS "DIFERENÇA PREÇO",
            ROUND(PERC_DIF_PRECO,2) AS "DIFERENÇA %",
            PRECO_CLUBE AS "PRECO CLUBE",
            DIF_PRECO_CLUBE,
            ROUND(PERC_DIF_PRECO_CLUBE,2) AS "DIFERENCA % CLUBE",
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
    
