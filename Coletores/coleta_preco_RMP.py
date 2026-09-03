from playwright.sync_api import sync_playwright
import pandas as pd
import random
from dotenv import load_dotenv
import os
from functions import clique_buscar
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from functions import selecionar_filial, retry_acao
import logging

# Função para carregar as credenciais de Login ao site
def executar(codigos, filiais):
    load_dotenv()
    usuario_login = os.getenv("RMP_USUARIO")
    senha_login = os.getenv("RMP_SENHA")

    resultados = []
    lista_filiais = filiais if filiais else [None]

    with sync_playwright() as p:
       
        # Bloco de acesso ao site
        browser = p.chromium.launch(headless = False)
        
        page = browser.new_page()
        
        url = "https://loja.rmp.com.br/customer/account/login"
        
        retry_acao(lambda: page.goto(url))

        usuario = page.get_by_role("textbox", name="Usuário *")
        retry_acao(lambda:usuario.click())

        page.wait_for_timeout(random.randint(1000, 2000))
        retry_acao(lambda:usuario.fill(usuario_login))
        
        senha = page.get_by_role("textbox", name="Senha")
        retry_acao(lambda:senha.click())
        
        page.wait_for_timeout(random.randint(1000, 2000))
        retry_acao(lambda:senha.fill(senha_login))
        
        page.wait_for_timeout(random.randint(1000, 2000))
        
        entrar = page.get_by_role("button", name="Entrar")
        
        retry_acao(lambda:entrar.click())
        
        retry_acao(lambda: page.get_by_role("textbox", name="Código da peça").wait_for(state="visible"))
        
        for filial in lista_filiais:
            
            if filial:
                
                selecionar_filial(page,filial)
                logging.info(f"RMP: entrando no loop de códigos. Total: {len(codigos)}")
                
                
                retry_acao(lambda:page.locator("div.c-prazo span.selected.popup-modal").click())
                
                retry_acao(lambda:page.wait_for_selector("form#form-prazo ul.scroll.items"))
                
                item = page.locator("form#form-prazo ul.scroll.items li.item").filter(has_text="60 Dias")
                retry_acao(lambda:item.locator("input[type='radio']").click())
                
                retry_acao(lambda:page.locator("form#form-prazo button.button", has_text="Aplicar").click() )
                
                
                processados = 0
        
            for codigo in codigos:
                
                processados += 1
                
                print(f"Processando {processados}/{len(codigos)}: {codigo}")
                try:
                    busca = page.get_by_role("textbox", name="Código da peça")
                    retry_acao(lambda:busca.click())
                    
                    retry_acao(lambda:busca.fill(codigo))
                    
                    clique_buscar(page)
                    
                    nao_encontrado = page.locator("div.message.notice")
            
                    try:
                        nao_encontrado.wait_for(state="visible", timeout=3000)
                        logging.info(f"RMP: {codigo} NÃO ENCONTRADO")

                        resultados.append({
                                            "fornecedor": "RMP",
                                            "cod_buscado": codigo,
                                            "cod_fabricante": None, 
                                            "descricao": None,                               
                                            "preco": None,
                                            "fabricante": None,
                                            "status": "NÃO ENCONTRADO",
                                            "prazo": None,
                                            "filial": None
                                            })
                        continue
            
                    except PlaywrightTimeoutError:
                        pass
            
                        produtos = page.locator("ol.products.list.items.product-items > li.item.product.product-item")

                        produtos.first.wait_for(state="attached", timeout=3000)
                        page.wait_for_load_state("domcontentloaded",timeout=5000)
            
                        count = produtos.count()
                        
                        if count == 0:
                            resultados.append({
                                "fornecedor": "RMP",
                                "cod_buscado": codigo,
                                "cod_fabricante": None,
                                "descricao": "SEM DADOS",
                                "preco": None,
                                "fabricante": None,
                                "status": "NAO ENCONTRADO",
                                "prazo": None,
                                "filial": None
                            })
                            continue
            
                        for i in range(count):
                            card = produtos.nth(i)
                            status = "OK"
                            erros_coleta = []
            
                            try:
                                descricao = card.locator("strong.product-item-name a.product-item-link").first.text_content(timeout=1000)  
                            except PlaywrightTimeoutError:
                                descricao = None
                                erros_coleta.append('DESCRICAO')
            
                            try:
                                preco = card.locator("div.product-item-inner div.price-box:not(.total-full) span.price").first.inner_text(timeout=1000)
                            except PlaywrightTimeoutError:
                                preco = None
                                erros_coleta.append('PRECO')
            
                            try:
                                cod_fabricante = card.locator("div.product-info.__row.__last div.cod-fabricante span").first.text_content(timeout=1000)
                            except PlaywrightTimeoutError:
                                cod_fabricante = None
                                erros_coleta.append('COD_FABRICANTE')
            
                            try:
                                fabricante = card.locator("div.product-block-fabricante div.fabricante span").first.inner_text(timeout=1000)
                            except PlaywrightTimeoutError:
                                fabricante = None
                                erros_coleta.append('FABRICANTE')

                            try:
                                prazo  = page.locator("div.c-prazo > span.selected").text_content(timeout=1000)
                            except PlaywrightTimeoutError:
                                prazo = None
                                erros_coleta.append('PRAZO')
                                
                            try:
                                filial = page.locator("div.c-dist > span.selected").text_content(timeout=1000)
                            except PlaywrightTimeoutError:
                                filial = None
                                erros_coleta.append('FILIAL')
                                
                            descricao_principal = descricao
                            preco_principal = preco
                            cod_fabricante_principal = cod_fabricante
                            fabricante_principal = fabricante 
                            
                            if erros_coleta:
                                status = "ERRO NA COLETA: " + ", ".join(erros_coleta)

                            resultados.append({
                                "fornecedor": "RMP",
                                "cod_buscado": codigo,
                                "cod_fabricante":cod_fabricante_principal,
                                "descricao": descricao_principal,
                                "preco":preco_principal,
                                "fabricante": fabricante_principal,
                                "status": status,
                                "prazo": prazo,
                                "filial": filial
                                })
                            

                            similares = card.get_by_role("link", name="Produtos Similares")
                            
                            tem_similar = similares.count()
                            
                            if not tem_similar:
                                continue
                            
                            try:
                            
                                page.wait_for_timeout(random.randint(1000, 2000))
                                
                                similares.click()
                                
                                popup_erro = page.locator("aside.modal-popup.similar-product-error._show")
                                
                                try:
                                    popup_erro.wait_for(state="attached", timeout=1000)

                                    page.wait_for_timeout(500)
                                    
                                    popup_erro.locator("button.action-close[data-role='closeBtn']").click(force=True)

                                    page.wait_for_timeout(500)
                                    continue
                                
                                except PlaywrightTimeoutError:
                                    
                                    pass
                                
                                retry_acao(lambda:page.wait_for_selector("div.products.list.items.popup-similares:visible"))
                                page.wait_for_timeout(1000)

                                card_similares = page.locator("div.related-product div.product-item")

                                for i in range(card_similares.count()):

                                    card_sim = card_similares.nth(i)
                                    status = 'Similar'
                                    erros_coleta = []

                                    try:
                                        descricao_similar = card_sim.locator("div.product-block-name a.product-item-link").inner_text(timeout=1000)
                                    except PlaywrightTimeoutError:
                                        descricao_similar = None
                                        erros_coleta.append('DESCRICAO')

                                    try:
                                        fabricante_similar = card_sim.locator("div.product-block-fabricante div.fabricante span[data-bind]").inner_text(timeout=1000)
                                    except PlaywrightTimeoutError:
                                        fabricante_similar = None
                                        erros_coleta.append('FABRICANTE')

                                    try:
                                        cod_fabricante_similar = card_sim.locator("div.product-block-fabricante div.cod-fabricante span[data-bind]").inner_text(timeout=1000)
                                    except PlaywrightTimeoutError:
                                        cod_fabricante_similar = None
                                        erros_coleta.append('COD_FABRICANTE')

                                    try:
                                        preco_similar = card_sim.locator("div.product-item-actions span.price-container span.price").inner_text(timeout=1000)
                                    except PlaywrightTimeoutError:
                                        preco_similar = None     
                                        erros_coleta.append('PRECO')
                                        
                                    if erros_coleta:
                                        status = "ERRO NA COLETA: " + ", ".join(erros_coleta)                                                                                                                                                                                                              

                                    resultados.append({
                                                                "fornecedor": "RMP",
                                                                "cod_buscado": codigo,
                                                                "cod_fabricante":cod_fabricante_similar,
                                                                "descricao": descricao_similar,
                                                                "preco":preco_similar,
                                                                "fabricante": fabricante_similar,
                                                                "status": status,
                                                                "prazo": prazo,
                                                                "filial": filial
                                                                
                                                            })
                                fechar_popup = page.locator("div.modal-inner-wrap button.action-close:visible")
                                
                                fechar_popup.click()
                                
                                page.locator(".modals-overlay").wait_for(state="hidden")
                                
                                page.wait_for_timeout(1000)
                            
                            except Exception as e:
                                print(f"Erro ao processar similares do produto'{codigo}' : {e}")
                                continue
                        
                            
                except Exception as e:
            
                        print(f"Erro ao buscar '{codigo}': {e}")
                        resultados.append({
                            "fornecedor": "RMP",               
                            "cod_buscado": codigo,
                            "cod_fabricante": None, 
                            "descricao": f"ERRO: {e}",  
                            "preco": None,
                            "fabricante": None,
                            "status": "NÃO ENCONTRADO",
                            "prazo": None,
                            "filial": None
                        })
                finally:
                        page.wait_for_timeout(random.randint(1000,2000))
                        
        print(f"Loop finalizado: {processados}/{len(codigos)} códigos processados")
        
        resultado_busca = pd.DataFrame(resultados)
        
        colunas = [
            "fornecedor",
            "cod_buscado",
            "cod_fabricante",
            "descricao",
            "preco",
            "fabricante",
            "status"
        ]
        
        resultado_busca[colunas] = resultado_busca[colunas].apply(lambda c: c.str.strip())

    return resultado_busca

if __name__ == "__main__":

    cod_busca = ["ECO1651","VC-232"]
             


















