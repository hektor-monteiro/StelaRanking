import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

st.set_page_config(page_title="Sistema PIBIC - UNIFEI", layout="wide", page_icon="📊")

st.title("📊 Sistema Multicritério de Avaliação Docente - PIBIC/UNIFEI")
st.markdown("""
Esta ferramenta processa os dados extraídos do Stela Experta para gerar o **ranking institucional de bolsas PIBIC**.
Selecione os eixos desejados, os tipos de produção/orientação válidos e o método matemático para a pontuação final.
""")

st.divider()

# ==========================================
# 1. ENTRADA DE FICHEIROS
# ==========================================
st.subheader("1. Upload das Planilhas Institucionais")
col1, col2, col3 = st.columns(3)

with col1:
    st.info("Planilha: 'Total de produções*'")
    file_docentes = st.file_uploader("Lista de Docentes Válidos", type=['xlsx', 'xls', 'csv'], key="docentes")

with col2:
    st.info("Planilha: 'busca_Produção_*'")
    file_prod = st.file_uploader("Base de Produções (Lattes)", type=['xlsx', 'xls', 'csv'], key="lattes")

with col3:
    st.info("Planilha: 'Quem são as pessoas*'")
    file_pessoas = st.file_uploader("Dados Cadastrais e Áreas", type=['xlsx', 'xls', 'csv'], key="pessoas")

st.divider()

# ==========================================
# 2. CONFIGURAÇÃO DE PARÂMETROS E LAYOUT
# ==========================================
st.subheader("2. Configuração do Cálculo e Eixos")

# Bloco A: Ativação dos Eixos (Layout corrigido para 3 colunas x 2 linhas)
st.markdown("#### A. Ativação de Eixos")
col_e1, col_e2, col_e3 = st.columns(3)
with col_e1: eixo1_active = st.checkbox("Eixo 1: Total Qualis", value=True)
with col_e2: eixo2_active = st.checkbox("Eixo 2: Razão Qualis", value=True)
with col_e3: eixo3_active = st.checkbox("Eixo 3: Produção Ampliada", value=True)

col_e4, col_e5, col_e6 = st.columns(3)
with col_e4: eixo4_active = st.checkbox("Eixo 4: Orientações", value=True)
with col_e5: eixo5_active = st.checkbox("Eixo 5: Bibliometria (Índice H)", value=True)
with col_e6: eixo6_active = st.checkbox("Eixo 6: Qualidade de Periódicos", value=True)

st.markdown("<br>", unsafe_allow_html=True) 

# Bloco B: Parametrização Interna (Prod. Ampliada e Orientações)
st.markdown("#### B. Parametrização de Categorias")
col_param1, col_param2 = st.columns(2)

with col_param1:
    opcoes_padrao_e3 = ['Trabalho publicado em anais de evento', 'Capítulo de livro publicado', 'Livro publicado', 'Programa de computador', 'Patentes e registros']
    todas_opcoes_e3 = opcoes_padrao_e3 + ['Trabalhos técnicos', 'Apresentação de Trabalho e palestra', 'Outra produção bibliográfica', 'Outra produção técnica']
    target_production_types = st.multiselect("Categorias do Eixo 3:", options=todas_opcoes_e3, default=opcoes_padrao_e3, disabled=not eixo3_active)

with col_param2:
    opcoes_padrao_e4 = ['Iniciação Científica', 'Dissertação de mestrado', 'Tese de doutorado']
    todas_opcoes_e4 = opcoes_padrao_e4 + ['Monografia de conclusão/especialização', 'Trabalho de conclusão de curso', 'Supervisão de pós-doutorado']
    target_advising_types = st.multiselect("Categorias do Eixo 4:", options=todas_opcoes_e4, default=opcoes_padrao_e4, disabled=not eixo4_active)

# Bloco C: Indicadores de Impacto (Eixos 5 e 6)
st.markdown("#### C. Indicadores de Impacto e Prestígio")
col_bib1, col_bib2 = st.columns(2)

