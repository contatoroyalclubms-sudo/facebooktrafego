
INSERT INTO campaigns (campaign_id, user_id, name, objective, status, daily_budget, total_budget, config_data, created_at, updated_at) VALUES
('23847656789012345', (SELECT id FROM users WHERE email = 'admin@metaads.com'), 'E-commerce Black Friday 2024', 'CONVERSIONS', 'ACTIVE', 150.00, NULL, '{"target_audience": {"age_min": 25, "age_max": 55, "interests": ["shopping", "fashion"]}, "placement": ["facebook_feeds", "instagram_stories"]}', NOW() - INTERVAL '15 days', NOW()),
('23847656789012346', (SELECT id FROM users WHERE email = 'admin@metaads.com'), 'Lead Generation - Real Estate', 'LEAD_GENERATION', 'ACTIVE', 80.00, NULL, '{"target_audience": {"age_min": 30, "age_max": 65, "interests": ["real estate", "investment"]}, "placement": ["facebook_feeds"]}', NOW() - INTERVAL '10 days', NOW()),
('23847656789012347', (SELECT id FROM users WHERE email = 'admin@metaads.com'), 'Brand Awareness - Tech Startup', 'BRAND_AWARENESS', 'PAUSED', 50.00, NULL, '{"target_audience": {"age_min": 22, "age_max": 45, "interests": ["technology", "startups"]}, "placement": ["instagram_feeds", "instagram_stories"]}', NOW() - INTERVAL '20 days', NOW()),
('23847656789012348', (SELECT id FROM users WHERE email = 'admin@metaads.com'), 'App Install Campaign - Fitness', 'APP_INSTALLS', 'ACTIVE', 120.00, NULL, '{"target_audience": {"age_min": 18, "age_max": 40, "interests": ["fitness", "health"]}, "placement": ["facebook_feeds", "instagram_feeds"]}', NOW() - INTERVAL '7 days', NOW()),
('23847656789012349', (SELECT id FROM users WHERE email = 'admin@metaads.com'), 'Video Views - Travel Agency', 'VIDEO_VIEWS', 'ACTIVE', 90.00, NULL, '{"target_audience": {"age_min": 25, "age_max": 60, "interests": ["travel", "vacation"]}, "placement": ["facebook_feeds", "instagram_stories"]}', NOW() - INTERVAL '12 days', NOW());

DO $$
DECLARE
    campaign_record RECORD;
    day_offset INTEGER;
    base_impressions INTEGER;
    base_clicks INTEGER;
    base_conversions INTEGER;
    base_spend DECIMAL;
    daily_impressions INTEGER;
    daily_clicks INTEGER;
    daily_conversions INTEGER;
    daily_spend DECIMAL;
    daily_ctr DECIMAL;
    daily_cpm DECIMAL;
    daily_roas DECIMAL;
