import streamlit as st
import pdfplumber
import pandas as pd
import io
from dotenv import load_dotenv
import os

# Carrega as variáveis do arquivo .env
load_dotenv()

api_key = os.getenv("SECRET_KEY")

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage
import json

# --- Configuração da Página ---
st.set_page_config(page_title="IA PDF to Excel", layout="wide")

st.title("📄 Extração de Dados PDF com IA 🤖")
st.markdown("Faça upload de um PDF (fatura/relatório) para extrair dados estruturados.")

# --- Configuração da OpenAI (IA) ---
# Dica: Use streamlit secrets para gerenciar API Keys em produção

#api_key = st.sidebar.text_input(OPENAI_API_KEY, type="password")

# --- Função de Extração com IA ---
def extract_data_with_ai(text, prompt_instruction):
    """ if not api_key:
        st.error("Por favor, insira sua OpenAI API Key na barra lateral.")
        return None """
    
    #chat = ChatOpenAI(temperature=0, openai_api_key=api_key, model="gpt-5.4") # Recomendado gpt-4o ou gpt-3.5-turbo
    chat = ChatOpenAI(temperature=0, openai_api_key=api_key, model="gpt-5.4")
    system_message = SystemMessage(content="""
        Você é um assistente especializado em estruturar dados de documentos.
        Extraia as informações do PDF fornecido e retorne APENAS um JSON válido.
        Não adicione explicações ou Markdown.
    """)
    
    human_message = HumanMessage(content=f"{prompt_instruction}\n\nTexto do PDF:\n{text}")
    
    try:
        response = chat([system_message, human_message])
        # Limpar a resposta caso a IA retorne markdown ```json
        content = response.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        return data
    except Exception as e:
        st.error(f"Erro na IA: {e}")
        return None

# --- Interface Streamlit ---
uploaded_file = st.file_uploader("Escolha o arquivo PDF", type="pdf")

if uploaded_file is not None:
    # 1. Leitura do PDF
    with pdfplumber.open(uploaded_file) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text()
            
    with st.expander("Ver texto extraído do PDF"):
        st.write(full_text)

    # 2. Definição do que extrair
    prompt = st.text_area("O que você deseja extrair?", 
                          """Ignorar a primeira página do documento. A partir da segunda página,
extraia e retorne os seguintes dados do texto fornecido:
- Nome do cliente
- Endereço
- Data de Vencimento
- TOTAL A PAGAR (R$)
- REF:MÊS/ANO
- N° do Documento
- CÓDIGO DO CLIENTE
- CLASSIFICAÇÃO
- ITENS DA FATURA
- MEDIDOR
a cada novo campo CÓDIGO DO CLIENTE diferente.""")
    
    if st.button("Processar com IA"):
        with st.spinner("IA analisando o documento..."):
            extracted_data = extract_data_with_ai(full_text, prompt)
            
            if extracted_data:
                st.success("Dados extraídos com sucesso!")
                st.json(extracted_data)
                
                # 3. Converter para DataFrame Pandas e Excel
                # Esta parte depende da estrutura do JSON retornado
                df = pd.json_normalize(extracted_data)
                
                # Converter DataFrame para Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Dados')
                
                st.download_button(
                    label="Baixar Excel",
                    data=output.getvalue(),
                    file_name="dados_extraidos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )