from playwright.sync_api import sync_playwright
import random
import os
from dotenv import load_dotenv
import logging
import pandas as pd
from functions import selecionar_filial_autonorte, retry_acao
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

# Função responsável por executar a busca dos códigos de produtos.
# Recebe como parâmetros a lista de códigos e a lista de filiais selecionadas no app.py.
def executar(codigos, filiais):
    
    # Carrega as variáveis de ambiente armazenadas no arquivo .env.
    # As credenciais são utilizadas para realizar o login na plataforma.
    load_dotenv()
    usuario_login = os.getenv("AUTONORTE_USER")
    senha_login = os.getenv("AUTONORTE_PASSWORD")

    # Cria uma lista vazia que armazenará os resultados encontrados durante a coleta.
    resultados = []
    
    # Define a lista de filiais que será utilizada na coleta.
    # Caso nenhuma filial tenha sido informada, utiliza [None] para executar a busca
    # utilizando a filial padrão da plataforma.
    lista_filiais = filiais if filiais else [None]

    # Inicializa o Playwright e mantém seu contexto ativo durante toda a execução.
    with sync_playwright() as p:
        
        # Inicializa o navegador Chromium em modo visível e cria uma nova página.
        # Em seguida, acessa a página inicial da plataforma.
        browser = p.chromium.launch(headless = False)
        page = browser.new_page()
        url = "https://kki.autonorte.com.br"
        retry_acao(lambda: page.goto(url))
        
        # Localiza o campo de e-mail, clica no campo e preenche com o usuário
        # obtido das variáveis de ambiente.
        usuario = page.get_by_role("textbox", name="E-mail")
        retry_acao(lambda: usuario.click())
        page.wait_for_timeout(random.randint(1000, 2000))
        retry_acao(lambda: usuario.fill(usuario_login))
        
        # Localiza o campo de senha, clica no campo e preenche com a senha
        # obtida das variáveis de ambiente.
        senha = page.get_by_role("textbox", name="Senha")
        retry_acao(lambda: senha.click())
        page.wait_for_timeout(random.randint(1000, 2000))
        retry_acao(lambda: senha.fill(senha_login))
        
        # Aguarda um intervalo aleatório antes de realizar o login.
        page.wait_for_timeout(random.randint(1000, 2000))
        
        # Localiza o botão "Entrar" e realiza o login na plataforma.
        entrar = page.get_by_role("button", name="Entrar")
        retry_acao(lambda: entrar.click())
        
        # Aguarda um intervalo aleatório após o login para permitir que a página
        # carregue os elementos necessários antes de iniciar a coleta.
        page.wait_for_timeout(random.randint(1000, 2000))
        
        # Percorre todas as filiais selecionadas para realizar a coleta
        # dos códigos em cada uma delas.
        for filial in lista_filiais:
            
            # Caso uma filial tenha sido informada, executa a função responsável
            # por selecionar a filial correspondente na plataforma.
            if filial:
                selecionar_filial_autonorte(page,filial)

            # Percorre todos os códigos informados para realizar a pesquisa
            # na filial atualmente selecionada.
            for codigo in codigos:
                
                try:
                    # Localiza o campo de busca pelo nome "Referência",
                    # clica no campo e preenche com o código que será pesquisado.
                    busca = page.get_by_role("textbox", name="Referência", exact=True)
                    retry_acao(lambda: busca.click())
                    page.wait_for_timeout(random.randint(1000, 2000))
                    retry_acao(lambda: busca.fill(codigo))
                    
                    # Aguarda um intervalo aleatório antes de executar a pesquisa.
                    page.wait_for_timeout(random.randint(1000, 2000))
                    
                    # Localiza o botão "Pesquisar" e executa a busca pelo código.
                    clique_buscar = page.get_by_role("button", name="Pesquisar")
                    retry_acao(lambda: clique_buscar.click())
                    
                    # Aguarda o carregamento inicial dos resultados da pesquisa no DOM
                    page.wait_for_timeout(2000)

                    try:
                        # Aguarda até que a primeira linha da tabela de resultados
                        # esteja presente no DOM.
                        # O estado "attached" verifica apenas se o elemento existe
                        # no DOM, não sendo necessário que esteja visível.
                        page.locator("table.chakra-table tbody tr").first.wait_for(state="attached", timeout=5000)
                        
                    except PlaywrightTimeoutError:
                        # Caso a tabela não apareça dentro do tempo limite,
                        # continua a execução para verificar outras possibilidades,
                        # como o produto não encontrado.
                        pass
                    # Localiza a mensagem apresentada pela plataforma quando
                    # nenhum produto é encontrado para o código pesquisado.
                    nao_encontrado = page.locator("table.chakra-table td p.chakra-text", has_text="Nenhum produto encontrado")
                    
                    try:
                        # Aguarda até que a mensagem de produto não encontrado
                        # esteja visível na página.
                        nao_encontrado.wait_for(state='visible', timeout=3000)
                        
                        # Registra no log que o código não foi encontrado.
                        logging.info(f"Auto Norte: {codigo} NÃO ENCONTRADO")
                        
                        # Adiciona o código à lista de resultados com status
                        # "NÃO ENCONTRADO" e os demais campos sem informação.
                        resultados.append({
                                        "fornecedor": "Auto Norte",
                                        "cod_buscado": codigo,
                                        "cod_fabricante": None, 
                                        "descricao": None,                               
                                        "preco": None,
                                        "fabricante": None,
                                        "status": "NÃO ENCONTRADO",
                                        "prazo": None,
                                        "filial": filial
                                        })
                        
                        # Interrompe o processamento do código atual e passa
                        # diretamente para o próximo código da lista.
                        continue
                                    
                    except PlaywrightTimeoutError:
                        
                        # Caso a mensagem de produto não encontrado não esteja
                        # visível, continua o processamento normalmente,
                        # considerando que existem resultados para analisar.
                        pass
                    
                    
                    # Localiza todas as linhas de produtos retornadas pela pesquisa.
                    produtos = page.locator("table.chakra-table tbody tr")
                    
                    # Conta quantos produtos foram retornados pela pesquisa.
                    total_produtos = produtos.count()
                    
                    # Percorre cada produto retornado pela plataforma.
                    for i in range (total_produtos):
                        # Define o status inicial da coleta.
                        status = "OK"
                        
                        # Lista utilizada para registrar campos que apresentaram erro.
                        erros_coleta = []
                        
                        # Obtém a linha correspondente ao produto atual.
                        # O nth(i) permite acessar uma linha específica do resultado.
                        card = produtos.nth(i)
                        
                        # Seleciona a segunda célula da linha, posição 1, onde estão as informações de código e fabricante
                        td_cod = card.locator("td").nth(1)

                        # Tenta extrair o código do fabricante a partir do primeiro elemento span encontrado dentro da célula.
                        try:
                            cod_fabricante_raw = td_cod.locator("span.chakra-text").first.inner_text(timeout=2000).strip()
                            
                            # Como o conteúdo pode possuir mais de uma informação separada por quebra de linha, mantém somente a primeira.
                            cod_fabricante = cod_fabricante_raw.split("\n")[0].strip()
                        except PlaywrightTimeoutError:
                            # Caso o código não seja encontrado, atribui None.
                            cod_fabricante = None
                            erros_coleta.append('COD_FABRICANTE')
                        
                        # Tenta localizar e extrair o nome do fabricante presente no elemento <strong>.   
                        try:
                            fabricante = td_cod.locator("strong").first.inner_text(timeout=2000).strip()
                        except PlaywrightTimeoutError:
                            # Caso o fabricante não seja encontrado, atribui None.
                            fabricante = None
                            erros_coleta.append('FABRICANTE')
                        
                        # Seleciona a terceira célula da linha, posição 2, onde está a descrição do produto.    
                        td_desc = card.locator("td").nth(2)
                        
                        # Tenta extrair a descrição do produto.
                        try:
                            descricao = td_desc.locator('p.chakra-text').first.inner_text(timeout=2000).strip()
                        except PlaywrightTimeoutError:
                            # Caso a descrição não seja encontrada, atribui None.
                            descricao = None
                            erros_coleta.append('DESCRICAO')
                        
                        # Seleciona a décima quinta célula da linha, posição 14, onde está o preço do produto. 
                        td_preco = card.locator("td").nth(14)
                        
                        # Tenta extrair o preço do produto.
                        try:
                            preco = td_preco.locator("span").first.inner_text(timeout=2000).strip()
                            
                            # Remove quebras de linha e espaços duplicados, mantendo o conteúdo do preço em uma única string.
                            preco = " ".join(preco.split())
                        except PlaywrightTimeoutError:
                            # Caso o preço não seja encontrado, atribui None.
                            preco = None
                            erros_coleta.append('PRECO')
                        
                        # Seleciona a sétima célula da linha, posição 6, onde está a informação de estoque
                        td_est = card.locator("td").nth(6)
                        
                         # Tenta extrair a quantidade disponível em estoque.
                        try:
                            estoque = td_est.locator("p.chakra-text").first.inner_text(timeout=2000).strip()
                            
                        except PlaywrightTimeoutError:
                            # Caso a informação de estoque não seja encontrada, atribui None.
                            estoque = None 
                            erros_coleta.append('ESTOQUE')
                            
                        
                        # Define o status do produto com base na quantidade em estoque.
                        # Estoque igual a zero recebe "Sem Estoque";
                        # qualquer outro valor recebe "OK".
                        # Caso algum campo tenha apresentado erro, altera o status informando quais campos falharam.  
                        if erros_coleta:
                            status = "ERRO NA COLETA: " + ", ".join(erros_coleta)
                        elif estoque == '0':
                            status = "Sem Estoque"
                        else:
                            status = "OK"
                        
                        # Adiciona todas as informações coletadas do produto à lista de resultados.  
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
                # Executa este bloco independentemente de ocorrer uma exceção durante o processamento do código atual.
                finally:
                    
                    # Aguarda um intervalo aleatório antes de iniciar a próxima pesquisa.
                    page.wait_for_timeout(random.randint(1000, 2000))
            
            # Aguarda um intervalo aleatório após terminar todos os códigos da filial atual.     
            page.wait_for_timeout(random.randint(1000, 2000))
            
            # apos o termino da filial, volta a pagina de seleção de filial para selecionar a proxima e fazer a busca pelos codigos
            voltar_clientes = page.locator("aside a[href='/ficha-clientes']")
            
            # Localiza o link responsável por retornar à tela de seleção de clientes/filiais e realiza o clique.
            retry_acao(lambda: voltar_clientes.click())
            
            # Aguarda o carregamento da tela antes de selecionar a próxima filial.
            page.wait_for_timeout(random.randint(1000, 2000))
            
    # Converte a lista de dicionários coletados em um DataFrame do Pandas.     
    resultado_busca = pd.DataFrame(resultados)
    
    # Retorna o DataFrame contendo todos os resultados da coleta.
    return resultado_busca


# Permite executar o módulo diretamente para realizar um teste da função.
if __name__ == "__main__":
    
    # Define uma lista de códigos para serem pesquisados.
    codigos = ["ECO1651","VC232"]  
    
    # Define as filiais que serão utilizadas durante o teste.
    filiais = ["Maranhão","Pernambuco"]
    
    # Executa a coleta utilizando os códigos e filiais definidos acima.
    resultado = executar(codigos, filiais)
    
    # Exibe no terminal o DataFrame com os resultados da coleta.
    print(resultado)