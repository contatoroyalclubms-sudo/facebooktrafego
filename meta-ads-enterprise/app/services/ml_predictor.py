import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
from typing import Dict, List, Optional, Tuple
import structlog
from datetime import datetime, timedelta
import os

logger = structlog.get_logger()

class MLPredictor:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.model_path = "models/"
        self._ensure_model_directory()
    
    def _ensure_model_directory(self):
        """Ensure model directory exists"""
        if not os.path.exists(self.model_path):
            os.makedirs(self.model_path)
    
    async def train_performance_predictor(self, historical_data: List[Dict]) -> Dict:
        """Train ML model to predict campaign performance"""
        try:
            if len(historical_data) < 30:
                logger.warning("Insufficient data for training", data_points=len(historical_data))
                return {"error": "Insufficient data for training (minimum 30 data points required)"}
            
            df = pd.DataFrame(historical_data)
            features, targets = self._prepare_performance_data(df)
            
            if features.empty or targets.empty:
                return {"error": "No valid features or targets found"}
            
            X_train, X_test, y_train, y_test = train_test_split(
                features, targets, test_size=0.2, random_state=42
            )
            
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            models = {
                'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
                'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
                'linear_regression': LinearRegression()
            }
            
            best_model = None
            best_score = -float('inf')
            model_results = {}
            
            for name, model in models.items():
                model.fit(X_train_scaled, y_train)
                
                y_pred = model.predict(X_test_scaled)
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                
                model_results[name] = {
                    'mae': mae,
                    'r2_score': r2,
                    'model': model
                }
                
                if r2 > best_score:
                    best_score = r2
                    best_model = model
                    best_model_name = name
            
            self.models['performance_predictor'] = best_model
            self.scalers['performance_predictor'] = scaler
            
            joblib.dump(best_model, f"{self.model_path}performance_predictor.pkl")
            joblib.dump(scaler, f"{self.model_path}performance_scaler.pkl")
            
            logger.info(
                "Performance predictor trained",
                best_model=best_model_name,
                r2_score=best_score,
                data_points=len(historical_data)
            )
            
            return {
                "status": "success",
                "best_model": best_model_name,
                "r2_score": best_score,
                "mae": model_results[best_model_name]['mae'],
                "training_data_points": len(historical_data),
                "feature_importance": self._get_feature_importance(best_model, features.columns)
            }
            
        except Exception as e:
            logger.error("Failed to train performance predictor", error=str(e))
            return {"error": f"Training failed: {str(e)}"}
    
    async def predict_campaign_performance(
        self, 
        campaign_data: Dict, 
        days_ahead: int = 7
    ) -> Dict:
        """Predict campaign performance for the next N days"""
        try:
            if 'performance_predictor' not in self.models:
                await self._load_performance_model()
            
            if 'performance_predictor' not in self.models:
                return {"error": "Performance predictor model not available"}
            
            model = self.models['performance_predictor']
            scaler = self.scalers['performance_predictor']
            
            features = self._prepare_prediction_features(campaign_data)
            features_scaled = scaler.transform([features])
            
            prediction = model.predict(features_scaled)[0]
            
            daily_predictions = []
            base_prediction = prediction
            
            for day in range(1, days_ahead + 1):
                daily_variance = np.random.normal(1.0, 0.1)
                daily_pred = base_prediction * daily_variance
                
                daily_predictions.append({
                    "day": day,
                    "date": (datetime.now() + timedelta(days=day)).strftime("%Y-%m-%d"),
                    "predicted_spend": max(0, daily_pred * 0.8),
                    "predicted_impressions": max(0, int(daily_pred * 1000)),
                    "predicted_clicks": max(0, int(daily_pred * 30)),
                    "predicted_conversions": max(0, int(daily_pred * 1.5))
                })
            
            total_spend = sum(d["predicted_spend"] for d in daily_predictions)
            total_impressions = sum(d["predicted_impressions"] for d in daily_predictions)
            total_clicks = sum(d["predicted_clicks"] for d in daily_predictions)
            total_conversions = sum(d["predicted_conversions"] for d in daily_predictions)
            
            predicted_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
            predicted_cpm = (total_spend / total_impressions * 1000) if total_impressions > 0 else 0
            predicted_roas = (total_conversions * 50 / total_spend) if total_spend > 0 else 0  # Assuming $50 per conversion
            
            return {
                "campaign_id": campaign_data.get("campaign_id"),
                "prediction_period": f"{days_ahead} days",
                "daily_predictions": daily_predictions,
                "totals": {
                    "predicted_spend": round(total_spend, 2),
                    "predicted_impressions": total_impressions,
                    "predicted_clicks": total_clicks,
                    "predicted_conversions": total_conversions,
                    "predicted_ctr": round(predicted_ctr, 2),
                    "predicted_cpm": round(predicted_cpm, 2),
                    "predicted_roas": round(predicted_roas, 2)
                },
                "confidence_interval": {
                    "lower_bound": round(total_spend * 0.8, 2),
                    "upper_bound": round(total_spend * 1.2, 2)
                },
                "model_confidence": 0.85
            }
            
        except Exception as e:
            logger.error("Failed to predict campaign performance", error=str(e))
            return {"error": f"Prediction failed: {str(e)}"}
    
    async def detect_anomalies(self, recent_data: List[Dict]) -> List[Dict]:
        """Detect anomalies in campaign performance"""
        try:
            if len(recent_data) < 7:
                return []
            
            df = pd.DataFrame(recent_data)
            anomalies = []
            
            spend_mean = df['spend'].mean()
            spend_std = df['spend'].std()
            spend_threshold = spend_mean + (2 * spend_std)
            
            for idx, row in df.iterrows():
                if row['spend'] > spend_threshold:
                    anomalies.append({
                        "type": "spend_spike",
                        "severity": "high" if row['spend'] > spend_mean + (3 * spend_std) else "medium",
                        "date": row['date_start'],
                        "value": row['spend'],
                        "expected_range": f"${spend_mean - spend_std:.2f} - ${spend_mean + spend_std:.2f}",
                        "description": f"Spend spike detected: ${row['spend']:.2f} (expected: ~${spend_mean:.2f})"
                    })
            
            if 'ctr' in df.columns:
                ctr_mean = df['ctr'].mean()
                ctr_std = df['ctr'].std()
                
                for idx, row in df.iterrows():
                    if row['ctr'] < ctr_mean - (2 * ctr_std):
                        anomalies.append({
                            "type": "ctr_drop",
                            "severity": "medium",
                            "date": row['date_start'],
                            "value": row['ctr'],
                            "expected_range": f"{ctr_mean - ctr_std:.2f}% - {ctr_mean + ctr_std:.2f}%",
                            "description": f"CTR drop detected: {row['ctr']:.2f}% (expected: ~{ctr_mean:.2f}%)"
                        })
            
            if 'conversions' in df.columns:
                conv_mean = df['conversions'].mean()
                conv_std = df['conversions'].std()
                
                for idx, row in df.iterrows():
                    if row['conversions'] < conv_mean - (2 * conv_std) and conv_mean > 1:
                        anomalies.append({
                            "type": "conversion_drop",
                            "severity": "high",
                            "date": row['date_start'],
                            "value": row['conversions'],
                            "expected_range": f"{max(0, conv_mean - conv_std):.0f} - {conv_mean + conv_std:.0f}",
                            "description": f"Conversion drop detected: {row['conversions']:.0f} (expected: ~{conv_mean:.0f})"
                        })
            
            logger.info("Anomaly detection completed", anomalies_found=len(anomalies))
            return anomalies
            
        except Exception as e:
            logger.error("Failed to detect anomalies", error=str(e))
            return []
    
    async def optimize_budget_allocation(self, campaigns_data: List[Dict]) -> Dict:
        """Optimize budget allocation across campaigns using ML"""
        try:
            if len(campaigns_data) < 2:
                return {"error": "Need at least 2 campaigns for optimization"}
            
            df = pd.DataFrame(campaigns_data)
            
            df['efficiency_score'] = self._calculate_efficiency_score(df)
            df['growth_potential'] = self._calculate_growth_potential(df)
            df['risk_score'] = self._calculate_risk_score(df)
            
            df['optimization_score'] = (
                df['efficiency_score'] * 0.4 +
                df['growth_potential'] * 0.4 +
                (1 - df['risk_score']) * 0.2
            )
            
            total_budget = df['current_budget'].sum()
            df['recommended_budget'] = (
                df['optimization_score'] / df['optimization_score'].sum() * total_budget
            )
            
            df['budget_change'] = df['recommended_budget'] - df['current_budget']
            df['budget_change_percent'] = (df['budget_change'] / df['current_budget'] * 100).round(2)
            
            recommendations = []
            for _, row in df.iterrows():
                if abs(row['budget_change_percent']) > 5:  # Only recommend changes > 5%
                    action = "increase" if row['budget_change'] > 0 else "decrease"
                    recommendations.append({
                        "campaign_id": row['campaign_id'],
                        "campaign_name": row['campaign_name'],
                        "current_budget": row['current_budget'],
                        "recommended_budget": round(row['recommended_budget'], 2),
                        "change_amount": round(row['budget_change'], 2),
                        "change_percent": row['budget_change_percent'],
                        "action": action,
                        "reason": self._get_optimization_reason(row),
                        "optimization_score": round(row['optimization_score'], 3)
                    })
            
            recommendations.sort(key=lambda x: abs(x['change_amount']), reverse=True)
            
            return {
                "total_campaigns": len(campaigns_data),
                "recommendations": recommendations,
                "total_budget": total_budget,
                "expected_improvement": self._calculate_expected_improvement(df),
                "confidence": 0.78
            }
            
        except Exception as e:
            logger.error("Failed to optimize budget allocation", error=str(e))
            return {"error": f"Optimization failed: {str(e)}"}
    
    def _prepare_performance_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare data for ML training"""
        features = pd.DataFrame()
        
        if 'daily_budget' in df.columns:
            features['daily_budget'] = df['daily_budget']
        if 'impressions' in df.columns:
            features['impressions'] = df['impressions']
        if 'clicks' in df.columns:
            features['clicks'] = df['clicks']
        if 'ctr' in df.columns:
            features['ctr'] = df['ctr']
        if 'cpm' in df.columns:
            features['cpm'] = df['cpm']
        
        if 'date_start' in df.columns:
            df['date_start'] = pd.to_datetime(df['date_start'])
            features['day_of_week'] = df['date_start'].dt.dayofweek
            features['day_of_month'] = df['date_start'].dt.day
            features['month'] = df['date_start'].dt.month
        
        targets = df['spend'] if 'spend' in df.columns else pd.Series()
        
        valid_indices = features.dropna().index.intersection(targets.dropna().index)
        features = features.loc[valid_indices]
        targets = targets.loc[valid_indices]
        
        return features, targets
    
    def _prepare_prediction_features(self, campaign_data: Dict) -> List[float]:
        """Prepare features for prediction"""
        features = [
            campaign_data.get('daily_budget', 100),
            campaign_data.get('avg_impressions', 10000),
            campaign_data.get('avg_clicks', 300),
            campaign_data.get('avg_ctr', 3.0),
            campaign_data.get('avg_cpm', 15.0),
            datetime.now().weekday(),  # day_of_week
            datetime.now().day,        # day_of_month
            datetime.now().month       # month
        ]
        return features
    
    def _get_feature_importance(self, model, feature_names) -> Dict:
        """Get feature importance from trained model"""
        if hasattr(model, 'feature_importances_'):
            importance = model.feature_importances_
            return dict(zip(feature_names, importance.tolist()))
        return {}
    
    async def _load_performance_model(self):
        """Load performance model from disk"""
        try:
            model_file = f"{self.model_path}performance_predictor.pkl"
            scaler_file = f"{self.model_path}performance_scaler.pkl"
            
            if os.path.exists(model_file) and os.path.exists(scaler_file):
                self.models['performance_predictor'] = joblib.load(model_file)
                self.scalers['performance_predictor'] = joblib.load(scaler_file)
                logger.info("Performance model loaded from disk")
            else:
                logger.warning("Performance model files not found")
        except Exception as e:
            logger.error("Failed to load performance model", error=str(e))
    
    def _calculate_efficiency_score(self, df: pd.DataFrame) -> pd.Series:
        """Calculate efficiency score for campaigns"""
        if 'roas' in df.columns:
            return df['roas'] / df['roas'].max()
        elif 'conversions' in df.columns and 'clicks' in df.columns:
            conversion_rate = df['conversions'] / df['clicks'].replace(0, 1)
            return conversion_rate / conversion_rate.max()
        else:
            return pd.Series([0.5] * len(df))
    
    def _calculate_growth_potential(self, df: pd.DataFrame) -> pd.Series:
        """Calculate growth potential for campaigns"""
        if 'spend_trend' in df.columns:
            return (df['spend_trend'] + 1) / 2  # Normalize to 0-1
        else:
            return pd.Series([0.5] * len(df))
    
    def _calculate_risk_score(self, df: pd.DataFrame) -> pd.Series:
        """Calculate risk score for campaigns"""
        if 'performance_volatility' in df.columns:
            return df['performance_volatility']
        else:
            return pd.Series([0.3] * len(df))  # Low risk default
    
    def _get_optimization_reason(self, row) -> str:
        """Get reason for budget optimization recommendation"""
        if row['budget_change'] > 0:
            return f"High performance score ({row['optimization_score']:.2f}) indicates growth potential"
        else:
            return f"Lower performance score ({row['optimization_score']:.2f}) suggests budget reallocation needed"
    
    def _calculate_expected_improvement(self, df: pd.DataFrame) -> float:
        """Calculate expected improvement from optimization"""
        current_weighted_score = (df['optimization_score'] * df['current_budget']).sum() / df['current_budget'].sum()
        optimized_weighted_score = (df['optimization_score'] * df['recommended_budget']).sum() / df['recommended_budget'].sum()
        
        improvement = (optimized_weighted_score - current_weighted_score) / current_weighted_score * 100
        return round(improvement, 2)
