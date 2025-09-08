# Gaming Advisor - Assistant IA pour Jeux de Société

## 🎯 Vue d'ensemble

**Gaming Advisor** est une application web moderne qui révolutionne l'expérience des jeux de société grâce à l'intelligence artificielle. Cette plateforme permet aux joueurs de discuter en temps réel avec une IA spécialisée pour obtenir des explications de règles, des conseils de stratégie et un accompagnement personnalisé pour leurs jeux préférés.

## ✨ Fonctionnalités Principales

### 🔐 Gestion des Utilisateurs
- **Inscription et connexion** sécurisées avec authentification JWT
- **Gestion de profil** utilisateur (nom, prénom, email, nom d'utilisateur)
- **Système de tokens** avec rafraîchissement automatique
- **Sessions persistantes** via localStorage

### 🎲 Gestion des Jeux
- **Création de jeux** personnalisés avec métadonnées (titre, description, éditeur)
- **Upload d'images** de jeux pour une meilleure identification
- **Catalogue de jeux** avec distinction entre jeux publics et privés
- **Organisation par utilisateur** avec gestion de la propriété

### 💬 Chat Intelligent avec IA
- **Conversations contextuelles** par jeu spécifique
- **Interface de chat moderne** avec messages en temps réel
- **Historique complet** des conversations sauvegardé
- **Système de feedback** (pouce haut/bas) pour améliorer les réponses de l'IA
- **Indicateur de frappe** de l'IA pour une expérience fluide

### 🎨 Expérience Utilisateur
- **Interface responsive** adaptée à tous les écrans
- **Thème sombre moderne** pour une expérience visuelle agréable
- **Navigation intuitive** entre les jeux et conversations
- **Design system cohérent** avec TailwindCSS

## 🏗️ Architecture Technique

### Frontend (Next.js 15)
- **Framework** : Next.js 15.4.7 avec App Router
- **Language** : TypeScript 5 pour la sécurité des types
- **UI Framework** : React 19 avec hooks modernes
- **Styling** : TailwindCSS 4.0 pour un design system consistant
- **Icons** : Heroicons React pour l'iconographie

### Backend API
- **Endpoint principal** : `https://gameadvisor-api-containerapp.purpleplant-bc5dabd4.francecentral.azurecontainerapps.io`
- **Architecture REST** avec authentification JWT
- **Hébergement** : Microsoft Azure Container Apps

### Infrastructure
- **Containerisation** : Docker avec multi-stage builds
- **Orchestration** : Docker Compose pour le développement
- **Mode standalone** : Build optimisé pour la production
- **Health checks** intégrés pour la surveillance

## 📁 Structure du Projet

```
gaming-advisor/
├── src/
│   ├── app/                          # App Router de Next.js
│   │   ├── account/                  # Gestion du profil utilisateur
│   │   ├── chat/
│   │   │   └── [conversationId]/     # Interface de chat dynamique
│   │   ├── games/
│   │   │   ├── create/               # Création de nouveaux jeux
│   │   │   ├── [gameId]/
│   │   │   │   └── conversations/    # Liste des conversations par jeu
│   │   │   └── page.tsx              # Catalogue des jeux
│   │   ├── login/                    # Authentification
│   │   ├── signup/                   # Inscription
│   │   ├── legal/                    # Mentions légales
│   │   ├── privacy/                  # Politique de confidentialité
│   │   ├── terms/                    # Conditions d'utilisation
│   │   ├── layout.tsx                # Layout global
│   │   ├── page.tsx                  # Page d'accueil
│   │   ├── globals.css               # Styles globaux
│   │   └── not-found.tsx             # Page 404
│   └── utils/
│       └── api.ts                    # Utilitaires API avec gestion auth
├── public/                           # Assets statiques
├── Dockerfile                        # Configuration Docker
├── docker-compose.yml               # Orchestration locale
├── next.config.ts                   # Configuration Next.js
├── tsconfig.json                    # Configuration TypeScript
├── tailwind.config.ts               # Configuration TailwindCSS
├── package.json                     # Dependencies et scripts
└── README.md                        # Documentation
```

## 🛠️ Technologies Utilisées

### Core Stack
- **Next.js 15.4.7** - Framework React full-stack
- **React 19.1.0** - Library UI moderne
- **TypeScript 5** - Typage statique pour la robustesse

### Styling & UI
- **TailwindCSS 4.0** - Framework CSS utilitaire
- **PostCSS** - Processeur CSS avancé
- **Heroicons** - Bibliothèque d'icônes React
- **Geist Font** - Police moderne de Vercel

### Développement & Outils
- **ESLint 9** - Linting JavaScript/TypeScript
- **Turbopack** - Bundler ultra-rapide pour le développement
- **Docker** - Containerisation et déploiement

## 🚀 Guide de Développement

### Prérequis
```bash
- Node.js 18+ 
- npm, yarn, ou pnpm
- Docker (optionnel)
```

### Installation
```bash
# Cloner le repository
git clone <repository-url>
cd gaming-advisor

# Installer les dépendances
npm install
# ou
yarn install
# ou
pnpm install
```

### Développement
```bash
# Lancer le serveur de développement avec Turbopack
npm run dev
# ou
yarn dev
# ou
pnpm dev
```

L'application sera accessible sur [http://localhost:3000](http://localhost:3000)

### Build Production
```bash
# Build de production
npm run build
npm start

# Avec Docker
docker build -t gaming-advisor .
docker run -p 3000:3000 gaming-advisor

# Avec Docker Compose
docker-compose up -d
```

## 🔌 API et Services

### Endpoints Principaux
- **Authentification** : `/auth/login`, `/auth/register`, `/auth/refresh`, `/auth/me`
- **Jeux** : `/games`, `/games/create`
- **Chat** : `/chat/conversations`, `/chat/messages`, `/chat/games/{gameId}/conversations`
- **Feedback** : `/chat/messages/{messageId}/feedback`

### Gestion de l'Authentification
Le projet utilise un système d'authentification JWT robuste avec :
- **Access tokens** courte durée pour la sécurité
- **Refresh tokens** pour le renouvellement automatique
- **Retry automatique** des requêtes en cas d'expiration
- **Redirection intelligente** vers la page de connexion

### Upload de Fichiers
- **Support des images** pour les avatars de jeux
- **Limite de 10MB** par upload
- **Validation côté client** pour les formats acceptés

## 🎨 Design System

### Palette de Couleurs
- **Background principal** : `gray-900` (#111827)
- **Surface secondaire** : `gray-800` (#1f2937)
- **Surface tertiaire** : `gray-700` (#374151)
- **Accent principal** : `indigo-600` (#4f46e5)
- **Accent secondaire** : `teal-600` (#0d9488)
- **Danger** : `red-600` (#dc2626)

### Typographie
- **Font principale** : Geist Sans (variable)
- **Font monospace** : Geist Mono (variable)
- **Échelle typographique** : De text-sm à text-6xl

### Composants UI
- **Formulaires** : Champs avec états focus et validation
- **Boutons** : États hover, active et disabled
- **Cards** : Bordures subtiles et effets de survol
- **Layout responsive** : Mobile-first avec breakpoints MD/LG

## 🔒 Sécurité et Conformité

### Mesures de Sécurité
- **Tokens JWT** avec expiration courte
- **Refresh tokens** sécurisés
- **Validation côté client** et serveur
- **Headers de sécurité** appropriés
- **Sanitisation** des données utilisateur

### Conformité RGPD
- **Pages légales** complètes (mentions légales, confidentialité, CGU)
- **Contact** : contact@gamingadvisor.fr
- **Hébergement** : Microsoft Azure (conformité européenne)

## 🔄 États et Flux Utilisateur

### Flux d'Authentification
1. **Visiteur** → Page d'accueil avec présentation
2. **Inscription** → Validation → Connexion automatique
3. **Connexion** → Récupération des tokens → Redirection vers /games
4. **Authentifié** → Accès complet aux fonctionnalités

### Flux de Jeu et Chat
1. **Sélection/Création** de jeu → Liste des conversations
2. **Création de conversation** → Interface de chat
3. **Chat avec IA** → Feedback → Sauvegarde automatique
4. **Historique** persistant pour chaque conversation

## 📱 Responsive Design

### Breakpoints TailwindCSS
- **Mobile** : < 640px (par défaut)
- **Tablet** : sm: 640px+
- **Desktop** : md: 768px+, lg: 1024px+
- **Wide** : xl: 1280px+

### Adaptations
- **Navigation** : Header responsive avec menu mobile
- **Grilles** : `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`
- **Formulaires** : Layout en colonne sur mobile, grille sur desktop
- **Chat** : Interface optimisée pour mobile et desktop

## 🏥 Monitoring et Health Checks

### Docker Health Check
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:3000"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### Gestion d'Erreurs
- **Retry automatique** pour les erreurs réseau
- **Fallback UI** pour les états d'erreur
- **Messages utilisateur** explicites et utiles
- **Logging** côté client pour le debugging

## 🔮 Évolutions Futures

### Fonctionnalités Prévues
- **Notifications temps réel** avec WebSocket
- **Système de recommandations** IA-powered
- **Communauté** avec partage de stratégies
- **Multi-langues** pour l'internationalisation
- **Mode hors-ligne** avec synchronisation

### Améliorations Techniques
- **Cache intelligent** avec React Query
- **Progressive Web App** (PWA)
- **Tests end-to-end** avec Playwright
- **CI/CD pipeline** automatisé
- **Monitoring avancé** avec métriques

## 📞 Support et Contact

- **Email** : contact@gamingadvisor.fr
- **Documentation** : Voir ce README et les commentaires dans le code
- **Issues** : Utiliser le système de tickets du repository

---

**Gaming Advisor** - Transformez votre expérience de jeu de société grâce à l'IA 🎲✨