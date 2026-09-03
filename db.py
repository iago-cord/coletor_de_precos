import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "Precos-db"
DB_PATH = DB_DIR / "precos.db"
# Armazena o caminho da pasta para salvar o precos.db
pasta = Path(DB_DIR)

# Armazena o caminho do arquivos precos.db
arquivo_db = DB_PATH

# Inicia a conexao com o Banco de Dados passando o caminho do arquivo precos.db
conexao = sqlite3.connect(DB_PATH)

# Ativação da função de FOREIGN KEYS (sem essa ativação as FOREIGN KEYS nao funcionam!!)
conexao.execute("PRAGMA foreign_keys = ON")

# Criando o cursor para executar as funçoes no Banco de Dados
cursor = conexao.cursor()

# Adiciona a TABELA COLETAS caso nao exista
cursor.execute("""
               CREATE TABLE IF NOT EXISTS COLETAS (
                   ID_COLETA INTEGER PRIMARY KEY,
                   DATA_COLETA TEXT,
                   STATUS TEXT,
                   QTD_RAW INTEGER,
                   QTD_ROLEMAR INTEGER
               )
               """)

# Adiciona a TABELAS_DESCONTO caso nao exista
cursor.execute("""
               CREATE TABLE IF NOT EXISTS TABELAS_DESCONTO(
                   COD_TABELA INTEGER PRIMARY KEY,
                   DESCRICAO_TABELA TEXT
               )
               """)

# Adiciona a TABELA FILIAIS_ROLEMAR caso nao exista
cursor.execute("""
               CREATE TABLE IF NOT EXISTS FILIAIS_ROLEMAR(
                   COD_FILIAL INTEGER PRIMARY KEY,
                   ESTADO TEXT
               )
               """)

# Adiciona a TABELA FILIAIS_CONCORRENTES caso nao exista
cursor.execute("""
               CREATE TABLE IF NOT EXISTS FILIAIS_CONCORRENTES(
                   ID_FILIAL INTEGER PRIMARY KEY,
                   NOME_FILIAL TEXT,
                   ESTADO TEXT
               )
               """)

# Adiciona a TABELA RAW_PRECOS caso nao exista
cursor.execute("""
               CREATE TABLE IF NOT EXISTS RAW_PRECOS(
                   ID_RAW INTEGER PRIMARY KEY,
                   ID_COLETA INTEGER NOT NULL,
                   CONCORRENTE TEXT,
                   COD_BUSCADO TEXT,
                   COD_FABRICANTE TEXT,
                   DESCRICAO TEXT,
                   PRECO REAL,
                   FABRICANTE TEXT,
                   STATUS TEXT,
                   PRAZO TEXT,
                   FILIAL_CONCORRENTE TEXT,
                   ID_FILIAL_CONCORRENTE INTEGER,
                   DATA_COLETA TEXT,
                   
                   
                   FOREIGN KEY (ID_COLETA)
                    REFERENCES COLETAS(ID_COLETA),
                   
                   FOREIGN KEY (ID_FILIAL_CONCORRENTE)
                    REFERENCES FILIAIS_CONCORRENTES(ID_FILIAL)
                   
                   UNIQUE (
                       ID_COLETA,
                       COD_FABRICANTE,
                       CONCORRENTE,
                       ID_FILIAL_CONCORRENTE)  
               )
               """)

# Adiciona a TABELA PRECOS_ROLEMAR caso nao exista
cursor.execute("""
               CREATE TABLE IF NOT EXISTS PRECOS_ROLEMAR(
                   ID_PRECO_ROLEMAR INTEGER PRIMARY KEY,
                   ID_COLETA INTEGER NOT NULL,
                   CODEMP INTEGER, 
                   ESTADO TEXT,
                   CODPROD INTEGER, 
                   CODGRUPOPROD INTEGER,
                   REFFORN TEXT,
                   CARACTERISTICAS TEXT,
                   PRECO_PRINCIPAL REAL,
                   TABELA_DESCONTO INTEGER,
                   PERC_DESCONTO_TABELA REAL,
                   PERC_DESCONTO_QUANT REAL,
                   PRECO_FINAL REAL,
                   MARCA TEXT,
                   DESCRICAO_GRUPO TEXT,
                   
                   FOREIGN KEY (ID_COLETA)
                    REFERENCES COLETAS(ID_COLETA),
                    
                   FOREIGN KEY (TABELA_DESCONTO)
                    REFERENCES TABELAS_DESCONTO(COD_TABELA)
                    
                   UNIQUE (
                       ID_COLETA,
                       CODEMP, 
                       REFFORN
                   )  
               )
               """)

# Adiciona a TABELA CURATED caso nao exista
cursor.execute("""
               CREATE TABLE IF NOT EXISTS CURATED(
                   ID_COLETA INTEGER,
                   FORNECEDOR TEXT,
                   COD_BUSCADO TEXT,
                   COD_FABRICANTE TEXT,
                   DESCRICAO TEXT,
                   PRECO REAL,
                   FABRICANTE TEXT,
                   STATUS TEXT,
                   PRAZO TEXT,
                   FILIAL_CONCORRENTE TEXT,
                   DATA_COLETA TEXT,
                   ESTADO TEXT,
                   CODPROD INTEGER,
                   REFFORN TEXT, 
                   PRECO_FINAL REAL,
                   TABELA_DESCONTO INTEGER, 
                   DESCRICAO_TABELA TEXT,
                   DIF_PRECO REAL,
                   PERC_DIF_PRECO REAL,
                   SITUACAO TEXT
               )
               """)

# Adiciona a tabela com REFFORN/CODGRUPOPROD
cursor.execute("""
               CREATE TABLE IF NOT EXISTS BUSCA_REFFORN(
                   CODPROD INTEGER,
                   REFFORN TEXT, 
                   CODGRUPOPROD INTEGER, 
                   DESCRGRUPOPROD TEXT,
                   FATURAMENTO REAL,
                   
                   UNIQUE (
                       REFFORN,
                        CODPROD)
               )
               """)

#cursor.execute('DROP TABLE BUSCA_REFFORN')


'''cursor.execute("""
    SELECT
        ID_COLETA,
        COD_FABRICANTE,
        CONCORRENTE,
        ID_FILIAL_CONCORRENTE
    FROM RAW_PRECOS
    LIMIT 30
""")'''

#cursor.execute('ALTER TABLE PRECOS_ROLEMAR ADD COLUMN PRECO_TOP_MASTER REAL')

#cursor.execute('ALTER TABLE CURATED ADD COLUMN PRECO_TOP_MASTER REAL')

#cursor.execute('ALTER TABLE CURATED ADD COLUMN DIF_PRECO_TOP_MASTER REAL')

cursor.execute('ALTER TABLE CURATED ADD COLUMN PERC_DIF_PRECO_TOP_MASTER REAL')

#for linha in cursor.fetchall():
#    print(linha)

#print(cursor.fetchone())

cursor.execute("ALTER TABLE CURATED DROP COLUMN PERC_DIF_PRECO_TOP_MASTER_MASTER ")

#cursor.execute("DELETE FROM COLETAS")

#cursor.execute("SELECT * FROM COLETAS")
#print(cursor.fetchall())

#id_coleta = cursor.lastrowid
#print(id_coleta)


# Aplica as alterações no Banco de dados de forma definitiva (Nao chamar esse metodo faz com que as alterações sejam
# desfeitas apos fechar a conexao)
conexao.commit()

# Encerrando a conexao com o Banco de Dados
conexao.close


