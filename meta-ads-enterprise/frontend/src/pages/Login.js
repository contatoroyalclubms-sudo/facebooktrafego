import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, Divider } from 'antd';
import { UserOutlined, LockOutlined, FacebookOutlined } from '@ant-design/icons';
import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;

const Login = () => {
  const [loading, setLoading] = useState(false);
  const [isRegister, setIsRegister] = useState(false);
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (values) => {
    setLoading(true);
    
    try {
      let result;
      if (isRegister) {
        result = await register(values);
        if (result.success) {
          setIsRegister(false);
        }
      } else {
        result = await login(values.email, values.password);
        if (result.success) {
          navigate('/');
        }
      }
    } catch (error) {
      console.error('Auth error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <Card
        style={{
          width: '100%',
          maxWidth: 400,
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <FacebookOutlined
            style={{
              fontSize: 48,
              color: '#1877f2',
              marginBottom: 16,
            }}
          />
          <Title level={2} style={{ margin: 0, color: '#333' }}>
            Meta Ads Enterprise
          </Title>
          <Text type="secondary">
            {isRegister ? 'Criar nova conta' : 'Faça login para continuar'}
          </Text>
        </div>

        <Form
          name="auth"
          onFinish={handleSubmit}
          layout="vertical"
          size="large"
        >
          <Form.Item
            name="email"
            label="Email"
            rules={[
              { required: true, message: 'Por favor, insira seu email!' },
              { type: 'email', message: 'Email inválido!' },
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="seu@email.com"
            />
          </Form.Item>

          {isRegister && (
            <Form.Item
              name="full_name"
              label="Nome Completo"
              rules={[
                { required: true, message: 'Por favor, insira seu nome!' },
              ]}
            >
              <Input placeholder="Seu nome completo" />
            </Form.Item>
          )}

          <Form.Item
            name="password"
            label="Senha"
            rules={[
              { required: true, message: 'Por favor, insira sua senha!' },
              { min: 8, message: 'Senha deve ter pelo menos 8 caracteres!' },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Sua senha"
            />
          </Form.Item>

          {isRegister && (
            <Form.Item
              name="confirmPassword"
              label="Confirmar Senha"
              dependencies={['password']}
              rules={[
                { required: true, message: 'Por favor, confirme sua senha!' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue('password') === value) {
                      return Promise.resolve();
                    }
                    return Promise.reject(new Error('As senhas não coincidem!'));
                  },
                }),
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="Confirme sua senha"
              />
            </Form.Item>
          )}

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              style={{
                width: '100%',
                height: 48,
                fontSize: 16,
                fontWeight: 500,
              }}
            >
              {isRegister ? 'Criar Conta' : 'Entrar'}
            </Button>
          </Form.Item>
        </Form>

        <Divider />

        <div style={{ textAlign: 'center' }}>
          <Text type="secondary">
            {isRegister ? 'Já tem uma conta?' : 'Não tem uma conta?'}
          </Text>
          <Button
            type="link"
            onClick={() => setIsRegister(!isRegister)}
            style={{ padding: '0 8px' }}
          >
            {isRegister ? 'Fazer Login' : 'Criar Conta'}
          </Button>
        </div>

        {!isRegister && (
          <div style={{ marginTop: 16, textAlign: 'center' }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              Conta de demonstração:
              <br />
              Email: admin@metaads.com
              <br />
              Senha: admin123
            </Text>
          </div>
        )}
      </Card>
    </div>
  );
};

export default Login;
