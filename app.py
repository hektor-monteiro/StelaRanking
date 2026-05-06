import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

# Configuração da página da aplicação
st.set_page_config(page_title="Sistema PIBIC - UNIFEI", layout="wide", page_icon="📊")

st.title("📊 Sistema Multicritério de Avaliação Docente - PIBIC/UNIFEI")
st.markdown("""
Esta ferramenta processa os dados em bruto do Lattes (extraídos do Stela Experta) para gerar o **ranking institucional de bolsas PIBIC**.
O algoritmo avalia 3 eixos: **(1) Qualis A e B, (2) Produção Ampliada e Inovação, e (3) Formação (IC)**, separando os docentes em 4 grandes áreas.
""")

st.divider()

# Áreas de Upload (lado a lado)
col1, col2 = st.columns(2)
with col1:
    st.subheader("1. Lista de Servidores (Filtro)")
    st.info("Carregue o ficheiro 'Total de produções.csv' (lista de indivíduos da instituição).")
    file_docentes = st.file_uploader("Lista de Docentes", type=['csv'], key="docentes")

with col2:
    st.subheader("2. Extração do Lattes")
    st.info("Carregue o ficheiro bruto 'busca_Produção.csv' extraído do Stela Experta.")
    file_prod = st.file_uploader("Base Lattes", type=['csv'], key="lattes")

st.divider()

