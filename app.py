import streamlit as st
import main
import pandas as pd
from io import BytesIO
from ui import background_local, adicionar_logo_header
import sqlite3
from pathlib import Path


# Caminhos Relativos 
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "Precos-db" / "precos.db"
BG_PATH = BASE_DIR / "Assets" / "background_rolemar.png"
LOGO_PATH = BASE_DIR / "Assets" / "logo.png"

# Inicia a conexao com o Banco de Dados passando o caminho do arquivo precos.db
conexao = sqlite3.connect(DB_PATH)

# Query para obter os dados da CURVA ABC
busca_refforn = pd.read_sql_query("""
                                  SELECT
                                  CODPROD,
                                  REFFORN,
                                  CODGRUPOPROD,
                                  DESCRGRUPOPROD,
                                  FATURAMENTO
                                  FROM BUSCA_REFFORN
                                  """, conexao)


# Definindo a imagem de Background e Logo
background_local(BG_PATH)
adicionar_logo_header(LOGO_PATH)

# Titulo da pagina
st.title("Coletor de Preços")

# Verificando se algum grupo foi selecionado para busca na aba lateral e adicionado ao estado da sessao
if 'codigos_grupo' not in st.session_state:
    st.session_state.codigos_grupo = None

# Campo da planilha de codigos
arquivo = st.file_uploader("Selecione a Planilha")

# Insere os Checkbox para escolher de quais concorrentes quais filiais buscar
disape = st.checkbox("DISAPE")
filiais_disape=[]
if disape:
    filiais_disape = st.multiselect(
        "Filiais DISAPE",
        ["CARIACICA/ES","SAO JOSE/SC"]
        #"PORTO ALEGRE/RS","GOIANIA/GO","CURITIBA/PR" - Fiiais desativadas da coleta por regra de negocio
    )
rmp = st.checkbox("RMP")
filiais_rmp = []
if rmp:
    filiais_rmp = st.multiselect(
        "Filiais RMP",
        ["PORTO ALEGRE/RS"]
        #"SAO PAULO/SP","CARIACICA/ES","CURITIBA/PR","SAO JOSE/SC" - Fiiais desativadas da coleta por regra de negocio
    )
    
sky = st.checkbox("SKY")
filiais_sky = []
if sky:
    filiais_sky = st.multiselect(
        "Filiais SKY",
        ["SKY AUTOMOTIVE (POA)", "ENVIA PEÇAS (PELOTAS)", "EMBREPAR (POA)"]
    )

pellegrino = st.checkbox("Pellegrino")

autonorte = st.checkbox("Auto Norte")
filiais_autonorte = []
if autonorte:
    filiais_autonorte = st.multiselect(
        "Filiais Auto Norte",
        ["Maranhão", "Pernambuco", "Pará", "Goiás"]
    )
    
sky_sp = st.checkbox("SKY - SP")
filiais_sky_sp = []
if sky_sp:
    filiais_sky_sp = st.multiselect(
    "Filiais SKY - SP",
    ['SKY AUTOMOTIVE (GUARULHOS)', 'SKY AUTOMOTIVE (BOM RETIRO)', 'Embrepar (GO - Perimetral)' ]
    )    

sky_pr = st.checkbox("SKY - PR")
filiais_sky_pr = []
if sky_pr:
    filiais_sky_pr = st.multiselect(
        "Filiais SKY - PR",
        ['EMBREPAR (Londrina)','ENVIA PEÇAS (LONDRINA)']
    )
    
dpk = st.checkbox("DPK - PR")
filiais_dpk = []
if dpk:
    filiais_dpk = st.multiselect(
        "Filiais DPK - PR",
        ['LONDRINA', 'CURITIBA', 'CASCAVEL']
    )


