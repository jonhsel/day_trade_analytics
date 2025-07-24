import streamlit as st
import pandas as pd
import hashlib
import random

# --- Funções e Classes de Suporte ---

def generate_sample_data():
    num_users = 30
    user_data = []
    for i in range(1, num_users + 1):
        email = f'user_{i}@example.com'
        email_hashed = hashlib.sha256(email.encode()).hexdigest()
        user_data.append({
            'user_id': f'user_{i}',
            'email_original': email,
            'email_hashed': email_hashed,
            'city': random.choice(['São Paulo', 'Rio de Janeiro', 'Belo Horizonte', 'Porto Alegre', 'Curitiba']),
            'clicked_ad': random.choice([True, False, False]), # Mais False para simular menos cliques
            'ad_campaign_id': random.choice(['camp_a', 'camp_b', 'camp_c'])
        })
    df_a = pd.DataFrame(user_data)

    purchase_data = []
    for i in range(5, num_users + 5): # Mais compras que cliques para criar alguma variabilidade
        email = f'user_{i}@example.com'
        email_hashed = hashlib.sha256(email.encode()).hexdigest()
        purchase_data.append({
            'user_id': f'user_b_{i}', # ID diferente para simular sistemas distintos
            'email_original': email,
            'email_hashed': email_hashed,
            'purchased': random.choice([True, True, False]), # Mais True para simular mais compras
            'purchase_value': round(random.uniform(10.0, 500.0), 2)
        })
    df_b = pd.DataFrame(purchase_data)
    return df_a, df_b

# --- Simulated Data Clean Room (DCR) V2.0 ---
class SimulatedDataCleanRoom:
    def __init__(self, data_a: pd.DataFrame, data_b: pd.DataFrame):
        self.data_a = data_a[['email_hashed', 'clicked_ad', 'ad_campaign_id', 'city']]
        self.data_b = data_b[['email_hashed', 'purchased', 'purchase_value']]
        st.success("DCR inicializada com sucesso. Pronta para receber consultas.")

    def execute_query(self, query_sql: str):
        """
        Simula a execução de uma consulta SQL na DCR.
        Implementa regras de segurança para evitar vazamento de dados.
        """
        st.info(f"DCR: Tentando executar a consulta SQL: \n```sql\n{query_sql}\n```")

        # Regras de segurança: Não permitir SELECT * ou seleção de IDs/hashes diretos
        if "SELECT *" in query_sql.upper() or "SELECT EMAIL_HASHED" in query_sql.upper() or "SELECT USER_ID" in query_sql.upper():
            return {"error": "Consulta violou as regras de privacidade: não é permitido selecionar dados brutos ou identificadores diretos."}
        
        try:
            # Simular JOIN e filtros
            merged_data = pd.merge(
                self.data_a,
                self.data_b,
                on='email_hashed',
                how='inner' # Focamos na interseção para análise de campanha
            )
            
            # Adaptação para simular parsing de SQL e execução
            # Este é o ponto onde um parser SQL real e um motor de banco de dados estariam
            # Para este exemplo, faremos um parsing MUITO simplificado do SQL
            
            # Exemplo de parsing para COUNT
            if "COUNT(DISTINCT email_hashed)" in query_sql.upper() and "WHERE T1.CLICKED_AD = TRUE AND T2.PURCHASED = TRUE" in query_sql.upper():
                result_df = merged_data[(merged_data['clicked_ad'] == True) & (merged_data['purchased'] == True)]
                return {"type": "count", "value": len(result_df)}
            
            # Exemplo de parsing para SUM de purchase_value
            elif "SUM(T2.PURCHASE_VALUE)" in query_sql.upper() and "WHERE T1.CLICKED_AD = TRUE AND T2.PURCHASED = TRUE" in query_sql.upper():
                result_df = merged_data[(merged_data['clicked_ad'] == True) & (merged_data['purchased'] == True)]
                if not result_df.empty:
                    return {"type": "sum_value", "value": round(result_df['purchase_value'].sum(), 2)}
                else:
                    return {"type": "sum_value", "value": 0.0}

            # Exemplo de parsing para contagem por cidade (agrupamento)
            elif "COUNT(DISTINCT email_hashed)" in query_sql.upper() and "GROUP BY T1.CITY" in query_sql.upper() and "WHERE T1.CLICKED_AD = TRUE AND T2.PURCHASED = TRUE" in query_sql.upper():
                result_df = merged_data[(merged_data['clicked_ad'] == True) & (merged_data['purchased'] == True)]
                if not result_df.empty:
                    city_counts = result_df['city'].value_counts().to_dict()
                    return {"type": "city_distribution", "value": city_counts}
                else:
                    return {"type": "city_distribution", "value": {}}
            
            # Caso a consulta não seja reconhecida ou não siga o padrão esperado
            return {"error": "Consulta SQL não suportada pela DCR simulada ou formato incorreto. Certifique-se de usar `T1` para dados do anunciante e `T2` para dados do varejista."}

        except Exception as e:
            return {"error": f"Erro inesperado durante a execução da consulta: {str(e)}"}

