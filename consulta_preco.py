import streamlit as st
import main
import pandas as pd
from io import BytesIO
from ui import background_local, formatar_dif, adicionar_logo_header
import sqlite3

st.set_page_config(layout="wide")

st.html(
    """
    <style>
    [data-testid="stDataFrame"] td, 
    [data-testid="stDataFrame"] th {
        font-size: 8px !important;
    }
    </style>
    """
)

# Definindo a imagem de Background
background_local(r'C:\Users\imercado2\OneDrive - GIRANDO COMERCIO DE PECAS LTDA\iMercado - Eder Iago\Coletor Precos\Assets\background_rolemar.png')

adicionar_logo_header('logo.png')

# Armazena o caminho do arquivos precos.db
arquivo_db = r'C:\Users\imercado2\OneDrive - GIRANDO COMERCIO DE PECAS LTDA\iMercado - Eder Iago\Coletor Precos\Precos-db\precos.db'

# Inicia a conexao com o Banco de Dados passando o caminho do arquivo precos.db
conexao = sqlite3.connect(arquivo_db)

# Buscando os dados Banco e salvando em um dataframe
consulta_precos = pd.read_sql_query("""
                                  SELECT
                                  CONCORRENTE,
                                  ESTADO,
                                  COD_BUSCADO,
                                  COD_FABRICANTE,
                                  FABRICANTE,
                                  STATUS,
                                  PRECO AS PRECO_CONCORRENTE,
                                  PRECO_FINAL AS PRECO_ROLEMAR,
                                  DIF_PRECO,
                                  ROUND(PERC_DIF_PRECO * 100,2) AS PERC_DIF_PRECO,
                                  SITUACAO,
                                  DATA_COLETA
                                  
                                  FROM CURATED
                                  
                                  """, conexao)

# Ajustando coluna data para formato mais amigavelm para visualização
consulta_precos['DATA_COLETA'] = pd.to_datetime(consulta_precos['DATA_COLETA']).dt.strftime("%d/%m/%Y")

# Lista de valores par os filtros
concorrentes = consulta_precos['CONCORRENTE'].unique().tolist()
estados = consulta_precos['ESTADO'].unique().tolist()
datas = consulta_precos['DATA_COLETA'].unique().tolist()
situacao = consulta_precos['SITUACAO'].unique().tolist()

# Titulo da pagina
st.title("Consulta Preços")

with st.sidebar:
    st.title('🔎 Filtros')
    # Inserindo os multiselect para filtragem do dataframe
    selec_concorrentes = st.multiselect(
        label='Concorrente',
        options=concorrentes,
        default=None
    )

    selec_estados = st.multiselect(
        label='Estado',
        options=estados,
        default=None
    )

    selec_data = st.multiselect(
        label='Data da Coleta',
        options=datas,
        default=None
    )

    selec_situacao = st.multiselect(
        label='Situação',
        options=situacao,
        default=None
    )

    # Armazenando os filtros e buscas selecionadas 
    busca_texto = st.text_input('Digite o Codigo do Fabricante:')

condicao_busca = consulta_precos['COD_FABRICANTE'].str.contains(busca_texto)

condicao_concorrente = consulta_precos['CONCORRENTE'].isin(selec_concorrentes)

condicao_estado = consulta_precos['ESTADO'].isin(selec_estados)

condicao_data = consulta_precos['DATA_COLETA'].isin(selec_data)

condicao_situacao = consulta_precos['SITUACAO'].isin(selec_situacao)

# Armazenando e concatenando os filtros e buscas para aplicar no dataframe
filtros_selec = condicao_estado & condicao_concorrente & condicao_data & condicao_situacao & condicao_busca

# Aplicando os filtros no dataframe
consulta_precos_filtrado = consulta_precos[filtros_selec]

consulta_precos_filtrado = consulta_precos_filtrado.style.map(formatar_dif, subset=['DIF_PRECO'])

# Exibindo o dataframe em forma de tabela 
st.dataframe(consulta_precos_filtrado, width='stretch', hide_index=True)

buffer = BytesIO()
consulta_precos_filtrado.to_excel(buffer, index=False, engine='openpyxl')
buffer.seek(0)

st.download_button(
    label="Exportar dados para o Excel",
    data=buffer,
    file_name='Comparativo Precos.xlsx',
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)