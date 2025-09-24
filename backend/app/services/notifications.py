"""
AgriIntel360 - Système d'Alertes et Notifications
Service complet pour gérer les alertes temps réel avec multi-canaux
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from enum import Enum

from fastapi import BackgroundTasks
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from twilio.rest import Client as TwilioClient
import requests

from app.core.config import get_settings
from app.core.database import get_redis, get_db, get_mongodb
from app.api.websocket import manager as websocket_manager
from app.models.sql.user import User
from app.models.sql.agricultural import Alert, Country, Crop

settings = get_settings()


class AlertType(str, Enum):
    """Types d'alertes"""
    WEATHER = "weather"
    PRICE = "price"
    YIELD = "yield"
    DROUGHT = "drought"
    FLOOD = "flood"
    PEST = "pest"
    MARKET = "market"
    TECHNICAL = "technical"
    SYSTEM = "system"


class AlertSeverity(str, Enum):
    """Niveaux de sévérité"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class NotificationChannel(str, Enum):
    """Canaux de notification"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBSOCKET = "websocket"
    SLACK = "slack"
    TELEGRAM = "telegram"


class AlertCondition:
    """Condition de déclenchement d'une alerte"""
    
    def __init__(self, 
                 metric: str,
                 operator: str,  # >, <, >=, <=, ==, !=
                 value: float,
                 duration_minutes: int = 0):
        self.metric = metric
        self.operator = operator
        self.value = value
        self.duration_minutes = duration_minutes
    
    def evaluate(self, current_value: float) -> bool:
        """Évalue si la condition est remplie"""
        operators = {
            '>': lambda a, b: a > b,
            '<': lambda a, b: a < b,
            '>=': lambda a, b: a >= b,
            '<=': lambda a, b: a <= b,
            '==': lambda a, b: a == b,
            '!=': lambda a, b: a != b,
        }
        
        op_func = operators.get(self.operator)
        if not op_func:
            return False
        
        return op_func(current_value, self.value)


