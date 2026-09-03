from playwright.sync_api import sync_playwright
import random
import os
from dotenv import load_dotenv
import logging
import pandas as pd
from functions import selecionar_filial_autonorte
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


def executar(codigos, filiais):
    load_dotenv()
    usuario_login = os.getenv("AUTONORTE_USER")
    senha_login = os.getenv("AUTONORTE_PASSWORD")

    resultados = []
    lista_filiais = filiais if filiais else [None]


    with sync_playwright() as p:
        
        browser = p.chromium.launch(headless = False)
        page = browser.new_page()
        
        page.goto("https://kki.autonorte.com.br")
        
        
        usuario = page.get_by_role("textbox", name="E-mail")
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
        
        page.wait_for_timeout(random.randint(1000, 2000))
        
        for filial in lista_filiais:
            
            if filial:
                selecionar_filial_autonorte(page,filial)
        
            for codigo in codigos:
                
                try:
                    
                    busca = page.get_by_role("textbox", name="Referência", exact=True)
                    busca.click()
                    page.wait_for_timeout(random.randint(1000, 2000))
                    busca.fill(codigo)
                    
                    page.wait_for_timeout(random.randint(1000, 2000))
                    clique_buscar = page.get_by_role("button", name="Pesquisar")
                    clique_buscar.click()
                    
                    page.wait_for_timeout(2000)

                    try:
                        page.locator("table.chakra-table tbody tr").first.wait_for(state="attached", timeout=5000)
                        
                    except PlaywrightTimeoutError:
                        pass
                    
                    nao_encontrado = page.locator("table.chakra-table td p.chakra-text", has_text="Nenhum produto encontrado")
                    
                    try:
                        nao_encontrado.wait_for(state='visible', timeout=3000)
                        logging.info(f"Auto Norte: {codigo} NÃO ENCONTRADO")
                        
                        resultados.append({
                                        "fornecedor": "Auto Norte",
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
                    
                    produtos = page.locator("table.chakra-table tbody tr")
                    total_produtos = produtos.count()
                    
                    for i in range (total_produtos):
                        card = produtos.nth(i)
                        
                        tds = card.locator("td")
                        total_tds = tds.count()

                        for i in range(total_tds):
                            texto = tds.nth(i).inner_text()
                    
                        td_cod = card.locator("td").nth(1)
    
                        try:
                            cod_fabricante_raw = td_cod.locator("span.chakra-text").first.inner_text(timeout=2000).strip()
                            cod_fabricante = cod_fabricante_raw.split("\n")[0].strip()
                        except:
                            cod_fabricante = None
                            
                        try:
                            fabricante = td_cod.locator("strong").first.inner_text(timeout=2000).strip()
                        except:
                            fabricante = None
                            
                        td_desc = card.locator("td").nth(2)
                        
                        try:
                            descricao = td_desc.locator('p.chakra-text').first.inner_text(timeout=2000).strip()
                        except:
                            descricao = None
                            
                        td_preco = card.locator("td").nth(14)
                        
                        try:
                            preco = td_preco.locator("span").first.inner_text(timeout=2000).strip()
                            preco = " ".join(preco.split())
                        except:
                            preco = None
                            
                        td_est = card.locator("td").nth(6)
                        
                        try:
                            estoque = td_est.locator("p.chakra-text").first.inner_text(timeout=2000).strip()
                            
                        except:
                            estoque = None 
                        
                        if estoque == '0':
                            status = "Sem Estoque"
                        else:
                            status = "OK"  
                            
                        resultados.append({
                            "fornecedor": "Auto Norte",
                            "cod_buscado": codigo,
                            "cod_fabricante":cod_fabricante,
                            "descricao": descricao,
                            "preco":preco,
                            "fabricante": fabricante,
                            "status": status,
                            "prazo": None,
                            "filial": filial
                            
                            })
                finally:
                    page.wait_for_timeout(random.randint(1000, 2000))
                    
            page.wait_for_timeout(random.randint(1000, 2000))
            voltar_clientes = page.locator("aside a[href='/ficha-clientes']")
            voltar_clientes.click()
            page.wait_for_timeout(random.randint(1000, 2000))
            
    resultado_busca = pd.DataFrame(resultados)
    
    return resultado_busca



if __name__ == "__main__":
    codigos = ["ECO1651","VC232"]  
    filiais = ["Maranhão","Pernambuco"]
    
    resultado = executar(codigos, filiais)
    print(resultado)