# --- Agentes de IA Aprimorados (Simulando LLMs) ---

class QueryGenerationAgent:
    def generate_query(self, business_goal: str) -> dict:
        """
        Simula um agente de IA (LLM) que gera a consulta SQL para a DCR
        baseado em objetivos de negócio mais complexos.
        Retorna um dicionário com 'query' e 'explanation'.
        """
        st.markdown(f"**Agente de Geração de Consulta (IA/LLM):** Analisando o objetivo: '{business_goal}'")
        query = ""
        explanation = ""

        goal_lower = business_goal.lower()

        if "contar usuarios que clicaram e compraram" in goal_lower or "eficacia da campanha" in goal_lower:
            query = """
            SELECT COUNT(DISTINCT T1.email_hashed)
            FROM Table_A T1
            JOIN Table_B T2 ON T1.email_hashed = T2.email_hashed
            WHERE T1.clicked_ad = TRUE AND T2.purchased = TRUE;
            """
            explanation = "Esta consulta contará o número de usuários únicos que tanto clicaram no anúncio (da Empresa A) quanto realizaram uma compra (na Empresa B), correlacionando os dados via hash de e-mail."
        elif "valor total de vendas de usuarios que clicaram" in goal_lower or "receita gerada por cliques" in goal_lower:
            query = """
            SELECT SUM(T2.purchase_value)
            FROM Table_A T1
            JOIN Table_B T2 ON T1.email_hashed = T2.email_hashed
            WHERE T1.clicked_ad = TRUE AND T2.purchased = TRUE;
            """
            explanation = "Esta consulta somará o valor de todas as compras realizadas por usuários que clicaram nos anúncios e efetuaram uma compra. Isso permite medir a receita gerada pela campanha."
        elif "distribuicao geografica" in goal_lower and "clicaram e compraram" in goal_lower:
            query = """
            SELECT T1.city, COUNT(DISTINCT T1.email_hashed)
            FROM Table_A T1
            JOIN Table_B T2 ON T1.email_hashed = T2.email_hashed
            WHERE T1.clicked_ad = TRUE AND T2.purchased = TRUE
            GROUP BY T1.city;
            """
            explanation = "Esta consulta mostrará a contagem de usuários que clicaram e compraram, agrupados por cidade. Isso ajuda a entender a performance da campanha em diferentes regiões."
        else:
            explanation = "Não consegui gerar uma consulta para este objetivo. Tente ser mais específico, por exemplo, sobre contagem de usuários que clicaram e compraram, valor total de vendas, ou distribuição geográfica."
            return {"query": None, "explanation": explanation}
        
        st.code(query, language='sql')
        st.info(f"**Agente de Geração de Consulta:** {explanation}")
        return {"query": query, "explanation": explanation}

class ResultAnalysisAgent:
    def analyze_results(self, dcr_result: dict, original_goal: str) -> str:
        """
        Simula um agente de IA (LLM) que analisa os resultados da DCR
        e gera insights mais ricos e sugestões de próximos passos.
        """
        st.markdown(f"**Agente de Análise de Resultados (IA/LLM):** Interpretando os resultados da DCR para o objetivo '{original_goal}'...")

        if "error" in dcr_result:
            st.error(f"**Erro na Análise:** A DCR retornou um erro - {dcr_result['error']}. Não foi possível gerar insights.")
            return "Sugestão: Verifique a consulta gerada pelo Agente de Geração ou reformule o objetivo de negócio."
        
        result_type = dcr_result.get("type")
        result_value = dcr_result.get("value")

        if result_type == "count":
            count = result_value
            st.success(f"**Insight Gerado:** Identificamos **{count}** usuários únicos que tanto clicaram em seus anúncios quanto realizaram uma compra. Isso é um forte indicador de que a campanha está gerando **conversões diretas**.")
            if count > 0:
                return "Recomendação: Considere aprofundar a análise na jornada desses usuários para otimizar os pontos de conversão. Talvez analisar o valor médio de compra para este grupo?"
            else:
                return "Recomendação: Nenhuma conversão direta foi identificada. Revise a segmentação da campanha, a criatividade do anúncio ou a experiência do usuário após o clique."
        
        elif result_type == "sum_value":
            total_value = result_value
            st.success(f"**Insight Gerado:** O valor total de vendas atribuíveis aos usuários que clicaram e compraram é de **R$ {total_value:.2f}**. Isso representa a receita direta gerada pela campanha.")
            return "Recomendação: Compare este valor com o custo da campanha para calcular o ROI. Além disso, investigue se há um padrão nos produtos comprados por esses usuários para otimizar futuras ofertas."
        
        elif result_type == "city_distribution":
            city_data = result_value
            if city_data:
                st.success(f"**Insight Gerado:** A distribuição geográfica dos usuários que clicaram e compraram é a seguinte: {city_data}.")
                top_city = max(city_data, key=city_data.get)
                st.info(f"**Destaque:** A cidade de **{top_city}** foi a que mais contribuiu com conversões diretas.")
                return f"Recomendação: Considere otimizar as campanhas de marketing para segmentar melhor as regiões com maior desempenho, como {top_city}, e investigar por que outras regiões tiveram menor engajamento."
            else:
                st.warning("Não foram encontradas conversões diretas para análise de distribuição geográfica.")
                return "Recomendação: Verifique se há dados suficientes para a análise de distribuição ou se a campanha gerou conversões."
        
        else:
            st.warning("Tipo de resultado não reconhecido. Não foi possível gerar um insight detalhado.")
            return "Recomendação: A consulta pode ter retornado um formato inesperado. Verifique a saída da DCR."

