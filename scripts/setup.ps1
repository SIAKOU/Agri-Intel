# AgriIntel360 - Script de démarrage rapide
# Usage: .\scripts\setup.ps1

Write-Host "🌍 AgriIntel360 - Configuration initiale" -ForegroundColor Green

# Vérifier si Docker est installé
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker trouvé: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker n'est pas installé. Veuillez installer Docker Desktop." -ForegroundColor Red
    exit 1
}

# Vérifier si Docker Compose est disponible
try {
    $composeVersion = docker-compose --version
    Write-Host "✅ Docker Compose trouvé: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose n'est pas disponible." -ForegroundColor Red
    exit 1
}

# Créer le fichier .env s'il n'existe pas
if (-Not (Test-Path ".env")) {
    Write-Host "📝 Création du fichier .env..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Fichier .env créé. Veuillez le personnaliser avec vos clés API." -ForegroundColor Green
}

# Créer les répertoires nécessaires
Write-Host "📁 Création des répertoires..." -ForegroundColor Yellow
$directories = @("logs", "uploads", "data", "infrastructure/monitoring")
foreach ($dir in $directories) {
    if (-Not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  ✅ $dir" -ForegroundColor Green
    }
}

# Configuration de monitoring
Write-Host "📊 Configuration du monitoring..." -ForegroundColor Yellow

# Créer le fichier prometheus.yml
$prometheusConfig = @"
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'agriintel360-backend'
    static_configs:
      - targets: ['backend:8000']
        labels:
          service: 'agriintel360-api'
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
    scrape_interval: 30s
"@

$prometheusConfig | Out-File -FilePath "infrastructure/monitoring/prometheus.yml" -Encoding UTF8

Write-Host "✅ Configuration Prometheus créée" -ForegroundColor Green

# Démarrer les services
Write-Host "🚀 Démarrage des services..." -ForegroundColor Yellow

try {
    # Démarrer les bases de données d'abord
    Write-Host "  📊 Démarrage des bases de données..." -ForegroundColor Cyan
    docker-compose up -d postgres mongodb redis elasticsearch
    
    # Attendre que les BDD soient prêtes
    Write-Host "  ⏳ Attente de la disponibilité des bases de données (30s)..." -ForegroundColor Cyan
    Start-Sleep -Seconds 30
    
    # Démarrer les autres services
    Write-Host "  🔧 Démarrage des services applicatifs..." -ForegroundColor Cyan
    docker-compose up -d
    
    Write-Host "✅ Tous les services sont démarrés!" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Erreur lors du démarrage des services: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Afficher les URLs d'accès
Write-Host "`n🌐 URLs d'accès:" -ForegroundColor Green
Write-Host "  • Frontend:         http://localhost:3000" -ForegroundColor Cyan
Write-Host "  • API Backend:      http://localhost:8000" -ForegroundColor Cyan
Write-Host "  • API Documentation: http://localhost:8000/api/v1/docs" -ForegroundColor Cyan
Write-Host "  • Airflow:          http://localhost:8080" -ForegroundColor Cyan
Write-Host "  • Prometheus:       http://localhost:9090" -ForegroundColor Cyan
Write-Host "  • Grafana:          http://localhost:3001" -ForegroundColor Cyan
Write-Host "  • RabbitMQ:         http://localhost:15672" -ForegroundColor Cyan

Write-Host "`n🔐 Identifiants par défaut:" -ForegroundColor Yellow
Write-Host "  • Airflow:    admin / admin" -ForegroundColor White
Write-Host "  • Grafana:    admin / secure_password_123" -ForegroundColor White
Write-Host "  • RabbitMQ:   admin / secure_password_123" -ForegroundColor White

Write-Host "`n📋 Prochaines étapes:" -ForegroundColor Green
Write-Host "  1. Configurer vos clés API dans le fichier .env" -ForegroundColor White
Write-Host "  2. Accéder à http://localhost:8000/api/v1/docs pour tester l'API" -ForegroundColor White
Write-Host "  3. Créer votre premier utilisateur via l'API" -ForegroundColor White
Write-Host "  4. Accéder au frontend sur http://localhost:3000" -ForegroundColor White

Write-Host "`n🎉 AgriIntel360 est prêt! Bon développement!" -ForegroundColor Green