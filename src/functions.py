import pandas as pd
import time
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
import logging

# faz mais de 1 tentativa para clicar no botao buscar, necessario pois as vezes acontece
# de o botao ainda nao estar disponivel, a função faz 3 tentativas de cliques esperando 2s entre cada tentativa
def clique_buscar(page):
    
    buscar = page.locator("#search-cod-fab-container").get_by_role("button", name="Buscar")
    
    retry_acao(lambda: buscar.click(no_wait_after=True, timeout = 1500), tentativas=3, espera=2)
    
def obter_filiais(page):
    """Abre o popup de filiais e retorna os nomes disponíveis, sem selecionar nada."""
    page.locator("div.c-dist span.selected.popup-modal").click()
    page.wait_for_selector("form#form-filial ul.scroll.items")

    nomes = page.locator("form#form-filial ul.scroll.items li.item span").all_inner_texts()

    return nomes

# Localiza e seleciona a filial, recebe como parametro o nome da filial e a pagina a ser procurada DS/R
def selecionar_filial(page, nome_filial):
    
    popup_filial = page.locator("div.c-dist span.selected.popup-modal")
    
    retry_acao(lambda: popup_filial.click())
    
    retry_acao(lambda:page.wait_for_selector("form#form-filial ul.scroll.items") )

    item = page.locator("form#form-filial ul.scroll.items li.item").filter(has_text=nome_filial)
    
    if item.count() == 0:
        raise ValueError(f"Filial não encontrada: {nome_filial}")
    
    retry_acao(lambda:item.locator("input[type='radio']").click() )
    
    retry_acao(lambda:page.locator("form#form-filial button.button", has_text="Aplicar").click())
   
# Localiza e seleciona a filial, recebe como parametro o nome da filial e a pagina a ser procurada S/SPR/SSP
def selecionar_filial_sky(page, filial):
    
    selec_filial = page.locator("select#secloja")
    
    retry_acao(lambda: selec_filial.select_option(label=filial))

    page.wait_for_load_state("networkidle", timeout=5000)
    
# Procura o campo de Busca de produtos e retorna o locator recebe como parametro a pagina P
def get_campo_busca(page):
    if page.locator('#ais-searchbox').is_visible():
        return page.locator('#ais-searchbox')
    return page.locator('#search-prod')

# Procura o Botao de Busca de produtos e retorna o locator recebe como parametro a pagina P
def get_botao_buscar(page):
    if page.locator('#btn-ais-BtnPesquisar').is_visible():
        return page.locator('#btn-ais-BtnPesquisar')
    return page.locator('#btn-search-btn-prod')

# Localiza e seleciona a filial, recebe como parametro o nome da filial e a pagina a ser procurada A
def selecionar_filial_autonorte(page,nome_filial):
    cliente_filial = {
        "Maranhão": "cod_cliente",
        "Pernambuco": "cod_cliente",
        "Pará": "cod_cliente",
        "Goiás": "cod_cliente",
        "Bahia": "cod_cliente"
    }       
    
    codigo = cliente_filial.get(nome_filial)
    
    if codigo is None:
        raise ValueError(f"Filial não cadastrada: {nome_filial}")
    
    cliente = page.get_by_role("textbox", name="COD ERP")
    retry_acao(lambda: cliente.fill(codigo))
    retry_acao(lambda: cliente.click())
    retry_acao(lambda: page.get_by_role("button", name="Pesquisar").click())
    retry_acao(lambda: page.get_by_role("button", name="Fazer pedido (abrir produtos").click())
    retry_acao(lambda: page.locator(".css-8mmkcg").first.click())
    retry_acao(lambda: page.get_by_role("option", name="60 dias").click())
    
# Faz o tratamento da coluna de preços e caso esteja vazia altera a coluna status para Sem Estoque    
def tratar_preco_sem_estoque(precos_concorrentes):

    preco_num = (
        precos_concorrentes['preco']
        .astype(str)
        .str.replace('R$', '', regex=False)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
        .str.strip()
    )

    preco_num = pd.to_numeric(preco_num, errors='coerce')

    mascara = (
        precos_concorrentes['status'].eq('OK')
        & (preco_num.isna() | preco_num.eq(0))
    )

    precos_concorrentes.loc[mascara, 'status'] = 'Sem Estoque'

    return precos_concorrentes

# Função de retry utilizada para tratamento de falhas em alguma parte do processo de coleta
# faz tentativas com intervalo de 5s entre cada uma delas
def retry_acao(acao, tentativas=5, espera=5):
    ultimo_erro = None
    
    for tentativa in range(1, tentativas + 1):
        try:
            return acao()
        
        except PlaywrightTimeoutError as e:
            ultimo_erro = e
            
            logging.warning(f"Timeout na tentativa {tentativa}/{tentativas}: {e}")
        
        except PlaywrightTimeoutError as e:
            ultimo_erro = e
            
            logging.warning(f"Erro Playwright na tentativa {tentativa}/{tentativas}: "
                            f"{type(e).__name__}: {e}")   
            
        if tentativa < tentativas:
            time.sleep(espera)
    
    logging.error(f"Ação falhou após {tentativa}/{tentativas}: "
                  f"{type(ultimo_erro).__name__}: {ultimo_erro}")
    
    raise ultimo_erro