from playwright.sync_api import sync_playwright
import random
import os
from dotenv import load_dotenv
import subprocess
import time
import logging
import pandas as pd
from functions import get_campo_busca, get_botao_buscar
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

def executar(codigos):
    
    resultados = []
    chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    profile = r"C:\Users\imercado2\chrome_profile_pellegrino"
    debug_port = 9222

    load_dotenv()

    USUARIO = os.getenv("PELLEGRINO_USER")
    SENHA = os.getenv("PELLEGRINO_PASSWORD")

    with sync_playwright() as p:
        
        processo_chrome = subprocess.Popen([
            chrome,
            f"--user-data-dir={profile}",
            f"--remote-debugging-port={debug_port}"
        ])
        
        time.sleep(3)

        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{debug_port}")

        context = browser.contexts[0]
        page = context.pages[0]

        page.goto("https://compreonline.pellegrino.com.br/Account/Login/?ReturnUrl=%2F")
        page.wait_for_load_state('domcontentloaded')

        if "/Account/Login/" in page.url:
            usuario = page.locator("#username")
            usuario.wait_for()
            usuario.click()
            page.wait_for_timeout(random.randint(1000, 2000))
            usuario.fill(USUARIO)

            senha = page.locator("#password")
            senha.click()
            page.wait_for_timeout(random.randint(1000, 2000))
            senha.fill(SENHA)

            page.wait_for_timeout(random.randint(2000, 3500))

            entrar = page.get_by_role("button", name="Entrar")
            entrar.click()
        else:
            print("Usuario Logado!")

        for codigo in codigos:

            try:
                busca = get_campo_busca(page)
                busca.click()
                page.wait_for_timeout(random.randint(1500, 3500))
                busca.fill(codigo)
                page.wait_for_timeout(random.randint(1500, 3500))

                clique_buscar = get_botao_buscar(page)
                
                
                with page.expect_response(lambda r: "algolia.net" in r.url.lower() and "/queries" in r.url.lower(),timeout=10000) as resp_info:
                    clique_buscar.click()
                
                page.wait_for_timeout(500)
                    
                nao_encontrado = page.locator('#hits .dataTables_empty')

                if nao_encontrado.is_visible():
                    logging.info(f"Pellegrino: {codigo} NÃO ENCONTRADO")
                    resultados.append({
                        "fornecedor": "PELLEGRINO",
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

                produtos = page.locator("#hits tr.odd, #hits tr.even")
                produtos.first.wait_for(state="attached", timeout=5000)

                count = produtos.count()
                
                try:
                    prazo = page.locator('span#page-header-cpgto-abrev').inner_text(timeout=1500).strip()
                except:
                    prazo = None

                for i in range(count):
                    card = produtos.nth(i)
                    
                    try:
                        fabricante = card.locator('span.w-125px').inner_text(timeout=1500).strip()
                    except:
                        fabricante = None
                        
                    popover_trigger = card.locator("[data-toggle='popover']")
                    popover_trigger.click()
                    
                    page.wait_for_timeout(1000)
                
                    try:
                        page.wait_for_load_state("networkidle", timeout=5000)
                    except PlaywrightTimeoutError:
                        pass
                    
                    try:
                        descricao = card.locator('span.mb-0').inner_text(timeout=1500).strip()

                    except Exception as e:
                        descricao = None

                    
                    try:
                        info_dict = {}
                        tabelas = page.locator('#container-pdp-ficha table.info-table')
                        total_tabelas = tabelas.count()
                        for t in range(total_tabelas):
                            linhas = tabelas.nth(t).locator('tbody tr')
                            total_linhas = linhas.count()

                            for j in range(total_linhas):
                                tds = linhas.nth(j).locator('td')
                                if tds.count() >= 2:
                                    label = tds.nth(0).inner_text().strip()
                                    valor = tds.nth(1).inner_text().strip()
                                    info_dict[label] = valor

                        cod_fabricante = info_dict.get("Código do Fabricante")

                    except Exception:
                        info_dict = {}
                        cod_fabricante = None
                        
                    try:
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
                        dados_filiais = []

                    if not dados_filiais:
                        resultados.append({
                            "fornecedor": "PELLEGRINO",
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
                        for item in dados_filiais:
                            resultados.append({
                                "fornecedor": "PELLEGRINO",
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
                        fechar_modal = page.locator(".modal.show .modal-header button.close")
                        fechar_modal.first.click(timeout=3000)
                        page.locator(".modal.show").wait_for(state="hidden", timeout=5000)
                    except Exception as e:
                        #print(">>> ERRO ao fechar modal:", e)
                        page.wait_for_timeout(500)
                        
                    backdrop_count = page.locator(".modal-backdrop").count()
                    #print(">>> Backdrops restantes:", backdrop_count)
                    #print(">>> Classes do body:", page.locator("body").get_attribute("class"))
                    
                    if backdrop_count > 0:
                        page.evaluate("""
                            document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
                            document.body.classList.remove('modal-open');
                            document.body.style.removeProperty('padding-right');
                            document.body.style.removeProperty('overflow');
                        """)
                    #print(">>> Backdrop removido via JS")

            finally:
                page.wait_for_timeout(random.randint(1500, 3500))
    
    try:
        processo_chrome.terminate()
        processo_chrome.wait(timeout=5)
    except:
        processo_chrome.kill()
               
    resultado_busca = pd.DataFrame(resultados)

    return resultado_busca


if __name__ == "__main__":

    codigos = ["ECO1651", "VC-232"]
    resultado = executar(codigos)
    print(resultado)
    
    teste = pd.DataFrame(resultado)
    
    print(teste)