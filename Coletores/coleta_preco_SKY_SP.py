from playwright.sync_api import sync_playwright
import pandas as pd
import logging
import random
from dotenv import load_dotenv
import os
from functions import selecionar_filial_sky

# Função principal responsável por realizar as buscas dos códigos no site da SKY
# e retornar os produtos encontrados, incluindo produtos similares.
def executar(codigos,filiais):

    # Carrega as credenciais armazenadas nas variáveis de ambiente.
    load_dotenv()
    cnpj_login = os.getenv("SKY_SP_CNPJ")
    usuario_login = os.getenv("SKY_SP_USUARIO")
    senha_login = os.getenv("SKY_SP_SENHA")

    # Lista onde serão armazenados todos os resultados coletados.
    resultados = []
    
    # Caso nenhuma filial seja informada, realiza a coleta sem seleção de filial.
    lista_filiais = filiais if filiais else [None]

    with sync_playwright() as p:

        # Inicializa o navegador em modo visível e cria uma nova página.
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Acessa a página de login da SKY.
        page.goto("https://cliente.skypecas.com.br/usuario/login")

        # Preenche o CNPJ/CPF utilizado no acesso.
        cnpj = page.get_by_role("textbox", name="CNPJ ou CPF")
        cnpj.click()
        page.wait_for_timeout(random.randint(1000, 2000))
        cnpj.fill(cnpj_login)
        
        # Preenche o usuário.
        usuario = page.get_by_role("textbox", name="Usuário")
        usuario.click()
        page.wait_for_timeout(random.randint(1000, 2000))
        usuario.fill(usuario_login)

        # Preenche a senha.
        senha = page.get_by_role("textbox", name="Senha")
        senha.click()
        page.wait_for_timeout(random.randint(1000, 2000))
        senha.fill(senha_login)
        page.wait_for_timeout(random.randint(1000, 2000))

        # Realiza o primeiro clique no botão de login.
        entrar = page.get_by_role("button", name="Entrar")
        entrar.click()
        page.wait_for_timeout(random.randint(1000, 2000))
        
        # Realiza o segundo clique caso o site apresente uma segunda etapa do processo de autenticação       
        page.get_by_role("button", name="Entrar").click()

        # Aguarda o campo de busca ficar disponível, confirmando o acesso.
        page.get_by_role("textbox", name="Código da Peça").wait_for(state="visible")
        
        # Percorre todas as filiais selecionadas.
        for filial in lista_filiais:
            
            # Quando uma filial foi informada, realiza sua seleção no site.
            if filial:
                selecionar_filial_sky(page, filial)
                
                # Após a troca de filial, verifica se o site apresentou algum aviso que precise ser confirmado.
                try:
                    erro_busca =  page.get_by_role("dialog", name="Aviso!")
                    erro_busca.wait_for(state='visible', timeout=1000)
                    erro_busca.get_by_role("button", name="OK").click()
                                            
                except:
                    # Caso nenhum aviso seja exibido, continua normalmente
                    pass
                
                page.wait_for_timeout(2000)

            # Percorre todos os códigos para a filial atual.
            for codigo in codigos:
                try:
                    # Localiza o campo de busca e preenche o código.
                    busca = page.get_by_role("textbox", name="Código da Peça")
                    busca.click()
                    page.wait_for_timeout(random.randint(1000, 2000))         
                    busca.fill(codigo)

                    # Localiza e aciona o botão de busca.
                    buscar = page.get_by_role("button", name=" Buscar")
                    page.wait_for_timeout(random.randint(1000, 2000))
                    buscar.click()

                    # Verifica se o site retornou um aviso indicando que o código não foi encontrado.
                    popup_ok = page.get_by_role("button", name="OK")

                    try:
                        popup_ok.wait_for(state="visible", timeout=1000)
                        popup_ok.click()

                        # Registra o código sem resultado.
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
                        # Se o aviso não aparecer, continua com a coleta.
                        pass
                    
                    # Localiza os cards dos produtos retornados pela busca.
                    cards = page.locator("div.bx_produto")
                    qtd_produtos = cards.count()
                    
                    # Percorre todos os produtos encontrados.
                    for i in range(qtd_produtos):
                        card = cards.nth(i)
                        
                        # Coleta o preço do produto principal.
                        try:
                            preco_principal = card.locator("span.preco_final").first.inner_text(timeout=1000)
                        except:
                            preco_principal = None
                        
                        # Coleta o código do fabricante.  
                        try:
                            cod_fabricante_principal = card.locator("div.fleft.codfab strong").first.inner_text(timeout=1000)
                        except:
                            cod_fabricante_principal = None
                        
                        # Coleta a descrição do produto.
                        try:
                            descricao_principal = card.locator("div.nome").first.inner_text(timeout=1000)
                        except:
                            descricao_principal = None
                        
                        # Coleta o fabricante.   
                        try: 
                            fabricante_principal = card.locator("div.fornecedor").first.inner_text(timeout=1000)
                        except:
                            fabricante_principal = None

                        # Registra o produto principal nos resultados.
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
                        
                        # Verifica se o produto possui produtos similares.
                        tem_similar = card.get_by_role("link", name="Similar").count() > 0
                        
                        # Caso não existam similares, passa para o próximo produto.
                        if not tem_similar:
                            continue
                        try:
                            # Abre a janela de produtos similares.
                            card.get_by_role("link",name="Similar").click(no_wait_after=True)
                            
                            # Aguarda a janela de similares ficar disponível.
                            page.wait_for_selector("div.ajax.modal:visible")
                            page.wait_for_timeout(2000)
                            
                            # Localiza os cards dos produtos similares.
                            cards_similares = page.locator("div#tb_produto div.bx_produto")
                            qtd_similares = cards_similares.count()
                            
                            # Percorre todos os produtos similares encontrados.
                            for j in range(qtd_similares):
                                card_similares = cards_similares.nth(j)
                                
                                # Coleta o preço do similar.
                                try:
                                    preco_similar = card_similares.locator("span.preco_final").inner_text(timeout=1000)
                                except:
                                    preco_similar = None
                                
                                # Coleta o código do fabricante do similar.
                                try:
                                    cod_fabricante_similar = card_similares.locator("div.fleft.codfab strong").inner_text(timeout=1000)
                                except:
                                    cod_fabricante_similar = None
                                
                                # Coleta a descrição do similar.   
                                try:
                                    descricao_similar = card_similares.locator("div.nome").inner_text(timeout=1000)
                                except:
                                    descricao_similar = None
                                
                                # Coleta o fabricante do similar. 
                                try:
                                    fabricante_similar = card_similares.locator("div.fornecedor").inner_text(timeout=1000)
                                except:
                                    fabricante_similar = None
                                
                                # Registra o produto similar nos resultados.   
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
                            
                            # Localiza o botão de fechamento da janela de similares.   
                            fechar_popup = page.locator("a.close-modal")
                            
                            # Fecha a janela caso o botão esteja disponível.
                            if fechar_popup.count() > 0:
                                fechar_popup.click(no_wait_after=True)
                                
                            # Aguarda o modal desaparecer antes de continuar.
                            page.locator("div.ajax.modal").wait_for(state="hidden", timeout=2000)
                        
                        except Exception as e:
                            # Registra erros ocorridos durante a coleta dos produtos similares.
                            logging.info(f"Erro ao processar similares do produto '{codigo}': {e}")
                            continue
                        
                # Trata erros gerais ocorridos durante a busca do código.           
                except Exception as e:
                    logging.info(f"Erro ao buscar '{codigo}': {e}")
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
                    # Aguarda um intervalo aleatório antes de iniciar a próxima busca.
                    page.wait_for_timeout(random.randint(1000, 2000))

    # Converte os resultados coletados em DataFrame.
    resultado_busca = pd.DataFrame(resultados)

    # Retorna o DataFrame contendo todos os resultados da coleta.
    return resultado_busca

# Permite executar este módulo individualmente para testes.
if __name__ == "__main__":

    # Códigos utilizados no teste.
    codigos = ["ECO1651","VC-232"]
    
    # Filiais utilizadas no teste.
    filiais = ['SKY AUTOMOTIVE (GUARULHOS)', 'SKY AUTOMOTIVE (BOM RETIRO)', 'Embrepar (GO - Perimetral)']
        
    # Executa o coletor individualmente.
    resultado = executar(codigos, filiais)
    
    # Exibe o resultado da coleta.
    print(resultado)
