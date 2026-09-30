# Coletor de Preços

Aplicação desenvolvida em Python para automação da coleta de preços de produtos em diferentes portais de fornecedores, centralizando os resultados em uma estrutura padronizada para posterior análise e comparação.

O projeto utiliza **Playwright** para automação da navegação web, **Pandas** para processamento dos dados e **Streamlit** como interface para execução e acompanhamento das coletas.

> **Nota:** Este repositório é uma versão anonimizada do projeto original. Informações proprietárias, credenciais, URLs, dados comerciais e arquivos internos foram removidos ou substituídos.

---

## Sobre o projeto

A comparação de preços entre diferentes fornecedores pode envolver uma quantidade significativa de consultas manuais, principalmente quando os produtos precisam ser pesquisados em diferentes portais, cada um com estruturas e comportamentos próprios.

O objetivo do projeto é automatizar esse processo, permitindo:

* selecionar os fornecedores que serão consultados;
* selecionar uma ou várias filiais;
* executar pesquisas automaticamente;
* localizar os produtos nos portais;
* extrair informações de preço;
* padronizar os resultados;
* registrar erros e ocorrências;
* acompanhar o progresso da execução;
* preservar o andamento da coleta por meio de checkpoints;
* gerar uma base consolidada para análise posterior.

O projeto foi desenvolvido com uma arquitetura modular, permitindo que cada fornecedor possua seu próprio processo de coleta sem comprometer a estrutura geral da aplicação.

---

## Funcionalidades

### Coleta automatizada

A aplicação utiliza automação de navegador para acessar os portais dos fornecedores e realizar as pesquisas necessárias.

O fluxo geral pode ser representado como:

```text
Seleção de fornecedores
        ↓
Seleção de filiais
        ↓
Inicialização da coleta
        ↓
Acesso ao portal
        ↓
Localização do produto
        ↓
Extração das informações
        ↓
Tratamento e padronização
        ↓
Registro do resultado
        ↓
Consolidação dos dados
```

---

### Múltiplos fornecedores

A arquitetura foi desenvolvida para trabalhar com diferentes portais, mantendo a lógica específica de cada fornecedor isolada em seu respectivo módulo.

Cada coletor pode implementar particularidades como:

* autenticação;
* navegação;
* pesquisa de produtos;
* tratamento de resultados;
* identificação de fabricante;
* extração de preço;
* tratamento de produtos não encontrados;
* tratamento de erros específicos do portal.

Essa separação permite adicionar ou alterar um fornecedor sem precisar modificar toda a aplicação.

---

### Seleção de filiais

A interface permite selecionar:

* uma filial específica;
* múltiplas filiais;
* todas as filiais;
* nenhuma filial, conforme a lógica de execução configurada.

Essa funcionalidade permite adaptar a coleta ao objetivo da análise e evitar execuções desnecessárias.

---

### Processamento dos resultados

Após a coleta, os dados são tratados e organizados em estruturas tabulares utilizando Pandas.

Entre as informações processadas estão:

* produto pesquisado;
* fornecedor;
* filial;
* fabricante;
* preço;
* status da pesquisa;
* informações de ocorrência;
* demais atributos necessários para a análise.

O processamento busca manter uma estrutura consistente mesmo quando os portais apresentam formatos diferentes.

---

### Tratamento de erros

A automação foi desenvolvida considerando que os portais podem apresentar comportamentos inesperados durante a execução.

Entre os problemas tratados estão:

* produto não localizado;
* alteração na estrutura da página;
* falha de navegação;
* timeout;
* erro de autenticação;
* indisponibilidade temporária do portal;
* informações ausentes;
* resultados inesperados.

Os eventos relevantes são registrados em log para facilitar o acompanhamento e a investigação de problemas.

---

### Logging

O projeto utiliza arquivos de log para registrar informações relacionadas à execução da coleta.

O logging permite acompanhar:

