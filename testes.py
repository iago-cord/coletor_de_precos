import pandas as pd
from transforms import precos_comparativo


    # Armazena o caminho do arquivo com os precos coletados
arquivo_precos_conc = r'C:\Users\imercado2\OneDrive - GIRANDO COMERCIO DE PECAS LTDA\iMercado - Eder Iago\Coletor Precos\precos_concorrentes.xlsx'

    # Armazena o caminho do arquivo SQLite referente ao banco de dados
arquivo_db = r'C:\Users\imercado2\OneDrive - GIRANDO COMERCIO DE PECAS LTDA\iMercado - Eder Iago\Coletor Precos\Precos-db\precos.db'

    # Armazena o caminho do arquivo de FILIAIS_CONCORRENTES
arquivo_filiais_conc = r'C:\Users\imercado2\OneDrive - GIRANDO COMERCIO DE PECAS LTDA\iMercado - Eder Iago\Analise Precos\Filiais Concorrentes x Estado.xlsx'

    # Armazena o caminho do arquivo com os precos rolemar
arquivo_precos_rolemar = r'C:\Users\imercado2\OneDrive - GIRANDO COMERCIO DE PECAS LTDA\iMercado - Eder Iago\Analise Precos\Precos Rolemar.xlsx'

    # Armazena o caminho do arquivo com as filiais rolemar
arquivo_filiais_rolemar = r'C:\Users\imercado2\OneDrive - GIRANDO COMERCIO DE PECAS LTDA\iMercado - Eder Iago\Analise Precos\Filiais Rolemar x Estado.xlsx'

    # Armazena o caminho do arquivo com tabela de descontos
arquivo_tab_desconto = r'C:\Users\imercado2\OneDrive - GIRANDO COMERCIO DE PECAS LTDA\iMercado - Eder Iago\Analise Precos\Tabelas de Desconto.xlsx'

# Faz a leitura do arquivo com os precos coletados
precos_raw = pd.read_excel(arquivo_precos_conc)

    
    # Faz a leitura do arquivo com os precos coletados
precos_rolemar = pd.read_excel(arquivo_precos_rolemar)

    # Faz a leitura do arquivo de FILIAIS_CONCORRENTES
filiais_conc = pd.read_excel(arquivo_filiais_conc)

    # Faz a leitura do arquivo de FILIAIS_ROLEMAR
filiais_rolemar = pd.read_excel(arquivo_filiais_rolemar)

    # Faz a leitura do arquivo de tabelas de desconto
tab_desconto =pd.read_excel(arquivo_tab_desconto)



debug_comparativo = precos_comparativo(tab_desconto,filiais_conc, filiais_rolemar, precos_raw, precos_rolemar)



#def precos_comparativo(tabela_desconto, filiais_concorrentes, filiais_rolemar, precos_concorrentes,
 
 
 
 '''
# Armazena o caminho do arquivo SQLite referente ao banco de dados
arquivo_db = r'C:\Users\imercado2\OneDrive - GIRANDO COMERCIO DE PECAS LTDA\iMercado - Eder Iago\Coletor Precos\Precos-db\precos.db'

# Inicia a conexao com o Banco de Dados passando o caminho do arquivo precos.db
conexao = sqlite3.connect(arquivo_db)

# Criando o cursor para executar as funçoes no Banco de Dados
cursor = conexao.cursor()



# Armazena o caminho do arquivo com tabela de REFFORN
arquivo_busca_refforn = r'C:\Users\imercado2\OneDrive - GIRANDO COMERCIO DE PECAS LTDA\iMercado - Eder Iago\Coletor Precos\Assets\REFFORN.xlsx'

busca_refforn = pd.read_excel(arquivo_busca_refforn)

busca_refforn = tratar_refforn(busca_refforn)

dados_refforn = preparar_refforn(busca_refforn)

insert_refforn (cursor, dados_refforn)

conexao.commit()
conexao.close()






import pandas as pd
from transforms import (tratar_preco, tratar_duplicados, adicionar_dados_filiais, renomear_colunas, 
                        adicionar_filiais_rolemar, renomear_colunas_rolemar, tratar_preco_rolemar, 
                        filtro_base_rolemar, precos_comparativo, renomear_colunas_curated, tratar_refforn)

from INSERT import (iniciar_coleta, preparar_dados, insert_raw_precos, finalizar_coleta,preparar_dados_rolemar,
                    insert_precos_rolemar, preparar_dados_curated, insert_precos_curated, preparar_refforn, insert_refforn)
import sqlite3

# Armazena o caminho do arquivo com tabela de REFFORN
arquivo_busca_refforn = r'C:\Users\imercado2\OneDrive - GIRANDO COMERCIO DE PECAS LTDA\iMercado - Eder Iago\Coletor Precos\Assets\REFFORN.xlsx'


curva_rede = pd.read_excel(arquivo_busca_refforn)

curva_rede = curva_rede.sort_values(
    ['FATURAMENTO'],
    ascending=[False]
)

curva_rede['PERC_FAT'] = (
    curva_rede['FATURAMENTO'] / curva_rede['FATURAMENTO'].sum()
)


curva_rede['PERC_ACUM'] = (
    curva_rede['PERC_FAT'].cumsum()
)

curva_rede.to_excel('Curva ABC - Rede.xlsx', index=False)

#print(curva_rede)
'''