import React, { useState } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  Typography,
  Row,
  Col,
  Statistic,
  Popconfirm,
  message,
  Drawer,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  SyncOutlined,
  BarChartOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import axios from 'axios';

const { Title, Text } = Typography;
const { Option } = Select;

const Campaigns = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingCampaign, setEditingCampaign] = useState(null);
  const [metricsDrawerVisible, setMetricsDrawerVisible] = useState(false);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const { data: campaigns, isLoading, refetch } = useQuery(
    'campaigns',
    () => axios.get('/api/v1/campaigns/').then(res => res.data),
    { refetchInterval: 30000 }
  );

  const { data: metrics, isLoading: metricsLoading } = useQuery(
    ['campaignMetrics', selectedCampaign?.campaign_id],
    () => axios.get(`/api/v1/campaigns/${selectedCampaign.campaign_id}/metrics`).then(res => res.data),
    { enabled: !!selectedCampaign }
  );

  const createCampaignMutation = useMutation(
    (campaignData) => axios.post('/api/v1/campaigns/', campaignData),
    {
      onSuccess: () => {
        message.success('Campanha criada com sucesso!');
        setIsModalVisible(false);
        form.resetFields();
        queryClient.invalidateQueries('campaigns');
      },
      onError: (error) => {
        message.error(error.response?.data?.detail || 'Erro ao criar campanha');
      },
    }
  );

  const updateCampaignMutation = useMutation(
    ({ campaignId, data }) => axios.put(`/api/v1/campaigns/${campaignId}`, data),
    {
      onSuccess: () => {
        message.success('Campanha atualizada com sucesso!');
        setIsModalVisible(false);
        setEditingCampaign(null);
        form.resetFields();
        queryClient.invalidateQueries('campaigns');
      },
      onError: (error) => {
        message.error(error.response?.data?.detail || 'Erro ao atualizar campanha');
      },
    }
  );

  const deleteCampaignMutation = useMutation(
    (campaignId) => axios.delete(`/api/v1/campaigns/${campaignId}`),
    {
      onSuccess: () => {
        message.success('Campanha excluída com sucesso!');
        queryClient.invalidateQueries('campaigns');
      },
      onError: (error) => {
        message.error(error.response?.data?.detail || 'Erro ao excluir campanha');
      },
    }
  );

  const syncMetricsMutation = useMutation(
    (campaignId) => axios.post(`/api/v1/campaigns/${campaignId}/sync-metrics`),
    {
      onSuccess: () => {
        message.success('Métricas sincronizadas com sucesso!');
        queryClient.invalidateQueries('campaigns');
      },
      onError: (error) => {
        message.error(error.response?.data?.detail || 'Erro ao sincronizar métricas');
      },
    }
  );

  const handleCreateCampaign = () => {
    setEditingCampaign(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEditCampaign = (campaign) => {
    setEditingCampaign(campaign);
    form.setFieldsValue({
      name: campaign.name,
      objective: campaign.objective,
      daily_budget: campaign.daily_budget,
      total_budget: campaign.total_budget,
    });
    setIsModalVisible(true);
  };

  const handleSubmit = async (values) => {
    try {
      if (editingCampaign) {
        await updateCampaignMutation.mutateAsync({
          campaignId: editingCampaign.campaign_id,
          data: values,
        });
      } else {
        await createCampaignMutation.mutateAsync(values);
      }
    } catch (error) {
      console.error('Submit error:', error);
    }
  };

  const handleDeleteCampaign = async (campaignId) => {
    try {
      await deleteCampaignMutation.mutateAsync(campaignId);
    } catch (error) {
      console.error('Delete error:', error);
    }
  };

  const handleSyncMetrics = async (campaignId) => {
    try {
      await syncMetricsMutation.mutateAsync(campaignId);
    } catch (error) {
      console.error('Sync error:', error);
    }
  };

  const showMetrics = (campaign) => {
    setSelectedCampaign(campaign);
    setMetricsDrawerVisible(true);
  };

  const getStatusColor = (status) => {
    const colors = {
      ACTIVE: 'green',
      PAUSED: 'orange',
      DELETED: 'red',
    };
    return colors[status] || 'default';
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'USD',
    }).format(value || 0);
  };

  const formatNumber = (value) => {
    return new Intl.NumberFormat('pt-BR').format(value || 0);
  };

  const columns = [
    {
      title: 'Nome da Campanha',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <div>
          <Text strong>{text}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.objective}
          </Text>
        </div>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={getStatusColor(status)}>
          {status}
        </Tag>
      ),
    },
    {
      title: 'Orçamento Diário',
      dataIndex: 'daily_budget',
      key: 'daily_budget',
      render: (value) => formatCurrency(value),
    },
    {
      title: 'Orçamento Total',
      dataIndex: 'total_budget',
      key: 'total_budget',
      render: (value) => value ? formatCurrency(value) : '-',
    },
    {
      title: 'Criado em',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => new Date(date).toLocaleDateString('pt-BR'),
    },
    {
      title: 'Ações',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            icon={<BarChartOutlined />}
            size="small"
            onClick={() => showMetrics(record)}
          >
            Métricas
          </Button>
          <Button
            icon={<EditOutlined />}
            size="small"
            onClick={() => handleEditCampaign(record)}
          >
            Editar
          </Button>
          <Button
            icon={<SyncOutlined />}
            size="small"
            loading={syncMetricsMutation.isLoading}
            onClick={() => handleSyncMetrics(record.campaign_id)}
          >
            Sincronizar
          </Button>
          <Popconfirm
            title="Tem certeza que deseja excluir esta campanha?"
            onConfirm={() => handleDeleteCampaign(record.campaign_id)}
            okText="Sim"
            cancelText="Não"
          >
            <Button
              icon={<DeleteOutlined />}
              size="small"
              danger
              loading={deleteCampaignMutation.isLoading}
            >
              Excluir
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* Page Header */}
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={2} style={{ margin: 0 }}>Campanhas</Title>
          <Text type="secondary">Gerencie suas campanhas Meta Ads</Text>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleCreateCampaign}
          size="large"
        >
          Nova Campanha
        </Button>
      </div>

      {/* Campaigns Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={campaigns}
          loading={isLoading}
          rowKey="campaign_id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `Total de ${total} campanhas`,
          }}
        />
      </Card>

      {/* Create/Edit Campaign Modal */}
      <Modal
        title={editingCampaign ? 'Editar Campanha' : 'Nova Campanha'}
        open={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false);
          setEditingCampaign(null);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="name"
            label="Nome da Campanha"
            rules={[{ required: true, message: 'Por favor, insira o nome da campanha' }]}
          >
            <Input placeholder="Nome da campanha" />
          </Form.Item>

          <Form.Item
            name="objective"
            label="Objetivo"
            rules={[{ required: true, message: 'Por favor, selecione o objetivo' }]}
          >
            <Select placeholder="Selecione o objetivo">
              <Option value="CONVERSIONS">Conversões</Option>
              <Option value="TRAFFIC">Tráfego</Option>
              <Option value="AWARENESS">Reconhecimento</Option>
              <Option value="ENGAGEMENT">Engajamento</Option>
              <Option value="APP_INSTALLS">Instalações de App</Option>
              <Option value="LEAD_GENERATION">Geração de Leads</Option>
              <Option value="MESSAGES">Mensagens</Option>
              <Option value="SALES">Vendas</Option>
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="daily_budget"
                label="Orçamento Diário (USD)"
                rules={[{ required: true, message: 'Por favor, insira o orçamento diário' }]}
              >
                <InputNumber
                  min={1}
                  max={10000}
                  style={{ width: '100%' }}
                  placeholder="0.00"
                  formatter={(value) => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                  parser={(value) => value.replace(/\$\s?|(,*)/g, '')}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="total_budget"
                label="Orçamento Total (USD)"
              >
                <InputNumber
                  min={1}
                  max={100000}
                  style={{ width: '100%' }}
                  placeholder="0.00"
                  formatter={(value) => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                  parser={(value) => value.replace(/\$\s?|(,*)/g, '')}
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setIsModalVisible(false)}>
                Cancelar
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={createCampaignMutation.isLoading || updateCampaignMutation.isLoading}
              >
                {editingCampaign ? 'Atualizar' : 'Criar'} Campanha
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Metrics Drawer */}
      <Drawer
        title={`Métricas - ${selectedCampaign?.name}`}
        placement="right"
        onClose={() => setMetricsDrawerVisible(false)}
        open={metricsDrawerVisible}
        width={600}
      >
        {selectedCampaign && (
          <div>
            {/* Campaign Info */}
            <Card size="small" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={8}>
                  <Statistic
                    title="Status"
                    value={selectedCampaign.status}
                    valueStyle={{ color: getStatusColor(selectedCampaign.status) === 'green' ? '#52c41a' : '#faad14' }}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="Orçamento Diário"
                    value={selectedCampaign.daily_budget}
                    formatter={(value) => formatCurrency(value)}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="Objetivo"
                    value={selectedCampaign.objective}
                  />
                </Col>
              </Row>
            </Card>

            {/* Metrics Table */}
            {metrics && metrics.length > 0 ? (
              <Table
                dataSource={metrics}
                loading={metricsLoading}
                size="small"
                pagination={{ pageSize: 5 }}
                rowKey="id"
                columns={[
                  {
                    title: 'Data',
                    dataIndex: 'date_start',
                    render: (date) => new Date(date).toLocaleDateString('pt-BR'),
                  },
                  {
                    title: 'Gasto',
                    dataIndex: 'spend',
                    render: (value) => formatCurrency(value),
                  },
                  {
                    title: 'Impressões',
                    dataIndex: 'impressions',
                    render: (value) => formatNumber(value),
                  },
                  {
                    title: 'Clicks',
                    dataIndex: 'clicks',
                    render: (value) => formatNumber(value),
                  },
                  {
                    title: 'CTR',
                    dataIndex: 'ctr',
                    render: (value) => `${value}%`,
                  },
                  {
                    title: 'Conversões',
                    dataIndex: 'conversions',
                    render: (value) => formatNumber(value),
                  },
                ]}
              />
            ) : (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <Text type="secondary">Nenhuma métrica encontrada</Text>
              </div>
            )}
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default Campaigns;