BEGIN
    FOR campaign_record IN SELECT campaign_id FROM campaigns LOOP
        CASE campaign_record.campaign_id
            WHEN '23847656789012345' THEN -- E-commerce Black Friday
                base_impressions := 15000;
                base_clicks := 450;
                base_conversions := 35;
                base_spend := 150.00;
            WHEN '23847656789012346' THEN -- Lead Generation
                base_impressions := 8000;
                base_clicks := 240;
                base_conversions := 18;
                base_spend := 80.00;
            WHEN '23847656789012347' THEN -- Brand Awareness (paused)
                base_impressions := 12000;
                base_clicks := 180;
                base_conversions := 8;
                base_spend := 50.00;
            WHEN '23847656789012348' THEN -- App Install
                base_impressions := 20000;
                base_clicks := 800;
                base_conversions := 120;
                base_spend := 120.00;
            WHEN '23847656789012349' THEN -- Video Views
                base_impressions := 25000;
                base_clicks := 500;
                base_conversions := 25;
                base_spend := 90.00;
        END CASE;

        FOR day_offset IN 0..29 LOOP
            daily_impressions := base_impressions + (RANDOM() * 5000 - 2500)::INTEGER;
            daily_clicks := base_clicks + (RANDOM() * 200 - 100)::INTEGER;
            daily_conversions := base_conversions + (RANDOM() * 20 - 10)::INTEGER;
            daily_spend := base_spend + (RANDOM() * 50 - 25);
            
            daily_impressions := GREATEST(daily_impressions, 1000);
            daily_clicks := GREATEST(daily_clicks, 10);
            daily_conversions := GREATEST(daily_conversions, 1);
            daily_spend := GREATEST(daily_spend, 10.00);
            
            daily_ctr := (daily_clicks::DECIMAL / daily_impressions * 100);
            daily_cpm := (daily_spend / daily_impressions * 1000);
            daily_roas := CASE 
                WHEN daily_conversions > 0 THEN (daily_conversions * 50.00 / daily_spend)
                ELSE 0 
            END;

            INSERT INTO campaign_metrics (
                campaign_id, 
                date_start, 
                date_stop, 
                impressions, 
                clicks, 
                conversions, 
                spend, 
                cpm, 
                ctr, 
                roas, 
                frequency, 
                reach, 
                cost_per_conversion,
                created_at
            ) VALUES (
                campaign_record.campaign_id,
                (CURRENT_DATE - day_offset),
                (CURRENT_DATE - day_offset),
                daily_impressions,
                daily_clicks,
                daily_conversions,
                daily_spend,
                daily_cpm,
                daily_ctr,
                daily_roas,
                1.2 + (RANDOM() * 0.8), -- frequency between 1.2 and 2.0
                (daily_impressions * 0.8)::INTEGER, -- reach is ~80% of impressions
                CASE WHEN daily_conversions > 0 THEN daily_spend / daily_conversions ELSE 0 END,
                NOW() - (day_offset || ' days')::INTERVAL
            );
        END LOOP;
    END LOOP;
END $$;

INSERT INTO alerts (user_id, campaign_id, alert_type, severity, title, message, data, is_read, created_at) VALUES
((SELECT id FROM users WHERE email = 'admin@metaads.com'), '23847656789012345', 'HIGH_SPEND', 'warning', 'Gasto Alto Detectado', 'A campanha "E-commerce Black Friday 2024" ultrapassou 120% do orçamento diário nas últimas 2 horas.', '{"current_spend": 180.50, "budget": 150.00, "percentage": 120.3}', FALSE, NOW() - INTERVAL '2 hours'),
((SELECT id FROM users WHERE email = 'admin@metaads.com'), '23847656789012346', 'LOW_CTR', 'info', 'CTR Baixo', 'A campanha "Lead Generation - Real Estate" apresenta CTR abaixo da média (1.8% vs 2.5% esperado).', '{"current_ctr": 1.8, "expected_ctr": 2.5, "impressions": 8500}', FALSE, NOW() - INTERVAL '4 hours'),
((SELECT id FROM users WHERE email = 'admin@metaads.com'), '23847656789012348', 'HIGH_PERFORMANCE', 'success', 'Excelente Performance!', 'A campanha "App Install Campaign - Fitness" está com ROAS de 4.2x, muito acima da meta de 2.5x.', '{"current_roas": 4.2, "target_roas": 2.5, "conversions": 145}', TRUE, NOW() - INTERVAL '1 day'),
((SELECT id FROM users WHERE email = 'admin@metaads.com'), '23847656789012349', 'OPTIMIZATION_SUGGESTION', 'info', 'Sugestão de Otimização', 'Recomendamos aumentar o orçamento da campanha "Video Views - Travel Agency" em 30% devido ao bom desempenho.', '{"suggested_budget": 117.00, "current_budget": 90.00, "reason": "high_engagement"}', FALSE, NOW() - INTERVAL '6 hours'),
((SELECT id FROM users WHERE email = 'admin@metaads.com'), NULL, 'SYSTEM_UPDATE', 'info', 'Atualização do Sistema', 'Nova funcionalidade de otimização automática foi ativada. Suas campanhas serão monitoradas 24/7.', '{"feature": "auto_optimization", "status": "enabled"}', TRUE, NOW() - INTERVAL '2 days');

