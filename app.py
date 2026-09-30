import streamlit as st
from src import main
import pandas as pd
from io import BytesIO
import sqlite3
from pathlib import Path
from src import analise_preco


# Caminhos Relativos 
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "Precos-db" / "database.db"
BG_PATH = BASE_DIR / "Assets" / "background_interface.png"
LOGO_PATH = BASE_DIR / "Assets" / "logo_empresa.png"

# Inicia a conexao com o Banco de Dados passando o caminho do arquivo precos.db
#conexao = sqlite3.connect(DB_PATH)

# Query para obter os dados da CURVA ABC
'''busca_cod_fornecedor = pd.read_sql_query("""
                                  SELECT
                                  COD_PRODUTO,
                                  COD_FORNECEDOR,
                                  COD_GRUPO,
                                  DESCRICAO_GRUPO,
                                  FATURAMENTO
                                  FROM BUSCA_COD_FORNECEDOR
                                  """, conexao)
'''

# Titulo da pagina
st.title("Coletor de Preços")

# Verificando se algum grupo foi selecionado para busca na aba lateral e adicionado ao estado da sessao
if 'codigos_grupo' not in st.session_state:
    st.session_state.codigos_grupo = None

# Campo da planilha de codigos
arquivo = st.file_uploader("Selecione a Planilha")

# Insere os Checkbox para escolher de quais concorrentes quais filiais buscar
ds = st.checkbox("DS")
filiais_ds=[]
if ds:
    filiais_ds = st.multiselect(
        "Filiais DS",
        ["Filial 01","Filial 02"]
    )
r = st.checkbox("R")
filiais_r = []
if r:
    filiais_r = st.multiselect(
        "Filiais R",
        ["Filial 01"]
    )
    
s = st.checkbox("S")
filiais_s = []
if s:
    filiais_s = st.multiselect(
        "Filiais S",
        ["Filial 01","Filial 02"]
    )

p = st.checkbox("P")

a = st.checkbox("A")
filiais_a = []
if a:
    filiais_a = st.multiselect(
        "Filiais A",
        ["Filial 01","Filial 02","Filial 03","Filial 04"]
    )
    
ssp = st.checkbox("SSP")
filiais_ssp = []
if ssp:
    filiais_ssp = st.multiselect(
    "Filiais SSP",
    ["Filial 01","Filial 02","Filial 03"]
    )    

spr = st.checkbox("SPR")
filiais_spr = []
if spr:
    filiais_spr = st.multiselect(
        "Filiais SPR",
        ["Filial 01"]
    )
    
d = st.checkbox("D")
filiais_d = []
if d:
    filiais_d = st.multiselect(
        "Filiais D",
        ["Filial 01","Filial 02","Filial 03"]
    )


