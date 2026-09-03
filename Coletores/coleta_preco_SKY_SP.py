from playwright.sync_api import sync_playwright
import pandas as pd
import re
import random
from dotenv import load_dotenv
import os
from functions import selecionar_filial_sky

def executar(codigos,filiais):

    load_dotenv()
    cnpj_login = os.getenv("SKY_SP_CNPJ")
    usuario_login = os.getenv("SKY_SP_USUARIO")
    senha_login = os.getenv("SKY_SP_SENHA")

    resultados = []
    lista_filiais = filiais if filiais else [None]

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("https://cliente.skypecas.com.br/usuario/login")

        cnpj = page.get_by_role("textbox", name="CNPJ ou CPF")
        cnpj.click()
        page.wait_for_timeout(random.randint(1000, 2000))
        cnpj.fill(cnpj_login)

        usuario = page.get_by_role("textbox", name="Usuário")
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
                
        page.get_by_role("button", name="Entrar").click()

        page.get_by_role("textbox", name="Código da Peça").wait_for(state="visible")
        
        for filial in lista_filiais:
            
            if filial:
                selecionar_filial_sky(page, filial)
                
                try:
                    erro_busca =  page.get_by_role("dialog", name="Aviso!")
                    erro_busca.wait_for(state='visible', timeout=1000)
                    erro_busca.get_by_role("button", name="OK").click()
                                            
                except:
                    pass
                
                page.wait_for_timeout(2000)

            for codigo in codigos:
                try:
                    busca = page.get_by_role("textbox", name="Código da Peça")
                    busca.click()
                    page.wait_for_timeout(random.randint(1000, 2000))         
                    busca.fill(codigo)

                    buscar = page.get_by_role("button", name=" Buscar")
                    page.wait_for_timeout(random.randint(1000, 2000))
                    buscar.click()

                    popup_ok = page.get_by_role("button", name="OK")

                    try:
                        popup_ok.wait_for(state="visible", timeout=1000)
                        popup_ok.click()

                        resultados.append({
                            "fornecedor": "SKY Auto Peças",
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

                    cards = page.locator("div.bx_produto")
                    qtd_produtos = cards.count()
                    
                    for i in range(qtd_produtos):
                        card = cards.nth(i)
                        
                        try:
                            preco_principal = card.locator("span.preco_final").first.inner_text(timeout=1000)
                        except:
                            preco_principal = None
                            
                        try:
                            cod_fabricante_principal = card.locator("div.fleft.codfab strong").first.inner_text(timeout=1000)
                        except:
                            cod_fabricante_principal = None
                        
                        try:
                            descricao_principal = card.locator("div.nome").first.inner_text(timeout=1000)
                        except:
                            descricao_principal = None
                            
                        try: 
                            fabricante_principal = card.locator("div.fornecedor").first.inner_text(timeout=1000)
                        except:
                            fabricante_principal = None

                        resultados.append({
                            "fornecedor": "SKY Auto Peças",
                            "cod_buscado": codigo,
                            "cod_fabricante": cod_fabricante_principal,
                            "descricao": descricao_principal,
                            "preco": preco_principal,
                            "fabricante": fabricante_principal,
                            "status": "OK",
                            "prazo": None,
                            "filial": filial
                        })
                        
                        tem_similar = card.get_by_role("link", name="Similar").count() > 0
                        
                        if not tem_similar:
                            continue
                        try:
                            card.get_by_role("link",name="Similar").click(no_wait_after=True)
                            page.wait_for_selector("div.ajax.modal:visible")
                            page.wait_for_timeout(2000)
                            
                            cards_similares = page.locator("div#tb_produto div.bx_produto")
                            qtd_similares = cards_similares.count()
                            
                            for j in range(qtd_similares):
                                card_similares = cards_similares.nth(j)
                                
                                try:
                                    preco_similar = card_similares.locator("span.preco_final").inner_text(timeout=1000)
                                except:
                                    preco_similar = None
                                
                                try:
                                    cod_fabricante_similar = card_similares.locator("div.fleft.codfab strong").inner_text(timeout=1000)
                                except:
                                    cod_fabricante_similar = None
                                    
                                try:
                                    descricao_similar = card_similares.locator("div.nome").inner_text(timeout=1000)
                                except:
                                    descricao_similar = None
                                    
                                try:
                                    fabricante_similar = card_similares.locator("div.fornecedor").inner_text(timeout=1000)
                                except:
                                    fabricante_similar = None
                                    
                                resultados.append({
                                    "fornecedor": "SKY Auto Peças",
                                    "cod_buscado": codigo,
                                    "cod_fabricante": cod_fabricante_similar,
                                    "descricao": descricao_similar,
                                    "preco": preco_similar,
                                    "fabricante": fabricante_similar,
                                    "status": "Similar",
                                    "prazo": None,
                                    "filial": filial
                                })
                                
                            fechar_popup = page.locator("a.close-modal")
                            if fechar_popup.count() > 0:
                                fechar_popup.click(no_wait_after=True)
                            page.locator("div.ajax.modal").wait_for(state="hidden", timeout=2000)
                        
                        except Exception as e:
                            print(f"Erro ao processar similares do produto '{codigo}': {e}")
                            continue
                            
                except Exception as e:
                    print(f"Erro ao buscar '{codigo}': {e}")
                    resultados.append({
                        "fornecedor": "SKY Auto Peças",
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
                    page.wait_for_timeout(random.randint(1000, 2000))

    resultado_busca = pd.DataFrame(resultados)

    return resultado_busca

if __name__ == "__main__":

    cod_busca = ["ECO1651","VC-232"]

    executar(cod_busca)
