# ✈️ Flight Hunter Pro 2026

Um monitor inteligente de passagens aéreas desenvolvido em **Python** para rodar em servidores domésticos (Mini PC / Raspberry Pi). O sistema combina monitoramento social em tempo real com buscas técnicas sistemáticas para encontrar "pérolas" e erros de tarifa.

## 🚀 Funcionalidades

- **Social Miner:** Monitora canais de promoções no Telegram em tempo real via Telethon (API de Usuário).
- **Multi-Provider Search:** Integração com **Duffel API** (direto com cias aéreas) e **Skyscanner** (via Web Scraping com Playwright).
- **Inteligência de Preços:** Banco de dados **SQLite** integrado para evitar notificações duplicadas e registrar o histórico de quedas de preço.
- **Filtros Dinâmicos:** Configuração total via `config.json` (destinos, teto de preço e palavras-chave).
- **Notificações Push:** Alertas instantâneos via Telegram Bot.

## 🛠️ Estrutura do Projeto

```text
flight-hunter-pro/
├── data/               # Banco SQLite e Logs de execução
├── providers/          # Módulos de busca (Duffel, Skyscanner, Social Miner)
├── utils/              # Notificador, Loader de Config e Banco de Dados
├── .env                # Chaves de API e Tokens (Privado)
├── config.json         # Definição de rotas e preferências
├── main.py             # Orquestrador assíncrono principal
└── requirements.txt    # Dependências do projeto
```

## 🔧 Instalação e Configuração

# 1. Requisitos

Python 3.10+

Playwright (para o scraper do Skyscanner)

# 2. Instalação

# Clone o repositório e entre na pasta

cd flight-hunter-pro

# Crie e ative o ambiente virtual

python3 -m venv venv
source venv/bin/activate

# Instale as dependências

pip install -r requirements.txt
playwright install chromium

# 3. Configuração do .env

Crie um arquivo .env na raiz e preencha com suas credenciais:
TELEGRAM_TOKEN=seu_bot_token
TELEGRAM_CHAT_ID=seu_chat_id
TELEGRAM_API_ID=seu_api_id
TELEGRAM_API_HASH=seu_api_hash
DUFFEL_TOKEN=seu_duffel_token

# 4. Personalização das Rotas

Edite o config.json para adicionar seus destinos de interesse e o preço máximo que deseja pagar.

## 🖥️ Execução

Para rodar o monitor 24/7 no seu servidor:
python3 main.py

## 📈 Melhorias Futuras

[ ] Implementação de dashboard para visualizar o histórico do SQLite
[ ] Integração com buscador de passagens por milhas.
[ ] Dockerização do projeto para facilitar o deploy.

Desenvolvido para fins de estudo e monitoramento pessoal de viagens.

---
