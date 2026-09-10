from playwright.sync_api import sync_playwright
import pandas as pd
import logging
import random
from dotenv import load_dotenv
import os
from functions import selecionar_filial_sky, retry_acao
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

# Função principal responsável por realizar as buscas dos códigos no site da SKY
# e retornar os produtos encontrados, incluindo produtos similares.
def executar(codigos,filiais):

    # Carrega as credenciais armazenadas nas variáveis de ambiente.
    load_dotenv()
    cnpj_login = os.getenv("SKY_CNPJ")
    usuario_login = os.getenv("SKY_USUARIO")
    senha_login = os.getenv("SKY_SENHA")

    # Lista onde serão armazenados todos os resultados coletados.
    resultados = []
    
    # Caso nenhuma filial seja informada, realiza a coleta sem seleção de filial.
    lista_filiais = filiais if filiais else [None]

    with sync_playwright() as p:

        # Inicializa o navegador em modo visível e cria uma nova página.
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # URL da página de login da SKY
        url = "https://cliente.skypecas.com.br/usuario/login"

        # Acessa a página de login da SKY.
        retry_acao(lambda: page.goto(url))

        # Preenche o CNPJ/CPF utilizado no acesso.
        cnpj = page.get_by_role("textbox", name="CNPJ ou CPF")
        retry_acao(lambda: cnpj.click())
        page.wait_for_timeout(random.randint(1000, 2000))
        retry_acao(lambda: cnpj.fill(cnpj_login))

        # Preenche o usuário.
        usuario = page.get_by_role("textbox", name="Usuário")
        retry_acao(lambda: usuario.click())
        page.wait_for_timeout(random.randint(1000, 2000))
        retry_acao(lambda: usuario.fill(usuario_login))

        # Preenche a senha.
        senha = page.get_by_role("textbox", name="Senha")
        retry_acao(lambda: senha.click())
        page.wait_for_timeout(random.randint(1000, 2000))
        retry_acao(lambda: senha.fill(senha_login))
        page.wait_for_timeout(random.randint(1000, 2000))

        # Realiza o primeiro clique no botão de login.
        entrar = page.get_by_role("button", name="Entrar")
        retry_acao(lambda: entrar.click())

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
                    retry_acao(lambda: erro_busca.get_by_role("button", name="OK").click())
                                            
                except PlaywrightTimeoutError:
                    # Caso nenhum aviso seja exibido, continua normalmente
                    pass
                
                page.wait_for_timeout(2000)

            # Percorre todos os códigos para a filial atual.
            for codigo in codigos:
                try:
                    # Localiza o campo de busca e preenche o código.
                    busca = page.get_by_role("textbox", name="Código da Peça")
                    page.wait_for_timeout(random.randint(1000, 2000))         
                    retry_acao(lambda: busca.fill(codigo))

                    # Localiza e aciona o botão de busca.
                    buscar = page.get_by_role("button", name=" Buscar")
                    page.wait_for_timeout(random.randint(1000, 2000))
                    retry_acao(lambda: buscar.click())

                    # Verifica se o site retornou um aviso indicando que o código não foi encontrado.
                    popup_ok = page.get_by_role("button", name="OK")

                    try:
                        popup_ok.wait_for(state="visible", timeout=2000)
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
                            "filial": filial

                            })
                        continue

                    except PlaywrightTimeoutError:
                        # Se o aviso não aparecer, continua com a coleta.
                        pass
                    
                    # Localiza os cards dos produtos retornados pela busca.
                    cards = page.locator("div.bx_produto")
                    qtd_produtos = cards.count()
                    
                    # Percorre todos os produtos encontrados.
                    for i in range(qtd_produtos):
                        card = cards.nth(i)
                        
                        # Define o status inicial da coleta
                        status = 'OK'
                                                
                        # Lista utilizada para registrar campos que apresentaram erro.
                        erros_coleta = []
                        
                        # Coleta o preço do produto principal.
                        try:
                            preco_principal = card.locator("span.preco_final").first.inner_text(timeout=1000)
                        except PlaywrightTimeoutError:
                            preco_principal = None
                            erros_coleta.append('PRECO')
                        
                        # Coleta o código do fabricante.  
                        try:
                            cod_fabricante_principal = card.locator("div.fleft.codfab strong").first.inner_text(timeout=1000)
                        except PlaywrightTimeoutError:
                            cod_fabricante_principal = None
                            erros_coleta.append('COD_FABRICANTE')
                        
                        # Coleta a descrição do produto.
                        try:
                            descricao_principal = card.locator("div.nome").first.inner_text(timeout=1000)
                        except PlaywrightTimeoutError:
                            descricao_principal = None
                            erros_coleta.append('DESCRICAO')
                        
                        # Coleta o fabricante.    
                        try: 
                            fabricante_principal = card.locator("div.fornecedor").first.inner_text(timeout=1000)
                        except PlaywrightTimeoutError:
                            fabricante_principal = None
                            erros_coleta.append('FABRICANTE')
                            
                        # Caso algum campo tenha apresentado erro, altera o status informando quais campos falharam.
                        if erros_coleta:
                            status = "ERRO NA COLETA: " + ", ".join(erros_coleta)
                        
                        # Registra o produto principal nos resultados.    
                        resultados.append({
                            "fornecedor": "SKY Auto Peças",
                            "cod_buscado": codigo,
                            "cod_fabricante": cod_fabricante_principal,
                            "descricao": descricao_principal,
                            "preco": preco_principal,
                            "fabricante": fabricante_principal,
                            "status": status,
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
                                
                                # Define o status inicial dos similares.
                                status = "Similar"
                                                                
                                # Lista de possíveis erros de coleta.
                                erros_coleta = []
                                
                                # Coleta o preço do similar.
                                try:
                                    preco_similar = card_similares.locator("span.preco_final").inner_text(timeout=1000)
                                except PlaywrightTimeoutError:
                                    preco_similar = None
                                    erros_coleta.append('PRECO')
                                
                                # Coleta o código do fabricante do similar.
                                try:
                                    cod_fabricante_similar = card_similares.locator("div.fleft.codfab strong").inner_text(timeout=1000)
                                except PlaywrightTimeoutError:
                                    cod_fabricante_similar = None
                                    erros_coleta.append('COD_FABRICANTE')
                                
                                # Coleta a descrição do similar.   
                                try:
                                    descricao_similar = card_similares.locator("div.nome").inner_text(timeout=1000)
                                except PlaywrightTimeoutError:
                                    descricao_similar = None
                                    erros_coleta.append('DESCRICAO')
                                
                                # Coleta o fabricante do similar.    
                                try:
                                    fabricante_similar = card_similares.locator("div.fornecedor").inner_text(timeout=1000)
                                except PlaywrightTimeoutError:
                                    fabricante_similar = None
                                    erros_coleta.append('FABRICANTE')
                                    
                                # Caso algum campo tenha apresentado erro, altera o status informando quais campos falharam.
                                if erros_coleta:
                                    status = "ERRO NA COLETA: " + ", ".join(erros_coleta)
                                
                                # Registra o produto similar nos resultados.   
                                resultados.append({
                                    "fornecedor": "SKY Auto Peças",
                                    "cod_buscado": codigo,
                                    "cod_fabricante": cod_fabricante_similar,
                                    "descricao": descricao_similar,
                                    "preco": preco_similar,
                                    "fabricante": fabricante_similar,
                                    "status": status,
                                    "prazo": None,
                                    "filial": filial
                                })
                            
                            # Localiza o botão de fechamento da janela de similares.    
                            fechar_popup = page.locator("a.close-modal")
                            
                            # Fecha a janela caso o botão esteja disponível.
                            if fechar_popup.count() > 0:
                                fechar_popup.click(no_wait_after=True)
                            
                            # Aguarda o modal desaparecer antes de continuar.
                            page.locator("div.ajax.modal").wait_for(state="hidden", timeout=3000)
                        
                        except Exception as e:
                            # Registra erros ocorridos durante a coleta dos produtos similares.
                            logging.exception(f"Erro ao processar similares do produto '{codigo}': {e}")
                            continue
                
                # Trata erros gerais ocorridos durante a busca do código.           
                except Exception as e:
                    logging.exception(f"SKY | filial={filial} | codigo={codigo} | erro na busca")
                    resultados.append({
                        "fornecedor": "SKY Auto Peças",
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
    filiais = ["SKY AUTOMOTIVE (POA)", "ENVIA PEÇAS (PELOTAS)", "EMBREPAR (POA)"]
        
    # Executa o coletor individualmente.
    resultado = executar(codigos, filiais)
    
    # Exibe o resultado da coleta.
    print(resultado)
