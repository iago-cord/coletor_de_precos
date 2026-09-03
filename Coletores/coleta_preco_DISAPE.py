from playwright.sync_api import sync_playwright
import pandas as pd
import random
from dotenv import load_dotenv
import os
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from functions import selecionar_filial,clique_buscar
import logging

def executar(codigos, filiais):
    load_dotenv()
    usuario_login = os.getenv("DISAPE_USUARIO")
    senha_login = os.getenv("DISAPE_SENHA")

    resultados = []
    lista_filiais = filiais if filiais else [None]

    with sync_playwright() as p:

        browser = p.chromium.launch(headless = False)
        page = browser.new_page()

        page.goto("https://loja.disape.com.br/customer/account/login")

        usuario = page.get_by_role("textbox", name="Usuário *")
        usuario.click()
        page.wait_for_timeout(random.randint(1000, 2000))
        usuario.fill(usuario_login)
        
        senha = page.get_by_role("textbox", name="Senha")
        senha.click()
        page.wait_for_timeout(random.randint(1000, 2000))
        senha.fill(senha_login)
        
        page.wait_for_timeout(random.randint(1000, 2000))
        
        entrar = page.get_by_role("button", name="Entrar")
        entrar.click()
        
        page.get_by_role("textbox", name="Código da peça").wait_for(state="visible")
        
        for filial in lista_filiais:
            
            if filial:
                selecionar_filial(page, filial)
                logging.info(f"Disape: entrando no loop de códigos. Total: {len(codigos)}")
                
                page.locator("div.c-prazo span.selected.popup-modal").click()
                page.wait_for_selector("form#form-prazo ul.scroll.items")
                item = page.locator("form#form-prazo ul.scroll.items li.item").filter(has_text="60 Dias")
                item.locator("input[type='radio']").click()
                page.locator("form#form-prazo button.button", has_text="Aplicar").click()
                
                processados = 0
        
            for codigo in codigos:
                                
                try:
                    busca = page.get_by_role("textbox", name="Código da peça")
                    busca.click()
                    
                    busca.fill(codigo)
                    
                    clique_buscar(page)
                    
                    nao_encontrado = page.locator("div.message.notice")
            
                    try:
                        nao_encontrado.wait_for(state="visible", timeout=3000)
                        logging.info(f"Disape: {codigo} NÃO ENCONTRADO")
                        resultados.append({
                            "fornecedor": "DISAPE",
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
            
                    except:
                        pass
            
                        produtos = page.locator("ol.products.list.items.product-items > li.item.product.product-item")
                        produtos.first.wait_for(state="attached", timeout=3000)
                        
                        
            
                        count = produtos.count()
            
                        if count == 0:
                            resultados.append({
                                "fornecedor": "DISAPE",
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
                    
                            try:
                                descricao = card.locator("strong.product-item-name a.product-item-link").first.text_content(timeout=1000)
                            except:
                                descricao = None
            
                            try:
                                preco = card.locator("div.product-info.__row.__last div.product-item-inner div.price-box:not(.total-full) span.price").first.inner_text(timeout=1000)
                                
                            except:
                                preco = None
            
                            try:
                                cod_fabricante = card.locator("div.product-info.__row.__last div.cod-fabricante span").first.text_content(timeout=1000)
                                
                            except:
                                cod_fabricante = None
            
                            try:
                                fabricante = card.locator("div.product-info.__row.__last div.fabricante span").first.text_content(timeout=1000)
                               
                            except:
                                fabricante = None

                            try:
                                prazo  = page.locator("div.c-prazo > span.selected").text_content(timeout=1000)
                            except:
                                prazo = None
                            
                            try:
                                filial = page.locator("div.c-dist > span.selected").text_content(timeout=1000)
                            except:
                                filial = None
                                
                            descricao_principal = descricao
                            preco_principal = preco
                            cod_fabricante_principal = cod_fabricante
                            fabricante_principal = fabricante 
                                

                            resultados.append({
                                "fornecedor": "DISAPE",
                                "cod_buscado": codigo,
                                "cod_fabricante":cod_fabricante_principal,
                                "descricao": descricao_principal,
                                "preco":preco_principal,
                                "fabricante": fabricante_principal,
                                "status": "OK",
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
                                
                                page.wait_for_selector("div.products.list.items.popup-similares:visible")
                                page.wait_for_timeout(1000)

                                card_similares = page.locator("div.related-product div.product-item")

                                for i in range(card_similares.count()):

                                    card_sim = card_similares.nth(i)

                                    try:
                                        descricao_similar = card_sim.locator("div.product-block-name a.product-item-link").first.inner_text(timeout=1000)
                                    except:
                                        descricao_similar = None

                                    try:
                                        fabricante_similar = card_sim.locator("div.product-block-fabricante div.fabricante span[data-bind]").first.inner_text(timeout=1000)
                                    except:
                                        fabricante_similar = None

                                    try:
                                        cod_fabricante_similar = card_sim.locator("div.product-block-fabricante div.cod-fabricante span[data-bind]").first.inner_text(timeout=1000)
                                    except:
                                        cod_fabricante_similar = None

                                    try:
                                        preco_similar = card_sim.locator("div.product-item-actions span.price-container span.price").first.inner_text(timeout=1000)
                                    except:
                                        preco_similar = None                                                                                                                                                                                                                     

                                    resultados.append({
                                        "fornecedor": "DISAPE",
                                        "cod_buscado": codigo,
                                        "cod_fabricante":cod_fabricante_similar,
                                        "descricao": descricao_similar,
                                        "preco":preco_similar,
                                        "fabricante": fabricante_similar,
                                        "status": "Similar",
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
                            "fornecedor": "DISAPE",               
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





