import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

st.set_page_config(page_title="Sistema PIBIC - UNIFEI", layout="wide", page_icon="📊")

# ==========================================
# NOVO: BARRA LATERAL COM SLIDERS DE PESO
# ==========================================
st.sidebar.header("⚖️ Pesos dos Eixos")
st.sidebar.markdown("Ajuste o multiplicador de cada eixo para o cálculo da Nota Final.")
w1 = st.sidebar.slider("Peso Eixo 1 (Total Qualis)", 0.0, 5.0, 1.0, 0.5)
w2 = st.sidebar.slider("Peso Eixo 2 (Razão Qualis)", 0.0, 5.0, 1.0, 0.5)
w3 = st.sidebar.slider("Peso Eixo 3 (Prod. Ampliada)", 0.0, 5.0, 1.0, 0.5)
w4 = st.sidebar.slider("Peso Eixo 4 (Orientações)", 0.0, 5.0, 1.0, 0.5)
w5 = st.sidebar.slider("Peso Eixo 5 (Bibliometria)", 0.0, 5.0, 1.0, 0.5)
w6 = st.sidebar.slider("Peso Eixo 6 (Periódicos)", 0.0, 5.0, 1.0, 0.5)
st.sidebar.divider()

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

# Bloco A: Ativação dos Eixos (Layout 3x2)
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

# Bloco B: Parametrização Interna
st.markdown("#### B. Parametrização de Categorias")
col_param1, col_param2 = st.columns(2)

with col_param1:
    opcoes_padrao_e3 = ['Trabalho publicado em anais de evento', 'Capítulo de livro publicado', 'Livro publicado', 'Programa de computador', 'Patentes e registros']
    todas_opcoes_e3 = opcoes_padrao_e3 + ['Trabalhos técnicos', 'Apresentação de Trabalho e palestra', 'Outra produção bibliográfica', 'Outra produção técnica']
    target_production_types = st.multiselect("Categorias do Eixo 3:", options=todas_opcoes_e3, default=opcoes_padrao_e3, disabled=not eixo3_active)

with col_param2:
    opcoes_padrao_e4 = ['Iniciação Científica', 'Dissertação de mestrado', 'Tese de doutorado', 'Trabalho de conclusão de curso de graduação']
    todas_opcoes_e4 = opcoes_padrao_e4 + ['Monografia de conclusão/especialização', 'Supervisão de pós-doutorado']
    target_advising_types = st.multiselect("Categorias do Eixo 4:", options=todas_opcoes_e4, default=opcoes_padrao_e4, disabled=not eixo4_active)

# Bloco C: Indicadores de Impacto
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
metodo_calculo = st.radio("Cálculo da Nota Final (após normalização global 0-10):", options=["Soma (Aditivo)", "Média (Compensatório)"], horizontal=True)