# --- Interface do Streamlit ---

st.set_page_config(layout="wide", page_title="Simulação de Data Clean Room com Agentes de IA (Avançado)")

st.title("Simulação de Data Clean Room (DCR) com Agentes de IA (V2.0)")
st.markdown("Esta versão demonstra **agentes de IA mais inteligentes** (simulando LLMs) e uma DCR capaz de **mais tipos de consultas agregadas**, sempre priorizando a privacidade.")

# --- Seção 1: Simulação dos Dados Iniciais ---
st.header("1. Simulação e Visualização dos Dados Iniciais")
st.markdown("Geramos dados de exemplo para o Anunciante (Empresa A) e para o Varejista (Empresa B).")
st.info("Lembre-se: os dados originais (email_original, user_id) NUNCA são compartilhados. A DCR opera apenas com os **hashes**.")

df_empresa_a, df_empresa_b = generate_sample_data()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Dados da Empresa A (Anunciante - Cliques)")
    st.dataframe(df_empresa_a[['email_original', 'email_hashed', 'clicked_ad', 'ad_campaign_id', 'city']], height=200)

with col2:
    st.subheader("Dados da Empresa B (Varejista - Compras)")
    st.dataframe(df_empresa_b[['email_original', 'email_hashed', 'purchased', 'purchase_value']], height=200)

st.markdown("---")

# --- Seção 2: A Data Clean Room e a Interação dos Agentes (Avançado) ---
st.header("2. A DCR e a Interação dos Agentes (LLM-Powered)")
st.markdown("Digite seu objetivo de negócio em linguagem natural. O **Agente de Geração de Consulta** "
            "tentará traduzir isso para uma consulta SQL segura para a DCR. "
            "A **DCR** executará a consulta de forma agregada. O **Agente de Análise** "
            "interpretará os resultados e fornecerá insights e recomendações.")

dcr = SimulatedDataCleanRoom(df_empresa_a, df_empresa_b)
query_agent = QueryGenerationAgent()
analysis_agent = ResultAnalysisAgent()

business_objective_examples = [
    "Quantos usuários que clicaram nos anúncios também fizeram uma compra?",
    "Qual o valor total de vendas gerado por usuários que clicaram nos anúncios e compraram?",
    "Quero ver a distribuição geográfica dos usuários que clicaram e compraram.",
    "Mostre-me todos os emails dos usuários." # Exemplo de consulta não permitida
]

selected_objective = st.selectbox(
    "Ou selecione um objetivo de exemplo:",
    [""] + business_objective_examples
)

custom_objective = st.text_area(
    "Ou digite seu próprio objetivo de negócio aqui:",
    value=selected_objective,
    height=100
)

st.write("---")

if st.button("Executar Análise na DCR com Agentes de IA"):
    if not custom_objective:
        st.warning("Por favor, insira ou selecione um objetivo de negócio.")
    else:
        st.subheader("Fluxo da Análise:")
        
        st.write("1. **Agente de Geração de Consulta** recebe o objetivo:")
        st.code(custom_objective, language='text')
        
        # Agente de Geração de Consulta atua (simulando LLM)
        st.spinner("Agente de Geração de Consulta pensando...")
        agent_query_output = query_agent.generate_query(custom_objective)
        
        generated_query_sql = agent_query_output["query"]
        
        if generated_query_sql:
            st.write("2. **DCR** recebe e executa a consulta:")
            st.spinner("DCR processando dados de forma segura...")
            dcr_output = dcr.execute_query(generated_query_sql)
            
            if "error" in dcr_output:
                st.error(f"**DCR retornou um erro:** {dcr_output['error']}")
            else:
                st.markdown(f"**Resultado Agregado da DCR (Privado):** `{dcr_output}`")

                st.write("3. **Agente de Análise de Resultados** interpreta e gera insights:")
                st.spinner("Agente de Análise de Resultados gerando insights...")
                insight = analysis_agent.analyze_results(dcr_output, custom_objective)
                st.markdown(f"**Recomendação Final:** {insight}")
        else:
            st.warning(f"Agente de Geração de Consulta não conseguiu formular uma consulta válida. {agent_query_output['explanation']}")
            st.info("Tente reformular o objetivo. Em um LLM real, ele poderia pedir esclarecimentos.")

st.markdown("---")
st.info("Este é um modelo simulado. Em sistemas reais, a DCR usaria **criptografia avançada (MPC, FHE)** e os agentes de IA seriam LLMs orquestrados para lidar com complexidade e garantir segurança.")


