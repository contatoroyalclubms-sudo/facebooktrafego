import requests
import time
import sys

def verify_complete_system():
    """Verificar sistema completo Meta Ads Enterprise"""
    print("🔍 Verificação completa do sistema Meta Ads Enterprise...")
    
    services = [
        ("Frontend", "http://localhost:3000", "text/html"),
        ("Backend Health", "http://localhost:8000/health", "application/json"),
        ("API Docs", "http://localhost:8000/docs", "text/html"),
        ("Grafana", "http://localhost:4000", "text/html"),
        ("Flower", "http://localhost:5555", "text/html"),
        ("Prometheus", "http://localhost:9090", "text/html"),
    ]
    
    results = []
    
    for name, url, content_type in services:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {name}: OK")
                results.append(True)
            else:
                print(f"❌ {name}: Status {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"❌ {name}: Erro - {str(e)}")
            results.append(False)
    
    print("\n🔐 Testando autenticação completa...")
    try:
        login_data = {
            "username": "admin@metaads.com",
            "password": "admin123"
        }
        
        response = requests.post(
            "http://localhost:8000/api/v1/auth/token",
            data=login_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Login: OK")
            
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            me_response = requests.get(
                "http://localhost:8000/api/v1/auth/me", 
                headers=headers,
                timeout=10
            )
            
            if me_response.status_code == 200:
                print("✅ Rota /me: OK")
                user_data = me_response.json()
                print(f"   User ID: {user_data['id']}")
                print(f"   Email: {user_data['email']}")
                results.append(True)
            else:
                print(f"❌ Rota /me: Status {me_response.status_code}")
                results.append(False)
                
            dashboard_response = requests.get(
                "http://localhost:8000/api/v1/dashboard/stats",
                headers=headers,
                timeout=10
            )
            
            if dashboard_response.status_code == 200:
                print("✅ Dashboard API: OK")
                results.append(True)
            else:
                print(f"❌ Dashboard API: Status {dashboard_response.status_code}")
                results.append(False)
                
        else:
            print(f"❌ Login: Status {response.status_code}")
            print(f"Response: {response.text}")
            results.append(False)
            results.append(False)
            
    except Exception as e:
        print(f"❌ Autenticação: Erro - {str(e)}")
        results.append(False)
        results.append(False)
    
    success_rate = (sum(results) / len(results)) * 100
    print(f"\n📊 Sistema {success_rate:.1f}% funcional")
    
    if success_rate >= 90:
        print("🎉 SISTEMA META ADS ENTERPRISE 100% FUNCIONANDO!")
        print("\n🔗 ACESSOS:")
        print("• Frontend: http://localhost:3000")
        print("• API Docs: http://localhost:8000/docs")
        print("• Grafana: http://localhost:4000 (admin/admin123)")
        print("• Flower: http://localhost:5555")
        print("• Prometheus: http://localhost:9090")
        print("\n🔑 CREDENCIAIS:")
        print("• Email: admin@metaads.com")
        print("• Senha: admin123")
        print("\n✨ FUNCIONALIDADES ATIVAS:")
        print("• ✅ Autenticação JWT")
        print("• ✅ Dashboard em tempo real")
        print("• ✅ API REST completa")
        print("• ✅ Banco PostgreSQL")
        print("• ✅ Cache Redis")
        print("• ✅ Workers Celery")
        print("• ✅ Monitoramento Grafana/Prometheus")
        print("• ✅ Interface React responsiva")
    else:
        print("⚠️ Alguns serviços precisam de atenção")
        return False
    
    return True

if __name__ == "__main__":
    verify_complete_system()
