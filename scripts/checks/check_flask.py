from app import app

if __name__ == '__main__':
    print("Démarrage du serveur Flask de test...")
    print("URL: http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
