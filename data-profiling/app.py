import pandas as pd
from ydata_profiling import ProfileReport
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from config import get_database_connection, close_database_connection  # type: ignore

def extract_gold_table(table_name="gold.ohlcv_kpis"):
    conn = get_database_connection()
    try:
        df = pd.read_sql_query(f'SELECT * FROM {table_name}', conn)
        return df
    finally:
        close_database_connection(conn)

def generate_gold_report(gold_df, output_path="gold_report.html"):
    profile = ProfileReport(gold_df, title="Rapport de Profilage - Schéma Gold")
    
    # Generate HTML report content
    html_content = profile.to_html()
    
    # Translate major UI elements to French
    translations = {
        "Overview": "Aperçu",
        "Variables": "Variables",
        "Interactions": "Interactions",
        "Correlations": "Corrélations",
        "Missing values": "Valeurs manquantes",
        "Sample": "Échantillon",
        "Dataset statistics": "Statistiques du jeu de données",
        "Variable types": "Types de variables",
        "Warnings": "Avertissements",
        "Number of variables": "Nombre de variables",
        "Number of observations": "Nombre d'observations",
        "Missing cells": "Cellules manquantes",
        "Missing cells (%)": "Cellules manquantes (%)",
        "Duplicate rows": "Lignes dupliquées",
        "Duplicate rows (%)": "Lignes dupliquées (%)",
        "Total size in memory": "Taille totale en mémoire",
        "Average record size in memory": "Taille moyenne par ligne",
        "Numeric": "Numérique",
        "Categorical": "Catégoriel",
        "DateTime": "Date et Heure",
        "Boolean": "Booléen",
        "Rejected": "Rejeté",
        "Distinct": "Distinct",
        "Distinct (%)": "Distinct (%)",
        "Missing": "Manquant",
        "Missing (%)": "Manquant (%)",
        "Infinite": "Infini",
        "Infinite (%)": "Infini (%)",
        "Mean": "Moyenne",
        "Minimum": "Minimum",
        "Maximum": "Maximum",
        "Zeros": "Zéros",
        "Zeros (%)": "Zéros (%)",
        "Rows": "Lignes"
    }
    
    for en, fr in translations.items():
        html_content = html_content.replace(f">{en}<", f">{fr}<")
        html_content = html_content.replace(f'"{en}"', f'"{fr}"')
        
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Generate PDF report
    try:
        profile.to_file(output_path.replace(".html", ".pdf"))
    except Exception as e:
        print(f"PDF report could not be generated: {e}")

if __name__ == "__main__":
    gold_df = extract_gold_table()
    if gold_df is not None and len(gold_df) > 0:
        generate_gold_report(gold_df)
    else:
        print("No data found in gold.ohlcv_kpis to profile.")
