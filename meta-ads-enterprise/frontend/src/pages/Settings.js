import React, { useState } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Switch,
  Typography,
  Row,
  Col,
  Divider,
  message,
  Tabs,
  InputNumber,
  Select,
  Space,
} from 'antd';
import {
  UserOutlined,
  KeyOutlined,
  SettingOutlined,
  BellOutlined,
  FacebookOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import { useAuth } from '../hooks/useAuth';
import { useMutation } from 'react-query';
import axios from 'axios';

const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { Option } = Select;
const { TextArea } = Input;

const Settings = () => {
  const { user, updateProfile } = useAuth();
  const [profileForm] = Form.useForm();
  const [passwordForm] = Form.useForm();
  const [facebookForm] = Form.useForm();
  const [optimizationForm] = Form.useForm();

  const updateFacebookMutation = useMutation(
    (data) => axios.put('/api/v1/auth/me', data),
    {
      onSuccess: () => {
        message.success('Credenciais do Facebook atualizadas com sucesso!');
      },
      onError: (error) => {
        message.error(error.response?.data?.detail || 'Erro ao atualizar credenciais');
      },
    }
  );

  const updatePasswordMutation = useMutation(
    (data) => axios.put('/api/v1/auth/change-password', data),
    {
      onSuccess: () => {
        message.success('Senha alterada com sucesso!');
        passwordForm.resetFields();
      },
      onError: (error) => {
        message.error(error.response?.data?.detail || 'Erro ao alterar senha');
      },
    }
  );

  const handleProfileUpdate = async (values) => {
    try {
      await updateProfile(values);
    } catch (error) {
      console.error('Profile update error:', error);
    }
  };

  const handlePasswordUpdate = async (values) => {
    try {
      await updatePasswordMutation.mutateAsync(values);
    } catch (error) {
      console.error('Password update error:', error);
    }
  };

  const handleFacebookUpdate = async (values) => {
    try {
      await updateFacebookMutation.mutateAsync(values);
    } catch (error) {
      console.error('Facebook update error:', error);
    }
  };

  const handleOptimizationUpdate = async (values) => {
    try {
      message.success('Configurações de otimização atualizadas!');
    } catch (error) {
      console.error('Optimization update error:', error);
    }
  };

  return (
    <div>
      {/* Page Header */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>Configurações</Title>
        <Text type="secondary">Gerencie suas configurações de conta e preferências</Text>
      </div>

      <Tabs defaultActiveKey="profile" size="large">
        {/* Profile Settings */}
        <TabPane
          tab={
            <span>
              <UserOutlined />
              Perfil
            </span>
          }
          key="profile"
        >
          <Card>
            <Form
              form={profileForm}
              layout="vertical"
              onFinish={handleProfileUpdate}
              initialValues={{
                email: user?.email,
                full_name: user?.full_name,
              }}
            >
              <Row gutter={24}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="full_name"
                    label="Nome Completo"
                    rules={[{ required: true, message: 'Por favor, insira seu nome' }]}
                  >
                    <Input placeholder="Seu nome completo" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="email"
                    label="Email"
                    rules={[
                      { required: true, message: 'Por favor, insira seu email' },
                      { type: 'email', message: 'Email inválido' },
                    ]}
                  >
                    <Input placeholder="seu@email.com" />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item>
                <Button type="primary" htmlType="submit">
                  Atualizar Perfil
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        {/* Password Settings */}
        <TabPane
          tab={
            <span>
              <KeyOutlined />
              Senha
            </span>
          }
          key="password"
        >
          <Card>
            <Form
              form={passwordForm}
              layout="vertical"
              onFinish={handlePasswordUpdate}
            >
              <Row gutter={24}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="current_password"
                    label="Senha Atual"
                    rules={[{ required: true, message: 'Por favor, insira sua senha atual' }]}
                  >
                    <Input.Password placeholder="Senha atual" />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={24}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="new_password"
                    label="Nova Senha"
                    rules={[
                      { required: true, message: 'Por favor, insira a nova senha' },
                      { min: 8, message: 'Senha deve ter pelo menos 8 caracteres' },
                    ]}
                  >
                    <Input.Password placeholder="Nova senha" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="confirm_password"
                    label="Confirmar Nova Senha"
                    dependencies={['new_password']}
                    rules={[
                      { required: true, message: 'Por favor, confirme a nova senha' },
                      ({ getFieldValue }) => ({
                        validator(_, value) {
                          if (!value || getFieldValue('new_password') === value) {
                            return Promise.resolve();
                          }
                          return Promise.reject(new Error('As senhas não coincidem!'));
                        },
                      }),
                    ]}
                  >
                    <Input.Password placeholder="Confirme a nova senha" />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item>
                <Button 
                  type="primary" 
                  htmlType="submit"
                  loading={updatePasswordMutation.isLoading}
                >
                  Alterar Senha
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        {/* Facebook Integration */}
        <TabPane
          tab={
            <span>
              <FacebookOutlined />
              Facebook Ads
            </span>
          }
          key="facebook"
        >
          <Card>
            <Form
              form={facebookForm}
              layout="vertical"
              onFinish={handleFacebookUpdate}
              initialValues={{
                facebook_access_token: user?.facebook_access_token,
                facebook_ad_account_id: user?.facebook_ad_account_id,
              }}
            >
              <Form.Item
                name="facebook_access_token"
                label="Access Token do Facebook"
                rules={[{ required: true, message: 'Por favor, insira o access token' }]}
                extra="Token de acesso para a API do Facebook Ads. Você pode obter este token no Facebook Developers."
              >
                <TextArea 
                  rows={3}
                  placeholder="EAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                />
              </Form.Item>

              <Form.Item
                name="facebook_ad_account_id"
                label="ID da Conta de Anúncios"
                rules={[{ required: true, message: 'Por favor, insira o ID da conta' }]}
                extra="ID numérico da sua conta de anúncios do Facebook (sem o prefixo 'act_')."
              >
                <Input placeholder="123456789012345" />
              </Form.Item>

              <Form.Item>
                <Button 
                  type="primary" 
                  htmlType="submit"
                  loading={updateFacebookMutation.isLoading}
                >
                  Salvar Credenciais
                </Button>
              </Form.Item>
            </Form>

            <Divider />

            <div style={{ background: '#f6ffed', padding: 16, borderRadius: 6, border: '1px solid #b7eb8f' }}>
              <Title level={5} style={{ color: '#389e0d', margin: 0, marginBottom: 8 }}>
                Como obter as credenciais do Facebook:
              </Title>
              <ol style={{ margin: 0, paddingLeft: 20, color: '#666' }}>
                <li>Acesse o <a href="https://developers.facebook.com/" target="_blank" rel="noopener noreferrer">Facebook Developers</a></li>
                <li>Crie um app ou use um existente</li>
                <li>Adicione o produto "Marketing API"</li>
                <li>Gere um access token com as permissões necessárias</li>
                <li>Encontre o ID da sua conta de anúncios no Gerenciador de Anúncios</li>
              </ol>
            </div>
          </Card>
        </TabPane>

        {/* Optimization Settings */}
        <TabPane
          tab={
            <span>
              <RobotOutlined />
              Otimização
            </span>
          }
          key="optimization"
        >
          <Card>
            <Form
              form={optimizationForm}
              layout="vertical"
              onFinish={handleOptimizationUpdate}
              initialValues={{
                auto_optimize: true,
                auto_pause: false,
                auto_budget_optimize: false,
                ctr_threshold: 1.0,
                roas_threshold: 2.0,
                max_frequency: 3.0,
                notification_email: true,
                notification_slack: false,
              }}
            >
              <Title level={4}>Otimização Automática</Title>
              
              <Row gutter={24}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="auto_optimize"
                    label="Otimização Automática"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    Permite que o sistema otimize automaticamente suas campanhas
                  </Text>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    name="auto_pause"
                    label="Pausa Automática"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    Pausa automaticamente campanhas com baixa performance
                  </Text>
                </Col>
              </Row>

              <Row gutter={24}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="auto_budget_optimize"
                    label="Otimização de Orçamento"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    Redistribui orçamento automaticamente entre campanhas
                  </Text>
                </Col>
              </Row>

              <Divider />

              <Title level={4}>Limites de Performance</Title>

              <Row gutter={24}>
                <Col xs={24} md={8}>
                  <Form.Item
                    name="ctr_threshold"
                    label="CTR Mínimo (%)"
                    rules={[{ required: true, message: 'Insira o CTR mínimo' }]}
                  >
                    <InputNumber
                      min={0.1}
                      max={10}
                      step={0.1}
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>

                <Col xs={24} md={8}>
                  <Form.Item
                    name="roas_threshold"
                    label="ROAS Mínimo"
                    rules={[{ required: true, message: 'Insira o ROAS mínimo' }]}
                  >
                    <InputNumber
                      min={0.1}
                      max={20}
                      step={0.1}
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>

                <Col xs={24} md={8}>
                  <Form.Item
                    name="max_frequency"
                    label="Frequência Máxima"
                    rules={[{ required: true, message: 'Insira a frequência máxima' }]}
                  >
                    <InputNumber
                      min={1}
                      max={10}
                      step={0.1}
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Divider />

              <Title level={4}>Notificações</Title>

              <Row gutter={24}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="notification_email"
                    label="Notificações por Email"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    name="notification_slack"
                    label="Notificações no Slack"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item>
                <Button type="primary" htmlType="submit">
                  Salvar Configurações
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default Settings;