class NotificationService:
    """Service de notifications multi-canaux"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Configuration Email
        self.smtp_host = self.settings.SMTP_HOST
        self.smtp_port = self.settings.SMTP_PORT
        self.smtp_username = self.settings.SMTP_USERNAME
        self.smtp_password = self.settings.SMTP_PASSWORD
        
        # Configuration Twilio (SMS)
        self.twilio_client = None
        if self.settings.TWILIO_ACCOUNT_SID and self.settings.TWILIO_AUTH_TOKEN:
            self.twilio_client = TwilioClient(
                self.settings.TWILIO_ACCOUNT_SID,
                self.settings.TWILIO_AUTH_TOKEN
            )
    
    async def send_notification(self,
                              user: User,
                              alert: Dict[str, Any],
                              channels: List[NotificationChannel]):
        """Envoie une notification sur plusieurs canaux"""
        
        tasks = []
        
        for channel in channels:
            if channel == NotificationChannel.EMAIL:
                tasks.append(self._send_email(user, alert))
            elif channel == NotificationChannel.SMS:
                tasks.append(self._send_sms(user, alert))
            elif channel == NotificationChannel.WEBSOCKET:
                tasks.append(self._send_websocket(user, alert))
            elif channel == NotificationChannel.PUSH:
                tasks.append(self._send_push_notification(user, alert))
        
        # Exécuter toutes les notifications en parallèle
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_email(self, user: User, alert: Dict[str, Any]):
        """Envoie une notification par email"""
        
        if not self.smtp_host or not user.email:
            return
        
        try:
            # Création du message email
            msg = MimeMultipart('alternative')
            msg['Subject'] = f"🚨 AgriIntel360 - {alert['title']}"
            msg['From'] = self.smtp_username
            msg['To'] = user.email
            
            # Template HTML pour l'email
            html_content = self._create_email_template(user, alert)
            
            # Ajout du contenu
            html_part = MimeText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Envoi de l'email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.settings.SMTP_TLS:
                    server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Email envoyé à {user.email}")
            
        except Exception as e:
            print(f"❌ Erreur envoi email: {e}")
    
    async def _send_sms(self, user: User, alert: Dict[str, Any]):
        """Envoie une notification par SMS"""
        
        if not self.twilio_client or not user.phone_number:
            return
        
        try:
            # Message SMS court
            sms_message = f"🚨 AgriIntel360: {alert['title']}\n{alert['message'][:100]}..."
            
            message = self.twilio_client.messages.create(
                body=sms_message,
                from_=self.settings.TWILIO_PHONE_NUMBER,
                to=user.phone_number
            )
            
            print(f"✅ SMS envoyé à {user.phone_number}: {message.sid}")
            
        except Exception as e:
            print(f"❌ Erreur envoi SMS: {e}")
    
    async def _send_websocket(self, user: User, alert: Dict[str, Any]):
        """Envoie une notification via WebSocket"""
        
        try:
            websocket_message = {
                'type': 'alert',
                'data': alert,
                'timestamp': datetime.now().isoformat()
            }
            
            await websocket_manager.send_personal_message(
                websocket_message, 
                str(user.id)
            )
            
            print(f"✅ WebSocket envoyé à l'utilisateur {user.id}")
            
        except Exception as e:
            print(f"❌ Erreur WebSocket: {e}")
    
    async def _send_push_notification(self, user: User, alert: Dict[str, Any]):
        """Envoie une notification push (à implémenter avec FCM)"""
        
        # TODO: Implémenter Firebase Cloud Messaging
        print(f"📱 Push notification (à implémenter): {alert['title']}")
    
    def _create_email_template(self, user: User, alert: Dict[str, Any]) -> str:
        """Crée le template HTML pour l'email"""
        
        severity_colors = {
            "info": "#3B82F6",
            "warning": "#F59E0B", 
            "critical": "#EF4444",
            "emergency": "#DC2626"
        }
        
        severity_icons = {
            "info": "ℹ️",
            "warning": "⚠️",
            "critical": "🚨", 
            "emergency": "🚨"
        }
        
        severity = alert.get('severity', 'info')
        color = severity_colors.get(severity, "#3B82F6")
        icon = severity_icons.get(severity, "ℹ️")
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AgriIntel360 - Alerte</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #22c55e, #16a34a); padding: 30px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 24px; font-weight: 600;">
                        🌾 AgriIntel360
                    </h1>
                    <p style="color: rgba(255, 255, 255, 0.9); margin: 5px 0 0 0; font-size: 14px;">
                        Plateforme Intelligente de Décision Agricole
                    </p>
                </div>
                
                <!-- Alert Content -->
                <div style="padding: 30px;">
                    <div style="background-color: {color}; color: white; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                        <h2 style="margin: 0; font-size: 18px; font-weight: 600;">
                            {icon} {alert['title']}
                        </h2>
                        <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.9;">
                            Niveau: {severity.upper()}
                        </p>
                    </div>
                    
                    <div style="margin-bottom: 20px;">
                        <p style="color: #374151; line-height: 1.6; margin: 0;">
                            Bonjour {user.full_name},
                        </p>
                        <br>
                        <p style="color: #374151; line-height: 1.6; margin: 0;">
                            {alert['message']}
                        </p>
                    </div>
                    
                    {self._get_alert_details_html(alert)}
                    
                    <!-- Action Button -->
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="http://localhost:3000/dashboard" 
                           style="background-color: #22c55e; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 500; display: inline-block;">
                            Voir le Tableau de Bord
                        </a>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background-color: #f9fafb; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb;">
                    <p style="color: #6b7280; font-size: 12px; margin: 0;">
                        Vous recevez cet email car vous êtes abonné aux alertes AgriIntel360.
                    </p>
                    <p style="color: #6b7280; font-size: 12px; margin: 10px 0 0 0;">
                        © 2024 AgriIntel360 - Intelligence Agricole pour l'Afrique
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_alert_details_html(self, alert: Dict[str, Any]) -> str:
        """Génère le HTML pour les détails de l'alerte"""
        
        details = alert.get('details', {})
        if not details:
            return ""
        
        html = '<div style="background-color: #f9fafb; padding: 15px; border-radius: 6px; margin-bottom: 20px;">'
        html += '<h3 style="color: #374151; margin: 0 0 10px 0; font-size: 14px;">Détails:</h3>'
        
        for key, value in details.items():
            html += f'<p style="margin: 5px 0; font-size: 13px; color: #6b7280;"><strong>{key}:</strong> {value}</p>'
        
        html += '</div>'
        return html


