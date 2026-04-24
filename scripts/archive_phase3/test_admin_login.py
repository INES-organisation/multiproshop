import requests
from requests.sessions import Session

def test_admin_login():
    print("=== TEST CONNEXION ADMIN ===")
    
    # Créer une session pour maintenir les cookies
    session = Session()
    base_url = "http://multiproshop.local"
    
    # 1. Accéder à la page de connexion admin
    print("1. Accès à la page de connexion admin...")
    login_page = session.get(f"{base_url}/auth/admin-login")
    print(f"   Status: {login_page.status_code}")
    
    if login_page.status_code != 200:
        print("❌ Erreur: Page de connexion inaccessible")
        return
    
    # 2. Tenter la connexion
    print("2. Tentative de connexion avec admin/admin123...")
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    login_response = session.post(f"{base_url}/auth/admin-login", data=login_data, allow_redirects=False)
    print(f"   Status: {login_response.status_code}")
    print(f"   Headers: {dict(login_response.headers)}")
    
    # 3. Vérifier la redirection
    if login_response.status_code == 302:
        redirect_url = login_response.headers.get('Location', '')
        print(f"   Redirection vers: {redirect_url}")
        
        if '/admin/' in redirect_url or 'admin.dashboard' in redirect_url:
            print("✅ Connexion réussie - redirection vers admin")
            
            # 4. Suivre la redirection
            print("3. Accès au dashboard admin...")
            dashboard_response = session.get(f"{base_url}/admin/")
            print(f"   Status dashboard: {dashboard_response.status_code}")
            
            if dashboard_response.status_code == 200:
                print("✅ Dashboard admin accessible!")
                if "Tableau de bord Administrateur" in dashboard_response.text:
                    print("✅ Contenu du dashboard correct!")
                else:
                    print("⚠️ Contenu du dashboard inattendu")
            else:
                print(f"❌ Dashboard inaccessible: {dashboard_response.status_code}")
                
        else:
            print(f"❌ Redirection incorrecte: {redirect_url}")
    else:
        print(f"❌ Connexion échouée: {login_response.status_code}")
        if login_response.text:
            print(f"   Contenu: {login_response.text[:200]}...")

if __name__ == '__main__':
    test_admin_login()