INSERT INTO ai_insights (user_id, insight_type, title, content, data, confidence_score, is_applied, created_at) VALUES
((SELECT id FROM users WHERE email = 'admin@metaads.com'), 'campaign_optimization', 'Otimização Recomendada - Black Friday', 'Com base na análise dos últimos 15 dias, recomendamos:\n\n1. **Aumentar orçamento em 25%** - A campanha está limitada por orçamento\n2. **Focar em Instagram Stories** - 40% melhor CTR que Facebook Feed\n3. **Ajustar público-alvo** - Expandir faixa etária para 22-60 anos\n4. **Otimizar horários** - Melhor performance entre 19h-22h\n\nImpacto esperado: +35% conversões, -15% CPA', '{"campaign_id": "23847656789012345", "recommendations": ["increase_budget", "focus_instagram", "expand_audience", "optimize_schedule"], "expected_impact": {"conversions": 35, "cpa_reduction": 15}}', 0.92, FALSE, NOW() - INTERVAL '1 day'),
((SELECT id FROM users WHERE email = 'admin@metaads.com'), 'performance_prediction', 'Previsão de Performance - Próximos 7 dias', 'Baseado nos padrões históricos e tendências atuais:\n\n**Campanhas Ativas:**\n- E-commerce: 245 conversões esperadas (+12%)\n- Lead Generation: 126 leads esperados (-5%)\n- App Install: 840 instalações esperadas (+28%)\n- Video Views: 15.2K visualizações esperadas (+8%)\n\n**Recomendações:**\n- Pausar campanha de Real Estate temporariamente\n- Dobrar investimento em App Install\n- Criar variação criativa para E-commerce', '{"predictions": {"ecommerce": 245, "leads": 126, "app_installs": 840, "video_views": 15200}, "confidence": 0.87}', 0.87, FALSE, NOW() - INTERVAL '3 hours'),
((SELECT id FROM users WHERE email = 'admin@metaads.com'), 'audience_insights', 'Insights de Audiência - Dezembro 2024', 'Análise detalhada do comportamento da audiência:\n\n**Descobertas Principais:**\n1. **Mulheres 25-35** respondem 3x melhor a criativos com vídeo\n2. **Homens 30-45** preferem anúncios informativos com texto\n3. **Fins de semana** apresentam 25% menos conversões\n4. **Mobile** representa 78% do tráfego total\n\n**Oportunidades:**\n- Criar campanhas específicas por gênero\n- Reduzir orçamento aos fins de semana\n- Priorizar criativos mobile-first', '{"gender_performance": {"female": 3.2, "male": 1.8}, "device_split": {"mobile": 78, "desktop": 22}, "weekend_impact": -25}', 0.89, TRUE, NOW() - INTERVAL '2 days');

INSERT INTO optimizations (campaign_id, optimization_type, action_type, old_value, new_value, reason, performance_before, performance_after, created_at) VALUES
('23847656789012345', 'BUDGET_OPTIMIZATION', 'INCREASE_BUDGET', 150.00, 180.00, 'Campanha limitada por orçamento com bom ROAS', '{"roas": 3.2, "cpa": 28.50, "conversions": 35}', '{"roas": 3.4, "cpa": 26.80, "conversions": 42}', NOW() - INTERVAL '3 days'),
('23847656789012346', 'AUDIENCE_OPTIMIZATION', 'EXPAND_AUDIENCE', 25.0, 30.0, 'Audiência muito restrita, expandindo faixa etária', '{"reach": 45000, "ctr": 1.8, "frequency": 2.1}', '{"reach": 68000, "ctr": 2.1, "frequency": 1.8}', NOW() - INTERVAL '5 days'),
('23847656789012348', 'BID_OPTIMIZATION', 'INCREASE_BID', 2.50, 3.20, 'Aumentar lance para melhorar posicionamento', '{"avg_position": 3.2, "impressions": 18000, "clicks": 720}', '{"avg_position": 2.1, "impressions": 22000, "clicks": 880}', NOW() - INTERVAL '1 day'),
('23847656789012349', 'PLACEMENT_OPTIMIZATION', 'REMOVE_PLACEMENT', 1.0, 0.0, 'Removendo Facebook Feed devido baixa performance', '{"facebook_feed_ctr": 1.2, "instagram_stories_ctr": 3.8}', '{"instagram_stories_ctr": 4.1, "overall_ctr": 3.9}', NOW() - INTERVAL '2 days');

ANALYZE campaigns;
ANALYZE campaign_metrics;
ANALYZE alerts;
ANALYZE ai_insights;
ANALYZE optimizations;
