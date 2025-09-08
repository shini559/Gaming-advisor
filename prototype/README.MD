# 🎲 GameAdvisor - Assistant IA pour Jeux de Société

## 🎯 Vue d'ensemble

**GameAdvisor** est un assistant intelligent spécialisé dans l'aide aux joueurs de jeux de société. L'application permet d'analyser les règles de jeux, répondre aux questions sur les mécaniques de jeu, aider à la mise en place et au calcul des scores.

*"Il se tape les règles, vous vous tapez des barres"*

## 🏗️ Architecture Technique

### Stack Technologique
- **Backend** : Python 3.10+
- **Interface** : Streamlit avec thème personnalisé
- **IA** : Azure OpenAI (GPT-4o) via LangChain
- **Base de données vectorielle** : ChromaDB
- **Traitement d'images** : PyMuPDF, Pillow
- **Containerisation** : Docker

### Structure du Projet
```
prototype/
├── classes/                    # Architecture modulaire
│   ├── agent_manager.py       # Gestionnaire agent principal
│   ├── hybrid_rag_manager.py  # RAG hybride (métadonnées + images)
│   ├── rag_manager.py         # RAG classique (texte uniquement)
│   ├── rag_factory.py         # Factory pattern pour RAG
│   ├── interface_manager.py   # Interface Streamlit
│   ├── message_manager.py     # Traitement messages/fichiers
│   ├── image_store_manager.py # Stockage local d'images
│   ├── audio_manager.py       # Gestion audio (expérimental)
│   └── settings.py           # Configuration centralisée
├── stored_images/             # Images de règles par jeu
│   ├── uno/                  # Règles UNO
│   ├── zombicide/            # Règles Zombicide
│   ├── fort/                 # Règles Fort
│   └── default/              # Jeux divers
├── chroma_db/                # Base vectorielle persistante
├── tests/                    # Tests unitaires
├── main.py                   # Point d'entrée
├── requirements.txt          # Dépendances Python
└── Dockerfile               # Configuration conteneur
```

## 🚀 Fonctionnalités Principales

### 1. **Assistant IA Conversationnel**
- Chat interactif avec historique persistant
- Réponses contextualisées basées sur les règles téléchargées
- Support multimodal (texte + images)

### 2. **Analyse Intelligente des Règles**
- **Upload** : PDF et images (PNG, JPG, JPEG)
- **Extraction** : Texte, diagrammes, composants de jeu
- **Classification** : Setup, gameplay, scoring, fin de partie

### 3. **Système RAG Avancé (3 Modes)**

#### **Mode Classique** 🔤
- Extraction complète du texte des documents
- Vectorisation avec embeddings Azure OpenAI
- Recherche sémantique dans ChromaDB
- Idéal pour : règles textuelles denses

#### **Mode Hybride** 🖼️
- Extraction de métadonnées structurées
- Stockage local des images + métadonnées vectorisées
- Combinaison contexte textuel + images directes à l'IA
- Idéal pour : règles avec schémas/diagrammes

#### **Mode Direct** ⚡
- Envoi direct des images au modèle vision
- Aucune vectorisation préalable
- Analyse en temps réel
- Idéal pour : questions ponctuelles

### 4. **Gestion Multi-Jeux**
- Organisation par nom de jeu
- Stockage séparé des règles
- Bases vectorielles dédiées par jeu

### 5. **Interface Utilisateur Avancée**
- Design personnalisé (thème GameAdvisor)
- Upload par glisser-déposer
- Mode debug avec logs détaillés
- Sélecteur de méthode RAG
- Boutons de gestion (reset, clear stores)

## ⚙️ Configuration

### Variables d'Environnement
```env
SUBSCRIPTION_KEY=your-azure-subscription-key
```

### Modèles Azure OpenAI Configurés
```python
# Agent principal (réponses finales)
agent-gpt-4o

# RAG Classique
rag_vision-gpt-4o          # Extraction texte
rag_embedding-text-embedding-3-large  # Vectorisation

# RAG Hybride  
hybrid_vision-gpt-4o       # Extraction métadonnées
hybrid_embedding-text-embedding-3-large  # Vectorisation métadonnées
```

## 🔧 Installation et Démarrage

### Installation Locale
```bash
# Cloner le repository
git clone [repository-url]
cd Gaming-advisor/prototype

# Créer environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou .venv\Scripts\activate  # Windows

# Installer dépendances
pip install -r requirements.txt

# Configurer variables d'environnement
cp .env.example .env
# Éditer .env avec vos clés API

# Lancer l'application
streamlit run main.py
```

