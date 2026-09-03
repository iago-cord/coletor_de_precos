from playwright.sync_api import sync_playwright
import pandas as pd
import random
from dotenv import load_dotenv
import os
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
import logging



def executar(codigos,filiais):
    
    load_dotenv()
    usuario_login = os.getenv("DPK_USUARIO")
    senha_login = os.getenv("DPK_SENHA")

    resultados = []
    lista_filiais = filiais if filiais else [None]

    with sync_playwright() as p:
        
        browser = p.chromium.launch(headless=False)
        
        page = browser.new_page()
        
        url = "https://www.dpk.com.br/#/login"
        
        page.goto(url)
        
        usuario = page.get_by_role("textbox", name="Email")
        usuario.click()
        usuario.fill(usuario_login)
        page.wait_for_timeout(random.randint(1000,2000))
        
        senha = page.get_by_role("textbox", name="Senha")
        senha.click()
        senha.fill(senha_login)
        page.wait_for_timeout(random.randint(1000,2000))
        
        entrar = page.get_by_role("button", name="Entrar")
        entrar.click()
        
        page.get_by_role("search", name="Busque por código ou descriçã").wait_for(state='visible')
        
        for filial in lista_filiais:
            
            page.locator(".mat-select-arrow").first.click()
            
            item = page.get_by_text(filial)
            
            item.click()
            
            for codigo in codigos:
                
                try:
                
                    page.get_by_role("search", name="Busque por código ou descriçã").wait_for(state='visible')
                    
                    busca = page.get_by_role("search", name="Busque por código ou descriçã")
                    
                    busca.click()
                    
                    busca.fill(codigo)
                    
                    buscar = page.get_by_role("button", name="Buscar")
                    
                    buscar.click()
                    
                    nao_encontrado = page.locator("div.kdp-favorito-vazio")
                
                    try:
                        nao_encontrado.wait_for(state='visible')
                        logging.info(f"DPK: {codigo} NÃO ENCONTRADO")
                        
                        resultados.append({
                            "fornecedor": "DPK",
                            "cod_buscado": codigo,
                            "cod_fabricante": None,
                            "descricao": None,
                            "preco": None,
                            "fabricante": None,
                            "status": "Não Encontrado",
                            "prazo": None,
                            "filial": None
                        })
                        continue
                    except PlaywrightTimeoutError:
                        pass
                    
                    produtos = page.locator("div.column-view-card:visible")
                    
                    count = produtos.count()
                    
                    print(count)
                    for i in range(count):
                        
                        card = produtos.nth(i)
                        status = "OK"
                        erros_coleta = []
                        
                        try:
                            descricao = card.locator("h2 a").text_content(timeout=1000)
                            
                        except PlaywrightTimeoutError:
                            descricao = None
                            erros_coleta.append('DESCRICAO')
                        
                        try:
                            fabricante = card.locator("xpath=//p[contains(text(), 'Fabricante')]/following-sibling::strong[1]").text_content(timeout=1000)
                        
                        except PlaywrightTimeoutError:
                            fabricante = None
                            erros_coleta.append('FABRICANTE')
                        
                        try:    
                            cod_fabricante = card.locator("xpath=//p[contains(text(), 'Cód de Fábrica')]/following-sibling::strong[1]").text_content(timeout=1000)
                            
                        except PlaywrightTimeoutError:
                            cod_fabricante = None
                            erros_coleta.append('COD_FABRICANTE')
                        
                        try:
                            preco = card.locator("div.preco-colum span.cor-preco").inner_text(timeout=1000)
                            
                        except PlaywrightTimeoutError:
                            preco = None
                            erros_coleta.append('PRECO')
                            
                        try:
                            filial = page.locator("div.mat-form-field-infix span.mat-select-value-text").text_content(timeout=1000)
                        
                        except PlaywrightTimeoutError:
                            filial = None
                            
                            
                        descricao_principal = descricao
                        preco_principal = preco
                        cod_fabricante_principal = cod_fabricante
                        fabricante_principal = fabricante
                            
                        if erros_coleta:
                            status = "ERRO NA COLETA: " + ", ".join(erros_coleta)
                        
                        resultados.append({
                            "fornecedor": "DPK",
                            "cod_buscado": codigo,
                            "cod_fabricante": cod_fabricante_principal,
                            "descricao": descricao_principal,
                            "preco": preco_principal,
                            "fabricante": fabricante_principal,
                            "status": status,
                            "prazo": "60",
                            "filial": filial
                        })
                        
                        botao_similar = card.locator("button#similaresBtn")
                        
                        print(botao_similar.count())
                        
                        url_busca = page.url
                        
                        botao_similar.click()
                        
                        page.wait_for_timeout(2000)
                        
                        similares = page.locator("div.conteudo_similares ul.slides-list li.ng-star-inserted")
                        
                        print(similares.count())
                        
                        for j in range(similares.count()):
                            
                            card_sim = similares.nth(j)
                            status = 'Similar'
                            erros_coleta= []
                            
                            try:
                                descricao_similar = card_sim.locator("h2.mat-h4").text_content(timeout=1000)
                            except PlaywrightTimeoutError:
                                descricao_similar = None
                                erros_coleta.append("DESCRICAO")
                            
                            try:
                                preco_similar = card_sim.locator("div.valor strong.mat-h2").text_content(timeout=1000)
                            except PlaywrightTimeoutError:
                                preco_similar = None
                                erros_coleta.append("PRECO")
                                
                            try:
                                campo_fabricante = card_sim.locator("ul.conteudo li", has_text="Fabricante")
                                fabricante_completo = campo_fabricante.text_content(timeout=1000)
                                fabricante_similar = fabricante_completo.split(":")[1].strip()
                            except PlaywrightTimeoutError:
                                fabricante_similar = None
                                erros_coleta.append("FABRICANTE")
                                
                            try:
                                campo_cod_fabricante = card_sim.locator("ul.conteudo li", has_text="Cód. de Fábrica")
                                cod_fabricante_completo = campo_cod_fabricante.text_content(timeout=1000)
                                cod_fabricante_similar = cod_fabricante_completo.split(":")[1].strip()
                            except PlaywrightTimeoutError:
                                cod_fabricante_similar = None
                                erros_coleta.append("COD_FABRICANTE")
                            
                            if erros_coleta:
                                status = "ERRO NA COLETA: " + ", ".join(erros_coleta)
                            
                            resultados.append({
                                "fornecedor": "DPK",
                                "cod_buscado": codigo,
                                "cod_fabricante": cod_fabricante_similar,
                                "descricao": descricao_similar,
                                "preco": preco_similar,
                                "fabricante": fabricante_similar,
                                "status": status,
                                "prazo": "60",
                                "filial": filial
                            })
                            
                        page.wait_for_timeout(2000)
                        page.goto(url_busca)
                                
                finally:
                    page.wait_for_timeout(random.randint(1000,2000))
                
            resultado_busca = pd.DataFrame(resultados)
            
            return resultado_busca
          


if __name__ == "__main__":

    codigos = ['pd1530', 'vc232', 'eco1615']  
    
   
    
    
    
    