if st.button("🚀 Buscar Preços"):
    # Se não tiver nenhuma planilha selecionada ele pede para selecionar uma 
    if arquivo is None and not st.session_state.codigos_grupo:
        st.warning("Selecione uma planilha ou um grupo no menu lateral antes de buscar.")
        
        # se nao tiver nenhum concorrente selecionado ele pede para selecionar um concorrente
    elif not (ds or r or s or p or a or ssp or spr or d):
        st.warning("⚠️ Selecione ao menos um concorrente.")   
    else:
        # verifica se algum grupo foi selecionado na aba lateral 
        if st.session_state.codigos_grupo:
            codigos = st.session_state.codigos_grupo
        # se nenhum grupo foi selecionado faz a leitura do arquivo upado com os codigos para busca
        else:
            df_codigos = pd.read_excel(arquivo)
            codigos = df_codigos["codigo"].dropna().astype(str).tolist()
       
        
        # Barra de progresso e progressao
        progress_bar = st.progress(0, text="🔎 Iniciando busca...")
        log_area = st.empty()
        log_linhas = []
        
        etapa_area = st.empty()

        # Log da busca exibindo qual concorrente esta sendo pesquisado e quantos ja foram concluidos
        def atualizar_progresso(atual, total, concorrente,etapa):
            if etapa == "Coleta Concluida":
                pct = int((atual / total) * 100)
                progress_bar.progress(pct, text=f"🔎 Buscando em {concorrente}... ({atual}/{total})")
                log_linhas.append(f"✅ {concorrente} — {atual}/{total} concluído")
                log_area.text("\n".join(log_linhas))
            else:
                etapa_area.info(f"{etapa}...")
        # chamando a função do main.py para iniciar a busca e callback para atualizar o progresso
        resultado = main.executar(
            codigos, ds=ds, r=r, s=s, p=p, a=a, ssp=ssp, spr = spr, d=d,
            filiais_ds=filiais_ds,
            filiais_r = filiais_r,
            filiais_s = filiais_s,
            filiais_a = filiais_a,
            filiais_ssp = filiais_ssp,
            filiais_spr = filiais_spr,
            filiais_d= filiais_d,
            callback=atualizar_progresso
        )
        
        st.write("Quantidade de códigos:", len(codigos))


        # Mensagem de conclusao da busca e exibição do resultado
        progress_bar.progress(100, text="Busca concluída!")
        st.success("Busca concluída!")
        st.dataframe(resultado)
        
        analise_precos = analise_preco(resultado)


        # botao de download com o resultado final
        st.download_button(
            label="📥 Baixar planilha de resultados",
            data=analise_precos,
            file_name="comparativo_precos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# pegando valores unicos de COD_GRUPO vindo da query para seleção na aba lateral
grupos = sorted(busca_cod_fornecedor['COD_GRUPO'].unique(), reverse=False)

# aba lateral para seleção dos grupos a serem pesquisados
with st.sidebar:
    st.title('🔎 Escolher Grupos P/ Coleta de Preços')
    
    selec_grupos = st.multiselect(
        label='Grupos',
        options=grupos,
        default=None
    )
    # recebe a lista do grupos selecionados no multiselect
    condicao_grupos = busca_cod_fornecedor['COD_GRUPO'].isin(selec_grupos)
    
    # Renomeando a coluna COD_FORNECEDOR para que os coletores identifiquem a coluna de codigos
    cod_fornecedor_busca = busca_cod_fornecedor.loc[
        condicao_grupos, ['COD_FORNECEDOR']
    ].rename(columns={'COD_FORNECEDOR': 'codigos'})
    
    # Checkbox para seleção de codigos pela CURVA ABC
    curva_abc = st.checkbox("CURVA ABC")
    
    # se a checkbox da curva ABC foi selecionada executa os calculos do bloco abaixo 
    if curva_abc:
        
        # Recebe a seleção de grupos para o calculo da Curva
        cod_fornecedor_busca = busca_cod_fornecedor[condicao_grupos]
        
        # Ordenando os produtos dentro dos grupos
        curva = cod_fornecedor_busca.sort_values(
            ['COD_GRUPO', 'FATURAMENTO'],
            ascending=[True, False]
        )
        
        # Calculando a participação de cada COD_PRODUTO no faturamento
        curva['PERC_FATURAMENTO'] = (
            curva['FATURAMENTO'] / 
            curva.groupby('COD_GRUPO')['FATURAMENTO'].transform('sum')
        )
        
        # Calculando o acumulado
        curva['PERC_ACUMULADO'] = (
            curva.groupby('COD_GRUPO')['PERC_FATURAMENTO'].cumsum()
        )
        
        # adiciona dois checkbox para escolher a forma de seleção dos cod_fornecedor de cada grupo
        criterio = st.radio(
        "Critério da curva",
        ["Quantidade de produtos", "Percentual do faturamento"]
        )
        
        # verifica qual criterio selecionado para retornar os cod_fornecedor para busca
        if criterio == "Quantidade de produtos":
            quantidade = st.number_input(
                "Quantidade de produtos",
                min_value=1,
                step=1
            )
            # se Quantidade de Produtos foi selecionado pega os x primeiros codigos da curva
            # sendo x a quantidade inserida no campo de quantidae
            curva = curva.groupby('COD_GRUPO').head(quantidade)
        
        # se o criterio foi o % vai selecionar o % da curva selecionado
        # o % da curva considera o % de faturamento acumulado   
        else:
            percentual = st.number_input(
                "Percentual do faturamento (%)",
                min_value=1.0,
                max_value=1000.0,
                step=1.0
            )
            
            curva = curva[
            curva['PERC_ACUMULADO'] <= percentual / 100
        ]
            
        cod_fornecedor_busca = curva[['COD_FORNECEDOR']].rename(
            columns={'COD_FORNECEDOR': 'codigos'}
        )
    # renomenado a coluna COD_FORNECEDOR para codigos que é o padrao utilizado nos coletores    
    else:
        cod_fornecedor_busca = busca_cod_fornecedor.loc[
        condicao_grupos, ['COD_FORNECEDOR']
        ].rename(columns={'COD_FORNECEDOR': 'codigos'})
        
    # exibe quantos grupos e quantos cod_fornecedor foram selecionados se la no criterio nada for selecionado retorna o total
    # de refforn de cada grupo
    st.write(f"**Grupos selecionados:** {len(selec_grupos)}")
    st.write(f"**Códigos encontrados:** {len(cod_fornecedor_busca)}")
    
    # botão para levar os codigos para busca incluindo no estao da sessao
    if st.button("Usar Grupos Selecionados"):
        st.session_state.codigos_grupo = (
            cod_fornecedor_busca['codigos'].dropna().astype(str).tolist()
        )


    


    
    

