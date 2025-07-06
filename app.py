# App para Day trade Analytics em tempo real

import re
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from phi.agent import Agent
from phi.model.groq  import Groq
#from phi.model.openai import OpenAI
from phi.model.anthropic import Claude
from phi.tools.yfinance import YFinanceTools
from phi.tools.duckduckgo import DuckDuckGo
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Usa o cache do Streamlit para melhorar a performance
@st.cache_data

# Define a função para obter os dados do Yahoo Finance
def js_get_stock_data(ticker, period='6mo'):

    # Cria um objeto ticker do Yahoo Fiance para a ação espedificada
    stock = yf.Ticker(ticker)

    # Obtém os dados históricos do preço da ação para o periodo definido
    hist = stock.history(period=period)

    # Reseta o índice do DataFrame para transformar a coluna de data em uma coluna normal
    hist.reset_index(inplace=True)

    # Retorna o DataFrame com os dados históricos    
    return hist

# Define a função para plotar o preço das ações com base no histórico fornecido
def js_plot_stock_price(hist, ticker):
    # Cria um gráfico de linha interativo usando Plotly Express
    # O eixo X representa a data e o eixo Y representa o preço de fechamento das ações
    # O título do gráfico inclui o ticker da ação e o período de análise
    fig = px.line(hist, x="Date", y="Close", title=f"{ticker} Preços das Ações (Últimos 6 Meses)", markers=True)
    
    # Exibe o gráfico no Streamlit
    st.plotly_chart(fig)

# Define a função para plotar um gráfico de candlestick com base no histórico fornecido
def js_plot_candlestick(hist, ticker):

    # Cria um objeto Figure do Plotly para armazenar o gráfico
    fig = go.Figure(

        # Adiciona um gráfico de candlestick com os dados do histórico da ação
        data=[go.Candlestick(x=hist['Date'],        # Define as datas no eixo X
                             open=hist['Open'],     # Define os preços de abertura
                             high=hist['High'],     # Define os preços mais altos
                             low=hist['Low'],       # Define os preços mais baixos
                             close=hist['Close'])]  # Define os preços de fechamento
    )
    
    # Atualiza o layout do gráfico, incluindo um título dinâmico com o ticker da ação
    fig.update_layout(title=f"{ticker} Candlestick Chart (Últimos 6 Meses)")
    
    # Exibe o gráfico no Streamlit
    st.plotly_chart(fig)

# Define a função para plotar médias móveis com base no histórico fornecido
def js_plot_media_movel(hist, ticker):

    # Calcula a Média Móvel Simples (SMA) de 20 períodos e adiciona ao DataFrame
    hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
    
    # Calcula a Média Móvel Exponencial (EMA) de 20 períodos e adiciona ao DataFrame
    hist['EMA_20'] = hist['Close'].ewm(span=20, adjust=False).mean()
    
    # Cria um gráfico de linha interativo usando Plotly Express
    # Plota os preços de fechamento, a SMA de 20 períodos e a EMA de 20 períodos
    fig = px.line(hist, 
                  x='Date', 
                  y=['Close', 'SMA_20', 'EMA_20'],
                  title=f"{ticker} Médias Móveis (Últimos 6 Meses)",  # Define o título do gráfico
                  labels={'value': 'Price (USD)', 'Date': 'Date'})    # Define os rótulos dos eixos
    
    # Exibe o gráfico no Streamlit
    st.plotly_chart(fig)

# Define a função para plotar o volume de negociação da ação com base no histórico fornecido
def js_plot_volume(hist, ticker):

    # Cria um gráfico de barras interativo usando Plotly Express
    # O eixo X representa a data e o eixo Y representa o volume negociado
    fig = px.bar(hist, 
                 x='Date', 
                 y='Volume', 
                 title=f"{ticker} Trading Volume (Últimos 6 Meses)")  # Define o título do gráfico
    
    # Exibe o gráfico no Streamlit
    st.plotly_chart(fig)

########## Configuração de Modelos ##########

def js_create_model(provider, model_name, api_key=None):
    """
    Cria o modelo de IA baseado no provedor selecionado
    """
    if provider == "Groq":
        return Groq(id=model_name)
    elif provider == "Claude/Anthropic":
        if api_key:
            # Define a API key no ambiente se fornecida
            os.environ["ANTHROPIC_API_KEY"] = api_key
        return Claude(id=model_name)
    else:
        # Fallback para Groq
        return Groq(id="deepseek-r1-distill-llama-70b")