### Démarrage Docker
```bash
# Construire l'image
docker build -t gameadvisor .

# Lancer le conteneur
docker run -p 8501:8501 --env-file .env gameadvisor
```

## 📱 Utilisation

### 1. **Préparer les Règles**
1. Sélectionner un nom de jeu dans la sidebar
2. Choisir la méthode RAG appropriée
3. Uploader les fichiers PDF/images des règles
4. Cliquer sur "Vectoriser les documents" (modes Classique/Hybride)

### 2. **Poser des Questions**
- Questions générales : *"Comment commence une partie ?"*
- Clarifications : *"Que faire en cas d'égalité ?"*
- Calculs : *"Comment calculer les points ?"*
- Images dans questions : Upload direct via chat

### 3. **Gestion**
- **Reset conversation** : Vider l'historique
- **Clear stores** : Supprimer données vectorisées
- **Mode debug** : Afficher logs détaillés

## 🧠 Intelligence Artificielle

### Prompts Système Spécialisés
- **Agent Principal** : Maître de jeu et assistant règles
- **RAG Vision Classique** : Extraction complète texte + schémas
- **RAG Vision Hybride** : Métadonnées structurées pour recherche

### Optimisations
- **Gestion mémoire** : Historique limité (20 messages)
- **Token management** : Exclusion images de l'historique
- **Cache intelligent** : Réutilisation contextes RAG
- **Multimodal efficace** : Images base64 optimisées

## 🔍 Architecture des Classes

### Patterns Utilisés
- **Singleton** : Settings, AgentManager (instance unique)
- **Factory** : RAGFactory (création dynamique RAG)
- **Adapter** : RAG adapters (interface commune)
- **Observer** : Log capture (mode debug)

### Classes Principales
- `AgentManager` : Orchestrateur IA principal
- `RAGFactory` : Factory pour gestionnaires RAG
- `InterfaceManager` : Gestionnaire interface Streamlit
- `MessageManager` : Traitement fichiers multimodaux
- `ImageStoreManager` : Stockage local optimisé

## 🧪 Tests

```bash
# Lancer tests unitaires
pytest tests/

# Tests spécifiques
pytest tests/test_message_manager.py -v
```

## 🎮 Jeux Supportés

Le système est conçu pour fonctionner avec tous types de jeux de société :
- **Jeux à règles complexes** : Zombicide, Gloomhaven
- **Jeux familiaux** : UNO, Monopoly  
- **Jeux de stratégie** : Catan, 7 Wonders
- **Jeux de cartes** : Magic, Pokémon

### Exemples Intégrés
- **UNO** : Règles + variantes
- **Zombicide** : Livret complet
- **Fort** : Mécaniques deck-building

## 🚀 Développement Futur

### Fonctionnalités Prévues
- [ ] Support audio (questions vocales)
- [ ] Détection automatique du jeu
- [ ] API REST pour intégrations externes  
- [ ] Mode multi-joueurs (session partagée)
- [ ] Export des règles résumées
- [ ] Statistiques d'utilisation

### Améliorations Techniques
- [ ] Cache Redis pour performances
- [ ] Support bases vectorielles cloud
- [ ] Pipeline CI/CD automatisé
- [ ] Monitoring et analytics
- [ ] Tests d'intégration complets

## 📊 Métriques et Performance

### Capacités Actuelles
- **Documents** : Support PDF multi-pages + images
- **Taille** : Jusqu'à 10MB par fichier
- **Formats** : PNG, JPG, JPEG, PDF
- **Langues** : Français (priorité), support multilingue
- **Temps de réponse** : ~2-5 secondes selon complexité

### Optimisations
- Redimensionnement automatique des images
- Compression intelligente base64
- Chunking adaptatif pour gros documents
- Cache embeddings pour réutilisation

## 🤝 Contribution

### Setup Développement
1. Fork du repository
2. Créer une branche feature
3. Implémenter + tests
4. Pull Request avec description détaillée

### Standards Code
- **Python** : PEP 8, type hints
- **Tests** : Coverage >80%
- **Documentation** : Docstrings obligatoires
- **Git** : Messages commits conventionnels

## 📄 Licence

Projet développé dans le cadre d'une formation. Tous droits réservés.

---

*Développé avec ❤️ pour simplifier vos soirées jeux*

**Version** : 1.0.0-prototype  
**Dernière mise à jour** : Septembre 2024