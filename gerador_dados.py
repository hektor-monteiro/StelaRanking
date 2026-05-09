import pandas as pd
import numpy as np

# Configurações de base para as 4 categorias
categorias = {
    "Exatas Artigo": {"area": "Exatas Artigo", "q": "A1", "jif": 5.2, "conf": 0.1, "book": 0.0, "tech": 0.0, "h_base": 30},
    "Exatas Tech":   {"area": "Exatas Tech", "q": "A2", "jif": 2.8, "conf": 0.5, "book": 0.1, "tech": 1.2, "h_base": 20},
    "Humanas":       {"area": "Humanas", "q": "A1", "jif": 0.2, "conf": 0.3, "book": 1.5, "tech": 0.0, "h_base": 15},
    "Computação":    {"area": "Computação", "q": "A3", "jif": 0.9, "conf": 4.0, "book": 0.2, "tech": 0.8, "h_base": 25}
}

docentes, pessoas, producoes = [], [], []

for cat_nome, c in categorias.items():
    for maturidade in ["Sênior", "Junior"]:
        for prod in ["Alta", "Média", "Baixa"]:
            nome = f"{cat_nome} | {maturidade} | {prod}"
            docentes.append(nome)
            
            # Multiplicadores
            m_mat = 1.0 if maturidade == "Sênior" else 0.3
            m_prod = 1.0 if prod == "Alta" else (0.5 if prod == "Média" else 0.2)
            
            # Cálculo de volumes
            vol_base = 40 * m_prod
            n_artigos = max(1, int(vol_base * (1.0 if cat_nome == "Exatas Artigo" else 0.6)))
            n_orient = max(0, int(25 * m_mat * m_prod))
            val_h = max(1, int(c["h_base"] * m_mat * (0.8 + m_prod/2)))
            
            # Eixo 5: Pessoas
            pessoas.append({
                "Nome": nome,
                "Área da titulação máxima informada no CV-Lattes": c["area"],
                "Índice H (todos os anos)": val_h,
                "Citações (todos os anos)": val_h * 25,
                "Índice i10 (todos os anos)": int(val_h * 0.8)
            })
            
            # Eixo 1, 2, 6: Artigos
            for _ in range(n_artigos):
                producoes.append({
                    "Informada por": nome, 
                    "Tipo agrupador da produção": "Produção bibliográfica",
                    "Tipo da produção": "Artigo publicado em periódicos",
                    "Estrato Qualis (2017/2020) unificado": c["q"],
                    "Journal Impact Factor (JIF) – WoS (ano da produção)": str(round(c["jif"], 2)).replace('.', ',')
                })
            
            # Eixo 3: Produção Ampliada
            for _ in range(int(vol_base * c["conf"])):
                producoes.append({"Informada por": nome, "Tipo agrupador da produção": "Produção bibliográfica", "Tipo da produção": "Trabalho publicado em anais de evento"})
            for _ in range(int(vol_base * c["book"])):
                producoes.append({"Informada por": nome, "Tipo agrupador da produção": "Produção bibliográfica", "Tipo da produção": "Livro publicado"})
            for _ in range(int(vol_base * c["tech"])):
                producoes.append({"Informada por": nome, "Tipo agrupador da produção": "Produção técnica", "Tipo da produção": "Patentes e registros"})
            
            # Eixo 4: Orientações
            for _ in range(n_orient):
                producoes.append({"Informada por": nome, "Tipo agrupador da produção": "Orientação concluída", "Tipo da produção": "Dissertação de mestrado"})

# --- EXPORTAÇÃO CORRIGIDA ---

# 1. Docentes (Skip 7 + 1 linha de lixo para o iloc[1:])
with open('sim_24_docentes.csv', 'w', encoding='utf-8') as f:
    for i in range(7): f.write(f"lixo_linha_{i+1}\n")
    f.write("Nome\n")         # Cabeçalho (linha 8)
    f.write("lixo_extra\n")  # Linha que o seu código pula com .iloc[1:]
    for d in docentes: f.write(f"{d}\n")

# 2. Pessoas (Skip 3)
df_p = pd.DataFrame(pessoas)
with open('sim_24_pessoas.csv', 'w', encoding='utf-8') as f:
    for i in range(3): f.write(f"lixo,lixo,lixo,lixo,lixo\n")
    df_p.to_csv(f, index=False)

# 3. Produções (Skip 3)
df_prod = pd.DataFrame(producoes)
with open('sim_24_producao.csv', 'w', encoding='utf-8') as f:
    for i in range(3): f.write(f"lixo;lixo;lixo;lixo;lixo;lixo\n")
    df_prod.to_csv(f, index=False, sep=';')

print("✅ 24 Perfis Gerados com Sucesso!")
