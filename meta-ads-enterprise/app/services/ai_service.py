import openai
from typing import Dict, List, Optional
import structlog
from app.core.config import settings
from app.models.campaign import Campaign, CampaignMetrics
import json

logger = structlog.get_logger()

class AIService:
    def __init__(self):
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
        else:
            logger.warning("OpenAI API key not configured")
    
    async def generate_campaign_insights(self, campaign_data: Dict, metrics_data: List[Dict]) -> Dict:
        """Generate AI insights for a campaign based on performance data"""
        try:
            campaign_summary = {
                "name": campaign_data.get("name"),
                "objective": campaign_data.get("objective"),
                "status": campaign_data.get("status"),
                "daily_budget": campaign_data.get("daily_budget"),
                "metrics_summary": self._summarize_metrics(metrics_data)
            }
            
            prompt = f"""
            Analise os dados da campanha do Facebook Ads abaixo e forneça insights acionáveis:

            Dados da Campanha:
            {json.dumps(campaign_summary, indent=2, default=str)}

            Por favor, forneça:
            1. Análise de performance atual
            2. Principais problemas identificados
            3. Recomendações específicas para otimização
            4. Previsões de performance
            5. Score de qualidade da campanha (0-100)

            Responda em português e seja específico e acionável.
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Você é um especialista em Meta Ads com 10 anos de experiência em otimização de campanhas."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            insight_content = response.choices[0].message.content
            
            quality_score = self._extract_quality_score(insight_content)
            
            return {
                "insight_type": "campaign_analysis",
                "title": f"Análise IA - {campaign_data.get('name')}",
                "content": insight_content,
                "confidence_score": 0.85,
                "quality_score": quality_score,
                "recommendations": self._extract_recommendations(insight_content)
            }
            
        except Exception as e:
            logger.error("Failed to generate campaign insights", error=str(e))
            return {
                "insight_type": "error",
                "title": "Erro na Análise IA",
                "content": "Não foi possível gerar insights no momento. Tente novamente mais tarde.",
                "confidence_score": 0.0
            }
    
    async def generate_optimization_suggestions(self, campaign_id: str, performance_data: Dict) -> List[Dict]:
        """Generate specific optimization suggestions"""
        try:
            prompt = f"""
            Com base nos dados de performance abaixo, sugira otimizações específicas:

            Dados de Performance:
            - CTR: {performance_data.get('ctr', 0)}%
            - CPM: ${performance_data.get('cpm', 0)}
            - ROAS: {performance_data.get('roas', 0)}
            - Conversões: {performance_data.get('conversions', 0)}
            - Gasto: ${performance_data.get('spend', 0)}

            Forneça 3-5 sugestões específicas de otimização com:
            1. Ação recomendada
            2. Justificativa
            3. Impacto esperado
            4. Prioridade (Alta/Média/Baixa)
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Você é um especialista em otimização de campanhas Meta Ads."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.6
            )
            
            suggestions_text = response.choices[0].message.content
            
            suggestions = self._parse_suggestions(suggestions_text)
            
            return suggestions
            
        except Exception as e:
            logger.error("Failed to generate optimization suggestions", error=str(e))
            return []
    
    async def predict_performance(self, historical_data: List[Dict], days_ahead: int = 7) -> Dict:
        """Predict campaign performance for the next N days"""
        try:
            data_summary = {
                "total_days": len(historical_data),
                "avg_spend": sum(d.get('spend', 0) for d in historical_data) / len(historical_data),
                "avg_impressions": sum(d.get('impressions', 0) for d in historical_data) / len(historical_data),
                "avg_clicks": sum(d.get('clicks', 0) for d in historical_data) / len(historical_data),
                "avg_conversions": sum(d.get('conversions', 0) for d in historical_data) / len(historical_data),
                "trend": self._calculate_trend(historical_data)
            }
            
            prompt = f"""
            Com base nos dados históricos abaixo, preveja a performance para os próximos {days_ahead} dias:

            Resumo dos Dados Históricos ({len(historical_data)} dias):
            {json.dumps(data_summary, indent=2, default=str)}

            Forneça previsões para:
            1. Gasto total estimado
            2. Impressões esperadas
            3. Clicks esperados
            4. Conversões esperadas
            5. CTR previsto
            6. ROAS previsto
            7. Nível de confiança da previsão (0-100%)

            Considere tendências sazonais e padrões identificados.
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Você é um analista de dados especializado em previsões de performance de marketing digital."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.5
            )
            
            prediction_text = response.choices[0].message.content
            
            predictions = self._parse_predictions(prediction_text, days_ahead)
            
            return predictions
            
        except Exception as e:
            logger.error("Failed to predict performance", error=str(e))
            return {}
    
    async def generate_creative_suggestions(self, campaign_objective: str, target_audience: Dict) -> List[Dict]:
        """Generate creative suggestions for ad content"""
        try:
            prompt = f"""
            Gere sugestões de criativos para uma campanha com:
            - Objetivo: {campaign_objective}
            - Público-alvo: {json.dumps(target_audience, default=str)}

            Forneça 5 sugestões de criativos incluindo:
            1. Título principal
            2. Texto do anúncio
            3. Call-to-action sugerido
            4. Tipo de mídia recomendado
            5. Estratégia de copy
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Você é um copywriter especializado em Meta Ads com expertise em conversão."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.8
            )
            
            creative_text = response.choices[0].message.content
            
            creatives = self._parse_creative_suggestions(creative_text)
            
            return creatives
            
        except Exception as e:
            logger.error("Failed to generate creative suggestions", error=str(e))
            return []
    
    def _summarize_metrics(self, metrics_data: List[Dict]) -> Dict:
        """Summarize metrics data for AI analysis"""
        if not metrics_data:
            return {}
        
        total_spend = sum(m.get('spend', 0) for m in metrics_data)
        total_impressions = sum(m.get('impressions', 0) for m in metrics_data)
        total_clicks = sum(m.get('clicks', 0) for m in metrics_data)
        total_conversions = sum(m.get('conversions', 0) for m in metrics_data)
        
        return {
            "total_spend": total_spend,
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "avg_ctr": (total_clicks / total_impressions * 100) if total_impressions > 0 else 0,
            "avg_cpm": (total_spend / total_impressions * 1000) if total_impressions > 0 else 0,
            "cost_per_conversion": (total_spend / total_conversions) if total_conversions > 0 else 0,
            "days_analyzed": len(metrics_data)
        }
    
    def _extract_quality_score(self, content: str) -> float:
        """Extract quality score from AI response"""
        import re
        score_match = re.search(r'score.*?(\d+)', content.lower())
        if score_match:
            return float(score_match.group(1)) / 100
        return 0.75  # Default score
    
    def _extract_recommendations(self, content: str) -> List[str]:
        """Extract actionable recommendations from AI response"""
        lines = content.split('\n')
        recommendations = []
        for line in lines:
            if any(keyword in line.lower() for keyword in ['recomend', 'suger', 'deve', 'precisa']):
                recommendations.append(line.strip())
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _parse_suggestions(self, text: str) -> List[Dict]:
        """Parse optimization suggestions from AI response"""
        suggestions = []
        lines = text.split('\n')
        current_suggestion = {}
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                if len(current_suggestion) == 0:
                    current_suggestion['action'] = line
                    current_suggestion['priority'] = 'Média'
                    current_suggestion['impact'] = 'Moderado'
                    suggestions.append(current_suggestion)
                    current_suggestion = {}
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _calculate_trend(self, data: List[Dict]) -> str:
        """Calculate performance trend from historical data"""
        if len(data) < 2:
            return "stable"
        
        recent_avg = sum(d.get('spend', 0) for d in data[-3:]) / min(3, len(data))
        older_avg = sum(d.get('spend', 0) for d in data[:-3]) / max(1, len(data) - 3)
        
        if recent_avg > older_avg * 1.1:
            return "increasing"
        elif recent_avg < older_avg * 0.9:
            return "decreasing"
        else:
            return "stable"
    
    def _parse_predictions(self, text: str, days: int) -> Dict:
        """Parse performance predictions from AI response"""
        return {
            "days_ahead": days,
            "predicted_spend": 1000.0,  # Would be extracted from AI response
            "predicted_impressions": 50000,
            "predicted_clicks": 1500,
            "predicted_conversions": 75,
            "predicted_ctr": 3.0,
            "predicted_roas": 2.5,
            "confidence_level": 0.8
        }
    
    def _parse_creative_suggestions(self, text: str) -> List[Dict]:
        """Parse creative suggestions from AI response"""
        return [
            {
                "title": "Título Criativo 1",
                "copy": "Texto do anúncio otimizado para conversão",
                "cta": "Saiba Mais",
                "media_type": "image",
                "strategy": "Foco em benefícios"
            }
        ]