* início e término das operações;
* fornecedor em execução;
* produto processado;
* ocorrência de erros;
* exceções;
* informações relevantes para diagnóstico.

Isso reduz a necessidade de acompanhar manualmente todo o processo pelo navegador ou pela interface.

---

### Checkpoints

Como algumas coletas podem envolver milhares de consultas e levar bastante tempo para serem concluídas, o projeto possui mecanismo de checkpoint.

A ideia é preservar o progresso da execução para evitar que uma interrupção obrigue a aplicação a iniciar todo o processamento novamente.

Fluxo simplificado:

```text
Produto 1 ──✓
Produto 2 ──✓
Produto 3 ──✓
Produto 4 ──✓
Produto 5 ──✓
       ↓
Checkpoint
       ↓
Interrupção
       ↓
Retomada
       ↓
Produto 6...
```

Esse mecanismo é especialmente importante em processos de coleta de longa duração.

---

## Interface

A interface foi desenvolvida utilizando **Streamlit**, permitindo executar e acompanhar o processo sem necessidade de interação direta com o código.

Entre os recursos disponíveis estão:

* seleção de fornecedores;
* seleção de filiais;
* configuração da coleta;
* acompanhamento do processamento;
* visualização do progresso;
* apresentação dos resultados.

### Capturas de tela

> **Adicionar aqui os prints da interface.**

Exemplo de organização:

```text
docs/
└── images/
    ├── interface_principal.png
    ├── selecao_fornecedores.png
    ├── acompanhamento_coleta.png
    └── resultado_final.png
```

As imagens podem ser inseridas posteriormente nesta seção.

---

## Relatório final

Ao final da execução, os dados coletados são organizados para permitir a análise dos preços encontrados.

> **Adicionar aqui um print do relatório final.**

Sugestão:

```text
![Relatório final](docs/images/resultado_final.png)
```

---

## Arquitetura

A aplicação foi estruturada de forma modular, separando interface, orquestração, regras auxiliares, processamento e coletores.

Estrutura simplificada:

```text
Coletor-de-Precos/
│
├── app.py
├── main.py
├── ui.py
│
├── functions.py
├── transforms.py
├── db.py
├── load_db.py
├── INSERT.py
├── consulta_preco.py
│
├── Coletores/
│   ├── __init__.py
│   ├── collector_01.py
│   ├── collector_02.py
│   ├── collector_03.py
│   ├── collector_04.py
│   ├── collector_05.py
│   ├── collector_06.py
│   ├── collector_07.py
│   └── collector_08.py
│
├── testes.py
├── requirements.txt
├── .gitignore
│
└── .streamlit/
    └── config.toml
```

Os nomes dos coletores apresentados neste repositório são genéricos devido à anonimização do projeto.

---

## Responsabilidade dos principais módulos

### `app.py`

Ponto de entrada da aplicação Streamlit.

Responsável pela interface disponibilizada ao usuário e pela configuração das opções de execução.

---

### `main.py`

Responsável pela orquestração da coleta.

Coordena:

* fornecedores selecionados;
* filiais selecionadas;
* execução dos coletores;
* processamento dos resultados;
* controle do fluxo geral da aplicação.

---

### `ui.py`

Concentra componentes e funções relacionados à interface.

A separação da camada de interface facilita a manutenção e evita concentrar toda a lógica de apresentação no arquivo principal.

---

### `functions.py`

Reúne funções auxiliares utilizadas por diferentes partes do projeto.

A centralização dessas funções reduz duplicação de código e facilita a manutenção das regras compartilhadas entre os coletores.

---

### `transforms.py`

Responsável por operações de transformação e padronização dos dados coletados.

Como diferentes fornecedores podem retornar informações em formatos diferentes, essa camada ajuda a transformar os resultados em uma estrutura comum.

---

### `Coletores/`

Contém os módulos responsáveis pela automação específica de cada fornecedor.

Cada coletor implementa as particularidades necessárias para:

