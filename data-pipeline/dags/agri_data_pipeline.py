"""
AgriIntel360 - Pipeline ETL Principal
DAG pour la collecte, transformation et chargement des données agricoles
"""

from datetime import datetime, timedelta
import pandas as pd
import requests
import psycopg2
from sqlalchemy import create_engine
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.models import Variable

# Configuration
default_args = {
    'owner': 'agriintel360',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Création du DAG
dag = DAG(
    'agri_data_pipeline',
    default_args=default_args,
    description='Pipeline de données agricoles complet',
    schedule_interval='@daily',
    catchup=False,
    max_active_runs=1,
)

# Configuration des connexions
DATABASE_URL = Variable.get("DATABASE_URL", default_var="postgresql://admin:secure_password_123@postgres:5432/agriintel360")
FAO_API_KEY = Variable.get("FAO_API_KEY", default_var="")
OPENWEATHER_API_KEY = Variable.get("OPENWEATHER_API_KEY", default_var="")
WORLD_BANK_API_KEY = Variable.get("WORLD_BANK_API_KEY", default_var="")

def extract_fao_data(**context):
    """Extraction des données FAO"""
    print("🌾 Extraction des données FAO...")
    
    # URLs FAO pour les données agricoles
    fao_urls = {
        'production': 'http://www.fao.org/faostat/api/v1/en/data/QCL',
        'prices': 'http://www.fao.org/faostat/api/v1/en/data/PP',
        'trade': 'http://www.fao.org/faostat/api/v1/en/data/TM',
    }
    
    extracted_data = {}
    
    for data_type, url in fao_urls.items():
        try:
            # Paramètres pour les pays d'Afrique de l'Ouest
            params = {
                'area': '231,232,233,234,288,270,183,53',  # Codes FAO des pays
                'years': f'{datetime.now().year-5}:{datetime.now().year}',
                'format': 'json'
            }
            
            if FAO_API_KEY:
                params['api_key'] = FAO_API_KEY
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            extracted_data[data_type] = data.get('data', [])
            
            print(f"  ✅ {data_type}: {len(extracted_data[data_type])} enregistrements")
            
        except Exception as e:
            print(f"  ❌ Erreur {data_type}: {e}")
            extracted_data[data_type] = []
    
    # Stockage temporaire
    context['task_instance'].xcom_push(key='fao_data', value=extracted_data)
    return extracted_data

def extract_weather_data(**context):
    """Extraction des données météorologiques"""
    print("🌤️ Extraction des données météo...")
    
    # Coordonnées des capitales d'Afrique de l'Ouest
    capitals = {
        'Abidjan': {'lat': 5.3600, 'lon': -4.0083, 'country': 'CI'},
        'Accra': {'lat': 5.6037, 'lon': -0.1870, 'country': 'GH'},
        'Lagos': {'lat': 6.5244, 'lon': 3.3792, 'country': 'NG'},
        'Dakar': {'lat': 14.7167, 'lon': -17.4677, 'country': 'SN'},
        'Bamako': {'lat': 12.6392, 'lon': -8.0029, 'country': 'ML'},
        'Ouagadougou': {'lat': 12.3714, 'lon': -1.5197, 'country': 'BF'},
        'Lomé': {'lat': 6.1375, 'lon': 1.2123, 'country': 'TG'},
    }
    
    weather_data = []
    
    if not OPENWEATHER_API_KEY:
        print("  ⚠️ Pas de clé API OpenWeather - génération de données simulées")
        # Générer des données simulées pour la démo
        for city, coords in capitals.items():
            weather_data.append({
                'city': city,
                'country': coords['country'],
                'temperature': 25 + (hash(city) % 15),
                'humidity': 60 + (hash(city) % 30),
                'precipitation': (hash(city) % 100) / 10,
                'date': datetime.now().date(),
                'lat': coords['lat'],
                'lon': coords['lon']
            })
    else:
        for city, coords in capitals.items():
            try:
                url = f"http://api.openweathermap.org/data/2.5/weather"
                params = {
                    'lat': coords['lat'],
                    'lon': coords['lon'],
                    'appid': OPENWEATHER_API_KEY,
                    'units': 'metric'
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                weather_data.append({
                    'city': city,
                    'country': coords['country'],
                    'temperature': data['main']['temp'],
                    'humidity': data['main']['humidity'],
                    'precipitation': data.get('rain', {}).get('1h', 0),
                    'date': datetime.now().date(),
                    'lat': coords['lat'],
                    'lon': coords['lon']
                })
                
            except Exception as e:
                print(f"  ❌ Erreur météo {city}: {e}")
    
    print(f"  ✅ Données météo: {len(weather_data)} enregistrements")
    context['task_instance'].xcom_push(key='weather_data', value=weather_data)
    return weather_data

def extract_world_bank_data(**context):
    """Extraction des données Banque Mondiale"""
    print("🏛️ Extraction des données Banque Mondiale...")
    
    # Indicateurs économiques importants
    indicators = {
        'AG.LND.AGRI.ZS': 'agricultural_land_percent',
        'AG.PRD.CREL.MT': 'cereal_production',
        'NY.GDP.MKTP.CD': 'gdp',
        'SP.POP.TOTL': 'population',
        'AG.CON.FERT.ZS': 'fertilizer_consumption',
    }
    
    # Codes ISO des pays
    countries = ['BF', 'CI', 'GH', 'ML', 'NG', 'SN', 'TG', 'BJ', 'NE', 'CM']
    
    wb_data = []
    
    for indicator, name in indicators.items():
        try:
            url = f"https://api.worldbank.org/v2/country/{';'.join(countries)}/indicator/{indicator}"
            params = {
                'format': 'json',
                'date': f'{datetime.now().year-5}:{datetime.now().year}',
                'per_page': 1000
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if len(data) > 1:
                for item in data[1]:  # Les données sont dans le deuxième élément
                    if item['value']:
                        wb_data.append({
                            'country_code': item['country']['id'],
                            'country_name': item['country']['value'],
                            'indicator': name,
                            'year': item['date'],
                            'value': item['value'],
                            'date_extracted': datetime.now()
                        })
            
        except Exception as e:
            print(f"  ❌ Erreur indicateur {indicator}: {e}")
    
    print(f"  ✅ Données Banque Mondiale: {len(wb_data)} enregistrements")
    context['task_instance'].xcom_push(key='wb_data', value=wb_data)
    return wb_data

def transform_data(**context):
    """Transformation et nettoyage des données"""
    print("🔄 Transformation des données...")
    
    # Récupération des données extraites
    fao_data = context['task_instance'].xcom_pull(key='fao_data') or {}
    weather_data = context['task_instance'].xcom_pull(key='weather_data') or []
    wb_data = context['task_instance'].xcom_pull(key='wb_data') or []
    
    transformed_data = {
        'production': [],
        'weather': [],
        'economic': []
    }
    
    # Transformation des données de production FAO
    if fao_data.get('production'):
        for item in fao_data['production'][:100]:  # Limiter pour la démo
            transformed_data['production'].append({
                'country_code': item.get('area_code'),
                'country_name': item.get('area'),
                'crop_code': item.get('item_code'),
                'crop_name': item.get('item'),
                'year': item.get('year'),
                'production_tonnes': item.get('value'),
                'unit': item.get('unit'),
                'data_quality': 'official' if item.get('flag') == '' else 'estimated',
                'created_at': datetime.now()
            })
    
    # Transformation des données météo
    for item in weather_data:
        transformed_data['weather'].append({
            'country_code': item['country'],
            'city': item['city'],
            'latitude': item['lat'],
            'longitude': item['lon'],
            'date': item['date'],
            'temperature_celsius': item['temperature'],
            'humidity_percent': item['humidity'],
            'precipitation_mm': item['precipitation'],
            'source': 'openweather',
            'created_at': datetime.now()
        })
    
    # Transformation des données économiques
    for item in wb_data:
        transformed_data['economic'].append({
            'country_code': item['country_code'],
            'country_name': item['country_name'],
            'indicator': item['indicator'],
            'year': int(item['year']),
            'value': float(item['value']),
            'source': 'worldbank',
            'created_at': datetime.now()
        })
    
    print(f"  ✅ Production: {len(transformed_data['production'])} enregistrements")
    print(f"  ✅ Météo: {len(transformed_data['weather'])} enregistrements")
    print(f"  ✅ Économie: {len(transformed_data['economic'])} enregistrements")
    
    context['task_instance'].xcom_push(key='transformed_data', value=transformed_data)
    return transformed_data

def load_data(**context):
    """Chargement des données dans PostgreSQL"""
    print("💾 Chargement des données...")
    
    transformed_data = context['task_instance'].xcom_pull(key='transformed_data')
    
    if not transformed_data:
        print("  ❌ Aucune donnée transformée à charger")
        return
    
    try:
        # Connexion à PostgreSQL
        engine = create_engine(DATABASE_URL)
        
        # Chargement des données de production
        if transformed_data['production']:
            df_production = pd.DataFrame(transformed_data['production'])
            df_production.to_sql('staging_production', engine, if_exists='append', index=False)
            print(f"  ✅ Production: {len(df_production)} enregistrements chargés")
        
        # Chargement des données météo
        if transformed_data['weather']:
            df_weather = pd.DataFrame(transformed_data['weather'])
            df_weather.to_sql('staging_weather', engine, if_exists='append', index=False)
            print(f"  ✅ Météo: {len(df_weather)} enregistrements chargés")
        
        # Chargement des données économiques
        if transformed_data['economic']:
            df_economic = pd.DataFrame(transformed_data['economic'])
            df_economic.to_sql('staging_economic', engine, if_exists='append', index=False)
            print(f"  ✅ Économie: {len(df_economic)} enregistrements chargés")
        
        print("  ✅ Toutes les données chargées avec succès!")
        
    except Exception as e:
        print(f"  ❌ Erreur lors du chargement: {e}")
        raise

def run_ml_predictions(**context):
    """Exécution des modèles de prédiction ML"""
    print("🤖 Exécution des prédictions ML...")
    
    try:
        # Ici nous appellerions nos modèles ML
        # Pour la démo, nous simulons les prédictions
        predictions = {
            'yield_predictions': [
                {'country': 'TG', 'crop': 'mais', 'predicted_yield': 2.5, 'confidence': 0.85},
                {'country': 'GH', 'crop': 'cacao', 'predicted_yield': 0.8, 'confidence': 0.92},
            ],
            'price_predictions': [
                {'country': 'NG', 'crop': 'riz', 'predicted_price': 450, 'confidence': 0.78},
                {'country': 'CI', 'crop': 'mais', 'predicted_price': 380, 'confidence': 0.81},
            ]
        }
        
        print(f"  ✅ Prédictions générées: {len(predictions['yield_predictions'])} rendements")
        print(f"  ✅ Prédictions générées: {len(predictions['price_predictions'])} prix")
        
        return predictions
        
    except Exception as e:
        print(f"  ❌ Erreur ML: {e}")
        raise

# Définition des tâches
extract_fao_task = PythonOperator(
    task_id='extract_fao_data',
    python_callable=extract_fao_data,
    dag=dag,
)

extract_weather_task = PythonOperator(
    task_id='extract_weather_data',
    python_callable=extract_weather_data,
    dag=dag,
)

extract_wb_task = PythonOperator(
    task_id='extract_world_bank_data',
    python_callable=extract_world_bank_data,
    dag=dag,
)

transform_task = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_data',
    python_callable=load_data,
    dag=dag,
)

ml_predictions_task = PythonOperator(
    task_id='run_ml_predictions',
    python_callable=run_ml_predictions,
    dag=dag,
)

# Définition des dépendances
[extract_fao_task, extract_weather_task, extract_wb_task] >> transform_task >> load_task >> ml_predictions_task