if file_docentes and file_prod:
    if st.button("🚀 Processar Dados e Gerar Ranking", use_container_width=True):
        with st.spinner("A limpar e processar milhares de registos Lattes. Por favor, aguarde..."):
            
            # ==========================================
            # 1. LEITURA E LIMPEZA
            # ==========================================
            try:
                # O Streamlit lê o ficheiro diretamente da memória
                df_docentes = pd.read_csv(file_docentes, skiprows=7)
                valid_names = df_docentes.iloc[:, 0].dropna().iloc[1:].unique()

                df = pd.read_csv(file_prod, sep=';', skiprows=3, encoding='utf-8', on_bad_lines='skip')
                df = df[df['Informada por'].isin(valid_names)]
            except Exception as e:
                st.error(f"Erro ao ler os ficheiros. Verifique se o formato está correto. Detalhe: {e}")
                st.stop()

            # ==========================================
            # 2. LÓGICA DE AVALIAÇÃO (OS 3 EIXOS)
            # ==========================================
            target_production_types = [
                'Trabalho publicado em anais de evento', 'Capítulo de livro publicado',
                'Programa de computador', 'Livro publicado', 'Patentes e registros',
                'Artigo publicado em periódicos'
            ]
            qualis_validos = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4']

            # Dicionários do classificador
            kw_eng = ['engenharia', 'civil', 'mecânica', 'mecatronica', 'elétrica', 'produção', 'hídrica', 'materiais', 'energia', 'automação', 'controle', 'sinais', 'potência', 'manufatura', 'aerospacial', 'mobilidade', 'telecomunicações', 'usinagem']
            kw_exatas = ['física', 'matemática', 'química', 'computação', 'estatística', 'meteorologia', 'geociências', 'dados', 'algoritmo', 'software', 'astro', 'equações', 'álgebra']
            kw_humanas = ['educação', 'ensino', 'humanidades', 'filosofia', 'sociologia', 'história', 'geografia', 'letras', 'linguística', 'pedagogia', 'aprendizagem', 'escola', 'administração', 'economia', 'direito', 'gestão', 'social', 'empreendedorismo', 'inovação', 'negócios']
            kw_bio = ['biologia', 'biociências', 'ecologia', 'meio ambiente', 'saúde', 'medicina', 'biodiversidade', 'botânica', 'zoologia', 'ambiental', 'água', 'clima', 'recursos naturais', 'sustentabilidade', 'climatologia']

            professors = df['Informada por'].unique()
            metrics = []

            for prof in professors:
                prof_data = df[df['Informada por'] == prof]
                
                # Eixo 1
                biblio_data = prof_data[prof_data['Tipo agrupador da produção'] == 'Produção bibliográfica']
                biblio_qualis_ab = biblio_data[biblio_data['Estrato Qualis (2017/2020) unificado'].isin(qualis_validos)]
                qualis_counts = biblio_qualis_ab['Estrato Qualis (2017/2020) unificado'].value_counts()
                
                eixo1_qualis = (qualis_counts.get('A1', 0) * 100) + (qualis_counts.get('A2', 0) * 85) + \
                               (qualis_counts.get('A3', 0) * 70) + (qualis_counts.get('A4', 0) * 55) + \
                               (qualis_counts.get('B1', 0) * 40) + (qualis_counts.get('B2', 0) * 30) + \
                               (qualis_counts.get('B3', 0) * 20) + (qualis_counts.get('B4', 0) * 10)
                
                # Eixo 2 e 3
                eixo2_ampliada = len(prof_data[prof_data['Tipo da produção'].isin(target_production_types)])
                advising_data = prof_data[prof_data['Tipo agrupador da produção'] == 'Orientação concluída']
                eixo3_ic = len(advising_data[advising_data['Tipo da produção'] == 'Iniciação Científica'])
                
                # Classificação de Área
                text_data = prof_data['Título da produção'].fillna('') + ' ' + prof_data['Palavra chave 1'].fillna('')
                text_data = ' '.join(text_data).lower()
                
                scores = {
                    'Engenharias': sum(text_data.count(kw) for kw in kw_eng),
                    'Exatas e da Terra': sum(text_data.count(kw) for kw in kw_exatas),
                    'Humanas, Sociais e Ed.': sum(text_data.count(kw) for kw in kw_humanas),
                    'Biológicas e Ambientais': sum(text_data.count(kw) for kw in kw_bio)
                }
                max_area = max(scores, key=scores.get)
                if scores[max_area] == 0: max_area = 'Engenharias'
                
                metrics.append({
                    'Docente': prof,
                    'Eixo 1 (Qualis AB)': eixo1_qualis,
                    'Eixo 2 (Ampliada Limpa)': eixo2_ampliada,
                    'Eixo 3 (IC)': eixo3_ic,
                    'Área': max_area
                })

            df_metrics = pd.DataFrame(metrics).fillna(0)

            # Normalização e Nota Final
            max_eixo1 = df_metrics['Eixo 1 (Qualis AB)'].max() if df_metrics['Eixo 1 (Qualis AB)'].max() > 0 else 1
            max_eixo2 = df_metrics['Eixo 2 (Ampliada Limpa)'].max() if df_metrics['Eixo 2 (Ampliada Limpa)'].max() > 0 else 1
            max_eixo3 = df_metrics['Eixo 3 (IC)'].max() if df_metrics['Eixo 3 (IC)'].max() > 0 else 1
            
            df_metrics['Eixo 1 Norm'] = df_metrics['Eixo 1 (Qualis AB)'] / max_eixo1
            df_metrics['Eixo 2 Norm'] = df_metrics['Eixo 2 (Ampliada Limpa)'] / max_eixo2
            df_metrics['Eixo 3 Norm'] = df_metrics['Eixo 3 (IC)'] / max_eixo3
            
            df_metrics['Nota Final (0-3)'] = df_metrics['Eixo 1 Norm'] + df_metrics['Eixo 2 Norm'] + df_metrics['Eixo 3 Norm']
            df_metrics.sort_values(by='Nota Final (0-3)', ascending=False, inplace=True)
            df_metrics['Posição Ranking'] = range(1, len(df_metrics) + 1)

            # ==========================================
            # 3. INTERFACE DE RESULTADOS
            # ==========================================
            st.success("✅ Processamento concluído com sucesso!")
            
            # Preparar ficheiro para descarregar
            csv_buffer = BytesIO()
            df_metrics.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8-sig')
            
            col_res1, col_res2 = st.columns([2, 1])
            with col_res1:
                st.subheader("🏆 Top 15 - Ranking Geral")
                # Mostrar as colunas mais relevantes
                display_cols = ['Posição Ranking', 'Docente', 'Nota Final (0-3)', 'Área', 'Eixo 1 (Qualis AB)', 'Eixo 2 (Ampliada Limpa)', 'Eixo 3 (IC)']
                st.dataframe(df_metrics[display_cols].head(15), use_container_width=True, hide_index=True)
                
            with col_res2:
                st.subheader("💾 Exportação")
                st.info("Descarregue o ranking completo de todos os docentes avaliados para utilizar no edital.")
                st.download_button(
                    label="📥 Descarregar Ranking Completo (CSV)",
                    data=csv_buffer.getvalue(),
                    file_name="ranking_final_pibic_3_eixos.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            st.divider()
            
            # Gráfico visual
            st.subheader("📈 Distribuição do Ranking por Área de Conhecimento")
            fig, ax = plt.subplots(figsize=(10, 5))
            sns.boxplot(data=df_metrics, x='Área', y='Posição Ranking', palette='Set2', ax=ax)
            ax.set_title('Competitividade por Área (Quanto mais perto do topo, melhor)')
            ax.invert_yaxis()
            ax.set_ylabel('Posição no Ranking')
            plt.xticks(rotation=15)
            st.pyplot(fig)
else:
    st.warning("⚠️ Aguarda o upload de ambos os ficheiros para iniciar o cálculo.")
