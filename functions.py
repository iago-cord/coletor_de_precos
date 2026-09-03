import pandas as pd
import time
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
import logging

# faz mais de 1 tentativa para clicar no botao buscar, necessario pois as vezes acontece
# de o botao ainda nao estar disponivel ai ela faz 3 tentativas de cliques 
def clique_buscar(page, tentativas=3):
    buscar = page.locator("#search-cod-fab-container").get_by_role("button", name="Buscar")
    for tentativa in range(1, tentativas + 1):
        try:
            buscar.click(no_wait_after=True, timeout=1500)
            return True
        except Exception as e:
            print(f"[tentativa {tentativa}] timeout ao clicar em Buscar: {e}")
            if tentativa == tentativas:
                raise
            page.wait_for_timeout(2000)
    return False


def obter_filiais(page):
    """Abre o popup de filiais e retorna os nomes disponíveis, sem selecionar nada."""
    page.locator("div.c-dist span.selected.popup-modal").click()
    page.wait_for_selector("form#form-filial ul.scroll.items")

    nomes = page.locator("form#form-filial ul.scroll.items li.item span").all_inner_texts()

    return nomes


def selecionar_filial(page, nome_filial):
    """Abre o popup de filiais e seleciona a filial pelo nome."""
    retry_acao(lambda:page.locator("div.c-dist span.selected.popup-modal").click())
    #page.locator("div.c-dist span.selected.popup-modal").click()
    
    retry_acao(lambda:page.wait_for_selector("form#form-filial ul.scroll.items") )
    #page.wait_for_selector("form#form-filial ul.scroll.items")

    item = page.locator("form#form-filial ul.scroll.items li.item").filter(has_text=nome_filial)
    
    retry_acao(lambda:item.locator("input[type='radio']").click() )
    #item.locator("input[type='radio']").click()
    
    retry_acao(lambda:page.locator("form#form-filial button.button", has_text="Aplicar").click())
    #page.locator("form#form-filial button.button", has_text="Aplicar").click()
    
def selecionar_filial_sky(page, filial):
    """Seleciona a filial no dropdown nativo da SKY, pelo value da option."""
    page.locator("select#secloja").select_option(label=filial)
    #page.locator("select#secloja").select_option(value=valor_filial)
    #page.wait_for_timeout(1500)
    page.wait_for_load_state("networkidle", timeout=8000)
    
    
def get_campo_busca(page):
    if page.locator('#ais-searchbox').is_visible():
        return page.locator('#ais-searchbox')
    return page.locator('#search-prod')

def get_botao_buscar(page):
    if page.locator('#btn-ais-BtnPesquisar').is_visible():
        return page.locator('#btn-ais-BtnPesquisar')
    return page.locator('#btn-search-btn-prod')

def selecionar_filial_autonorte(page, nome_filial):
    if nome_filial == "Maranhão":
        cliente = page.get_by_role("textbox", name="COD ERP")
        cliente.fill('26570')
        cliente.click()
        page.get_by_role("button", name="Pesquisar").click()
        page.get_by_role("button", name="Fazer pedido (abrir produtos").click()
        page.locator(".css-8mmkcg").first.click()
        page.get_by_role("option", name="60 dias").click()
    elif nome_filial == "Pernambuco":
        cliente = page.get_by_role("textbox", name="COD ERP")
        cliente.fill('00238')
        cliente.click()
        page.get_by_role("button", name="Pesquisar").click()
        page.get_by_role("button", name="Fazer pedido (abrir produtos").click()
        page.locator(".css-8mmkcg").first.click()
        page.get_by_role("option", name="60 dias").click()
    elif nome_filial == "Pará":
        cliente = page.get_by_role("textbox", name="COD ERP")
        cliente.fill('84001')
        cliente.click()
        page.get_by_role("button", name="Pesquisar").click()
        page.get_by_role("button", name="Fazer pedido (abrir produtos").click()
        page.locator(".css-8mmkcg").first.click()
        page.get_by_role("option", name="60 dias").click()
    elif nome_filial == "Goiás":
        cliente = page.get_by_role("textbox", name="COD ERP")
        cliente.fill('66976')
        cliente.click()
        page.get_by_role("button", name="Pesquisar").click()
        page.get_by_role("button", name="Fazer pedido (abrir produtos").click()
        page.locator(".css-8mmkcg").first.click()
        page.get_by_role("option", name="60 dias").click()
        
        
'''def tratar_preco_sem_estoque(precos_concorrentes):
        valores_sem_estoque = [None, "--", "R$0,00","R$ 0,00", "0,00", "0",""," "]
        mascara = (precos_concorrentes['preco'].isin(valores_sem_estoque) | precos_concorrentes['preco'].isna ()) & (precos_concorrentes['status'] == 'OK')
        precos_concorrentes.loc[mascara, 'status'] = "Sem Estoque"
        return precos_concorrentes'''
    
    
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


def retry_acao(acao, tentativas=5, espera=5):
    for tentativa in range(1, tentativas + 1):
        try:
            return acao()
        
        except PlaywrightTimeoutError:
            logging.warning(
                f"Timeout na tentativa {tentativa}/{tentativas}"
            )
            
            if tentativa < tentativas:
                time.sleep(espera)
            else:
                raise