1. acessar o portal;
2. realizar a pesquisa;
3. localizar o produto;
4. extrair as informações;
5. tratar situações específicas;
6. devolver o resultado para o fluxo principal.

A separação por fornecedor é uma das principais características da arquitetura do projeto.

---

### `db.py`

Módulo relacionado à comunicação e operações com a camada de persistência utilizada pelo projeto.

---

### `load_db.py`

Responsável por operações relacionadas ao carregamento dos dados na estrutura de persistência.

---

### `INSERT.py`

Concentra operações de inserção utilizadas pelo projeto.

---

### `consulta_preco.py`

Reúne operações relacionadas à consulta e recuperação dos dados de preços.

---

### `testes.py`

Arquivo utilizado para testes e validações durante o desenvolvimento.

---

## Tecnologias utilizadas

### Python

Linguagem principal utilizada no desenvolvimento da aplicação.

---

### Playwright

Utilizado para automação dos navegadores e interação com os portais dos fornecedores.

Principais aplicações:

* abertura de páginas;
* preenchimento de campos;
* interação com elementos;
* pesquisa de produtos;
* navegação;
* extração de informações;
* tratamento de páginas dinâmicas.

---

### Pandas

Utilizado para manipulação e processamento dos dados coletados.

Principais aplicações:

* criação de DataFrames;
* transformação de dados;
* padronização;
* consolidação dos resultados;
* preparação dos dados para análise.

---

### Streamlit

Utilizado para construção da interface da aplicação.

Permite transformar o processo de coleta em uma aplicação interativa, reduzindo a necessidade de execução manual diretamente pelo terminal.

---

### Git / GitHub

Utilizados para versionamento e gerenciamento do código-fonte.

---

## Requisitos

* Python 3.x
* Git
* Navegador compatível com Playwright
* Dependências listadas em `requirements.txt`

As versões específicas das bibliotecas devem ser consultadas no arquivo:

```text
requirements.txt
```

---

## Instalação

Clone o repositório:

```bash
git clone https://github.com/imercado2/Coletor-de-Precos.git
```

Entre no diretório:

```bash
cd Coletor-de-Precos
```

Crie um ambiente virtual:

```bash
python -m venv .venv
```

Ative o ambiente virtual no Windows:

```bash
.venv\Scripts\activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Instale os navegadores necessários para o Playwright:

```bash
playwright install
```

---

## Configuração

Informações sensíveis não devem ser armazenadas diretamente no código-fonte.

Utilize variáveis de ambiente para informações como:

* credenciais;
* URLs privadas;
* configurações de acesso;
* parâmetros específicos do ambiente.

Um arquivo `.env.example` pode ser utilizado como referência para a configuração:

```text
# Exemplo
USUARIO=
SENHA=
URL=
```

> Os nomes das variáveis acima são apenas ilustrativos. As configurações reais utilizadas pelo projeto devem ser definidas de acordo com o ambiente de execução.

O arquivo `.env` deve permanecer fora do controle de versão.

---

## Execução

Com o ambiente virtual ativado e as dependências instaladas:

```bash
streamlit run app.py
```

A aplicação será disponibilizada pelo Streamlit para acesso pelo navegador.

---

## Fluxo de execução

De forma simplificada, a execução ocorre da seguinte maneira:

```text
                    ┌───────────────────┐
                    │     Streamlit     │
                    │      app.py       │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │   Orquestração    │
                    │      main.py      │
                    └─────────┬─────────┘
                              │
                 ┌────────────┼────────────┐
                 ▼            ▼            ▼
            Coletor A    Coletor B    Coletor C   ...
                 │            │            │
                 └────────────┼────────────┘
                              ▼
                         Playwright
                              │
                              ▼
                     Portal do fornecedor
                              │
                              ▼
                       Dados coletados
                              │
                              ▼
                    Transformação / limpeza
                              │
                              ▼
                     Persistência / saída
                              │
                              ▼
                       Relatório final
