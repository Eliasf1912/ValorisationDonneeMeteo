# CI/CD & Monitoring - Etat du projet

Ce document resume ce qui a ete mis en place cote CI/CD et monitoring (Prometheus), pour que l'equipe s'y retrouve facilement.

---

## 1. CI/CD (GitHub Actions)

Fichier : `.github/workflows/ci.yml`

### Declencheurs

- `pull_request` vers `main`
- `push` sur `main`

### Jobs

| Job                       | Role                                                                  |
| ------------------------- | --------------------------------------------------------------------- |
| `install-frontend`        | install deps, run tests (Vitest), run linter                          |
| `install-backend`         | install deps (uv), run tests (pytest), run linter (ruff)              |
| `Security-scan-frontend`  | scan Trivy (frontend)                                                 |
| `Security-scan-backend`   | scan Trivy (backend)                                                  |
| `build-and-push-frontend` | build et push image Docker sur GHCR (uniquement sur push vers `main`) |
| `build-and-push-backend`  | build et push image Docker sur GHCR (uniquement sur push vers `main`) |

### Ce qui est genere a chaque run (artifacts telechargeables)

Dans Actions, choisir un run, section Artifacts en bas de page :

- `frontend-test-report` / `backend-test-report` : resultats de tests au format JUnit XML
- `frontend-trivy-report` / `backend-trivy-report` : rapport de scan securite Trivy (JSON, lisible en dehors de GitHub)
- `frontend-vex` / `backend-vex` : fichier VEX (format OpenVEX)

Le scan Trivy est aussi envoye en SARIF vers l'onglet Security du repo (alertes classiques GitHub).

### Fichier VEX

Le fichier VEX genere declare un statut `not_affected` de facon generique pour tout le produit, pas vulnerabilite par vulnerabilite. Ce niveau est considere suffisant pour le projet : le format et le pipeline sont en place et repondent a la consigne. Reste tel quel, aucune action supplementaire requise.

### Build et push Docker

- Registry : GHCR (`ghcr.io`)
- Se declenche uniquement sur un vrai push sur `main` (pas sur les PR), donc pas de pollution du registry a chaque PR
- Images : `ghcr.io/<owner>/14_valorisationdonneemeteo-backend` et `-frontend`, tags `latest` et SHA du commit

### Badge CI

Ajoute dans le README principal du projet.

### Pipeline testing (valide)

Un test a ete volontairement casse sur une PR pour verifier que la CI le detecte (job passe en rouge, jobs dependants correctement skippes). Le test a ensuite ete corrige, la PR mergee, tout repasse au vert. Comportement confirme de bout en bout.

---

## 2. Monitoring - Prometheus

### Ce qui a ete fait

- Service `prometheus` ajoute dans `docker-compose.dev.yml`, sur le reseau `app_net`
- Config dans `prometheus/prometheus.yml`
- `django-prometheus` installe et configure cote backend (`INSTALLED_APPS`, middlewares before et after, route `/metrics` exposee)
- Prometheus scrape avec succes :
  - lui-meme (job `prometheus`, `localhost:9090`)
  - le backend Django (job `backend`, `backend:8000`, nom du service Docker et non `localhost`, vu que Prometheus tourne dans le reseau Docker interne)
- Verifie en interrogeant une vraie metrique applicative (`django_http_requests_total_by_method_total`) dans l'UI Prometheus (`localhost:9090`), resultat coherent avec les vraies requetes faites sur le backend

### Comment lancer

```bash
docker compose -f docker-compose.dev.yml up -d
```

UI Prometheus : `http://localhost:9090`
Aller dans Status puis Targets pour voir l'etat des jobs scrapes (doit afficher `prometheus` et `backend` en UP)

### Note sur le lien metrics dans l'UI Prometheus

Le lien "metrics" cliquable dans l'UI Prometheus (page Targets) peut renvoyer une erreur DNS car il utilise le hostname interne du conteneur. Ce n'est pas un bug : il suffit de taper `http://localhost:9090/metrics` directement dans la barre d'adresse pour acceder a l'endpoint depuis l'exterieur du reseau Docker.

### Reste a faire cote Prometheus

- Ajouter le frontend comme target si des metriques y sont exposees (a voir si pertinent selon la stack Nuxt)

---

## 3. Monitoring - Grafana

### Ce qui a été fait

- Service `grafana` ajouté dans `docker-compose.dev.yml` (image `grafana/grafana:latest`, port `3000:3000`, réseau `app_net`)
- Provisioning automatique de la datasource Prometheus dans `grafana/provisioning/datasources/prometheus.yml` (cible : `http://prometheus:9090`)
- Provisioning automatique des dashboards dans `grafana/provisioning/dashboards/dashboards.yml`
- Dashboard complet pré-configuré dans `grafana/dashboards/meteo_dashboard.json` avec les visualisations suivantes :
  - Statut en direct des cibles (Backend Django et Prometheus)
  - Débit de requêtes HTTP par méthode (`req/s`)
  - Répartition des codes de réponses HTTP (`2xx`, `4xx`, `5xx`)
  - Utilisation de la mémoire RAM par le backend
  - Débit d'exécution des requêtes base de données (PostgreSQL/TimescaleDB)

### Accès à Grafana

- URL : `http://localhost:3000`
- Identifiants par défaut : `admin` / `admin`
- Le tableau de bord **Meteo Backend Dashboard** est automatiquement disponible dès le démarrage sans configuration manuelle requise.


---

## 4. Docker Hardened Image (pas encore commence)

- Trouver les images hardened Python et npm sur https://dhi.io
- Adapter les Dockerfile (backend et frontend) pour utiliser ces images en base, dans une optique prod ready