# ==========================================
# 3. PROCESSAMENTO DOS DADOS
# ==========================================
if file_docentes and file_prod and file_pessoas:
    if st.button("🚀 Processar Dados e Gerar Ranking", use_container_width=True, type="primary"):
        
        with st.spinner("Calculando eixos e processando indicadores..."):
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
                e1_abs = sum(q_counts.get(q, 0) for q in qualis_validos) 
                
                count_a = sum(q_counts.get(q, 0) for q in ['A1','A2','A3','A4'])
                count_b = sum(q_counts.get(q, 0) for q in ['B1','B2','B3','B4'])
                e2_abs = (count_a / count_b) if count_b > 0 else float(count_a)
                
                # E3 & E4
                e3_abs = len(prof_data[prof_data['Tipo da produção'].isin(target_production_types)])
                e4_abs = len(prof_data[(prof_data['Tipo agrupador da produção'] == 'Orientação concluída') & (prof_data['Tipo da produção'].isin(target_advising_types))])
                
                # E6
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

            # ==========================================
            # NORMALIZAÇÕES (Escala 0 a 10)
            # ==========================================
            
            # E5
            e5_norms = []
            for col in h_cols:
                df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0)
                df_final[col+'_N'] = (df_final[col] / df_final[col].max() * 10) if df_final[col].max() > 0 else 0
                e5_norms.append(df_final[col+'_N'])
            df_final['E5_N'] = sum(e5_norms)/len(e5_norms) if e5_norms else 0
            if isinstance(df_final['E5_N'], pd.Series) and df_final['E5_N'].max() > 0:
                df_final['E5_N'] = (df_final['E5_N'] / df_final['E5_N'].max()) * 10

            # E6
            e6_norms = []
            for col in target_journal_metrics:
                df_final[col+'_N'] = (df_final[col] / df_final[col].max() * 10) if df_final[col].max() > 0 else 0
                e6_norms.append(df_final[col+'_N'])
            df_final['E6_N'] = sum(e6_norms)/len(e6_norms) if e6_norms else 0
            if isinstance(df_final['E6_N'], pd.Series) and df_final['E6_N'].max() > 0:
                df_final['E6_N'] = (df_final['E6_N'] / df_final['E6_N'].max()) * 10

            # Normalização Global (E1 a E4)
            for n, a in [('E1_N','E1_Abs'), ('E2_N','E2_Abs'), ('E3_N','E3_Abs'), ('E4_N','E4_Abs')]:
                df_final[n] = (df_final[a] / df_final[a].max() * 10) if df_final[a].max() > 0 else 0

            # -----------------------------------------------------
            # Cálculo da Nota Final aplicando os pesos
            # -----------------------------------------------------
            active_weighted = []
            active_weights = []
            
            if eixo1_active: 
                active_weighted.append(df_final['E1_N'] * w1)
                active_weights.append(w1)
            if eixo2_active: 
                active_weighted.append(df_final['E2_N'] * w2)
                active_weights.append(w2)
            if eixo3_active: 
                active_weighted.append(df_final['E3_N'] * w3)
                active_weights.append(w3)
            if eixo4_active: 
                active_weighted.append(df_final['E4_N'] * w4)
                active_weights.append(w4)
            if eixo5_active: 
                active_weighted.append(df_final['E5_N'] * w5)
                active_weights.append(w5)
            if eixo6_active: 
                active_weighted.append(df_final['E6_N'] * w6)
                active_weights.append(w6)

            col_f = 'Nota Final (' + metodo_calculo.split()[0] + ')'
            
            if "Soma" in metodo_calculo:
                df_final[col_f] = sum(active_weighted) if active_weighted else 0
            else:
                total_w = sum(active_weights)
                df_final[col_f] = sum(active_weighted) / total_w if total_w > 0 else 0
            
            # Normalização final para garantir escala exata de 0 a 10 na classificação geral
            max_nf = df_final[col_f].max()
            if max_nf > 0:
                df_final[col_f] = (df_final[col_f] / max_nf) * 10
                
            df_final.sort_values(by=col_f, ascending=False, inplace=True)
            df_final['Posição'] = range(1, len(df_final) + 1)
            # -----------------------------------------------------

            # ==========================================
            # 4. RESULTADOS E EXPORTAÇÃO
            # ==========================================
            st.success("✅ Ranking gerado com sucesso!")
            
            col_v = ['Posição', 'Docente', col_f, 'Área']
            st.dataframe(df_final[col_v].head(15), use_container_width=True, hide_index=True)
            
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df_final.to_excel(writer, index=False, sheet_name='Ranking')
            st.download_button("📥 Baixar Ranking (.xlsx)", data=excel_buffer.getvalue(), file_name="ranking_pibic_final.xlsx", use_container_width=True)

            # ==========================================
            # 5. DIAGNÓSTICO DE VIESES (Layout Matrix / Dashboard)
            # ==========================================
            
            st.divider()
            st.header("🕵️ Dashboard Analítico de Vieses")
            st.markdown("Avalie se o conjunto de regras atual favorece injustamente algum perfil de investigador ou área de conhecimento.")

            # Mapeamento para legendas
            axis_cols = []
            if eixo1_active: axis_cols.append('E1_N')
            if eixo2_active: axis_cols.append('E2_N')
            if eixo3_active: axis_cols.append('E3_N')
            if eixo4_active: axis_cols.append('E4_N')
            if eixo5_active: axis_cols.append('E5_N')
            if eixo6_active: axis_cols.append('E6_N')
            
            axis_labels = {
                'E1_N': 'E1: Qualis', 'E2_N': 'E2: Razão A/B', 
                'E3_N': 'E3: Prod. Ampliada', 'E4_N': 'E4: Orientações', 
                'E5_N': 'E5: Bibliometria', 'E6_N': 'E6: Periódicos'
            }

            # Primeira Linha da Matriz
            dash_col1, dash_col2 = st.columns(2)

            with dash_col1:
                st.subheader("1. Redundância (Correlação)")
                st.markdown("""
                **Uso:** Cores quentes (próximas de 1.0) indicam que dois eixos medem quase a mesma coisa. 
                Se um eixo tiver correlação alta com a Nota Final, ele está a decidir o edital sozinho.
                """)
                corr_cols = axis_cols + [col_f]
                corr_df = df_final[corr_cols].rename(columns=axis_labels).corr()
                fig_corr, ax_corr = plt.subplots(figsize=(7, 5))
                sns.heatmap(corr_df, annot=True, cmap='coolwarm', vmin=-1, vmax=1, fmt=".2f", ax=ax_corr, annot_kws={"size": 9})
                plt.xticks(rotation=45, ha='right')
                st.pyplot(fig_corr)

            with dash_col2:
                st.subheader("2. Composição da Nota (Top 20)")
                st.markdown("""
                **Uso:** Avalia o perfil dos líderes. Barras equilibradas indicam docentes 'generalistas'. 
                Uma única cor dominante indica que a pessoa ganhou apenas por uma métrica específica.
                """)
                top20 = df_final.head(20).copy()
                top20.set_index('Docente', inplace=True)
                top20_axes = top20[axis_cols].rename(columns=axis_labels)
                fig_bar, ax_bar = plt.subplots(figsize=(7, 5.5))
                top20_axes.plot(kind='barh', stacked=True, ax=ax_bar, colormap='viridis')
                ax_bar.invert_yaxis()
                ax_bar.set_xlabel("Pontuação Acumulada")
                ax_bar.legend(loc='lower right', fontsize=8)
                st.pyplot(fig_bar)

            # Segunda Linha da Matriz
            dash_col3, dash_col4 = st.columns(2)

            with dash_col3:
                st.subheader("3. Viés Disciplinar (Radar)")
                st.markdown("""
                **Uso:** Compara a força média das 4 maiores áreas. Uma teia 'puxada' para um lado 
                indica que a métrica favorece a cultura de publicação daquela ciência específica.
                """)
                if len(axis_cols) >= 3:
                    top4_areas = df_final['Área'].value_counts().nlargest(4).index
                    radar_data = df_final[df_final['Área'].isin(top4_areas)].groupby('Área')[axis_cols].mean()
                    angles = np.linspace(0, 2 * np.pi, len(axis_cols), endpoint=False).tolist()
                    angles += angles[:1]
                    fig_radar, ax_radar = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
                    for idx, row in radar_data.iterrows():
                        values = row.tolist() + row.tolist()[:1]
                        ax_radar.plot(angles, values, label=idx, linewidth=2)
                        ax_radar.fill(angles, values, alpha=0.1)
                    ax_radar.set_xticks(angles[:-1])
                    ax_radar.set_xticklabels([axis_labels[c] for c in axis_cols], size=9)
                    ax_radar.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=8)
                    st.pyplot(fig_radar)
                else:
                    st.warning("Necessário 3+ eixos ativos para Radar.")

            with dash_col4:
                st.subheader("4. Efeito Mateus (Senioridade)")
                st.markdown("""
                **Uso:** Se a linha for muito íngreme e os pontos se aglomerarem no topo à esquerda, 
                o edital pode estar a privilegiar apenas investigadores consolidados, dificultando a entrada de jovens.
                """)
                seniority_col = 'E1_Abs'
                label_sen = "Volume de Publicações"
                for col in df_final.columns:
                    if 'Índice H' in col and not col.endswith('_N'):
                        seniority_col, label_sen = col, col
                        break
                fig_scatter, ax_scatter = plt.subplots(figsize=(7, 5))
                sns.regplot(data=df_final, x='Posição', y=seniority_col, ax=ax_scatter, scatter_kws={'alpha':0.4}, line_kws={'color':'red'})
                ax_scatter.set_xlim(df_final['Posição'].max() + 5, -5)
                ax_scatter.set_ylabel(label_sen)
                st.pyplot(fig_scatter)

            # Terceira Linha (Largura Total)
            st.divider()
            st.subheader("5. Competitividade Geral por Área")
            st.markdown("""
            **Uso:** Distribuição das 15 áreas mais frequentes, ordenadas da melhor classificada (menor mediana) para a pior. 
            Permite ver se áreas inteiras estão a ser 'empurradas' para o fim da lista.
            """)
            top_areas = df_final['Área'].value_counts().nlargest(15).index
            df_plot = df_final[df_final['Área'].isin(top_areas)].copy()
            area_order = df_plot.groupby('Área')['Posição'].median().sort_values().index
            fig_box, ax_box = plt.subplots(figsize=(12, 6))
            sns.boxplot(data=df_plot, x='Área', y='Posição', order=area_order, palette='Set3', showfliers=False, ax=ax_box)
            sns.stripplot(data=df_plot, x='Área', y='Posição', order=area_order, color='black', alpha=0.3, size=3, ax=ax_box)
            ax_box.invert_yaxis()
            plt.xticks(rotation=45, ha='right', fontsize=9)
            ax_box.set_ylabel('Posição (Menor é Melhor)')
            st.pyplot(fig_box)

            # Quarta Linha (Largura Total) - TOP 50%
            st.divider()
            st.subheader("6. Competitividade Geral por Área (Top 50%)")
            st.markdown("""
            **Uso:** Semelhante ao gráfico anterior, mas filtrando apenas os 50% dos investigadores mais bem pontuados do ranking. 
            Permite verificar se a elite do edital é monopolizada por alguma ciência específica.
            """)
            df_top50 = df_final.head(max(1, len(df_final) // 2)).copy()
            if not df_top50.empty:
                top_areas_50 = df_top50['Área'].value_counts().nlargest(15).index
                df_plot_50 = df_top50[df_top50['Área'].isin(top_areas_50)].copy()
                area_order_50 = df_plot_50.groupby('Área')['Posição'].median().sort_values().index
                fig_box_50, ax_box_50 = plt.subplots(figsize=(12, 6))
                sns.boxplot(data=df_plot_50, x='Área', y='Posição', order=area_order_50, palette='Set3', showfliers=False, ax=ax_box_50)
                sns.stripplot(data=df_plot_50, x='Área', y='Posição', order=area_order_50, color='black', alpha=0.3, size=3, ax=ax_box_50)
                ax_box_50.invert_yaxis()
                plt.xticks(rotation=45, ha='right', fontsize=9)
                ax_box_50.set_ylabel('Posição (Menor é Melhor)')
                st.pyplot(fig_box_50)
            else:
                st.warning("Dados insuficientes para gerar o gráfico de Top 50%.")

else:
    st.info("⚠️ Aguarde o upload das três planilhas.")
