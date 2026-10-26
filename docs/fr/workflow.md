# Documentation du Workflow du Projet

Ce document explique comment les données circulent dans le projet, de l'extraction à la visualisation.

## 1. Architecture Globale
Le projet est divisé en deux parties principales :
- **Frontend** : Interface utilisateur (Angular) pour visualiser les données.
- **Backend** : Extraction des données, transformation et API (Python/Flask).

---

## 2. Le Backend : Pipeline de Données
Le backend utilise une architecture **Medallion** pour organiser les données dans la base de données PostgreSQL.

### Étape 1 : Couche Bronze (Extraction Raw)
- Les données sont extraites de deux sources : fichiers **CSV** (Stooq) et **API REST** (Tiingo).
- Elles sont stockées telles quelles dans le schéma `bronze` de la base de données.
- Fichier : `backend/data_pipeline/medallion/bronze_layer.py`

### Étape 2 : Couche Silver (Nettoyage & Standardisation)
- Les données de la couche Bronze sont fusionnées et nettoyées.
- On standardise les colonnes (Open, High, Low, Close, Volume) et on supprime les doublons.
- Les données propres sont stockées dans le schéma `silver`.
- Fichier : `backend/data_pipeline/medallion/silver_layer.py`

### Étape 3 : Couche Gold (Calcul des KPIs)
- C'est la couche finale pour l'analyse.
- On calcule des indicateurs financiers (KPIs) comme les moyennes mobiles (SMA), le rendement mensuel, la volatilité et le drawdown.
- Les résultats sont stockés dans le schéma `gold`.
- Fichier : `backend/data_pipeline/medallion/gold_layer.py`

---

## 3. Le Backend : API Linking
L'API sert de pont entre la base de données et le frontend.

- **Serveur Flask** : Initialisé dans `backend/api/`.
- **Routes** : Situées dans `backend/api/routes/`, elles permettent de récupérer les données propres (Silver) et les indicateurs (Gold) au format JSON.
- **Lancement** : Utiliser `backend/start_api.py`.

---

## 4. Frontend : Visualisation
- Le frontend récupère les données via des appels HTTP vers l'API.
- Les données sont ensuite affichées sous forme de graphiques interactifs (Candlesticks, Volatilité, Drawdown).

---

## 5. Automatisation
Le pipeline de données peut être exécuté manuellement ou via une tâche planifiée (Windows Task Scheduler) en utilisant le script :
- `backend/run_pipeline.bat` (exécute `backend/data_pipeline/main.py`).
