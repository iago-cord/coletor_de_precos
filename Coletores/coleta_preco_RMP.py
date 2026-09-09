from playwright.sync_api import sync_playwright
import pandas as pd
import random
from dotenv import load_dotenv
import os
from functions import clique_buscar
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from functions import selecionar_filial, retry_acao
import logging

# Função principal responsável por realizar as buscas dos códigos no site da RMP
# e retornar os resultados coletados em um DataFrame.
def executar(codigos, filiais):
    
    # Carrega as variáveis de ambiente contendo usuário e senha.
    load_dotenv()
    usuario_login = os.getenv("RMP_USUARIO")
    senha_login = os.getenv("RMP_SENHA")
    
    # Lista onde serão armazenados todos os resultados coletados.
    resultados = []
    
    # Caso nenhuma filial seja informada, realiza a coleta sem seleção de filial.
    lista_filiais = filiais if filiais else [None]

    with sync_playwright() as p:

        # Inicializa o navegador Chromium em modo visível.
        browser = p.chromium.launch(headless = False)
        
        # Cria uma nova página para acesso ao site.
        page = browser.new_page()
        
         # URL da página de login da RMP
        url = "https://loja.rmp.com.br/customer/account/login"
        
        # Acessa o site utilizando a função de retry para tratar possíveis falhas.
        retry_acao(lambda: page.goto(url))

        # Localiza o campo de usuário e realiza o preenchimento.
        usuario = page.get_by_role("textbox", name="Usuário *")
        retry_acao(lambda:usuario.click())
        page.wait_for_timeout(random.randint(1000, 2000))
        retry_acao(lambda:usuario.fill(usuario_login))
        
        # Localiza o campo de senha e realiza o preenchimento.
        senha = page.get_by_role("textbox", name="Senha")
        retry_acao(lambda:senha.click())
        page.wait_for_timeout(random.randint(1000, 2000))
        retry_acao(lambda:senha.fill(senha_login))
        
        page.wait_for_timeout(random.randint(1000, 2000))
        
        # Localiza e aciona o botão de login.
        entrar = page.get_by_role("button", name="Entrar")
        retry_acao(lambda:entrar.click())
        
        # Aguarda o carregamento do campo de busca para confirmar que o login foi concluído.
        retry_acao(lambda: page.get_by_role("textbox", name="Código da peça").wait_for(state="visible"))
        
        # Percorre todas as filiais selecionadas para realizar a coleta.
        for filial in lista_filiais:
            
            if filial:
                
                # Quando uma filial foi informada, realiza sua seleção no site.
                selecionar_filial(page,filial)
                logging.info(f"RMP: entrando no loop de códigos. Total: {len(codigos)}")
                
                # Abre o seletor de prazo.
                retry_acao(lambda:page.locator("div.c-prazo span.selected.popup-modal").click())
                
                # Aguarda o carregamento das opções de prazo.
                retry_acao(lambda:page.wait_for_selector("form#form-prazo ul.scroll.items"))
                
                # Localiza a opção de pagamento em 60 dias.
                item = page.locator("form#form-prazo ul.scroll.items li.item").filter(has_text="60 Dias")
                retry_acao(lambda:item.locator("input[type='radio']").click())
                
                # Aplica a alteração do prazo.
                retry_acao(lambda:page.locator("form#form-prazo button.button", has_text="Aplicar").click() )
                
                # Contador de códigos processados para a filial atual.
                processados = 0
                
            # Percorre todos os códigos informados.
            for codigo in codigos:
                
                processados += 1
                
                try:
                    # Localiza o campo de busca do código da peça.
                    busca = page.get_by_role("textbox", name="Código da peça")
                    
                    # Clica no campo e preenche o código.
                    retry_acao(lambda:busca.click())
                    retry_acao(lambda:busca.fill(codigo))
                    
                    # Executa a busca através da função auxiliar.
                    clique_buscar(page)
                    
                    # Localiza a mensagem exibida quando nenhum produto é encontrado.
                    nao_encontrado = page.locator("div.message.notice")
            
                    try:
                        # Aguarda a mensagem de produto não encontrado.
                        nao_encontrado.wait_for(state="visible", timeout=3000)
                        logging.info(f"RMP: {codigo} NÃO ENCONTRADO")

                        # Registra o código sem resultado.
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
                        # Se a mensagem não apareceu, continua normalmente
                        # para a etapa de coleta dos produtos.
                        pass
                        
                        # Localiza os cards dos produtos retornados pela busca.
                        produtos = page.locator("ol.products.list.items.product-items > li.item.product.product-item")

                         # Aguarda o primeiro produto ser inserido no DOM.
                        produtos.first.wait_for(state="attached", timeout=3000)
                        page.wait_for_load_state("domcontentloaded",timeout=5000)
            
                        count = produtos.count()
                        
                        # Trata o caso em que a busca não retornou nenhum produto.
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
                        
                        # Percorre todos os produtos encontrados para o código.
                        for i in range(count):
                            card = produtos.nth(i)
                            
                            # Define o status inicial da coleta.
                            status = "OK"
                            
                            # Lista utilizada para registrar campos que apresentaram erro.
                            erros_coleta = []

                            # Coleta a descrição do produto.
                            try:
                                descricao = card.locator("strong.product-item-name a.product-item-link").first.text_content(timeout=1000)  
                            except PlaywrightTimeoutError:
                                descricao = None
                                erros_coleta.append('DESCRICAO')

                            # Coleta o preço do produto.
                            try:
                                preco = card.locator("div.product-item-inner div.price-box:not(.total-full) span.price").first.inner_text(timeout=1000)
                            except PlaywrightTimeoutError:
                                preco = None
                                erros_coleta.append('PRECO')

                            # Coleta o código do fabricante.
                            try:
                                cod_fabricante = card.locator("div.product-info.__row.__last div.cod-fabricante span").first.text_content(timeout=1000)
                            except PlaywrightTimeoutError:
                                cod_fabricante = None
                                erros_coleta.append('COD_FABRICANTE')

                            # Coleta o fabricante.
                            try:
                                fabricante = card.locator("div.product-block-fabricante div.fabricante span").first.inner_text(timeout=1000)
                            except PlaywrightTimeoutError:
                                fabricante = None
                                erros_coleta.append('FABRICANTE')

                            # Coleta o prazo atualmente selecionado.
                            try:
                                prazo  = page.locator("div.c-prazo > span.selected").text_content(timeout=1000)
                            except PlaywrightTimeoutError:
                                prazo = None
                                erros_coleta.append('PRAZO')
                                
                            # Coleta a filial atualmente selecionada.
                            try:
                                filial = page.locator("div.c-dist > span.selected").text_content(timeout=1000)
                            except PlaywrightTimeoutError:
                                filial = None
                                erros_coleta.append('FILIAL')
                            
                            # Mantém os dados principais coletados para o produto.
                            # Para evitar overwrite dos dados
                            descricao_principal = descricao
                            preco_principal = preco
                            cod_fabricante_principal = cod_fabricante
                            fabricante_principal = fabricante 
                            
                            # Caso algum campo tenha apresentado erro, altera o status informando quais campos falharam.
                            if erros_coleta:
                                status = "ERRO NA COLETA: " + ", ".join(erros_coleta)
                            
                            # Armazena o produto principal nos resultados.
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
                            
                            # Verifica se o produto possui produtos similares.
                            similares = card.get_by_role("link", name="Produtos Similares")
                            tem_similar = similares.count()
                            
                            # Se não houver similares, passa para o próximo produto.
                            if not tem_similar:
                                continue
                            
                            try:
                                # Pequena espera antes de abrir a janela de similares.
                                page.wait_for_timeout(random.randint(1000, 2000))
                                
                                # Abre a janela de produtos similares.
                                similares.click()
                                
                                # Localiza a mensagem de erro que pode aparecer quando os similares não estão disponíveis.
                                popup_erro = page.locator("aside.modal-popup.similar-product-error._show")
                                
                                try:
                                    # Verifica se o popup de erro foi criado.
                                    popup_erro.wait_for(state="attached", timeout=1000)
                                    page.wait_for_timeout(500)
                                    
                                    # Fecha o popup de erro.
                                    popup_erro.locator("button.action-close[data-role='closeBtn']").click(force=True)
                                    page.wait_for_timeout(500)
                                    continue
                                
                                except PlaywrightTimeoutError:
                                    # Caso o popup de erro não apareça, continua com a coleta dos similares.
                                    pass
                                
                                # Aguarda a janela de produtos similares ficar visível.
                                retry_acao(lambda:page.wait_for_selector("div.products.list.items.popup-similares:visible"))
                                page.wait_for_timeout(1000)

                                # Localiza os cards dos produtos similares.
                                card_similares = page.locator("div.related-product div.product-item")

                                # Percorre todos os produtos similares encontrados.
                                for i in range(card_similares.count()):
                                    card_sim = card_similares.nth(i)
                                    
                                    # Define o status inicial dos similares.
                                    status = 'Similar'
                                    
                                    # Lista de possíveis erros de coleta.
                                    erros_coleta = []

                                    # Coleta a descrição do similar.
                                    try:
                                        descricao_similar = card_sim.locator("div.product-block-name a.product-item-link").inner_text(timeout=1000)
                                    except PlaywrightTimeoutError:
                                        descricao_similar = None
                                        erros_coleta.append('DESCRICAO')

                                    # Coleta o fabricante do similar.
                                    try:
                                        fabricante_similar = card_sim.locator("div.product-block-fabricante div.fabricante span[data-bind]").inner_text(timeout=1000)
                                    except PlaywrightTimeoutError:
                                        fabricante_similar = None
                                        erros_coleta.append('FABRICANTE')

                                    # Coleta o código do fabricante do similar.
                                    try:
                                        cod_fabricante_similar = card_sim.locator("div.product-block-fabricante div.cod-fabricante span[data-bind]").inner_text(timeout=1000)
                                    except PlaywrightTimeoutError:
                                        cod_fabricante_similar = None
                                        erros_coleta.append('COD_FABRICANTE')

                                    # Coleta o preço do produto similar.
                                    try:
                                        preco_similar = card_sim.locator("div.product-item-actions span.price-container span.price").inner_text(timeout=1000)
                                    except PlaywrightTimeoutError:
                                        preco_similar = None     
                                        erros_coleta.append('PRECO')
                                        
                                    # Caso algum campo tenha falhado, registra os campos afetados no status.
                                    if erros_coleta:
                                        status = "ERRO NA COLETA: " + ", ".join(erros_coleta)                                                                                                                                                                                                              

                                    # Armazena o produto similar nos resultados.
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
                                # Localiza e fecha a janela de produtos similares.
                                fechar_popup = page.locator("div.modal-inner-wrap button.action-close:visible")
                                fechar_popup.click()
                                
                                # Aguarda o overlay desaparecer.
                                page.locator(".modals-overlay").wait_for(state="hidden")
                                page.wait_for_timeout(1000)
                                
                            # Registra qualquer erro ocorrido durante o processamento dos produtos similares.
                            except Exception as e:
                                logging.exception(f"Erro ao processar similares do produto'{codigo}' : {e}")
                                continue
                        
                            
                except Exception as e:

                        # Trata erros gerais ocorridos durante a busca do código.
                        logging.exception(f"RMP | filial={filial} | codigo={codigo} | erro na busca")
                        
                        # Registra o erro nos resultados para não perder o código que estava sendo processado.
                        resultados.append({
                            "fornecedor": "RMP",               
                            "cod_buscado": codigo,
                            "cod_fabricante": None, 
                            "descricao": f"ERRO: {e}",  
                            "preco": None,
                            "fabricante": None,
                            "status": f"ERRO DE COLETA: {type(e).__name__}",
                            "prazo": None,
                            "filial": None
                        })
                finally:
                        # Aguarda um intervalo aleatório antes de iniciar a próxima busca.
                        page.wait_for_timeout(random.randint(1000,2000))
                        
        logging.info(f"Loop finalizado: {processados}/{len(codigos)} códigos processados")
        
        # Converte a lista de resultados em DataFrame.
        resultado_busca = pd.DataFrame(resultados)
        
        # Define as colunas textuais que serão tratadas.
        colunas = [
            "fornecedor",
            "cod_buscado",
            "cod_fabricante",
            "descricao",
            "preco",
            "fabricante",
            "status"
        ]
        
        # Remove espaços extras dos campos textuais.
        resultado_busca[colunas] = resultado_busca[colunas].apply(lambda c: c.str.strip())
        
    # Retorna o DataFrame contendo todos os resultados da coleta.
    return resultado_busca

if __name__ == "__main__":

    # Define os códigos que serão utilizados durante o teste.
    codigos = ["ECO1651","VC-232"]
    
    # Define as filiais que serão utilizadas durante o teste.
    filiais = []
            
    # Executa a coleta utilizando os códigos e filiais definidos acima.
    resultado = executar(codigos, filiais)
            
    # Exibe no terminal o DataFrame com os resultados da coleta.
    print(resultado)
             


















