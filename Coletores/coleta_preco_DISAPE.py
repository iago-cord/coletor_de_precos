from playwright.sync_api import sync_playwright
import pandas as pd
import random
from dotenv import load_dotenv
import os
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from functions import selecionar_filial,clique_buscar
import logging

# Função responsável por executar a busca dos códigos de produtos.
# Recebe como parâmetros a lista de códigos e a lista de filiais selecionadas.
def executar(codigos, filiais):
    
    # Carrega as variáveis de ambiente armazenadas no arquivo .env.
    # As credenciais serão utilizadas para realizar o login na plataforma.
    load_dotenv()
    usuario_login = os.getenv("DISAPE_USUARIO")
    senha_login = os.getenv("DISAPE_SENHA")

    # Cria uma lista vazia onde serão armazenados os resultados
    # encontrados durante a coleta.
    resultados = []
    
    # Define a lista de filiais que será utilizada durante a coleta.
    # Caso nenhuma filial seja informada, utiliza [None] para realizar
    # a busca utilizando a filial padrão da plataforma.
    lista_filiais = filiais if filiais else [None]

    # Inicializa o Playwright e mantém seu contexto ativo durante
    # toda a execução da coleta.
    with sync_playwright() as p:
        
        # Inicializa o navegador Chromium em modo visível e cria uma nova página.
        browser = p.chromium.launch(headless = False)
        page = browser.new_page()

        # Acessa a página de login da plataforma DISAPE.
        page.goto("https://loja.disape.com.br/customer/account/login")

        # Localiza o campo de usuário, clica no campo e preenche
        # com o usuário armazenado nas variáveis de ambiente.
        usuario = page.get_by_role("textbox", name="Usuário *")
        usuario.click()
        page.wait_for_timeout(random.randint(1000, 2000))
        usuario.fill(usuario_login)
        
        # Localiza o campo de senha, clica no campo e preenche
        # com a senha armazenada nas variáveis de ambiente.
        senha = page.get_by_role("textbox", name="Senha")
        senha.click()
        page.wait_for_timeout(random.randint(1000, 2000))
        senha.fill(senha_login)
        
        # Aguarda um intervalo aleatório antes de realizar o login.
        page.wait_for_timeout(random.randint(1000, 2000))
        
        # Localiza o botão "Entrar" e realiza o login na plataforma.
        entrar = page.get_by_role("button", name="Entrar")
        entrar.click()
        
        # Aguarda o campo de pesquisa de código ficar visível,
        # indicando que a página principal foi carregada após o login.
        page.get_by_role("textbox", name="Código da peça").wait_for(state="visible")
        
        # Percorre todas as filiais selecionadas para realizar
        # a coleta dos códigos em cada uma delas.
        for filial in lista_filiais:
            
            # Caso uma filial tenha sido informada, executa a função
            # responsável por selecionar a filial na plataforma.
            if filial:
                selecionar_filial(page, filial)
                
                # Registra no log o início do processamento dos códigos
                # para a filial atual e informa a quantidade de códigos.
                logging.info(f"Disape: entrando no loop de códigos. Total: {len(codigos)}")
                
                # Abre o seletor de prazo da plataforma.
                page.locator("div.c-prazo span.selected.popup-modal").click()
                
                # Aguarda a lista de opções de prazo ficar disponível.
                page.wait_for_selector("form#form-prazo ul.scroll.items")
                
                 # Localiza a opção de prazo "60 Dias".
                item = page.locator("form#form-prazo ul.scroll.items li.item").filter(has_text="60 Dias")
                
                # Seleciona a opção de prazo através do botão de rádio.
                item.locator("input[type='radio']").click()
                
                # Confirma a seleção do prazo clicando no botão "Aplicar".
                page.locator("form#form-prazo button.button", has_text="Aplicar").click()

            # Percorre todos os códigos informados para realizar
            # a pesquisa na filial atualmente selecionada.
            for codigo in codigos:
                                
                try:
                    # Localiza o campo de pesquisa pelo nome "Código da peça",
                    # clica no campo e preenche com o código atual.
                    busca = page.get_by_role("textbox", name="Código da peça")
                    busca.click()
                    busca.fill(codigo)
                    
                    # Executa a função responsável por clicar no botão de pesquisa da plataforma.
                    # A pagina as vezes demora a carregar, entao foi necessario implementar um retry no click
                    clique_buscar(page)
                    
                    # Localiza a mensagem apresentada quando nenhum produto é encontrado para o código pesquisado.
                    nao_encontrado = page.locator("div.message.notice")
            
                    try:
                        # Aguarda até que a mensagem de produto não encontrado esteja visível na página.
                        nao_encontrado.wait_for(state="visible", timeout=3000)
                        
                        # Registra no log que o código não foi encontrado.
                        logging.info(f"Disape: {codigo} NÃO ENCONTRADO")
                        
                        # Adiciona o código à lista de resultados com status
                        # "NÃO ENCONTRADO" e os demais campos sem informação.
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
                        
                        # Interrompe o processamento do código atual e passa para o próximo código da lista.
                        continue
            
                    except:
                        
                        # Caso a mensagem de produto não encontrado não esteja
                        # visível, continua o processamento dos produtos encontrados.
                        pass
                        
                        # Localiza todos os produtos retornados pela pesquisa.
                        produtos = page.locator("ol.products.list.items.product-items > li.item.product.product-item")
                        
                        # Aguarda o primeiro produto ser inserido no DOM.
                        produtos.first.wait_for(state="attached", timeout=3000)
                        
                        # Conta quantos produtos foram retornados pela pesquisa.
                        count = produtos.count()

                        # Caso nenhum produto seja encontrado, registra o resultado
                        # como "NAO ENCONTRADO" e passa para o próximo código.
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
                            
                        # Percorre todos os produtos retornados pela pesquisa.
                        for i in range(count):
                            
                            # Obtém o produto correspondente à posição atual.
                            card = produtos.nth(i)

                            # Tenta extrair a descrição do produto.
                            try:
                                descricao = card.locator("strong.product-item-name a.product-item-link").first.text_content(timeout=1000)
                            except:
                                descricao = None
                                
                            # Tenta extrair o preço do produto.
                            try:
                                preco = card.locator("div.product-info.__row.__last div.product-item-inner div.price-box:not(.total-full) span.price").first.inner_text(timeout=1000) 
                            except:
                                preco = None
                                
                            # Tenta extrair o código do fabricante.
                            try:
                                cod_fabricante = card.locator("div.product-info.__row.__last div.cod-fabricante span").first.text_content(timeout=1000)   
                            except:
                                cod_fabricante = None

                            # Tenta extrair o fabricante do produto.
                            try:
                                fabricante = card.locator("div.product-info.__row.__last div.fabricante span").first.text_content(timeout=1000)
                            except:
                                fabricante = None

                            # Tenta obter o prazo atualmente selecionado na plataforma.
                            try:
                                prazo  = page.locator("div.c-prazo > span.selected").text_content(timeout=1000)
                            except:
                                prazo = None
                            
                            # Armazena os dados principais do produto em variáveis específicas antes de adicioná-los aos resultados.
                            # Necessario para evitar overwrite dos dados
                            descricao_principal = descricao
                            preco_principal = preco
                            cod_fabricante_principal = cod_fabricante
                            fabricante_principal = fabricante 
                                
                            # Adiciona o produto principal à lista de resultados.
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
                            
                            # Localiza o link de produtos similares dentro do produto atual.
                            similares = card.get_by_role("link", name="Produtos Similares")
                            
                            # Verifica se o produto possui a opção de consultar produtos similares.
                            tem_similar = similares.count()
                            
                            # Caso não exista a opção de similares, passa para o próximo produto.
                            if not tem_similar:
                                continue
                            
                            try:
                                
                                # Aguarda um intervalo aleatório antes de abrir a janela de produtos similares
                                page.wait_for_timeout(random.randint(1000, 2000))
                                
                                # Abre a janela de produtos similares.
                                similares.click()
                                
                                # Localiza o popup apresentado quando ocorre um erro ao consultar produtos similares.
                                popup_erro = page.locator("aside.modal-popup.similar-product-error._show")
                                
                                try:
                                    # Aguarda o popup de erro (produto sem similares) ser inserido no DOM.
                                    popup_erro.wait_for(state="attached", timeout=1000)
                                    
                                    # Aguarda brevemente o popup terminar de carregar.
                                    page.wait_for_timeout(500)
                                    
                                    # Fecha o popup de erro.
                                    popup_erro.locator("button.action-close[data-role='closeBtn']").click(force=True)
                                    
                                    # Aguarda o fechamento do popup.
                                    page.wait_for_timeout(500)
                                    
                                    # Interrompe o processamento dos similares e passa para o próximo produto.
                                    continue
                                
                                except PlaywrightTimeoutError:
                                    
                                    # Caso o popup de erro não apareça dentro do tempo limite, continua normalmente
                                    # para processar os produtos similares.
                                    pass
                                
                                # # Aguarda a lista de produtos similares ficar visível.
                                page.wait_for_selector("div.products.list.items.popup-similares:visible")
                                
                                # Aguarda um pequeno intervalo para garantir que os dados dos similares tenham sido carregados.
                                page.wait_for_timeout(1000)
                                
                                # Localiza todos os produtos similares exibidos dentro da janela aberta.
                                card_similares = page.locator("div.related-product div.product-item")

                                # Percorre todos os produtos similares encontrados.
                                for i in range(card_similares.count()):
                                    
                                    # Obtém o produto similar correspondente à posição atual.
                                    card_sim = card_similares.nth(i)

                                    # Tenta extrair a descrição do produto similar.
                                    try:
                                        descricao_similar = card_sim.locator("div.product-block-name a.product-item-link").first.inner_text(timeout=1000)
                                    except:
                                        descricao_similar = None
                                    
                                    # Tenta extrair o fabricante do produto similar.
                                    try:
                                        fabricante_similar = card_sim.locator("div.product-block-fabricante div.fabricante span[data-bind]").first.inner_text(timeout=1000)
                                    except:
                                        fabricante_similar = None
                                    # Tenta extrair o código do fabricante do produto similar.
                                    try:
                                        cod_fabricante_similar = card_sim.locator("div.product-block-fabricante div.cod-fabricante span[data-bind]").first.inner_text(timeout=1000)
                                    except:
                                        cod_fabricante_similar = None

                                    # Tenta extrair o preço do produto similar.
                                    try:
                                        preco_similar = card_sim.locator("div.product-item-actions span.price-container span.price").first.inner_text(timeout=1000)
                                    except:
                                        preco_similar = None                                                                                                                                                                                                                     

                                    # Adiciona o produto similar à lista de resultados.
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
                                
                                # Localiza o botão de fechamento da janela de produtos similares e fecha o popup.
                                fechar_popup = page.locator("div.modal-inner-wrap button.action-close:visible")
                                fechar_popup.click()

                                # Aguarda o overlay utilizado pelo popup ficar oculto após o fechamento.
                                page.locator(".modals-overlay").wait_for(state="hidden")
                                
                                # Aguarda um pequeno intervalo antes de continuar.
                                page.wait_for_timeout(1000)
                            
                            except Exception as e:
                                
                                # Registra no terminal o erro ocorrido durante o processamento dos produtos similares.
                                print(f"Erro ao processar similares do produto'{codigo}' : {e}")
                                
                                # Continua a execução para o próximo produto.
                                continue
                             
                except Exception as e:

                        # Registra o código com status de erro e armazena a mensagem da exceção na descrição.
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
                    
                        # Aguarda um intervalo aleatório após o processamento do código antes de iniciar a próxima pesquisa.
                        page.wait_for_timeout(random.randint(1000,2000))
                
        # Converte a lista de dicionários coletados em um DataFrame do Pandas.       
        resultado_busca = pd.DataFrame(resultados)
        
        # Define as colunas que receberão o tratamento de texto.
        colunas = [
            "fornecedor",
            "cod_buscado",
            "cod_fabricante",
            "descricao",
            "preco",
            "fabricante",
            "status"
        ]
        
        # Remove espaços desnecessários no início e no final dos valores das colunas selecionadas.
        resultado_busca[colunas] = resultado_busca[colunas].apply(lambda c: c.str.strip())

    # Retorna o DataFrame contendo todos os resultados da coleta.
    return resultado_busca

# Permite executar o módulo diretamente para realizar um teste da função.
if __name__ == "__main__":

    # Define os códigos que serão utilizados durante o teste.
    codigos = ["ECO1651","VC-232"]

    # Define as filiais que serão utilizadas durante o teste.
    filiais = []
        
    # Executa a coleta utilizando os códigos e filiais definidos acima.
    resultado = executar(codigos, filiais)
        
    # Exibe no terminal o DataFrame com os resultados da coleta.
    print(resultado)




