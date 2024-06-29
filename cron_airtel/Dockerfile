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
EXPOSE 2906
ENV HOST=0.0.0.0
ENV PORT=2906

# Commande pour démarrer l'application
CMD ["python", "search_update.py"]