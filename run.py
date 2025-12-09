from app import create_app

# Alege config_name corespunzator (ex: "development", "production")
app = create_app(config_name="development")

if __name__ == "__main__":
    # Configureaza debug / host / port dupa nevoie
    app.run(debug=True, host='0.0.0.0', port=5000)
