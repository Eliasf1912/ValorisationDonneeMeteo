# Backend - API Meteo

API REST Django/DRF pour les donnees meteorologiques InfoClimat.

## Prerequis

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) pour la gestion des dependances
- Docker pour TimescaleDB et les services de monitoring

## Installation

Depuis la racine du projet :

```bash
cd backend
uv sync --group dev
cp .env.example .env
```

## Donnees simulees

Le backend peut fonctionner sans donnees meteo reelles. Dans `.env`, definir :

```env
MOCKED_DATA=true
```

Pour utiliser la base TimescaleDB et les donnees reelles, definir `MOCKED_DATA=false` et demarrer la base avec Docker Compose.

## Demarrage

### API seule

```bash
cd backend
uv run python manage.py runserver
```

L'API est disponible sur http://localhost:8000.

### Environnement Docker complet

Depuis la racine du projet :

```bash
docker compose -f docker-compose.dev.yml up -d --build
```

Les services disponibles sont :

- API backend : http://localhost:8000
- Prometheus : http://localhost:9090
- Grafana : http://localhost:3000

## Tests et qualite

Depuis `backend/` :

```bash
uv run pytest weather/tests/unit
uv run pytest weather/tests/unit/test_date_range.py
uv run ruff check
```

La CI GitHub Actions execute les tests unitaires Pytest et Ruff. Elle genere aussi un rapport de tests JUnit telechargeable depuis les artifacts du run.

## CI/CD et securite

Le workflow est defini dans [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

Pour le backend, il :

- installe les dependances avec `uv`
- execute les tests unitaires et Ruff
- analyse le code et les dependances avec Trivy
- publie les resultats Trivy en SARIF dans l'onglet Security de GitHub
- exporte un rapport Trivy JSON et un fichier VEX comme artifacts telechargeables
- construit et publie l'image backend sur GHCR uniquement lors d'un push sur `main`

L'image de production utilise une Docker Hardened Image Python et s'execute avec un utilisateur non-root.

## Monitoring Prometheus

Le projet utilise `django-prometheus` pour exposer les metriques du backend sur :

```text
http://localhost:8000/metrics
```

Prometheus scrape le backend via le nom de service Docker `backend:8000`. Dans l'interface Prometheus, aller dans **Status > Targets** et verifier que les cibles `backend` et `prometheus` sont `UP`.

Quelques metriques utiles :

- `django_http_requests_total_by_method_total`
- metriques de temps et de volume des requetes HTTP
- metriques des requetes PostgreSQL
- utilisation memoire du processus backend

Grafana est provisionne automatiquement avec Prometheus comme datasource et le dashboard **Meteo Backend Dashboard**. Les identifiants locaux par defaut sont `admin` / `admin`.

Le monitoring Prometheus couvre le backend Django. Le frontend Nuxt n'est pas une cible Prometheus dans ce projet.

## API

| Endpoint                                 | Description                        |
| ---------------------------------------- | ---------------------------------- |
| `/api/v1/stations/`                      | Liste des stations meteo           |
| `/api/v1/temperature/national-indicator` | Indicateur thermique national      |
| `/api/v1/temperature/deviation`          | Ecart a la normale                 |
| `/api/v1/temperature/records`            | Records de temperature par station |
| `/metrics`                               | Metriques Prometheus du backend    |

Exemple :

```bash
curl "http://localhost:8000/api/v1/temperature/national-indicator?date_start=2025-01-01&date_end=2025-01-31&granularity=month"
```

Les specifications OpenAPI sont disponibles dans [`openapi/target-specs/openapi.yaml`](openapi/target-specs/openapi.yaml).

## Architecture

Le backend ne manipule pas directement les tables sources via l'ORM Django. Les modeles Django s'appuient sur des vues SQL, puis les data sources et services metier construisent les reponses de l'API.

```text
Tables sources -> vues SQL -> modeles Django -> data sources -> services metier -> API REST
```

## Base de developpement

TimescaleDB peut etre demarree avec :

```bash
docker compose -f docker-compose.dev.yml up -d timescaledb
```

Les scripts de seed et les fichiers SQL associes se trouvent dans `backend/dev_scripts/` et `backend/sql/`. Les fichiers de donnees necessaires au seed sont documentes dans la configuration de l'environnement de developpement.