```

---

## Desafios técnicos

O desenvolvimento desse tipo de automação apresenta desafios que vão além de simplesmente realizar uma requisição HTTP.

Entre os principais desafios enfrentados no projeto estão:

### Portais diferentes

Cada fornecedor possui uma estrutura própria de navegação e pesquisa.

Por isso, não é possível utilizar uma única implementação genérica para todas as fontes.

---

### Páginas dinâmicas

Os portais utilizam elementos carregados dinamicamente, tornando necessário controlar o momento correto para interação e extração dos dados.

---

### Instabilidade

Automação web está sujeita a:

* timeouts;
* lentidão;
* alterações de página;
* indisponibilidade temporária;
* falhas de sessão;
* elementos que não aparecem conforme esperado.

O projeto foi desenvolvido considerando essas situações.

---

### Grande volume de consultas

Uma coleta pode envolver centenas ou milhares de produtos multiplicados por diferentes fornecedores e filiais.

Isso torna importantes mecanismos como:

* logging;
* checkpoints;
* tratamento de exceções;
* controle de execução;
* processamento incremental.

---

## Decisões de arquitetura

Algumas decisões importantes tomadas durante o desenvolvimento foram:

### Separação dos coletores

Cada fornecedor possui sua própria implementação.

Isso reduz o acoplamento e facilita manutenção quando um portal sofre alterações.

---

### Separação entre coleta e transformação

A extração dos dados e o tratamento posterior são responsabilidades diferentes.

Isso permite alterar regras de padronização sem necessariamente modificar a automação do navegador.

---

### Reutilização de funções

Operações comuns foram centralizadas em módulos auxiliares para reduzir duplicação.

---

### Persistência do progresso

Como algumas execuções podem ser longas, o uso de checkpoints reduz o impacto de interrupções.

---

## Desempenho

O tempo de execução depende principalmente de:

* quantidade de produtos;
* quantidade de fornecedores;
* quantidade de filiais;
* velocidade dos portais;
* tempo de resposta das páginas;
* necessidade de autenticação;
* quantidade de tentativas ocasionadas por falhas.

Em execuções de grande volume, o tempo total pode ser significativo.

Por esse motivo, o projeto prioriza confiabilidade e capacidade de retomada em vez de depender de uma única execução contínua.

---

## Segurança e anonimização

Este repositório foi preparado para publicação sem exposição de informações proprietárias.

Foram removidos ou anonimizados elementos como:

* nomes de empresas;
* URLs internas;
* credenciais;
* dados comerciais;
* bases proprietárias;
* arquivos internos;
* caminhos de diretórios específicos;
* informações que permitam identificar o ambiente original.

Credenciais e configurações sensíveis devem ser mantidas fora do código-fonte e nunca devem ser commitadas no Git.

---


## Aprendizados

O desenvolvimento do projeto proporcionou experiência prática em diferentes etapas de uma aplicação de dados automatizada:

* automação de processos web;
* Python;
* Playwright;
* Pandas;
* Streamlit;
* tratamento e transformação de dados;
* arquitetura modular;
* logging;
* tratamento de exceções;
* checkpoints;
* persistência;
* versionamento com Git;
* organização de projetos;
* desenvolvimento de interfaces para processos de dados.

Além da implementação técnica, o projeto também envolveu a necessidade de lidar com problemas reais de automação, como instabilidade de páginas, diferenças entre fornecedores, grande volume de consultas e necessidade de recuperação após interrupções.

---

## Status

**Projeto funcional / em evolução.**

A versão pública deste repositório representa uma versão anonimizada do projeto desenvolvido originalmente para automação de coleta de preços.

Novas melhorias podem ser incorporadas posteriormente conforme a evolução da arquitetura e das necessidades de automação.

---

## Autor

**Eder Iago**

Projeto desenvolvido em Python com foco em automação de coleta, processamento e análise de dados.

[GitHub](https://github.com/iago_cord)