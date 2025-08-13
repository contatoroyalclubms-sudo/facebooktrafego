import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Typography, Spin, Alert, Button } from 'antd';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  DollarOutlined,
  EyeOutlined,
  ShoppingCartOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { useQuery } from 'react-query';
import axios from 'axios';
import io from 'socket.io-client';

const { Title, Text } = Typography;

const Dashboard = () => {
  const [socket, setSocket] = useState(null);
  const [realTimeData, setRealTimeData] = useState(null);

  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery(
    'dashboardStats',
    () => axios.get('/api/v1/dashboard/stats').then(res => res.data),
    { refetchInterval: 30000 } // Refetch every 30 seconds
  );

  const { data: alerts, isLoading: alertsLoading } = useQuery(
    'recentAlerts',
    () => axios.get('/api/v1/dashboard/alerts?limit=5').then(res => res.data),
    { refetchInterval: 60000 }
  );

  const { data: campaigns, isLoading: campaignsLoading } = useQuery(
    'campaignSummaries',
    () => axios.get('/api/v1/dashboard/campaigns/summary?limit=5').then(res => res.data),
    { refetchInterval: 30000 }
  );

  const { data: analyticsData, isLoading: analyticsLoading } = useQuery(
    'dashboardAnalytics',
    () => axios.get('/api/v1/analytics/timeseries?date_start=' + 
      new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()).then(res => res.data),
    { refetchInterval: 300000 } // Refetch every 5 minutes
  );

  useEffect(() => {
    const newSocket = io('/ws');
    setSocket(newSocket);

    newSocket.on('stats_update', (data) => {
      setRealTimeData(data);
    });

    return () => newSocket.close();
  }, []);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatNumber = (value) => {
    return new Intl.NumberFormat('pt-BR').format(value);
  };

  const getTrendIcon = (trend) => {
    if (trend === 'up') return <ArrowUpOutlined style={{ color: '#52c41a' }} />;
    if (trend === 'down') return <ArrowDownOutlined style={{ color: '#ff4d4f' }} />;
    return null;
  };

  const getAlertSeverityColor = (severity) => {
    const colors = {
      low: '#52c41a',
      medium: '#faad14',
      high: '#ff7a45',
      critical: '#ff4d4f',
    };
    return colors[severity] || '#666';
  };

  if (statsLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      {/* Page Header */}
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={2} style={{ margin: 0 }}>Dashboard</Title>
          <Text type="secondary">Visão geral das suas campanhas Meta Ads</Text>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <div className="real-time-indicator">
            <div className="real-time-dot"></div>
            Tempo Real
          </div>
          <Button icon={<ReloadOutlined />} onClick={() => refetchStats()}>
            Atualizar
          </Button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Gasto Hoje"
              value={stats?.total_spend_today || 0}
              formatter={(value) => formatCurrency(value)}
              prefix={<DollarOutlined />}
              suffix={getTrendIcon(stats?.performance_trend)}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Impressões Hoje"
              value={stats?.total_impressions_today || 0}
              formatter={(value) => formatNumber(value)}
              prefix={<EyeOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Clicks Hoje"
              value={stats?.total_clicks_today || 0}
              formatter={(value) => formatNumber(value)}
              prefix={<EyeOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Conversões Hoje"
              value={stats?.total_conversions_today || 0}
              formatter={(value) => formatNumber(value)}
              prefix={<ShoppingCartOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Campaign Status and Alerts */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="Status das Campanhas" loading={statsLoading}>
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="Total de Campanhas"
                  value={stats?.total_campaigns || 0}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="Campanhas Ativas"
                  value={stats?.active_campaigns || 0}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Alertas Recentes" loading={alertsLoading}>
            {alerts && alerts.length > 0 ? (
              <div style={{ maxHeight: 200, overflowY: 'auto' }}>
                {alerts.map((alert) => (
                  <div
                    key={alert.id}
                    style={{
                      padding: '8px 0',
                      borderBottom: '1px solid #f0f0f0',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <div>
                      <Text strong style={{ color: getAlertSeverityColor(alert.severity) }}>
                        {alert.title}
                      </Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {new Date(alert.created_at).toLocaleString('pt-BR')}
                      </Text>
                    </div>
                    {!alert.is_read && (
                      <div
                        style={{
                          width: 8,
                          height: 8,
                          borderRadius: '50%',
                          backgroundColor: getAlertSeverityColor(alert.severity),
                        }}
                      />
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <Text type="secondary">Nenhum alerta recente</Text>
            )}
          </Card>
        </Col>
      </Row>

      {/* Performance Charts */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={16}>
          <Card title="Performance dos Últimos 7 Dias" loading={analyticsLoading}>
            {analyticsData && analyticsData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={analyticsData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={(value) => new Date(value).toLocaleDateString('pt-BR')}
                  />
                  <YAxis />
                  <Tooltip 
                    labelFormatter={(value) => new Date(value).toLocaleDateString('pt-BR')}
                    formatter={(value, name) => {
                      if (name === 'spend') return [formatCurrency(value), 'Gasto'];
                      if (name === 'impressions') return [formatNumber(value), 'Impressões'];
                      if (name === 'clicks') return [formatNumber(value), 'Clicks'];
                      if (name === 'conversions') return [formatNumber(value), 'Conversões'];
                      return [value, name];
                    }}
                  />
                  <Line type="monotone" dataKey="spend" stroke="#1890ff" strokeWidth={2} />
                  <Line type="monotone" dataKey="conversions" stroke="#52c41a" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <Text type="secondary">Dados insuficientes para exibir o gráfico</Text>
              </div>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="CTR por Dia" loading={analyticsLoading}>
            {analyticsData && analyticsData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={analyticsData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={(value) => new Date(value).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}
                  />
                  <YAxis />
                  <Tooltip 
                    labelFormatter={(value) => new Date(value).toLocaleDateString('pt-BR')}
                    formatter={(value) => [`${value}%`, 'CTR']}
                  />
                  <Bar dataKey="ctr" fill="#faad14" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <Text type="secondary">Dados insuficientes para exibir o gráfico</Text>
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* Top Campaigns */}
      <Card title="Top 5 Campanhas" loading={campaignsLoading}>
        {campaigns && campaigns.length > 0 ? (
          <Row gutter={[16, 16]}>
            {campaigns.map((campaign) => (
              <Col xs={24} lg={12} xl={8} key={campaign.campaign_id}>
                <Card size="small" className="campaign-card">
                  <div className="campaign-header">
                    <Text strong className="campaign-name">{campaign.name}</Text>
                    <Text 
                      style={{ 
                        color: campaign.status === 'ACTIVE' ? '#52c41a' : '#faad14',
                        fontSize: 12,
                        fontWeight: 500 
                      }}
                    >
                      {campaign.status}
                    </Text>
                  </div>
                  <div className="campaign-metrics">
                    <div className="metric-item">
                      <div className="metric-item-value">{formatCurrency(campaign.spend_today)}</div>
                      <div className="metric-item-label">Gasto Hoje</div>
                    </div>
                    <div className="metric-item">
                      <div className="metric-item-value">{formatNumber(campaign.impressions_today)}</div>
                      <div className="metric-item-label">Impressões</div>
                    </div>
                    <div className="metric-item">
                      <div className="metric-item-value">{campaign.ctr_today}%</div>
                      <div className="metric-item-label">CTR</div>
                    </div>
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        ) : (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Text type="secondary">Nenhuma campanha encontrada</Text>
          </div>
        )}
      </Card>

      {/* Real-time Updates Alert */}
      {realTimeData && (
        <Alert
          message="Atualização em Tempo Real"
          description={`Dados atualizados em ${new Date(realTimeData.timestamp).toLocaleTimeString('pt-BR')}`}
          type="info"
          showIcon
          style={{ marginTop: 16 }}
          closable
        />
      )}
    </div>
  );
};

export default Dashboard;
