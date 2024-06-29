FROM python:3.10.6

# Définir le répertoire de travail dans le conteneur
RUN pip install --no-cache-dir --upgrade pip
WORKDIR /app

# Copier le fichier requirements.txt dans le conteneur
COPY cron_airtel/requirements.txt .

# Installer les dépendances du projet
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le contenu de l'application
COPY cron_airtel/ .

# Exposer le port utilisé par l'application (ici, le port 2800)
EXPOSE 2802

# Commande pour démarrer l'application
CMD ["uvicorn", "support:app", "--host", "0.0.0.0", "--port", "2802"]