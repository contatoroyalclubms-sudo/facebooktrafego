import React, { useState } from 'react';
import {
  Card,
  List,
  Tag,
  Button,
  Space,
  Typography,
  Row,
  Col,
  Select,
  Input,
  Badge,
  Empty,
  Popconfirm,
  message,
} from 'antd';
import {
  BellOutlined,
  CheckOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import axios from 'axios';

const { Title, Text } = Typography;
const { Option } = Select;
const { Search } = Input;

const Alerts = () => {
  const [filter, setFilter] = useState('all');
  const [searchText, setSearchText] = useState('');
  const queryClient = useQueryClient();

  const { data: alerts, isLoading } = useQuery(
    ['alerts', filter],
    () => {
      const params = new URLSearchParams();
      if (filter !== 'all') {
        if (filter === 'unread') {
          params.append('is_read', 'false');
        } else {
          params.append('severity', filter);
        }
      }
      return axios.get(`/api/v1/dashboard/alerts?${params}`).then(res => res.data);
    },
    { refetchInterval: 30000 }
  );

  const markAsReadMutation = useMutation(
    (alertId) => axios.post(`/api/v1/dashboard/alerts/${alertId}/mark-read`),
    {
      onSuccess: () => {
        message.success('Alerta marcado como lido');
        queryClient.invalidateQueries('alerts');
      },
      onError: () => {
        message.error('Erro ao marcar alerta como lido');
      },
    }
  );

  const getSeverityIcon = (severity) => {
    const icons = {
      low: <InfoCircleOutlined style={{ color: '#52c41a' }} />,
      medium: <ExclamationCircleOutlined style={{ color: '#faad14' }} />,
      high: <WarningOutlined style={{ color: '#ff7a45' }} />,
      critical: <CloseCircleOutlined style={{ color: '#ff4d4f' }} />,
    };
    return icons[severity] || <InfoCircleOutlined />;
  };

  const getSeverityColor = (severity) => {
    const colors = {
      low: 'green',
      medium: 'orange',
      high: 'red',
      critical: 'red',
    };
    return colors[severity] || 'default';
  };

  const getSeverityText = (severity) => {
    const texts = {
      low: 'Baixa',
      medium: 'Média',
      high: 'Alta',
      critical: 'Crítica',
    };
    return texts[severity] || severity;
  };

  const getAlertTypeText = (type) => {
    const types = {
      performance: 'Performance',
      budget: 'Orçamento',
      optimization: 'Otimização',
      system: 'Sistema',
      daily_report: 'Relatório Diário',
      no_conversions: 'Sem Conversões',
      auto_pause: 'Pausa Automática',
    };
    return types[type] || type;
  };

  const handleMarkAsRead = async (alertId) => {
    try {
      await markAsReadMutation.mutateAsync(alertId);
    } catch (error) {
      console.error('Mark as read error:', error);
    }
  };

  const filteredAlerts = alerts?.filter(alert => {
    if (searchText) {
      return alert.title.toLowerCase().includes(searchText.toLowerCase()) ||
             alert.message.toLowerCase().includes(searchText.toLowerCase());
    }
    return true;
  }) || [];

  const unreadCount = alerts?.filter(alert => !alert.is_read).length || 0;

  return (
    <div>
      {/* Page Header */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
          <BellOutlined />
          Alertas
          {unreadCount > 0 && (
            <Badge count={unreadCount} style={{ marginLeft: 8 }} />
          )}
        </Title>
        <Text type="secondary">Monitore alertas e notificações do sistema</Text>
      </div>

      {/* Filters */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16} align="middle">
          <Col>
            <Text strong>Filtrar por:</Text>
          </Col>
          <Col>
            <Select
              value={filter}
              onChange={setFilter}
              style={{ width: 150 }}
            >
              <Option value="all">Todos</Option>
              <Option value="unread">Não lidos</Option>
              <Option value="critical">Críticos</Option>
              <Option value="high">Alta prioridade</Option>
              <Option value="medium">Média prioridade</Option>
              <Option value="low">Baixa prioridade</Option>
            </Select>
          </Col>
          <Col flex="auto">
            <Search
              placeholder="Buscar alertas..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ maxWidth: 300 }}
              allowClear
            />
          </Col>
        </Row>
      </Card>

      {/* Alerts List */}
      <Card>
        {filteredAlerts.length > 0 ? (
          <List
            itemLayout="vertical"
            dataSource={filteredAlerts}
            loading={isLoading}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `Total de ${total} alertas`,
            }}
            renderItem={(alert) => (
              <List.Item
                key={alert.id}
                style={{
                  backgroundColor: alert.is_read ? '#fafafa' : '#fff',
                  border: alert.is_read ? '1px solid #f0f0f0' : '1px solid #d9d9d9',
                  borderRadius: 6,
                  marginBottom: 12,
                  padding: 16,
                  borderLeft: `4px solid ${
                    alert.severity === 'critical' ? '#ff4d4f' :
                    alert.severity === 'high' ? '#ff7a45' :
                    alert.severity === 'medium' ? '#faad14' : '#52c41a'
                  }`,
                }}
                actions={[
                  !alert.is_read && (
                    <Button
                      type="link"
                      icon={<CheckOutlined />}
                      onClick={() => handleMarkAsRead(alert.id)}
                      loading={markAsReadMutation.isLoading}
                    >
                      Marcar como lido
                    </Button>
                  ),
                ].filter(Boolean)}
              >
                <List.Item.Meta
                  avatar={getSeverityIcon(alert.severity)}
                  title={
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Text strong style={{ fontSize: 16 }}>
                        {alert.title}
                      </Text>
                      {!alert.is_read && (
                        <Badge status="processing" />
                      )}
                    </div>
                  }
                  description={
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                        <Tag color={getSeverityColor(alert.severity)}>
                          {getSeverityText(alert.severity)}
                        </Tag>
                        <Tag>{getAlertTypeText(alert.alert_type)}</Tag>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {new Date(alert.created_at).toLocaleString('pt-BR')}
                        </Text>
                      </div>
                      <Text style={{ fontSize: 14, lineHeight: 1.5 }}>
                        {alert.message}
                      </Text>
                      {alert.campaign_id && (
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          Campanha: {alert.campaign_id}
                        </Text>
                      )}
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        ) : (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              searchText ? 
                `Nenhum alerta encontrado para "${searchText}"` : 
                'Nenhum alerta encontrado'
            }
          />
        )}
      </Card>

      {/* Summary Stats */}
      {alerts && alerts.length > 0 && (
        <Card title="Resumo de Alertas" style={{ marginTop: 24 }}>
          <Row gutter={16}>
            <Col xs={12} sm={6}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 24, fontWeight: 'bold', color: '#ff4d4f' }}>
                  {alerts.filter(a => a.severity === 'critical').length}
                </div>
                <div style={{ color: '#666', fontSize: 12 }}>Críticos</div>
              </div>
            </Col>
            <Col xs={12} sm={6}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 24, fontWeight: 'bold', color: '#ff7a45' }}>
                  {alerts.filter(a => a.severity === 'high').length}
                </div>
                <div style={{ color: '#666', fontSize: 12 }}>Alta Prioridade</div>
              </div>
            </Col>
            <Col xs={12} sm={6}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 24, fontWeight: 'bold', color: '#faad14' }}>
                  {alerts.filter(a => a.severity === 'medium').length}
                </div>
                <div style={{ color: '#666', fontSize: 12 }}>Média Prioridade</div>
              </div>
            </Col>
            <Col xs={12} sm={6}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 24, fontWeight: 'bold', color: '#52c41a' }}>
                  {alerts.filter(a => a.severity === 'low').length}
                </div>
                <div style={{ color: '#666', fontSize: 12 }}>Baixa Prioridade</div>
              </div>
            </Col>
          </Row>
        </Card>
      )}
    </div>
  );
};

export default Alerts;