with col_bib1:
    opcoes_e5 = ["Índice H (todos os anos)", "Índice i10 (todos os anos)", "Citações (todos os anos)", "Índice H (últimos 5 anos)"]
    target_biblio_h = st.multiselect("Eixo 5 (Dados da Planilha de Pessoal):", options=opcoes_e5, default=["Índice H (todos os anos)"], disabled=not eixo5_active)

with col_bib2:
    opcoes_e6 = [
        "Journal Impact Factor (JIF) – WoS atual (2024)", "Journal Impact Factor (JIF) – WoS (ano da produção)",
        "Índice H SCImago – Scopus atual (2024)", "Índice H SCImago – Scopus (ano da produção)",
        "SCImago Journal Rank (SJR) – Scopus atual (2024)", "SCImago Journal Rank (SJR) – Scopus (ano da produção)",
        "Source Normalized Impact per Paper (SNIP) – Scopus atual (2024)", "CiteScore - Scopus"
    ]
    target_journal_metrics = st.multiselect("Eixo 6 (Dados da Planilha de Produções):", options=opcoes_e6, default=["Journal Impact Factor (JIF) – WoS (ano da produção)"], disabled=not eixo6_active)

st.markdown("<br><hr>", unsafe_allow_html=True) 

# Bloco D: Método de Agregação
st.markdown("#### D. Método de Agregação")
metodo_calculo = st.radio("Cálculo da Nota Final (após normalização global 0-1):", options=["Soma (Aditivo)", "Média (Compensatório)"], horizontal=True)

