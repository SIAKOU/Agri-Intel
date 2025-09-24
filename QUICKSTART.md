# 🚀 Guide de Démarrage Rapide - AgriIntel360

## 📋 Prérequis

- **Docker Desktop** installé et démarré
- **PowerShell 5.0+** (Windows)
- **4GB RAM minimum** disponible
- **Port 3000, 8000, 5432, 27017, 6379, 9200** libres

## ⚡ Démarrage en 2 minutes

### 1. Configuration initiale

```powershell
# Dans PowerShell, depuis le dossier du projet
.\scripts\setup.ps1
```

Ce script va :
- ✅ Vérifier Docker
- 📝 Créer le fichier `.env`
- 🏗️ Créer l'architecture des dossiers
- 🚀 Démarrer tous les services
- 📊 Configurer le monitoring

### 2. Tester l'API

```powershell
# Tester que tout fonctionne
.\scripts\test-api.ps1
```

### 3. Accéder aux services

| Service | URL | Identifiants |
|---------|-----|--------------|
| 🌐 **Frontend** | http://localhost:3000 | - |
| 📡 **API Backend** | http://localhost:8000 | - |
| 📖 **Documentation API** | http://localhost:8000/api/v1/docs | - |
| 🔄 **Airflow** | http://localhost:8080 | admin / admin |
| 📊 **Grafana** | http://localhost:3001 | admin / secure_password_123 |
| 🐰 **RabbitMQ** | http://localhost:15672 | admin / secure_password_123 |

## 🔧 Configuration des clés API

Éditez le fichier `.env` et ajoutez vos clés :

```env
# APIs Externes
OPENWEATHER_API_KEY=votre_cle_openweather
FAO_API_KEY=votre_cle_fao
MAPBOX_ACCESS_TOKEN=votre_token_mapbox

# IA/ML
OPENAI_API_KEY=votre_cle_openai
HUGGINGFACE_API_KEY=votre_cle_huggingface

# Notifications
SMTP_USERNAME=votre_email@gmail.com
SMTP_PASSWORD=votre_mot_de_passe_app
TWILIO_ACCOUNT_SID=votre_twilio_sid
```

## 📱 Premier test de l'API

```powershell
# 1. Créer un utilisateur admin
$user = @{
    email = "admin@agriintel360.com"
    username = "admin" 
    full_name = "Admin AgriIntel360"
    password = "AdminPassword123!"
    country = "Togo"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/register" -Method POST -Body $user -ContentType "application/json"

# 2. Se connecter
$login = @{
    username = "admin"
    password = "AdminPassword123!"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body $login -ContentType "application/json"
$token = $response.access_token

# 3. Tester un endpoint protégé
$headers = @{ Authorization = "Bearer $token" }
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/dashboard/overview" -Headers $headers
```

## 🏗️ Architecture

```
AgriIntel360/
├── 🐳 Docker Services
│   ├── PostgreSQL + PostGIS (port 5432)
│   ├── MongoDB (port 27017)
│   ├── Redis (port 6379)
│   ├── Elasticsearch (port 9200)
│   ├── FastAPI Backend (port 8000)
│   ├── Next.js Frontend (port 3000)
│   ├── Apache Airflow (port 8080)
│   ├── Prometheus (port 9090)
│   ├── Grafana (port 3001)
│   └── RabbitMQ (port 15672)
│
├── 📁 Backend (FastAPI + Python)
│   ├── API REST + GraphQL
│   ├── Authentification JWT
│   ├── WebSocket temps réel
│   ├── Modèles ML intégrés
│   └── Pipelines ETL
│
├── 📁 Frontend (React + Next.js) [À développer]
│   ├── Tableaux de bord interactifs
│   ├── Cartes géospatiales
│   ├── Visualisations D3.js
│   └── Interface responsive
│
└── 📁 Data Pipeline (Apache Airflow)
    ├── Collecte API externes
    ├── Transformation données
    ├── Modèles ML automatisés
    └── Génération d'alertes
```

## 🛑 Arrêter les services

```powershell
docker-compose down
```

## 🔄 Redémarrer les services

```powershell
docker-compose up -d
```

## 📊 Monitoring

- **Logs des services** : `docker-compose logs -f [service]`
- **Métriques** : http://localhost:9090 (Prometheus)
- **Dashboards** : http://localhost:3001 (Grafana)
- **Santé API** : http://localhost:8000/health/detailed

## 🐛 Dépannage

### Problème de ports occupés
```powershell
# Vérifier les ports utilisés
netstat -an | findstr "LISTENING"

# Arrêter tous les conteneurs
docker-compose down
```

### Problème de base de données
```powershell
# Supprimer les volumes et recréer
docker-compose down -v
docker-compose up -d
```

### Logs de débogage
```powershell
# Voir les logs d'un service
docker-compose logs backend
docker-compose logs postgres
```

## 🚀 Développement

### Backend
```powershell
# Installer les dépendances Python
cd backend
pip install -r requirements.txt

# Lancer en mode développement
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (À développer)
```bash
cd frontend
npm install
npm run dev
```

## 📚 Ressources

- 📖 **Documentation API** : http://localhost:8000/api/v1/docs
- 🔗 **WebSocket Test** : ws://localhost:8000/ws/{user_id}
- 📊 **Métriques Prometheus** : http://localhost:8000/metrics
- 🏥 **Health Check** : http://localhost:8000/health

---

🎉 **AgriIntel360 est maintenant prêt !** Commencez par tester l'API et développer votre frontend !

Pour plus de détails, consultez le [README.md](README.md) principal.