import React, { useState } from 'react';
import {
  Card,
  Row,
  Col,
  DatePicker,
  Select,
  Button,
  Typography,
  Statistic,
  Table,
  Space,
} from 'antd';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useQuery } from 'react-query';
import axios from 'axios';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

const Analytics = () => {
  const [dateRange, setDateRange] = useState([
    dayjs().subtract(30, 'days'),
    dayjs(),
  ]);
  const [selectedCampaign, setSelectedCampaign] = useState(null);

  const { data: overview, isLoading: overviewLoading } = useQuery(
    ['analyticsOverview', dateRange],
    () => {
      const params = new URLSearchParams({
        date_start: dateRange[0].toISOString(),
        date_end: dateRange[1].toISOString(),
      });
      return axios.get(`/api/v1/analytics/overview?${params}`).then(res => res.data);
    },
    { enabled: !!dateRange }
  );

  const { data: campaignPerformance, isLoading: performanceLoading } = useQuery(
    ['campaignPerformance', dateRange],
    () => {
      const params = new URLSearchParams({
        date_start: dateRange[0].toISOString(),
        date_end: dateRange[1].toISOString(),
        limit: '10',
      });
      return axios.get(`/api/v1/analytics/campaigns/performance?${params}`).then(res => res.data);
    },
    { enabled: !!dateRange }
  );

  const { data: timeseriesData, isLoading: timeseriesLoading } = useQuery(
    ['timeseriesData', dateRange, selectedCampaign],
    () => {
      const params = new URLSearchParams({
        date_start: dateRange[0].toISOString(),
        date_end: dateRange[1].toISOString(),
      });
      if (selectedCampaign) {
        params.append('campaign_id', selectedCampaign);
      }
      return axios.get(`/api/v1/analytics/timeseries?${params}`).then(res => res.data);
    },
    { enabled: !!dateRange }
  );

  const { data: campaigns } = useQuery(
    'campaigns',
    () => axios.get('/api/v1/campaigns/').then(res => res.data)
  );

  const { data: insights } = useQuery(
    'insights',
    () => axios.get('/api/v1/analytics/insights').then(res => res.data)
  );

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'USD',
    }).format(value || 0);
  };

  const formatNumber = (value) => {
    return new Intl.NumberFormat('pt-BR').format(value || 0);
  };

  const formatPercentage = (value) => {
    return `${(value || 0).toFixed(2)}%`;
  };

  const COLORS = ['#1890ff', '#52c41a', '#faad14', '#ff4d4f', '#722ed1', '#13c2c2'];

  const performanceColumns = [
    {
      title: 'Campanha',
      dataIndex: 'campaign_name',
      key: 'campaign_name',
    },
    {
      title: 'Gasto',
      dataIndex: 'spend',
      key: 'spend',
      render: (value) => formatCurrency(value),
      sorter: (a, b) => a.spend - b.spend,
    },
    {
      title: 'Impressões',
      dataIndex: 'impressions',
      key: 'impressions',
      render: (value) => formatNumber(value),
      sorter: (a, b) => a.impressions - b.impressions,
    },
    {
      title: 'Clicks',
      dataIndex: 'clicks',
      key: 'clicks',
      render: (value) => formatNumber(value),
      sorter: (a, b) => a.clicks - b.clicks,
    },
    {
      title: 'CTR',
      dataIndex: 'ctr',
      key: 'ctr',
      render: (value) => formatPercentage(value),
      sorter: (a, b) => a.ctr - b.ctr,
    },
    {
      title: 'CPM',
      dataIndex: 'cpm',
      key: 'cpm',
      render: (value) => formatCurrency(value),
      sorter: (a, b) => a.cpm - b.cpm,
    },
    {
      title: 'ROAS',
      dataIndex: 'roas',
      key: 'roas',
      render: (value) => value?.toFixed(2) || '0.00',
      sorter: (a, b) => a.roas - b.roas,
    },
    {
      title: 'Score',
      dataIndex: 'performance_score',
      key: 'performance_score',
      render: (value) => (
        <span style={{ 
          color: value >= 70 ? '#52c41a' : value >= 40 ? '#faad14' : '#ff4d4f',
          fontWeight: 'bold'
        }}>
          {value?.toFixed(1) || '0.0'}
        </span>
      ),
      sorter: (a, b) => a.performance_score - b.performance_score,
    },
  ];

  return (
    <div>
      {/* Page Header */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>Analytics</Title>
        <Text type="secondary">Análise detalhada de performance das campanhas</Text>
      </div>

      {/* Filters */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16} align="middle">
          <Col>
            <Text strong>Período:</Text>
          </Col>
          <Col>
            <RangePicker
              value={dateRange}
              onChange={setDateRange}
              format="DD/MM/YYYY"
              allowClear={false}
            />
          </Col>
          <Col>
            <Text strong>Campanha:</Text>
          </Col>
          <Col>
            <Select
              style={{ width: 200 }}
              placeholder="Todas as campanhas"
              allowClear
              value={selectedCampaign}
              onChange={setSelectedCampaign}
            >
              {campaigns?.map(campaign => (
                <Option key={campaign.campaign_id} value={campaign.campaign_id}>
                  {campaign.name}
                </Option>
              ))}
            </Select>
          </Col>
        </Row>
      </Card>

      {/* Overview Stats */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={overviewLoading}>
            <Statistic
              title="Gasto Total"
              value={overview?.total_spend || 0}
              formatter={(value) => formatCurrency(value)}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={overviewLoading}>
            <Statistic
              title="Impressões Totais"
              value={overview?.total_impressions || 0}
              formatter={(value) => formatNumber(value)}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={overviewLoading}>
            <Statistic
              title="CTR Médio"
              value={overview?.average_ctr || 0}
              suffix="%"
              precision={2}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={overviewLoading}>
            <Statistic
              title="ROAS Médio"
              value={overview?.average_roas || 0}
              precision={2}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Charts */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {/* Performance Timeline */}
        <Col xs={24} lg={16}>
          <Card title="Performance ao Longo do Tempo" loading={timeseriesLoading}>
            {timeseriesData && timeseriesData.length > 0 ? (
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={timeseriesData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={(value) => new Date(value).toLocaleDateString('pt-BR')}
                  />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
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
                  <Legend />
                  <Line 
                    yAxisId="left"
                    type="monotone" 
                    dataKey="spend" 
                    stroke="#1890ff" 
                    strokeWidth={2}
                    name="Gasto"
                  />
                  <Line 
                    yAxisId="right"
                    type="monotone" 
                    dataKey="conversions" 
                    stroke="#52c41a" 
                    strokeWidth={2}
                    name="Conversões"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ textAlign: 'center', padding: 60 }}>
                <Text type="secondary">Nenhum dado disponível para o período selecionado</Text>
              </div>
            )}
          </Card>
        </Col>

        {/* CTR and CPM Chart */}
        <Col xs={24} lg={8}>
          <Card title="CTR vs CPM" loading={timeseriesLoading}>
            {timeseriesData && timeseriesData.length > 0 ? (
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={timeseriesData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={(value) => new Date(value).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}
                  />
                  <YAxis />
                  <Tooltip 
                    labelFormatter={(value) => new Date(value).toLocaleDateString('pt-BR')}
                    formatter={(value, name) => {
                      if (name === 'ctr') return [`${value}%`, 'CTR'];
                      if (name === 'cpm') return [formatCurrency(value), 'CPM'];
                      return [value, name];
                    }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="ctr" 
                    stackId="1" 
                    stroke="#faad14" 
                    fill="#faad14" 
                    fillOpacity={0.6}
                    name="CTR"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ textAlign: 'center', padding: 60 }}>
                <Text type="secondary">Nenhum dado disponível</Text>
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* Performance Table and Insights */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card title="Performance por Campanha" loading={performanceLoading}>
            <Table
              columns={performanceColumns}
              dataSource={campaignPerformance}
              rowKey="campaign_id"
              pagination={{ pageSize: 10 }}
              size="small"
            />
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card title="Insights de IA">
            {insights?.insights && insights.insights.length > 0 ? (
              <Space direction="vertical" style={{ width: '100%' }}>
                {insights.insights.map((insight, index) => (
                  <Card 
                    key={index}
                    size="small" 
                    style={{ 
                      borderLeft: `4px solid ${
                        insight.type === 'warning' ? '#faad14' : 
                        insight.type === 'alert' ? '#ff4d4f' : '#1890ff'
                      }`
                    }}
                  >
                    <Text strong style={{ display: 'block', marginBottom: 8 }}>
                      {insight.title}
                    </Text>
                    <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>
                      {insight.message}
                    </Text>
                    <Text style={{ fontSize: 12, color: '#52c41a' }}>
                      💡 {insight.recommendation}
                    </Text>
                  </Card>
                ))}
              </Space>
            ) : (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <Text type="secondary">Nenhum insight disponível</Text>
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Analytics;
