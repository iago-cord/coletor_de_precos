from datetime import datetime

# função para incluir uma nova coleta na tabela COLETAS, retorna o ultimo ID_COLETAS inserido na tabela
def iniciar_coleta(cursor):
    data_coleta = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
                INSERT INTO COLETAS (
                    DATA_COLETA,
                    STATUS,
                    QTD_RAW,
                    QTD_EMPRESA
                )
                VALUES (?, ?, ?, ?)
                """, (
                    data_coleta,
                    "EM ANDAMENTO",
                    0,
                    0
                ))
    return cursor.lastrowid

# transforma cada linha do df em tuplas com os valores para o fazer o INSERT no banco 
def preparar_dados(df):
    return df[[
        "ID_COLETA",
        "CONCORRENTE",
        "COD_BUSCADO",
        "COD_FABRICANTE",
        "DESCRICAO",
        "PRECO",
        "FABRICANTE",
        "STATUS",
        "PRAZO",
        "FILIAL_CONCORRENTE",
        "ID_FILIAL_CONCORRENTE",
        "DATA_COLETA",
        "ESTADO"
    ]].itertuples(index=False, name=None)

# transforma cada linha do df em tuplas com os valores para o fazer o INSERT no banco
def preparar_dados_empresa(df):
    return df [[
        'ID_COLETA',
        'FILIAL',
        'ESTADO',
        'COD_PRODUTO',
        'COD_GRUPO_PRODUTO',
        'COD_FORNECEDOR',
        'CARACTERISTICAS',
        'PRECO_PRINCIPAL',
        'TABELA_DESCONTO',
        'PERC_DESCONTO_TABELA',
        'PERC_DESCONTO_QUANT',
        'PRECO_FINAL',
        'MARCA',
        'DESCRICAO_GRUPO',
        'PRECO_CLUBE'
    ]].itertuples(index=False, name=None)
    
# transforma cada linha do df em tuplas com os valores para o fazer o INSERT no banco
def preparar_dados_curated(df):
    return df [[
        'ID_COLETA',
        'CONCORRENTE',
        'COD_BUSCADO',
        'COD_FABRICANTE',
        'DESCRICAO',
        'PRECO',
        'FABRICANTE',
        'STATUS',
        'PRAZO',
        'FILIAL_CONCORRENTE',
        'DATA_COLETA',
        'ESTADO',
        'COD_PRODUTO',
        'COD_FORNECEDOR',
        'PRECO_FINAL',
        'TABELA_DESCONTO',
        'DESCRICAO_TABELA',
        'DIF_PRECO',
        'PERC_DIF_PRECO',
        'SITUACAO',
        'DESCRICAO_GRUPO',
        'PRECO_CLUBE',
        'DIF_PRECO_CLUBE',
        'PERC_DIF_PRECO_CLUBE'
    ]].itertuples(index=False, name=None)
    
    
def preparar_cod_fornecedor(df):
    return df[[
        'COD_PRODUTO',
        'COD_FORNECEDOR',
        'COD_GRUPO',
        'DESCRICAO_GRUPO',
        'FATURAMENTO'
        
    ]].itertuples(index=False, name=None)

# Executa o INSERT no banco baseado na tuplas criadas na função preparar_dados   
def insert_cod_fornecedor(cursor, cod_fornecedor):
    cursor.executemany("""
        INSERT INTO BUSCA_COD_FORNECEDOR (
          COD_PRODUTO,
          COD_FORNECEDOR,
          COD_GRUPO,
          DESCRICAO_GRUPO,
          FATURAMENTO
        )
        VALUES (?, ?, ?, ?, ?)
    """, cod_fornecedor)



# Executa o INSERT no banco baseado na tuplas criadas na função preparar_dados   
def insert_raw_precos(cursor, dados):
    cursor.executemany("""
        INSERT INTO RAW_PRECOS (
            ID_COLETA,
            CONCORRENTE,
            COD_BUSCADO,
            COD_FABRICANTE,
            DESCRICAO,
            PRECO,
            FABRICANTE,
            STATUS,
            PRAZO,
            FILIAL_CONCORRENTE,
            ID_FILIAL_CONCORRENTE,
            DATA_COLETA,
            ESTADO
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, dados)
    
# Executa o INSERT no banco baseado na tuplas criadas na função preparar_dados   
def insert_precos_empresa(cursor, dados_empresa):
    cursor.executemany("""
                       INSERT INTO PRECOS_EMPRESA (
                           ID_COLETA,
                           FILIAL,
                           ESTADO,
                           COD_PRODUTO,
                           COD_GRUPO_PRODUTO,
                           COD_FORNECEDOR,
                           CARACTERISTICAS,
                           PRECO_PRINCIPAL,
                           TABELA_DESCONTO,
                           PERC_DESCONTO_TABELA,
                           PERC_DESCONTO_QUANT,
                           PRECO_FINAL,
                           MARCA,
                           DESCRICAO_GRUPO,
                           PRECO_CLUBE
                       )
                       VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       """, dados_empresa)
    
# Executa o INSERT no banco baseado na tuplas criadas na função preparar_dados  
def insert_precos_curated(cursor, dados_curated):
    cursor.executemany("""
                       INSERT INTO CURATED (
                           ID_COLETA,
                           CONCORRENTE,
                           COD_BUSCADO,
                           COD_FABRICANTE,
                           DESCRICAO,
                           PRECO,
                           FABRICANTE,
                           STATUS,
                           PRAZO,
                           FILIAL_CONCORRENTE,
                           DATA_COLETA,
                           ESTADO,
                           COD_PRODUTO,
                           COD_FORNECEDOR,
                           PRECO_FINAL,
                           TABELA_DESCONTO,
                           DESCRICAO_TABELA,
                           DIF_PRECO,
                           PERC_DIF_PRECO,
                           SITUACAO,
                           DESCRICAO_GRUPO,
                           PRECO_CLUBE,
                           DIF_PRECO_CLUBE,
                           PERC_DIF_PRECO_CLUBE
                       )
                       VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       """, dados_curated)
    
# Faz um UPDATE na tabela COLETAS sinalizando que o carregamento terminou e uma contagem de quantas linhas 
# foram inseridas
def finalizar_coleta(cursor, id_coleta, qtd_raw, qtd_empresa):
    
    cursor.execute("""
                   UPDATE COLETAS
                   SET
                        STATUS = 'CONCLUIDA',
                        QTD_RAW = ?,
                        QTD_EMPRESA = ?
                        WHERE ID_COLETA = ?
                   """, (qtd_raw, qtd_empresa, id_coleta))