class AlertService:
    """Service principal de gestion des alertes"""
    
    def __init__(self):
        self.notification_service = NotificationService()
        self.active_alerts = {}  # Cache des alertes actives
        
    async def create_alert(self,
                          title: str,
                          message: str,
                          alert_type: AlertType,
                          severity: AlertSeverity,
                          country_id: str = None,
                          crop_id: str = None,
                          user_id: str = None,
                          details: Dict[str, Any] = None,
                          expires_at: datetime = None) -> str:
        """Crée une nouvelle alerte"""
        
        try:
            # Créer l'alerte en base
            async for db in get_db():
                alert = Alert(
                    title=title,
                    message=message,
                    alert_type=alert_type.value,
                    severity=severity.value,
                    country_id=country_id,
                    crop_id=crop_id,
                    user_id=user_id,
                    data_source=details or {},
                    expires_at=expires_at or datetime.now() + timedelta(hours=24)
                )
                
                db.add(alert)
                await db.commit()
                await db.refresh(alert)
                
                alert_id = str(alert.id)
                
                # Mettre en cache
                self.active_alerts[alert_id] = {
                    'id': alert_id,
                    'title': title,
                    'message': message,
                    'type': alert_type.value,
                    'severity': severity.value,
                    'details': details,
                    'created_at': datetime.now(),
                    'expires_at': expires_at
                }
                
                # Déclencher les notifications
                await self._trigger_notifications(alert_id)
                
                return alert_id
                
        except Exception as e:
            print(f"❌ Erreur création alerte: {e}")
            raise
    
    async def _trigger_notifications(self, alert_id: str):
        """Déclenche les notifications pour une alerte"""
        
        alert_data = self.active_alerts.get(alert_id)
        if not alert_data:
            return
        
        try:
            # Récupérer les utilisateurs à notifier
            users_to_notify = await self._get_users_for_alert(alert_data)
            
            # Envoyer les notifications
            for user in users_to_notify:
                channels = await self._get_user_notification_channels(user)
                await self.notification_service.send_notification(
                    user, alert_data, channels
                )
                
        except Exception as e:
            print(f"❌ Erreur notifications: {e}")
    
    async def _get_users_for_alert(self, alert_data: Dict[str, Any]) -> List[User]:
        """Récupère les utilisateurs à notifier pour une alerte"""
        
        # TODO: Implémenter la logique de ciblage des utilisateurs
        # Basé sur les préférences, rôles, pays, cultures, etc.
        
        # Pour l'instant, retourne tous les utilisateurs actifs
        async for db in get_db():
            from sqlalchemy import select
            result = await db.execute(
                select(User).where(User.is_active == True)
            )
            return result.scalars().all()
    
    async def _get_user_notification_channels(self, user: User) -> List[NotificationChannel]:
        """Récupère les canaux de notification préférés d'un utilisateur"""
        
        # TODO: Récupérer les préférences de l'utilisateur
        # Pour l'instant, utilise les canaux par défaut
        
        channels = [NotificationChannel.WEBSOCKET]
        
        if user.email:
            channels.append(NotificationChannel.EMAIL)
        
        if user.phone_number:
            channels.append(NotificationChannel.SMS)
        
        return channels
    
    async def check_weather_conditions(self):
        """Vérifie les conditions météo et génère des alertes"""
        
        try:
            # TODO: Récupérer les données météo actuelles
            # Analyser les conditions critiques
            # Générer des alertes si nécessaire
            
            # Exemple: Alerte canicule
            temperature_threshold = 35  # °C
            
            # Simuler une vérification
            current_temp = 38  # Température simulée
            
            if current_temp > temperature_threshold:
                await self.create_alert(
                    title="Alerte Canicule",
                    message=f"Température élevée détectée: {current_temp}°C. Risque de stress hydrique pour les cultures.",
                    alert_type=AlertType.WEATHER,
                    severity=AlertSeverity.WARNING,
                    details={
                        "température": f"{current_temp}°C",
                        "seuil": f"{temperature_threshold}°C",
                        "recommandation": "Augmenter l'irrigation si possible"
                    }
                )
                
        except Exception as e:
            print(f"❌ Erreur vérification météo: {e}")
    
    async def check_price_variations(self):
        """Vérifie les variations de prix et génère des alertes"""
        
        try:
            # TODO: Analyser les variations de prix
            # Détecter les anomalies
            
            # Exemple: Chute de prix significative
            price_drop_threshold = -15  # %
            
            # Simuler une vérification
            cacao_variation = -18  # %
            
            if cacao_variation < price_drop_threshold:
                await self.create_alert(
                    title="Chute des Prix du Cacao",
                    message=f"Le prix du cacao a chuté de {abs(cacao_variation)}% cette semaine.",
                    alert_type=AlertType.PRICE,
                    severity=AlertSeverity.CRITICAL,
                    details={
                        "variation": f"{cacao_variation}%",
                        "prix_actuel": "2,450 USD/tonne",
                        "prix_précédent": "2,990 USD/tonne",
                        "impact": "Revenus agriculteurs affectés"
                    }
                )
                
        except Exception as e:
            print(f"❌ Erreur vérification prix: {e}")
    
    async def get_active_alerts(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Récupère les alertes actives"""
        
        try:
            async for db in get_db():
                from sqlalchemy import select, and_
                
                query = select(Alert).where(
                    and_(
                        Alert.is_active == True,
                        Alert.expires_at > datetime.now()
                    )
                )
                
                if user_id:
                    query = query.where(Alert.user_id == user_id)
                
                result = await db.execute(query.order_by(Alert.created_at.desc()))
                alerts = result.scalars().all()
                
                return [
                    {
                        'id': str(alert.id),
                        'title': alert.title,
                        'message': alert.message,
                        'type': alert.alert_type,
                        'severity': alert.severity,
                        'created_at': alert.created_at.isoformat(),
                        'expires_at': alert.expires_at.isoformat() if alert.expires_at else None
                    }
                    for alert in alerts
                ]
                
        except Exception as e:
            print(f"❌ Erreur récupération alertes: {e}")
            return []
    
    async def mark_alert_as_read(self, alert_id: str, user_id: str):
        """Marque une alerte comme lue"""
        
        try:
            async for db in get_db():
                result = await db.execute(
                    select(Alert).where(Alert.id == alert_id)
                )
                alert = result.scalar_one_or_none()
                
                if alert:
                    alert.is_read = True
                    await db.commit()
                    
        except Exception as e:
            print(f"❌ Erreur marquage alerte: {e}")


# Instance globale du service d'alertes
alert_service = AlertService()


async def create_system_alert(title: str, message: str, severity: AlertSeverity = AlertSeverity.INFO):
    """Créer une alerte système"""
    return await alert_service.create_alert(
        title=title,
        message=message,
        alert_type=AlertType.SYSTEM,
        severity=severity
    )


async def run_alert_checks():
    """Lance les vérifications périodiques d'alertes"""
    print("🔍 Vérifications des conditions d'alertes...")
    
    await alert_service.check_weather_conditions()
    await alert_service.check_price_variations()
    
    print("✅ Vérifications terminées")