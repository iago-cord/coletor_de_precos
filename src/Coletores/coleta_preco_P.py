from playwright.sync_api import sync_playwright
import random
import os
from dotenv import load_dotenv
import subprocess
import time
import logging
import pandas as pd
from src.functions import get_campo_busca, get_botao_buscar, retry_acao
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

# Função responsável por executar a busca dos códigos no site
def executar(codigos):
    
    # Cria a lista onde serão armazenados os resultados coletados
    resultados = []
    
     # Armazena o caminho do executável do Google Chrome instalado no computador
    chrome = "Caminho do Executavel do Chrome"
    
    # Define o diretório do perfil do Chrome que será utilizado na coleta
    profile = "Caminho do profile do Chrome usado para o acesso"
    
    # Define a porta utilizada para realizar a conexão com o Chrome através do protocolo CDP
    debug_port = 9222

    # Carrega as variáveis de ambiente presentes no arquivo .env
    load_dotenv()

    # Recupera o usuário e senha de acesso armazenado no .env
    USUARIO = os.getenv("USER")
    SENHA = os.getenv("PASSWORD")

    # Inicializa o Playwright
    with sync_playwright() as p:
        
        # Inicia o Chrome utilizando um perfil específico e habilitando a porta
        # para permitir a conexão do Playwright através do protocolo CDP
        processo_chrome = subprocess.Popen([
            chrome,
            f"--user-data-dir={profile}",
            f"--remote-debugging-port={debug_port}"
        ])
        
        # Aguarda alguns segundos para garantir que o Chrome esteja completamente iniciado
        time.sleep(3)

        # Conecta o Playwright ao Chrome que foi iniciado anteriormente através do CDP
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{debug_port}")

        # Recupera o primeiro contexto já existente no navegador
        context = browser.contexts[0]
        
        # Recupera a primeira página aberta dentro do contexto
        page = context.pages[0]
        
        # URL da página de login
        url = "https://www.sitedoconcorrente.com.br"

        # Acessa a página de login
        retry_acao(lambda: page.goto(url))
        
        # Aguarda o carregamento inicial do documento HTML
        page.wait_for_load_state('domcontentloaded')

        # Verifica se o usuário foi direcionado para a página de login
        if "/Account/Login/" in page.url:
            
            # Localiza o campo de usuário através do ID
            usuario = page.locator("#username")
            
            # Aguarda o campo de usuário estar disponível
            usuario.wait_for()
            
            # Clica no campo de usuário
            retry_acao(lambda: usuario.click())
            
            # Aguarda um intervalo aleatório antes de preencher o campo
            page.wait_for_timeout(random.randint(1000, 2000))
            
            # Preenche o campo de usuário com a credencial armazenada no .env
            retry_acao(lambda: usuario.fill(USUARIO))
            
            # Localiza o campo de senha através do ID
            senha = page.locator("#password")
            
            # Clica no campo de senha
            retry_acao(lambda: senha.click())
            
            # Aguarda um intervalo aleatório antes de preencher o campo
            page.wait_for_timeout(random.randint(1000, 2000))
            
            # Preenche o campo de senha com a credencial armazenada no .env
            retry_acao(lambda: senha.fill(SENHA))

            # Aguarda alguns segundos antes de realizar o login
            page.wait_for_timeout(random.randint(2000, 3500))

            # Localiza o botão de login e realiza o login
            entrar = page.get_by_role("button", name="Entrar")
            retry_acao(lambda: entrar.click())
            
        else:
            # Informa que a sessão já estava autenticada
            print("Usuario Logado!")
        
        # Percorre todos os códigos recebidos pela função
        for codigo in codigos:

            try:
                # Utiliza a função auxiliar para localizar o campo de busca
                busca = get_campo_busca(page)
                
                # Clica no campo de busca
                retry_acao(lambda: busca.click())
                
                # Aguarda um intervalo aleatório antes de realizar a busca
                page.wait_for_timeout(random.randint(1500, 3500))
                
                # Preenche o campo com o código que será pesquisado
                retry_acao(lambda: busca.fill(codigo))
                
                # Aguarda um intervalo aleatório antes de executar a pesquisa
                page.wait_for_timeout(random.randint(1500, 3500))
                
                 # Utiliza a função auxiliar para localizar o botão de busca
                clique_buscar = get_botao_buscar(page)
                
                # Aguarda a resposta da requisição enviada para a API do Algolia antes de continuar a execução da coleta
                with page.expect_response(lambda r: "algolia.net" in r.url.lower() and "/queries" in r.url.lower(),timeout=10000) as resp_info:
                    
                    # Executa a pesquisa do código
                    clique_buscar.click()
                    
                # Aguarda um pequeno intervalo para a atualização dos elementos da página
                page.wait_for_timeout(500)
                
                # Localiza o elemento exibido quando nenhum produto é encontrado   
                nao_encontrado = page.locator('#hits .dataTables_empty')

                # Verifica se a mensagem de produto não encontrado está visível
                if nao_encontrado.is_visible():
                    
                    # Registra no log que o código não foi encontrado
                    logging.info(f"P: {codigo} NÃO ENCONTRADO")
                    
                    # Adiciona o resultado como produto não encontrado
                    resultados.append({
                        "fornecedor": "P",
                        "cod_buscado": codigo,
                        "cod_fabricante": None,
                        "descricao": None,
                        "preco": None,
                        "fabricante": None,
                        "status": "NÃO ENCONTRADO",
                        "prazo": None,
                        "filial": None
                    })
                    
                    # Interrompe o processamento desse código e passa para o próximo
                    continue
                
                # Localiza as linhas da tabela que representam os produtos retornados
                produtos = page.locator("#hits tr.odd, #hits tr.even")
                
                # Aguarda o primeiro produto ser anexado ao DOM
                produtos.first.wait_for(state="attached", timeout=5000)

                # Conta quantos produtos foram retornados pela pesquisa
                count = produtos.count()
                
                try:
                    # Tenta capturar o prazo de pagamento exibido na página
                    prazo = page.locator('span#page-header-cpgto-abrev').inner_text(timeout=1500).strip()
                except:
                    # Caso o prazo não seja encontrado, atribui None
                    prazo = None
                    
                # Percorre todos os produtos retornados pela pesquisa
                for i in range(count):
                    
                    # Recupera o produto atual através do índice
                    card = produtos.nth(i)
                    
                    try:
                        # Localiza e captura o fabricante do produto
                        fabricante = card.locator('span.w-125px').inner_text(timeout=1500).strip()
                    except:
                        # Caso o fabricante não seja encontrado, atribui None
                        fabricante = None
                    
                    # Localiza o elemento responsável por abrir o popover com os detalhes do produto
                    popover_trigger = card.locator("[data-toggle='popover']")
                    
                    # Abre o popover do produto
                    popover_trigger.click()
                    
                    # Aguarda o carregamento das informações do produto
                    page.wait_for_timeout(1000)
                
                    try:
                        # Aguarda a página atingir o estado de rede ociosa caso a aplicação faça novas requisições após abrir o popover
                        page.wait_for_load_state("networkidle", timeout=5000)
                        
                    except PlaywrightTimeoutError:
                        # Continua a execução caso a rede não fique ociosa dentro do tempo limite
                        pass
                    
                    try:
                        # Captura a descrição do produto dentro do popover
                        descricao = card.locator('span.mb-0').inner_text(timeout=1500).strip()

                    except Exception as e:
                        # Caso a descrição não seja encontrada, atribui None
                        descricao = None

                    try:
                        # Cria um dicionário para armazenar as informações encontradas
                        # na tabela de características técnicas do produto
                        info_dict = {}
                        
                         # Localiza todas as tabelas de informações presentes no popover
                        tabelas = page.locator('#container-pdp-ficha table.info-table')
                        
                        # Conta a quantidade de tabelas encontradas
                        total_tabelas = tabelas.count()
                        
                        # Percorre todas as tabelas encontradas
                        for t in range(total_tabelas):
                            
                            # Localiza as linhas da tabela atual
                            linhas = tabelas.nth(t).locator('tbody tr')
                            
                            # Conta a quantidade de linhas existentes
                            total_linhas = linhas.count()

                            # Percorre todas as linhas da tabela
                            for j in range(total_linhas):
                                
                                # Localiza as células da linha atual
                                tds = linhas.nth(j).locator('td')
                                
                                # Verifica se a linha possui pelo menos duas células
                                if tds.count() >= 2:
                                    
                                    # Captura o nome da informação
                                    label = tds.nth(0).inner_text().strip()
                                    
                                    # Captura o valor da informação
                                    valor = tds.nth(1).inner_text().strip()
                                    
                                    # Armazena a informação no dicionário
                                    info_dict[label] = valor

                        # Recupera o código do fabricante através do dicionário
                        cod_fabricante = info_dict.get("Código do Fabricante")

                    except Exception:
                        # Caso ocorra algum erro na coleta das informações técnicas,
                        # inicializa o dicionário e o código do fabricante como None
                        info_dict = {}
                        cod_fabricante = None
                        
                    try:
                        # Executa JavaScript diretamente no navegador para coletar
                        # as filiais e respectivos preços disponíveis para o produto
                        dados_filiais = page.evaluate("""
                            () => {
                                const blocos = document.querySelectorAll('#list-estoques1 [data-id]');
                                return Array.from(blocos).map(bloco => {
                                    const nomeEl = bloco.querySelector("[id^='p-'] .w-100");
                                    const precoEl = bloco.querySelector("[id^='preco-comprar-'] .font-size-h5");
                                    return {
                                        filial: nomeEl ? nomeEl.innerText.trim() : null,
                                        preco: precoEl ? precoEl.innerText.trim() : null
                                    };
                                });
                            }
                        """)
                    except Exception:
                        
                        # Caso ocorra algum erro na coleta das filiais, retorna uma lista vazia
                        dados_filiais = []

                    # Verifica se nenhuma filial foi encontrada para o produto
                    if not dados_filiais:
                        
                        # Registra o produto como sem estoque ou sem filial disponível
                        resultados.append({
                            "fornecedor": "P",
                            "cod_buscado": codigo,
                            "cod_fabricante": cod_fabricante,
                            "descricao": descricao,
                            "preco": None,
                            "fabricante": fabricante,
                            "status": "SEM ESTOQUE/FILIAL",
                            "prazo": None,
                            "filial": None
                        })
                
                    else:
                        
                        # Percorre todas as filiais encontradas para o produto
                        for item in dados_filiais:
                            
                            # Adiciona uma linha de resultado para cada filial encontrada
                            resultados.append({
                                "fornecedor": "P",
                                "cod_buscado": codigo,
                                "cod_fabricante": cod_fabricante,
                                "descricao": descricao,
                                "preco": item["preco"],
                                "fabricante": fabricante,
                                "status": "OK",
                                "prazo": prazo,
                                "filial": item["filial"]
                            })

                    try:
                        # Localiza o botão responsável por fechar o modal
                        fechar_modal = page.locator(".modal.show .modal-header button.close")
                        
                        # Clica no primeiro botão encontrado
                        fechar_modal.first.click(timeout=3000)
                        
                        # Aguarda o modal desaparecer
                        page.locator(".modal.show").wait_for(state="hidden", timeout=5000)
                        
                    except Exception as e:
                        # Caso não consiga fechar o modal normalmente,
                        # aguarda um pequeno intervalo antes de continuar
                        page.wait_for_timeout(500)
                    
                    # Conta quantos elementos de backdrop do modal ainda existem na página  
                    backdrop_count = page.locator(".modal-backdrop").count()
                    
                    # Caso ainda exista algum backdrop, remove os elementos diretamente através de JavaScript
                    if backdrop_count > 0:
                        page.evaluate("""
                            document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
                            document.body.classList.remove('modal-open');
                            document.body.style.removeProperty('padding-right');
                            document.body.style.removeProperty('overflow');
                        """)

            finally:
                # Aguarda um intervalo aleatório antes de iniciar a próxima pesquisa
                page.wait_for_timeout(random.randint(1500, 3500))
    
    try:
        # Encerra o processo do Chrome iniciado pela automação
        processo_chrome.terminate()
        
        # Aguarda até 5 segundos para que o processo seja encerrado
        processo_chrome.wait(timeout=5)
    except:
        # Caso o processo não seja encerrado normalmente,
        # força o encerramento do Chrome
        processo_chrome.kill()
    
    # Converte a lista de resultados em um DataFrame do Pandas         
    resultado_busca = pd.DataFrame(resultados)
    
    # Retorna o DataFrame contendo os resultados da coleta
    return resultado_busca

# Permite executar este módulo individualmente para realizar testes
# sem precisar executar o programa principal
if __name__ == "__main__":

    # Define uma lista de códigos para utilizar no teste
    codigos = ["1234", "2345678"]
    
    # Executa a função de coleta passando os códigos definidos acima
    resultado = executar(codigos)
    
    # Exibe o DataFrame retornado pela função
    print(resultado)
    
