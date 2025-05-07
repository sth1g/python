#!/usr/bin/env python
# coding: utf-8

# In[1]:

import streamlit as st
import json
import os
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import pandas as pd


# In[2]:

# Defina o escopo de acesso
escopos = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']


# In[3]:

# Carrega as credenciais do secret do Streamlit
json_credenciais = st.secrets["google_credentials"]
# Converte o dict em string JSON para simular um arquivo
credenciais_dict = dict(json_credenciais)
credenciais_json = json.dumps(credenciais_dict)
# Cria as credenciais a partir do JSON em string
credenciais = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(credenciais_json), escopos)

# Autenticar e acessar a planilha
gc = gspread.authorize(credenciais)


# In[4]:

# Abra a planilha e a aba desejada
planilha = gc.open("Simulador_Damare")  # substitua pelo nome correto


# In[5]:

# ----------- LEITURA DOS DADOS ----------- 
# Custos
custos_sheet = planilha.worksheet("Custos")
custos_df = pd.DataFrame(custos_sheet.get_all_records())
custos_df = custos_df.rename(columns=lambda x: x.strip())  # remove espaços

# Filial
filial_sheet = planilha.worksheet("Filial")
filial_df = pd.DataFrame(filial_sheet.get_all_records())
filial_df = filial_df.rename(columns=lambda x: x.strip())

# UF
uf_sheet = planilha.worksheet("UF")
uf_df = pd.DataFrame(uf_sheet.get_all_records())
uf_df = uf_df.rename(columns=lambda x: x.strip())

# Mes
meses_sheet = planilha.worksheet("Mes")
meses_df = pd.DataFrame(meses_sheet.get_all_records())
meses_df = meses_df.rename(columns=lambda x: x.strip())

# In[6]:

import streamlit as st


# In[7]:

# ----------- INTERFACE STREAMLIT ----------- 
# Configuração inicial
st.set_page_config(page_title="Simulador de Margem", layout="wide")
st.title("📊 Simulador de Margem Real")


def formatar_reais(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Unidades de produção e saída
fabricas = filial_df[filial_df["TIPO"] == "FABRICA"]["NOME"].tolist()
todas_unidades = filial_df["NOME"].tolist()

col1, col2 = st.columns(2)
with col1:
    unidade_producao = st.selectbox("Unidade de Produção (somente Fábricas)", options=fabricas)

with col2:
    unidade_saida = st.selectbox("Unidade de Saída", options=todas_unidades)

# Produto e UF lado a lado
st.markdown("### Selecione Produto e UF de Venda")

col5, col6 = st.columns(2)

with col5:
    produtos = custos_df["DESC_PROD"].unique().tolist()
    produto_selecionado = st.selectbox("Produto", options=produtos)

with col6:
    ufs = uf_df["UF"].unique().tolist()
    uf_selecionado = st.selectbox("UF", options=ufs)

# Linha separadora
st.markdown("---")

# Recupera dados padrão do produto selecionado
dados_produto = custos_df[custos_df["DESC_PROD"] == produto_selecionado].iloc[0]

# Mês (Definindo a seleção do mês aqui)
st.markdown("### Selecione o Mês")
meses = meses_df["MES_NUM"].unique().tolist()  # Lista de meses em número
mes_num = st.selectbox("Mês (Número)", options=meses)

# Encontrar o nome do mês
mes_nome = meses_df[meses_df["MES_NUM"] == mes_num]["MES_NM"].iloc[0]
st.write(f"Mês Selecionado: {mes_nome}")

# ----------- PREENCHE CUSTO DO MÊS NO CAMPO "Custo Líquido (R$)" -----------

# Obter o custo do produto no mês selecionado
custo_mes = dados_produto[str(mes_num)]  # A coluna vai de 1 a 12, onde cada número representa um mês

# Caso o custo esteja em centavos, dividimos por 100 para converter para reais
custo_liquido = float(custo_mes) / 100

# Preencher o campo de "Custo Líquido" com o valor do custo do mês
custo_liquido = st.number_input("Custo Líquido (R$):", min_value=0.0, step=0.01, value=custo_liquido)

# Inputs manuais
col3, col4, col7 = st.columns(3)
with col3:
    preco_venda = st.number_input("Preço de Venda (R$):", step=0.01, format="%.2f")

with col4:
    quantidade_str = st.text_input("Quantidade (ex: 1.000)", value="1")
    try:
        quantidade = int(quantidade_str.replace(".", ""))
    except:
        quantidade = 0
        st.error("Digite uma quantidade válida (ex: 1.000)")

with col7:
    frete_unitario  = st.number_input("Frete Unitário", step=0.01, format="%.2f")

# Linha separadora
st.markdown("---")

# Inputs manuais Sob Impostos

st.markdown("### Insira os valores dos impostos e descontos")
st.markdown("<h4>Caso nao tenha, basta deixa zerado</h4>", unsafe_allow_html=True)

col8, col9, col10, col11 = st.columns(4)
with col8:
    icms = st.number_input("ICMS (%)", min_value=0.0, max_value=100.0, step=0.01, format="%.2f")
    
with col9:
    pis = st.number_input("PIS (%)", min_value=0.0, max_value=100.0, step=0.01, format="%.2f")

with col10:
    cofins = st.number_input("COFINS (%)", min_value=0.0, max_value=100.0, step=0.01, format="%.2f")

with col11:
    descontos = st.number_input("OUTROS DESCONTOS", min_value=0.0, max_value=100.0, step=0.01, format="%.2f")

# Linha separadora
st.markdown("---")

# ----------- CÁLCULOS -----------
if preco_venda > 0 and quantidade > 0:
    custo_unitario = custo_liquido + frete_unitario
    custo_total = custo_unitario * quantidade
    faturamento = preco_venda * quantidade
    impostos = ((icms/100) + (pis/100) + (cofins/100) + (descontos/100)) * faturamento
    preco_liquido = (faturamento - impostos) / quantidade
    margem = (preco_liquido - custo_unitario) / custo_unitario
    resultado = faturamento - custo_total - impostos

    # Resultados

    st.markdown("### Resultados")
    st.write(f"**Faturamento:** {formatar_reais(faturamento)}")
    st.write(f"**Custo  Total:** {formatar_reais(custo_total)}")
    st.write(f"**Resultado:** {formatar_reais(resultado)}")
    st.metric("Margem Real", f"{margem:.2%}")  # Usa porcentagem real

    # Preços sugeridos para margens-alvo
    st.markdown("### Preço sugerido para margens-alvo:")
    for alvo in [0.01, 0.02, 0.03, 0.04, 0.05]:
        preco_alvo = custo_unitario / (1 - alvo)
        st.write(f"{int(alvo * 100)}% de margem → R$ {preco_alvo:.2f}")
else:
    st.warning("Informe um preço de venda e uma quantidade válidos para realizar os cálculos.")
