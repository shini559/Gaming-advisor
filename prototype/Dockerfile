# Étape 1 : Utiliser une image de base Python
FROM python:3.10-slim

# Étape 2 : Définir le répertoire de travail
WORKDIR /app

# Étape 3 : Copier le fichier des dépendances et les installer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Étape 4 : Copier TOUT le reste du code de l'application
COPY . .

# Étape 5 : Exposer le port par défaut de Streamlit
EXPOSE 8501

# Étape 6 : Définir la commande de démarrage pour une application Streamlit
CMD ["streamlit", "run", "main.py"]