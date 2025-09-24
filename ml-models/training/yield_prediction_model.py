"""
AgriIntel360 - Modèle de Prédiction de Rendements Agricoles
Utilise XGBoost et des features d'ingénierie avancées
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class YieldPredictionModel:
    """Modèle de prédiction de rendements agricoles"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = []
        self.target_column = 'yield_tonnes_per_ha'
        
    def create_features(self, df):
        """Ingénierie des features"""
        print("🔧 Création des features...")
        
        # Copie du dataframe
        features_df = df.copy()
        
        # Features temporelles
        if 'year' in features_df.columns:
            features_df['year_sin'] = np.sin(2 * np.pi * features_df['year'] / 10)
            features_df['year_cos'] = np.cos(2 * np.pi * features_df['year'] / 10)
            features_df['years_since_2000'] = features_df['year'] - 2000
        
        # Features météorologiques dérivées
        if all(col in features_df.columns for col in ['temperature_avg', 'precipitation_total']):
            # Indice de stress hydrique
            features_df['water_stress_index'] = (features_df['temperature_avg'] - 25) / (features_df['precipitation_total'] + 1)
            
            # Indice de croissance optimal
            features_df['growth_index'] = np.where(
                (features_df['temperature_avg'] >= 20) & 
                (features_df['temperature_avg'] <= 30) & 
                (features_df['precipitation_total'] >= 500),
                1, 0
            )
            
            # Features d'interaction
            features_df['temp_precip_interaction'] = features_df['temperature_avg'] * features_df['precipitation_total'] / 1000
        
        # Features économiques dérivées
        if 'gdp_per_capita' in features_df.columns:
            features_df['gdp_log'] = np.log1p(features_df['gdp_per_capita'])
        
        if 'fertilizer_use' in features_df.columns:
            features_df['fertilizer_log'] = np.log1p(features_df['fertilizer_use'])
        
        # Features de surface
        if 'area_harvested' in features_df.columns:
            features_df['area_log'] = np.log1p(features_df['area_harvested'])
            
            # Intensité agricole (production par unité de surface)
            if 'production_total' in features_df.columns:
                features_df['intensity'] = features_df['production_total'] / (features_df['area_harvested'] + 1)
        
        # Features de tendances (moyennes mobiles)
        if 'year' in features_df.columns:
            # Grouper par pays et culture pour calculer les tendances
            for col in ['yield_tonnes_per_ha', 'temperature_avg', 'precipitation_total']:
                if col in features_df.columns:
                    features_df[f'{col}_trend_3y'] = features_df.groupby(['country', 'crop'])[col].rolling(3, min_periods=1).mean().values
                    features_df[f'{col}_volatility_3y'] = features_df.groupby(['country', 'crop'])[col].rolling(3, min_periods=1).std().fillna(0).values
        
        # Encoder les variables catégorielles
        categorical_columns = ['country', 'crop', 'season', 'soil_type']
        for col in categorical_columns:
            if col in features_df.columns:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    features_df[f'{col}_encoded'] = self.label_encoders[col].fit_transform(features_df[col].astype(str))
                else:
                    # Gérer les nouvelles catégories lors de la prédiction
                    unique_values = set(self.label_encoders[col].classes_)
                    features_df[col] = features_df[col].astype(str)
                    features_df[col] = features_df[col].apply(lambda x: x if x in unique_values else 'unknown')
                    features_df[f'{col}_encoded'] = self.label_encoders[col].transform(features_df[col])
        
        print(f"  ✅ Features créées: {features_df.shape[1]} colonnes")
        return features_df
    
    def prepare_data(self, df):
        """Préparation des données pour l'entraînement"""
        print("📊 Préparation des données...")
        
        # Nettoyage des données
        df_clean = df.dropna(subset=[self.target_column])
        
        # Suppression des outliers (Z-score > 3)
        z_scores = np.abs((df_clean[self.target_column] - df_clean[self.target_column].mean()) / df_clean[self.target_column].std())
        df_clean = df_clean[z_scores < 3]
        
        # Création des features
        df_features = self.create_features(df_clean)
        
        # Sélection des features numériques pour l'entraînement
        numeric_features = df_features.select_dtypes(include=[np.number]).columns.tolist()
        if self.target_column in numeric_features:
            numeric_features.remove(self.target_column)
        
        self.feature_columns = numeric_features
        
        X = df_features[self.feature_columns]
        y = df_features[self.target_column]
        
        print(f"  ✅ Données préparées: {X.shape[0]} échantillons, {X.shape[1]} features")
        return X, y
    
    def train(self, df, test_size=0.2, random_state=42):
        """Entraînement du modèle"""
        print("🚀 Entraînement du modèle...")
        
        # Préparation des données
        X, y = self.prepare_data(df)
        
        # Division train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=None
        )
        
        # Normalisation des features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Configuration du modèle XGBoost
        xgb_params = {
            'objective': 'reg:squarederror',
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 200,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': random_state,
            'early_stopping_rounds': 20,
            'eval_metric': 'rmse'
        }
        
        # Entraînement avec validation
        self.model = xgb.XGBRegressor(**xgb_params)
        self.model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_test_scaled, y_test)],
            verbose=False
        )
        
        # Évaluation
        y_pred_train = self.model.predict(X_train_scaled)
        y_pred_test = self.model.predict(X_test_scaled)
        
        # Métriques
        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)
        
        print(f"  ✅ RMSE Train: {train_rmse:.3f}, Test: {test_rmse:.3f}")
        print(f"  ✅ R² Train: {train_r2:.3f}, Test: {test_r2:.3f}")
        
        # Feature importance
        self.plot_feature_importance()
        
        return {
            'train_rmse': train_rmse,
            'test_rmse': test_rmse,
            'train_r2': train_r2,
            'test_r2': test_r2,
            'feature_importance': dict(zip(self.feature_columns, self.model.feature_importances_))
        }
    
    def predict(self, df):
        """Prédiction sur nouvelles données"""
        if self.model is None:
            raise ValueError("Le modèle n'a pas été entraîné")
        
        # Préparation des données
        df_features = self.create_features(df)
        X = df_features[self.feature_columns]
        X_scaled = self.scaler.transform(X)
        
        # Prédictions
        predictions = self.model.predict(X_scaled)
        
        # Intervalles de confiance (approximation)
        # Utilise la variance des résidus d'entraînement
        std_residuals = 0.5  # À calculer à partir des données d'entraînement
        confidence_lower = predictions - 1.96 * std_residuals
        confidence_upper = predictions + 1.96 * std_residuals
        
        return {
            'predictions': predictions,
            'confidence_lower': confidence_lower,
            'confidence_upper': confidence_upper
        }
    
    def plot_feature_importance(self, top_n=15):
        """Visualisation de l'importance des features"""
        if self.model is None:
            return
        
        importance_df = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False).head(top_n)
        
        plt.figure(figsize=(10, 8))
        sns.barplot(data=importance_df, x='importance', y='feature', palette='viridis')
        plt.title('Top Features - Importance pour la Prédiction de Rendement')
        plt.xlabel('Importance')
        plt.tight_layout()
        plt.savefig('ml-models/training/feature_importance_yield.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("  ✅ Graphique d'importance sauvegardé")
    
    def save_model(self, filepath='ml-models/training/yield_prediction_model.pkl'):
        """Sauvegarde du modèle"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_columns': self.feature_columns,
            'target_column': self.target_column,
            'trained_at': datetime.now()
        }
        
        joblib.dump(model_data, filepath)
        print(f"  ✅ Modèle sauvegardé: {filepath}")
    
    def load_model(self, filepath='ml-models/training/yield_prediction_model.pkl'):
        """Chargement du modèle"""
        model_data = joblib.load(filepath)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.label_encoders = model_data['label_encoders']
        self.feature_columns = model_data['feature_columns']
        self.target_column = model_data['target_column']
        
        print(f"  ✅ Modèle chargé: {filepath}")
        print(f"  📅 Entraîné le: {model_data.get('trained_at', 'Non spécifié')}")

def generate_sample_data(n_samples=1000):
    """Génère des données d'exemple pour tester le modèle"""
    print("📝 Génération de données d'exemple...")
    
    np.random.seed(42)
    
    countries = ['TG', 'GH', 'NG', 'CI', 'BF', 'ML', 'SN', 'BJ']
    crops = ['mais', 'riz', 'manioc', 'igname', 'arachide']
    seasons = ['wet', 'dry', 'annual']
    soil_types = ['clay', 'sandy', 'loam', 'mixed']
    
    data = {
        'country': np.random.choice(countries, n_samples),
        'crop': np.random.choice(crops, n_samples),
        'year': np.random.randint(2015, 2024, n_samples),
        'season': np.random.choice(seasons, n_samples),
        'soil_type': np.random.choice(soil_types, n_samples),
        'area_harvested': np.random.lognormal(8, 1, n_samples),  # hectares
        'temperature_avg': np.random.normal(27, 3, n_samples),  # °C
        'precipitation_total': np.random.normal(1200, 400, n_samples),  # mm
        'fertilizer_use': np.random.lognormal(3, 1, n_samples),  # kg/ha
        'gdp_per_capita': np.random.lognormal(7, 0.5, n_samples),  # USD
    }
    
    df = pd.DataFrame(data)
    
    # Génération du rendement basé sur des relations réalistes
    df['yield_base'] = (
        2.0 +  # Base yield
        (df['fertilizer_use'] / 100) * 0.5 +  # Effect of fertilizer
        np.maximum(0, (df['precipitation_total'] - 500) / 1000) * 2 +  # Precipitation effect
        np.where((df['temperature_avg'] >= 22) & (df['temperature_avg'] <= 32), 1, 0) * 0.5 +  # Optimal temperature
        (df['gdp_per_capita'] / 10000) * 0.3 +  # Economic development effect
        np.random.normal(0, 0.5, n_samples)  # Random noise
    )
    
    # Ajustements par culture
    crop_multipliers = {'mais': 1.2, 'riz': 1.0, 'manioc': 0.8, 'igname': 0.7, 'arachide': 0.9}
    df['yield_tonnes_per_ha'] = df.apply(lambda x: max(0.1, x['yield_base'] * crop_multipliers[x['crop']]), axis=1)
    
    # Ajout de production totale
    df['production_total'] = df['area_harvested'] * df['yield_tonnes_per_ha']
    
    print(f"  ✅ {n_samples} échantillons générés")
    return df

# Script principal pour entraîner le modèle
if __name__ == "__main__":
    print("🌾 AgriIntel360 - Entraînement Modèle de Rendement")
    print("=" * 60)
    
    # Génération de données d'exemple
    sample_data = generate_sample_data(2000)
    
    # Initialisation et entraînement du modèle
    yield_model = YieldPredictionModel()
    
    try:
        # Entraînement
        results = yield_model.train(sample_data)
        
        # Sauvegarde
        yield_model.save_model()
        
        # Test de prédiction
        print("\n🔮 Test de prédiction...")
        test_data = generate_sample_data(10)
        predictions = yield_model.predict(test_data)
        
        # Affichage des résultats
        results_df = pd.DataFrame({
            'pays': test_data['country'].values,
            'culture': test_data['crop'].values,
            'rendement_predit': predictions['predictions'],
            'confiance_min': predictions['confidence_lower'],
            'confiance_max': predictions['confidence_upper']
        })
        
        print(results_df.round(2))
        
        print("\n✅ Modèle de rendement entraîné avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'entraînement: {e}")
        raise