if st.button("🚀 Buscar Preços"):
    # Se não tiver nenhuma planilha selecionada ele pede para selecionar uma 
    if arquivo is None and not st.session_state.codigos_grupo:
        st.warning("Selecione uma planilha ou um grupo no menu lateral antes de buscar.")
        
        # se nao tiver nenhum concorrente selecionado ele pede para selecionar um concorrente
    elif not (disape or rmp or sky or pellegrino or autonorte or sky_sp or sky_pr or dpk):
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
            codigos, disape=disape, rmp=rmp, sky=sky,pellegrino=pellegrino,autonorte=autonorte,sky_sp=sky_sp,sky_pr = sky_pr,dpk=dpk,
            filiais_disape=filiais_disape,
            filiais_rmp = filiais_rmp,
            filiais_sky = filiais_sky,
            filiais_autonorte = filiais_autonorte,
            filiais_sky_sp = filiais_sky_sp,
            filiais_sky_pr = filiais_sky_pr,
            filiais_dpk= filiais_dpk,
            callback=atualizar_progresso
        )
        
        st.write("Quantidade de códigos:", len(codigos))
        #st.write("Primeiros códigos:", codigos[:10])

        # Mensagem de conclusao da busca e exibição do resultado
        progress_bar.progress(100, text="Busca concluída!")
        st.success("Busca concluída!")
        st.dataframe(resultado)

        # salvando o dataframe na memoria para disponibilizar para download
        buffer = BytesIO()
        resultado.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)

        # botao de download com o resultado final
        st.download_button(
            label="📥 Baixar planilha de resultados",
            data=buffer,
            file_name="comparativo_precos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# pegando valores unicos de CODGRUPOPROD vindo da query para seleção na aba lateral
grupos = sorted(busca_refforn['CODGRUPOPROD'].unique(), reverse=False)

# aba lateral para seleção dos grupos a serem pesquisados
with st.sidebar:
    st.title('🔎 Escolher Grupos P/ Coleta de Preços')
    
    selec_grupos = st.multiselect(
        label='Grupos',
        options=grupos,
        default=None
    )
    # recebe a lista do grupos selecionados no multiselect
    condicao_grupos = busca_refforn['CODGRUPOPROD'].isin(selec_grupos)
    
    # Renomeando a coluna REFFORN para que os coletores identifiquem a coluna de codigos
    refforn_busca = busca_refforn.loc[
        condicao_grupos, ['REFFORN']
    ].rename(columns={'REFFORN': 'codigos'})
    
    # Checkbox para seleção de codigos pela CURVA ABC
    curva_abc = st.checkbox("CURVA ABC")
    
    # se a checkbox da curva ABC foi selecionada executa os calculos do bloco abaixo 
    if curva_abc:
        
        # Recebe a seleção de grupos para o calculo da Curva
        refforn_busca = busca_refforn[condicao_grupos]
        
        # Ordenando os produtos dentro dos grupos
        curva = refforn_busca.sort_values(
            ['CODGRUPOPROD', 'FATURAMENTO'],
            ascending=[True, False]
        )
        
        # Calculando a participação de cada CODPROD no faturamento
        curva['PERC_FATURAMENTO'] = (
            curva['FATURAMENTO'] / 
            curva.groupby('CODGRUPOPROD')['FATURAMENTO'].transform('sum')
        )
        
        # Calculando o acumulado
        curva['PERC_ACUMULADO'] = (
            curva.groupby('CODGRUPOPROD')['PERC_FATURAMENTO'].cumsum()
        )
        
        # adiciona dois checkbox para escolher a forma de seleção dos refforn de cada grupo
        criterio = st.radio(
        "Critério da curva",
        ["Quantidade de produtos", "Percentual do faturamento"]
        )
        
        # verifica qual criterio selecionado para retornar os refforn para busca
        if criterio == "Quantidade de produtos":
            quantidade = st.number_input(
                "Quantidade de produtos",
                min_value=1,
                step=1
            )
            # se Quantidade de Produtos foi selecionado pega os x primeiros codigos da curva
            # sendo x a quantidade inserida no campo de quantidae
            curva = curva.groupby('CODGRUPOPROD').head(quantidade)
            #st.write("Linhas na curva:", len(curva))
            #st.write("REFFORN únicos:", curva['REFFORN'].nunique())
        
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
            
        refforn_busca = curva[['REFFORN']].rename(
            columns={'REFFORN': 'codigos'}
        )
    # renomenado a coluna REFFORN para codigos que é o padrao utilizado nos coletores    
    else:
        refforn_busca = busca_refforn.loc[
        condicao_grupos, ['REFFORN']
        ].rename(columns={'REFFORN': 'codigos'})
        
    # exibe quantos grupos e quantos refforn foram selecionados se la no criterio nada for selecionado retorna o total
    # de refforn de cada grupo
    st.write(f"**Grupos selecionados:** {len(selec_grupos)}")
    st.write(f"**Códigos encontrados:** {len(refforn_busca)}")
    
    # botão para levar os codigos para busca incluindo no estao da sessao
    if st.button("Usar Grupos Selecionados"):
        st.session_state.codigos_grupo = (
            refforn_busca['codigos'].dropna().astype(str).tolist()
        )


    


    
    

