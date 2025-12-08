# Introduction à la CI/CD avec GitHub Actions

Ce cours a pour but de vous introduire aux concepts de l'Intégration Continue (CI) et du Déploiement Continu (CD), en mettant l'accent sur l'outil **GitHub Actions**.

## 1. Concepts Fondamentaux : CI/CD

### Qu'est-ce que la CI (Continuous Integration) ?
L'intégration continue est une pratique de développement logiciel où les développeurs fusionnent leurs modifications de code dans un dépôt central de manière fréquente (plusieurs fois par jour).
- **But** : Détecter les erreurs d'intégration le plus tôt possible.
- **Moyens** : Builds automatisés et exécutions de tests à chaque push.

### Qu'est-ce que la CD (Continuous Delivery / Deployment) ?
La CD étend la CI en automatisant la livraison des modifications de code après la phase de build.
- **Continuous Delivery** : Le code est prêt à être déployé à tout moment, mais le déploiement final en production nécessite une action humaine.
- **Continuous Deployment** : Chaque modification qui passe les tests est automatiquement déployée en production sans intervention humaine.

### Pourquoi utiliser la CI/CD ?
- **Réduction des risques** : Les bugs sont détectés plus tôt.
- **Rapidité** : Accélération du cycle de release.
- **Qualité** : Tests automatisés constants.
- **Satisfaction** : Les développeurs passent moins de temps sur des tâches manuelles répétitives.

---

## 2. Découverte de GitHub Actions

GitHub Actions est la plateforme d'automatisation native de GitHub. Elle permet de créer des workflows personnalisés directement dans votre dépôt GitHub.

### Concepts Clés

1.  **Workflow (Flux de travail)** :
    - Un processus automatisé configurable composé d'un ou plusieurs jobs.
    - Défini dans un fichier YAML dans le dossier `.github/workflows/`.

2.  **Event (Événement)** :
    - Ce qui déclenche le workflow (ex: `push`, `pull_request`, `schedule` (cron)).

3.  **Job (Tâche)** :
    - Un ensemble d'étapes (steps) qui s'exécutent sur le même runner.
    - Par défaut, les jobs s'exécutent en parallèle, mais on peut définir des dépendances.

4.  **Step (Étape)** :
    - Une action individuelle dans un job. Cela peut être une commande shell (`run`) ou l'utilisation d'une Action pré-packagée (`uses`).

5.  **Action** :
    - Une application personnalisée pour la plateforme GitHub Actions qui effectue une tâche complexe mais fréquente (ex: `actions/checkout` pour récupérer le code).

6.  **Runner** :
    - Le serveur qui exécute le workflow. GitHub fournit des runners hébergés (Ubuntu, Windows, macOS), ou vous pouvez héberger les vôtres (Self-hosted).

---

## 3. Structure d'un fichier Workflow YAML

Les fichiers workflow se placent obligatoirement dans `.github/workflows/nom-du-fichier.yml`.

### Exemple : "Hello World"

```yaml
name: Mon Premier Workflow

# Déclencheur : Sur un push vers la branche main
on:
  push:
    branches:
      - main

jobs:
  dire-bonjour:
    runs-on: ubuntu-latest # Environnement d'exécution
    steps:
      - name: Checkout du code
        uses: actions/checkout@v4 # Action officielle pour cloner le repo

      - name: Afficher un message
        run: echo "Bonjour, ceci est mon premier workflow CI/CD !"
```

---

## 4. Cas Pratique : CI pour un projet Python

Imaginons un projet Python simple. Nous voulons :
1. Installer les dépendances.
2. Analyser le code (Linting) avec `flake8`.
3. Lancer les tests avec `pytest`.

Créez un fichier `.github/workflows/ci-python.yml` :

```yaml
name: Python CI

on: [push, pull_request]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    
    steps:
    - name: Récupération du code
      uses: actions/checkout@v4
      
    - name: Configurer Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'
        
    - name: Installer les dépendances
      run: |
        python -m pip install --upgrade pip
        pip install flake8 pytest
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
        
    - name: Lint avec flake8
      run: |
        # arrêter le build s'il y a des erreurs de syntaxe Python ou des noms indéfinis
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        # exit-zero traite toutes les erreurs comme des avertissements
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
        
    - name: Lancer les tests
      run: |
        pytest
```

---

## 5. Gestion des Secrets

Ne mettez **jamais** de mots de passe ou de clés API en clair dans votre code ou vos fichiers YAML. Utilisez les **GitHub Secrets**.

1. Allez dans `Settings` > `Secrets and variables` > `Actions` de votre dépôt.
2. Créez un secret, par exemple `API_KEY`.
3. Utilisez-le dans votre workflow :

```yaml
    - name: Utiliser une clé API
      env:
        MA_CLE: ${{ secrets.API_KEY }}
      run: echo "Je peux utiliser ma clé secrète ici de manière sécurisée."
```

---

## 6. Conclusion

GitHub Actions est un outil puissant et flexible.
- Il est gratuit pour les dépôts publics.
- Il s'intègre parfaitement à l'écosystème GitHub.
- Il existe une Marketplace immense d'Actions prêtes à l'emploi.

Pour aller plus loin : explorez les matrices de build, le déploiement vers le cloud (AWS, Azure, GCP), ou la création de vos propres Actions customisées.