# ==========================================
# 3. PROCESSAMENTO DOS DADOS
# ==========================================
if file_docentes and file_prod and file_pessoas:
    if st.button("🚀 Processar Dados e Gerar Ranking", use_container_width=True, type="primary"):
        
        with st.spinner("Calculando eixos e processando indicadores de periódicos..."):
            try:
                def load_file(file, skip=0, separator=';'):
                    if file.name.endswith('.csv'): return pd.read_csv(file, sep=separator, skiprows=skip, encoding='utf-8', on_bad_lines='skip')
                    return pd.read_excel(file, skiprows=skip)

                df_docentes_raw = load_file(file_docentes, skip=7)
                valid_names = df_docentes_raw.iloc[:, 0].dropna().iloc[1:].astype(str).str.strip().unique()

                df_prod = load_file(file_prod, skip=3)
                df_prod['Informada por'] = df_prod['Informada por'].astype(str)

                df_pessoas = load_file(file_pessoas, skip=3, separator=',')
                df_pessoas.columns = df_pessoas.columns.str.strip()
                df_pessoas['Nome'] = df_pessoas['Nome'].astype(str).str.strip()

                # Função para converter métricas de texto para número (trata vírgulas e NAs)
                def parse_metric(val):
                    if pd.isna(val) or val in ['Não se aplica', 'Não informado', 'NP']: return 0.0
                    try: return float(str(val).replace(',', '.'))
                    except: return 0.0

            except Exception as e:
                st.error(f"Erro na leitura: {e}"); st.stop()

            # Lógica por Docente
            qualis_validos = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4']
            results_list = []

            for prof in valid_names:
                prof_data = df_prod[df_prod['Informada por'].str.contains(prof, na=False, regex=False)]
                if prof_data.empty: continue
                
                # E1 & E2
                if 'Estrato Qualis (2021/2024) oficial' in prof_data.columns:
                    col_q = 'Estrato Qualis (2021/2024) oficial'
                else:
                    col_q = 'Estrato Qualis (2017/2020) unificado'
                
                q_counts = prof_data[prof_data[col_q].isin(qualis_validos)][col_q].value_counts()
                e1_abs = sum(q_counts.get(q, 0) for q in qualis_validos) # Peso 1
                
                count_a = sum(q_counts.get(q, 0) for q in ['A1','A2','A3','A4'])
                count_b = sum(q_counts.get(q, 0) for q in ['B1','B2','B3','B4'])
                e2_abs = (count_a / count_b) if count_b > 0 else float(count_a)
                
                # E3 & E4
                e3_abs = len(prof_data[prof_data['Tipo da produção'].isin(target_production_types)])
                e4_abs = len(prof_data[(prof_data['Tipo agrupador da produção'] == 'Orientação concluída') & (prof_data['Tipo da produção'].isin(target_advising_types))])
                
                # E6 - Métricas de Periódicos (Soma por docente para cada indicador escolhido)
                e6_data = {}
                for metric in target_journal_metrics:
                    if metric in prof_data.columns:
                        e6_data[metric] = prof_data[metric].apply(parse_metric).sum()
                    else:
                        e6_data[metric] = 0.0

                results_list.append({
                    'Docente': prof, 'E1_Abs': e1_abs, 'E2_Abs': e2_abs, 
                    'E3_Abs': e3_abs, 'E4_Abs': e4_abs, **e6_data
                })

            df_res = pd.DataFrame(results_list).fillna(0)

            # Join com Pessoas para E5
            h_cols = [c for c in target_biblio_h if c in df_pessoas.columns]
            df_final = pd.merge(df_res, df_pessoas[['Nome', 'Área da titulação máxima informada no CV-Lattes'] + h_cols], left_on='Docente', right_on='Nome', how='left')
            df_final.rename(columns={'Área da titulação máxima informada no CV-Lattes': 'Área'}, inplace=True)

            # Normalizações Individuais
            # E5
            e5_norms = []
            for col in h_cols:
                df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0)
                df_final[col+'_N'] = df_final[col] / df_final[col].max() if df_final[col].max() > 0 else 0
                e5_norms.append(df_final[col+'_N'])
            df_final['E5_N'] = sum(e5_norms)/len(e5_norms) if e5_norms else 0

            # E6
            e6_norms = []
            for col in target_journal_metrics:
                df_final[col+'_N'] = df_final[col] / df_final[col].max() if df_final[col].max() > 0 else 0
                e6_norms.append(df_final[col+'_N'])
            df_final['E6_N'] = sum(e6_norms)/len(e6_norms) if e6_norms else 0

            # Normalização Global (E1 a E4)
            for n, a in [('E1_N','E1_Abs'), ('E2_N','E2_Abs'), ('E3_N','E3_Abs'), ('E4_N','E4_Abs')]:
                df_final[n] = df_final[a] / df_final[a].max() if df_final[a].max() > 0 else 0

            # Nota Final
            active = []
            if eixo1_active: active.append(df_final['E1_N'])
            if eixo2_active: active.append(df_final['E2_N'])
            if eixo3_active: active.append(df_final['E3_N'])
            if eixo4_active: active.append(df_final['E4_N'])
            if eixo5_active: active.append(df_final['E5_N'])
            if eixo6_active: active.append(df_final['E6_N'])

            col_f = 'Nota Final (' + metodo_calculo.split()[0] + ')'
            df_final[col_f] = sum(active) if "Soma" in metodo_calculo else sum(active)/len(active)
            df_final.sort_values(by=col_f, ascending=False, inplace=True)
            df_final['Posição'] = range(1, len(df_final) + 1)

            # Resultados
            st.success("✅ Ranking gerado com sucesso!")
            col_v = ['Posição', 'Docente', col_f, 'Área']
            if eixo6_active: col_v.append('E6_N')
            st.dataframe(df_final[col_v].head(15), use_container_width=True, hide_index=True)
            
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df_final.to_excel(writer, index=False, sheet_name='Ranking')
            st.download_button("📥 Baixar Ranking (.xlsx)", data=excel_buffer.getvalue(), file_name="ranking_pibic_final.xlsx", use_container_width=True)

            # Gráfico
            st.divider()
            top_areas = df_final['Área'].value_counts().nlargest(15).index
            df_plot = df_final[df_final['Área'].isin(top_areas)]
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.boxplot(data=df_plot, x='Área', y='Posição', palette='Set3', showfliers=False, ax=ax)
            sns.stripplot(data=df_plot, x='Área', y='Posição', color='black', alpha=0.3, size=3, ax=ax)
            ax.invert_yaxis(); plt.xticks(rotation=45, ha='right')
            st.pyplot(fig)
else:
    st.info("⚠️ Aguarde o upload das três planilhas.")