########## Agentes de IA ##########

def js_create_agents(provider, model_name, api_key=None):
    """
    Cria os agentes de IA baseados no provedor selecionado
    """
    # Modelo principal para agentes especializados
    main_model = js_create_model(provider, model_name, api_key)
    
    # Modelo para o agente coordenador (sempre usa um modelo versátil)
    if provider == "Claude/Anthropic":
        coord_model = Claude(id="claude-3-5-sonnet-20241022")
    else:
        coord_model = Groq(id="llama-3.3-70b-versatile")
    
    # Agente de busca web
    web_search_agent = Agent(name="JonhSelmo DayTrade Agente Web Search",
                             role="Fazer busca na web",
                             model=main_model,
                             tools=[DuckDuckGo()],
                             instructions=["Sempre inclua as fontes"],
                             show_tool_calls=True, markdown=True)

    # Agente financeiro
    finance_agent = Agent(name="JonhSelmo Agente Financeiro",
                          model=main_model,
                          tools=[YFinanceTools(stock_price=True,
                                               analyst_recommendations=True,
                                               stock_fundamentals=True,
                                               company_news=True)],
                          instructions=["Use tabelas para mostrar os dados"],
                          show_tool_calls=True, markdown=True)

    # Agente coordenador multi-AI
    multi_ai_agent = Agent(team=[web_search_agent, finance_agent],
                           model=coord_model,
                           instructions=["Sempre inclua as fontes", "Use tabelas para mostrar os dados"],
                           show_tool_calls=True, markdown=True)
    
    return multi_ai_agent

########## App Web ##########

# Configuração da página do Streamlit
st.set_page_config(page_title="JONH DAY TRADE", page_icon="🤖", layout="wide")

# Barra Lateral com abas
st.sidebar.title("Configurações")

# Criação das abas na sidebar
sidebar_tab1, sidebar_tab2 = st.sidebar.tabs(["📋 Instruções", "⚙️ Configuração"])

with sidebar_tab1:
    st.markdown("""
    ### Como Utilizar a App:

    1. **Configure a API** na aba "Configuração"
    2. Insira o símbolo do ticker da ação desejada
    3. Clique no botão **Analisar** para análise em tempo real

    ### Exemplos de tickers válidos:
    - MSFT (Microsoft)
    - TSLA (Tesla)
    - AMZN (Amazon)
    - GOOG (Alphabet)

    Mais tickers podem ser encontrados aqui: https://stockanalysis.com/list/nasdaq-stocks/

    ### Finalidade da App:
    Este aplicativo realiza análises avançadas de preços de ações da Nasdaq em tempo real utilizando Agentes de IA com modelos DeepSeek (via Groq) ou Claude (Anthropic) para apoio a estratégias de Day Trade para monetização.
    """)
    
    # Botão de suporte
    if st.button("Suporte"):
        st.write("No caso de dúvidas envie e-mail para: suporte@datascienceacademy.com.br")

