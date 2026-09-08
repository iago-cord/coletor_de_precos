from playwright.sync_api import sync_playwright
import pandas as pd
import random
from dotenv import load_dotenv
import os
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
import logging

# Função responsável por executar a busca dos códigos de produtos.
# Recebe como parâmetros a lista de códigos e a lista de filiais selecionadas.
def executar(codigos,filiais):
    
    # Carrega as variáveis de ambiente armazenadas no arquivo .env.
    # As credenciais serão utilizadas para realizar o login na plataforma DPK.
    load_dotenv()
    usuario_login = os.getenv("DPK_USUARIO")
    senha_login = os.getenv("DPK_SENHA")

    # Cria uma lista vazia onde serão armazenados todos os resultados
    # encontrados durante a coleta.
    resultados = []
    
    # Define a lista de filiais que será utilizada durante a coleta.
    # Caso nenhuma filial seja informada, utiliza [None].
    lista_filiais = filiais if filiais else [None]

    # Inicializa o Playwright e mantém seu contexto ativo durante toda a execução da coleta.
    with sync_playwright() as p:
        
        # Inicializa o navegador Chromium em modo visível.
        browser = p.chromium.launch(headless=False)
        
        # Cria uma nova página no navegador.
        page = browser.new_page()
        
        # Define a URL da página de login da plataforma DPK.
        url = "https://www.dpk.com.br/#/login"
        
        # Acessa a página de login.
        page.goto(url)
        
        # Localiza o campo de e-mail, clica no campo e preenche
        # com o usuário armazenado nas variáveis de ambiente.
        usuario = page.get_by_role("textbox", name="Email")
        usuario.click()
        usuario.fill(usuario_login)
        
        # Aguarda um intervalo aleatório antes de continuar.
        page.wait_for_timeout(random.randint(1000,2000))
        
        # Localiza o campo de senha, clica no campo e preenche
        # com a senha armazenada nas variáveis de ambiente.
        senha = page.get_by_role("textbox", name="Senha")
        senha.click()
        senha.fill(senha_login)
        
        # Aguarda um intervalo aleatório antes de continuar.
        page.wait_for_timeout(random.randint(1000,2000))
        
        # Localiza o botão "Entrar" e realiza o login na plataforma.
        entrar = page.get_by_role("button", name="Entrar")
        entrar.click()
        
        # Aguarda o campo de pesquisa ficar visível.
        # A disponibilidade desse elemento indica que a página principal foi carregada após o login.
        page.get_by_role("search", name="Busque por código ou descriçã").wait_for(state='visible')
        
        # Percorre todas as filiais informadas para realizar a coleta dos códigos em cada uma delas.
        for filial in lista_filiais:
            
            # Abre o seletor de filiais da plataforma.
            page.locator(".mat-select-arrow").first.click()
            
            # Localiza a filial correspondente ao nome recebido e realiza sua seleção.
            item = page.get_by_text(filial)
            item.click()
            
            # Percorre todos os códigos informados para realizar a pesquisa na filial atualmente selecionada.
            for codigo in codigos:
                
                try:
                    
                    # Aguarda o campo de pesquisa ficar visível antes de iniciar a pesquisa do código.
                    page.get_by_role("search", name="Busque por código ou descriçã").wait_for(state='visible')
                    
                    # Localiza o campo de pesquisa.
                    busca = page.get_by_role("search", name="Busque por código ou descriçã")
                    
                    # Clica no campo e preenche com o código atual.
                    busca.click()
                    busca.fill(codigo)
                    
                    # Localiza o botão "Buscar" e executa a pesquisa.
                    buscar = page.get_by_role("button", name="Buscar")
                    buscar.click()
                    
                    # Localiza o elemento utilizado pela plataforma para informar que nenhum produto foi encontrado.
                    nao_encontrado = page.locator("div.kdp-favorito-vazio")
                
                    try:
                        
                        # Aguarda até que o elemento de produto não encontrado fique visível na página
                        nao_encontrado.wait_for(state='visible')
                        
                        # Registra no log que o código não foi encontrado.
                        logging.info(f"DPK: {codigo} NÃO ENCONTRADO")
                        
                        # Adiciona o código à lista de resultados com status
                        # "Não Encontrado" e os demais campos sem informação.
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
                        
                        # Interrompe o processamento do código atual
                        # e passa para o próximo código da lista.
                        continue
                    except PlaywrightTimeoutError:
                        
                        # Caso a mensagem de produto não encontrado não apareça dentro do tempo limite, continua o processamento
                        # considerando que existem produtos para coletar.
                        pass
                    
                    # Localiza todos os cards de produtos que estão visíveis na página após a pesquisa.
                    produtos = page.locator("div.column-view-card:visible")
                    
                    # Conta quantos produtos foram retornados pela pesquisa.
                    count = produtos.count()

                    # Percorre todos os produtos retornados pela pesquisa.
                    for i in range(count):
                        
                        # Obtém o card correspondente ao produto atual.
                        card = produtos.nth(i)
                        # Inicializa o status como "OK".
                        status = "OK"
                        
                        # Cria uma lista para armazenar quais campos apresentaram erro durante a coleta.
                        erros_coleta = []
                        
                        # Tenta extrair a descrição do produto.
                        try:
                            descricao = card.locator("h2 a").text_content(timeout=1000) 
                        except PlaywrightTimeoutError:
                            # Caso a descrição não seja encontrada, atribui None e registra o campo com erro.
                            descricao = None
                            erros_coleta.append('DESCRICAO')
                            
                        # Tenta extrair o fabricante do produto.
                        try:
                            fabricante = card.locator("xpath=//p[contains(text(), 'Fabricante')]/following-sibling::strong[1]").text_content(timeout=1000)
                        except PlaywrightTimeoutError:
                            # Caso o fabricante não seja encontrado, atribui None e registra o campo com erro.
                            fabricante = None
                            erros_coleta.append('FABRICANTE')
                            
                        # Tenta extrair o código do fabricante.
                        try:    
                            cod_fabricante = card.locator("xpath=//p[contains(text(), 'Cód de Fábrica')]/following-sibling::strong[1]").text_content(timeout=1000) 
                        except PlaywrightTimeoutError:
                            # Caso o código do fabricante não seja encontrado, atribui None e registra o campo com erro.
                            cod_fabricante = None
                            erros_coleta.append('COD_FABRICANTE')
                            
                         # Tenta extrair o preço do produto.
                        try:
                            preco = card.locator("div.preco-colum span.cor-preco").inner_text(timeout=1000)
                        except PlaywrightTimeoutError:
                            # Caso o preço não seja encontrado, atribui None e registra o campo com erro.
                            preco = None
                            erros_coleta.append('PRECO')
                        
                        # Tenta identificar a filial atualmente selecionada na plataforma. 
                        try:
                            filial = page.locator("div.mat-form-field-infix span.mat-select-value-text").text_content(timeout=1000)
                        except PlaywrightTimeoutError:
                            # Caso a filial não seja identificada, atribui None.
                            filial = None
                        
                        # Armazena os dados principais do produto em variáveis específicas antes de adicioná-los aos resultados.
                        # Necessario para evitar overwrite dos dados
                        descricao_principal = descricao
                        preco_principal = preco
                        cod_fabricante_principal = cod_fabricante
                        fabricante_principal = fabricante
                        
                        # Caso algum campo tenha apresentado erro durante a coleta,
                        # altera o status informando quais campos apresentaram problema.   
                        if erros_coleta:
                            status = "ERRO NA COLETA: " + ", ".join(erros_coleta)
                        
                        # Adiciona o produto principal à lista de resultados.
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
                        
                        # Localiza o botão responsável por abrir os produtos similares do produto atual.
                        botao_similar = card.locator("button#similaresBtn")
                        
                        # Armazena a URL atual antes de abrir a tela de produtos similares.
                        # Necessário para retornar a pagina de pesquisa.
                        url_busca = page.url
                        
                        # Clica no botão para abrir os produtos similares.
                        botao_similar.click()
                        
                        # Aguarda o carregamento da janela de produtos similares.
                        page.wait_for_timeout(2000)
                        
                        # Localiza todos os produtos similares exibidos dentro da janela de similares.
                        similares = page.locator("div.conteudo_similares ul.slides-list li.ng-star-inserted")
                        
                        # Percorre todos os produtos similares encontrados.
                        for j in range(similares.count()):
                            
                            # Obtém o card correspondente ao produto similar atual.
                            card_sim = similares.nth(j)
                            
                            # Define inicialmente o status do similar como "Similar".
                            status = 'Similar'
                            
                            # Cria uma lista para armazenar os campos que apresentarem erro durante a coleta.
                            erros_coleta= []
                            
                            # Tenta extrair a descrição do produto similar.
                            try:
                                descricao_similar = card_sim.locator("h2.mat-h4").text_content(timeout=1000)
                            except PlaywrightTimeoutError:
                                # Caso a descrição não seja encontrada, atribui None e registra o campo com erro.
                                descricao_similar = None
                                erros_coleta.append("DESCRICAO")
                            
                            # Tenta extrair o preço do produto similar.
                            try:
                                preco_similar = card_sim.locator("div.valor strong.mat-h2").text_content(timeout=1000)
                            except PlaywrightTimeoutError:
                                # Caso o preço não seja encontrado, atribui None e registra o campo com erro.
                                preco_similar = None
                                erros_coleta.append("PRECO")
                            
                            # Tenta localizar e extrair o fabricante do produto similar.
                            try:
                                campo_fabricante = card_sim.locator("ul.conteudo li", has_text="Fabricante")
                                fabricante_completo = campo_fabricante.text_content(timeout=1000)
                                # Separa o texto pelo ":" e mantém somente a parte correspondente ao nome do fabricante.
                                fabricante_similar = fabricante_completo.split(":")[1].strip()
                            except PlaywrightTimeoutError:
                                # Caso o fabricante não seja encontrado, atribui None e registra o campo com erro.
                                fabricante_similar = None
                                erros_coleta.append("FABRICANTE")
                            
                            # Tenta localizar e extrair o código do fabricante do produto similar.
                            try:
                                campo_cod_fabricante = card_sim.locator("ul.conteudo li", has_text="Cód. de Fábrica")
                                cod_fabricante_completo = campo_cod_fabricante.text_content(timeout=1000)
                                # Separa o texto pelo ":" e mantém somente a parte correspondente ao código do fabricante.
                                cod_fabricante_similar = cod_fabricante_completo.split(":")[1].strip()
                            except PlaywrightTimeoutError:
                                # Caso o código do fabricante não seja encontrado, atribui None e registra o campo com erro.
                                cod_fabricante_similar = None
                                erros_coleta.append("COD_FABRICANTE")
                            
                            # Caso algum campo tenha apresentado erro durante
                            # a coleta, altera o status informando os campos afetados.
                            if erros_coleta:
                                status = "ERRO NA COLETA: " + ", ".join(erros_coleta)
                            
                            # Adiciona o produto similar à lista de resultados.
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
                        
                        # Aguarda o encerramento do processamentodos produtos similares.
                        page.wait_for_timeout(2000)
                        
                        # Retorna para a URL da página onde a busca do produto principal estava sendo realizada.
                        page.goto(url_busca)
                # Garante que o intervalo entre as pesquisas seja executado
                # mesmo quando ocorrer uma exceção durante o processamento.                
                finally:
                    # Aguarda um intervalo aleatório antes de iniciar o processamento do próximo código.
                    page.wait_for_timeout(random.randint(1000,2000))
                    
            # Converte a lista de resultados coletados em um DataFrame do Pandas.    
            resultado_busca = pd.DataFrame(resultados)
            
            # Retorna o DataFrame contendo os resultados da coleta.
            return resultado_busca
          

# Permite executar este módulo diretamente para realizar um teste,
# sem precisar chamá-lo através do arquivo principal da aplicação.
if __name__ == "__main__":

    # Define uma lista de códigos que será utilizada no teste.
    codigos = ['pd1530', 'vc232', 'eco1615']  
    
    # Define uma lista de filiais que será utilizada no teste.
    filiais = []

    # Executa a função principal passando os códigos e as filiais
    # definidos exclusivamente para o teste deste módulo.
    resultado = executar(codigos, filiais)

    # Exibe no terminal o DataFrame contendo os resultados da coleta.
    print(resultado)

    
    
    
    