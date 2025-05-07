#!/usr/bin/env python
# coding: utf-8

# In[1]:

import streamlit as st
import json
import os
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import pandas as pd

# Carrega as credenciais do secrets.toml
users = st.secrets["login"]["users"]
passwords = st.secrets["login"]["passwords"]

# Inicializa sessão
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""

# Se não estiver logado, exibe tela de login
if not st.session_state.logado:
    st.subheader("🔐 Insira suas credenciais para realizar Login")

    user_input = st.text_input("Usuário")
    pass_input = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if user_input in users:
            idx = users.index(user_input)
            if pass_input == passwords[idx]:
                st.session_state.logado = True
                st.session_state.usuario = user_input
                st.rerun()  # <- Roda o app de novo imediatamente após o login
            else:
                st.error("Senha incorreta.")
        else:
            st.error("Usuário não encontrado.")

    st.stop()


if st.session_state.logado:
    st.success(f"🔓 Bem-vindo, {st.session_state.usuario}!")

    if st.button("Sair"):
        st.session_state.logado = False
        st.session_state.usuario = ""
        st.rerun()

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
import base64

def imagem_para_base64(caminho_imagem):
    with open(caminho_imagem, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

img_base64 = imagem_para_base64("logo.png")

st.markdown(
    f"""
    <div style="display: flex; align-items: center; justify-content: center;">
        <img src="data:image/png;base64,{img_base64}" width="150" style="margin-right: 20px;">
        <div style="text-align: center;">
            <h1 style="margin: 0;">Simulador de Margem</h1>
            <h4>Damare Alimentos:</h4>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Linha separadora
st.markdown("---")


def formatar_reais(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Unidades de produção e saída
fabricas = filial_df[filial_df["TIPO"] == "FABRICA"]["NOME"].tolist()
todas_unidades = filial_df["NOME"].tolist()

col1, col2, col6 = st.columns(3)
with col1:
    unidade_producao = st.selectbox("Fabrica de Produção)", options=fabricas)

with col2:
    unidade_saida = st.selectbox("Unidade de Saída", options=todas_unidades)

with col6:
    ufs = uf_df["UF"].unique().tolist()
    uf_selecionado = st.selectbox("UF Destino", options=ufs)

# Filtra os produtos com base na unidade de produção selecionada
# Primeiro, obtém o número da filial que corresponde à unidade de produção selecionada
numero_filial = filial_df[filial_df["NOME"] == unidade_producao]["FILIAL"].iloc[0]

# Filtra os produtos na aba de Custos, onde a filial corresponde ao número da filial da unidade de produção
produtos_filtrados = custos_df[custos_df["FILIAL"] == numero_filial]["DESC_PROD"].unique().tolist()

# Se não houver produtos para a unidade de produção selecionada, mostrar mensagem
if not produtos_filtrados:
    st.warning(f"Não há produtos disponíveis para a filial '{unidade_producao}'.")
else:
    produtos_sorted = sorted(produtos_filtrados)  # Ordena os produtos de A a Z
    
    # Exibe o selectbox com os produtos filtrados
    produto_selecionado = st.selectbox("Produto", options=produtos_sorted)

    # Verifica se um produto foi selecionado
    if produto_selecionado:
        # Recupera os dados do produto selecionado e da filial correspondente
        dados_produto = custos_df[
            (custos_df["DESC_PROD"] == produto_selecionado) &
            (custos_df["FILIAL"] == numero_filial)
        ]

        if not dados_produto.empty:
            dados_produto = dados_produto.iloc[0]
        else:
            st.error(f"Produto '{produto_selecionado}' não encontrado para a filial '{unidade_producao}'.")




# Linha separadora
st.markdown("---")

# Recupera dados padrão do produto selecionado
dados_produto = custos_df[custos_df["DESC_PROD"] == produto_selecionado].iloc[0]

# Mês (Definindo a seleção do mês aqui)
st.markdown("""
    <style>
        h4 {
            font-size: 20px;  # Ajuste o tamanho da fonte conforme necessário
            font-weight: bold;  # Deixa o título mais destacado
        }
    </style>
    <h4>Selecione o mês para buscar o custo do produto:</h4>
""", unsafe_allow_html=True)

# Criar um dicionário com Nome -> Número (ex: "Janeiro" -> 1)
meses_dict = dict(zip(meses_df["MES_NM"], meses_df["MES_NUM"]))

# Selectbox com nomes visíveis
mes_nome = st.selectbox("Mês", options=list(meses_dict.keys()))

# Pega o número correspondente ao nome selecionado
mes_num = meses_dict[mes_nome]

# Mostrar o mês selecionado (opcional)
st.write(f"Mês Selecionado: {mes_nome}")



# ----------- PREENCHE CUSTO DO MÊS NO CAMPO "Custo Líquido (R$)" -----------

# Obter o custo do produto no mês selecionado
custo_mes = dados_produto[str(mes_num)]  # Colunas de 1 a 12

# Caso o custo esteja em centavos, dividimos por 100 para converter para reais
custo_liquido = float(custo_mes) / 100

# Exibir o campo como desabilitado, apenas leitura
st.number_input(
    "Custo Líquido (R$):",
    min_value=0.0,
    step=0.01,
    value=custo_liquido,
    disabled=True
)


# Inputs manuais (colocando dentro de um botão "Gerar Simulação")
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
    frete_unitario = st.number_input("Frete Unitário", step=0.01, format="%.2f")

# Inputs manuais Sob Impostos
st.markdown("""
    <style>
        h4 {
            font-size: 20px;  # Ajuste o tamanho da fonte conforme necessário
            font-weight: bold;  # Deixa o título mais destacado
        }
    </style>
    <h4>Preenchimento de Impostos e Descontos</h4>
""", unsafe_allow_html=True)

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

if st.button("Gerar Simulação"):
    if preco_venda > 0 and quantidade > 0:
        custo_unitario = custo_liquido + frete_unitario
        custo_total = custo_unitario * quantidade
        faturamento = preco_venda * quantidade
        taxa_total = (icms + pis + cofins + descontos) / 100
        impostos = taxa_total * faturamento
        preco_liquido = (faturamento - impostos) / quantidade
        margem = (preco_liquido - custo_unitario) / custo_unitario
        resultado = faturamento - custo_total - impostos

        st.markdown("### Resultados")
        st.write(f"**Faturamento:** {formatar_reais(faturamento)}")
        st.write(f"**Custo Total:** {formatar_reais(custo_total)}")
        st.write(f"**Resultado:** {formatar_reais(resultado)}")
        st.metric("Margem Real", f"{margem:.2%}")

        # Preços sugeridos para margens-alvo (com impostos)
        st.markdown("### Preço sugerido para margens-alvo:")
        for alvo in [0.01, 0.02, 0.03, 0.04, 0.05]:
            preco_alvo = custo_unitario * (1 + alvo) / (1 - taxa_total)
            st.write(f"{int(alvo * 100)}% de margem → R$ {preco_alvo:.2f}")
    else:
        st.warning("Informe um preço de venda e uma quantidade válidos para realizar os cálculos.")