with sidebar_tab2:
    st.markdown("### Provedor de IA")
    
    # Seleção do provedor
    provider = st.selectbox(
        "Selecione o Provedor:",
        ["Groq", "Claude/Anthropic"],
        index=0,
        key="provider_select"
    )
    
    # Configuração baseada no provedor selecionado
    if provider == "Groq":
        st.info("🔧 **Groq** - Usando variáveis de ambiente")
        
        model_options = [
            "deepseek-r1-distill-llama-70b",
            "llama-3.3-70b-versatile",
            "llama-3.1-70b-versatile",
            "mixtral-8x7b-32768"
        ]
        
        selected_model = st.selectbox(
            "Modelo:",
            model_options,
            index=0,
            key="groq_model_select"
        )
        
        st.markdown("""
        **Instruções:**
        - Configure `GROQ_API_KEY` no arquivo `.env`
        - Modelos com alta performance
        """)
        
        api_key_input = None
        
    elif provider == "Claude/Anthropic":
        st.info("🧠 **Claude/Anthropic** - IA Avançada")
        
        model_options = [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229"
        ]
        
        selected_model = st.selectbox(
            "Modelo:",
            model_options,
            index=0,
            key="claude_model_select"
        )
        
        # Campo para API key
        api_key_input = st.text_input(
            "API Key:",
            type="password",
            placeholder="sk-ant-api03-...",
            help="Insira sua chave da Anthropic",
            key="claude_api_key"
        )
        
        st.markdown("""
        **Instruções:**
        - API key: https://console.anthropic.com/
        - Análises mais detalhadas
        - Melhor compreensão contextual
        """)
        
        if not api_key_input:
            st.warning("⚠️ Insira sua API Key da Anthropic")
    
    # Salvar configurações na sessão
    st.session_state['provider'] = provider
    st.session_state['model_name'] = selected_model
    st.session_state['api_key'] = api_key_input
    
    # Botão para testar configuração
    if st.button("🧪 Testar", key="test_config"):
        try:
            if provider == "Claude/Anthropic" and not api_key_input:
                st.error("❌ API Key obrigatória!")
            else:
                test_model = js_create_model(provider, selected_model, api_key_input)
                st.success(f"✅ Configuração OK!")
                st.info(f"🤖 {provider} - {selected_model}")
        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")

# Título principal
st.title("📊 JONH - Jointed Organization of Not-neural Humans")

# Interface principal
st.header("Day Trade Analytics em Tempo Real com Agentes de IA")

# Mostrar configuração atual
current_provider = st.session_state.get('provider', 'Groq')
current_model = st.session_state.get('model_name', 'deepseek-r1-distill-llama-70b')

# Status da configuração
if current_provider == "Claude/Anthropic":
    has_api_key = bool(st.session_state.get('api_key'))
    if has_api_key:
        st.success(f"🤖 **Configuração Ativa:** {current_provider} - {current_model}")
    else:
        st.warning(f"⚠️ **Configuração Incompleta:** {current_provider} - Configure API Key na sidebar")
else:
    st.success(f"🤖 **Configuração Ativa:** {current_provider} - {current_model}")

# Caixa de texto para input do usuário
ticker = st.text_input("Digite o Código (símbolo do ticker):").upper()

# Se o usuário pressionar o botão, entramos neste bloco
if st.button("Analisar"):

    # Verificar se Claude está configurado corretamente
    if st.session_state.get('provider') == 'Claude/Anthropic' and not st.session_state.get('api_key'):
        st.error("❌ Por favor, configure sua API Key da Anthropic na sidebar → Configuração")
        st.stop()

    # Se temos o código da ação (ticker)
    if ticker:

        # Inicia o processamento
        with st.spinner("Buscando os Dados em Tempo Real. Aguarde..."):
            
            try:
                # Obtém os dados
                hist = js_get_stock_data(ticker)
                
                # Cria os agentes com a configuração atual
                multi_ai_agent = js_create_agents(
                    st.session_state.get('provider', 'Groq'),
                    st.session_state.get('model_name', 'deepseek-r1-distill-llama-70b'),
                    st.session_state.get('api_key')
                )
                
                # Renderiza um subtítulo
                st.subheader("Análise Gerada Por IA")
                
                # Executa o time de Agentes de IA
                ai_response = multi_ai_agent.run(f"Resumir a recomendação do analista e compartilhar as últimas notícias para {ticker}")

                # Remove linhas que começam com "Running:"
                # Remove o bloco "Running:" e também linhas "transfer_task_to_finance_ai_agent"
                clean_response = re.sub(r"(Running:[\s\S]*?\n\n)|(^transfer_task_to_finance_ai_agent.*\n?)","", ai_response.content, flags=re.MULTILINE).strip()

                # Imprime a resposta
                st.markdown(clean_response)

                # Renderiza os gráficos
                st.subheader("Visualização dos Dados")
                js_plot_stock_price(hist, ticker)
                js_plot_candlestick(hist, ticker)
                js_plot_media_movel(hist, ticker)
                js_plot_volume(hist, ticker)
                
            except Exception as e:
                st.error(f"❌ Erro durante a análise: {str(e)}")
                st.info("💡 Verifique se a configuração da API está correta na sidebar")
    else:
        st.error("Ticker inválido. Insira um símbolo de ação válido.")

