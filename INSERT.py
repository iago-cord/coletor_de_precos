from datetime import datetime

# função para incluir uma nova coleta na tabela COLETAS, retorna o ultimo ID_COLETAS inserido na tabela
def iniciar_coleta(cursor):
    data_coleta = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
                INSERT INTO COLETAS (
                    DATA_COLETA,
                    STATUS,
                    QTD_RAW,
                    QTD_ROLEMAR
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
def preparar_dados_rolemar(df):
    return df [[
        'ID_COLETA',
        'FILIAL',
        'ESTADO',
        'COD_PRODUTO',
        'COD_GRUPO_PRODUTO',
        'REF_FORN',
        'CARACTERISTICAS',
        'PRECO_PRINCIPAL',
        'TABELA_DESCONTO',
        'PERC_DESCONTO_TABELA',
        'PERC_DESCONTO_QUANT',
        'PRECO_FINAL',
        'MARCA',
        'DESCRICAO_GRUPO',
        'PRECO_TOP_MASTER'
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
        'REF_FORN',
        'PRECO_FINAL',
        'TABELA_DESCONTO',
        'DESCRICAO_TABELA',
        'DIF_PRECO',
        'PERC_DIF_PRECO',
        'SITUACAO',
        'DESCRICAO_GRUPO',
        'PRECO_TOP_MASTER',
        'DIF_PRECO_TOP_MASTER',
        'PERC_DIF_PRECO_TOP_MASTER'
    ]].itertuples(index=False, name=None)
    
    
def preparar_refforn(df):
    return df[[
        'CODPROD',
        'REFFORN',
        'CODGRUPOPROD',
        'DESCRGRUPOPROD',
        'FATURAMENTO'
        
    ]].itertuples(index=False, name=None)

# Executa o INSERT no banco baseado na tuplas criadas na função preparar_dados   
def insert_refforn(cursor, refforn):
    cursor.executemany("""
        INSERT INTO BUSCA_REFFORN (
          CODPROD,
          REFFORN,
          CODGRUPOPROD,
          DESCRGRUPOPROD,
          FATURAMENTO
        )
        VALUES (?, ?, ?, ?, ?)
    """, refforn)



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
def insert_precos_rolemar(cursor, dados_rolemar):
    cursor.executemany("""
                       INSERT INTO PRECOS_ROLEMAR (
                           ID_COLETA,
                           FILIAL,
                           ESTADO,
                           COD_PRODUTO,
                           COD_GRUPO_PRODUTO,
                           REF_FORN,
                           CARACTERISTICAS,
                           PRECO_PRINCIPAL,
                           TABELA_DESCONTO,
                           PERC_DESCONTO_TABELA,
                           PERC_DESCONTO_QUANT,
                           PRECO_FINAL,
                           MARCA,
                           DESCRICAO_GRUPO,
                           PRECO_TOP_MASTER
                       )
                       VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       """, dados_rolemar)
    
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
                           REF_FORN,
                           PRECO_FINAL,
                           TABELA_DESCONTO,
                           DESCRICAO_TABELA,
                           DIF_PRECO,
                           PERC_DIF_PRECO,
                           SITUACAO,
                           DESCRICAO_GRUPO,
                           PRECO_TOP_MASTER,
                           DIF_PRECO_TOP_MASTER,
                           PERC_DIF_PRECO_TOP_MASTER
                       )
                       VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       """, dados_curated)
    
# Faz um UPDATE na tabela COLETAS sinalizando que o carregamento terminou e uma contagem de quantas linhas 
# foram inseridas
def finalizar_coleta(cursor, id_coleta, qtd_raw, qtd_rolemar):
    
    cursor.execute("""
                   UPDATE COLETAS
                   SET
                        STATUS = 'CONCLUIDA',
                        QTD_RAW = ?,
                        QTD_ROLEMAR = ?
                        WHERE ID_COLETA = ?
                   """, (qtd_raw, qtd_rolemar, id_coleta))
