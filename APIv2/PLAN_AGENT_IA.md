# Plan d'implémentation - Agent IA avec RAG

## Vision
Créer un agent IA conversationnel spécialisé dans les règles de jeux de société, utilisant RAG avec recherche vectorielle et capacités visuelles.

## Architecture générale
```
[Question utilisateur] 
    ↓
[Recherche vectorielle filtrée par game_id]
    ↓  
[Récupération images associées + optimisation contexte]
    ↓
[Génération réponse GPT-4 Vision avec contexte multimodal]
    ↓
[Post-traitement + formatage réponse avec sources]
```

## TODO List détaillée

### Phase 1 : Fondations données ✅ [EN COURS]
- [ ] Créer entité `ChatConversation`
  - id, game_id, user_id, title, created_at, updated_at
- [ ] Créer entité `ChatMessage` 
  - id, conversation_id, role (user/assistant), content, sources, created_at
- [ ] Créer entité `ChatFeedback`
  - id, message_id, rating (boolean), created_at
- [ ] Créer modèles SQLAlchemy correspondants
- [ ] Migration base de données
- [ ] Repository interfaces et implémentations
- [ ] Tests unitaires des entités

### Phase 2 : Configuration système
- [ ] Ajouter config vectorielle dans config.py :
  - vector_search_top_k: int = 3
  - vector_similarity_threshold: float = 0.7
  - agent_max_context_length: int = 8000
- [ ] Ajouter variables environnement si nécessaire

### Phase 3 : Service de recherche vectorielle
- [ ] Interface `IVectorSearchService`
- [ ] Classe `VectorSearchResult` (vector, image_info, similarity_score)
- [ ] Implémentation `VectorSearchService`
  - Recherche par similarité cosine sur game_id spécifique
  - Filtrage par seuil de similarité
  - Récupération métadonnées images associées
- [ ] Tests du service de recherche

### Phase 4 : Service Agent IA
- [ ] Interface `IGameRulesAgent` 
- [ ] Classe `AgentResponse` (text, sources, confidence)
- [ ] Implémentation `GameRulesAgent`
  - Construction contexte multimodal (texte + images)
  - Prompting spécialisé jeux de société
  - Appel GPT-4 Vision avec contraintes domaine
  - Extraction et formatage sources
- [ ] Gestion des échecs et fallbacks
- [ ] Tests du service agent

### Phase 5 : Use Cases
- [ ] `CreateConversationUseCase`
- [ ] `SendMessageUseCase` (core : question → agent → réponse)
- [ ] `GetConversationHistoryUseCase`
- [ ] `AddMessageFeedbackUseCase`
- [ ] Tests des use cases

### Phase 6 : API Endpoints
- [ ] `POST /games/{game_id}/conversations` - Créer conversation
- [ ] `POST /conversations/{conv_id}/messages` - Poser question  
- [ ] `GET /conversations/{conv_id}/messages` - Historique
- [ ] `GET /conversations/my` - Mes conversations
- [ ] `POST /messages/{msg_id}/feedback` - Évaluer réponse
- [ ] Schémas Pydantic pour requests/responses
- [ ] Documentation OpenAPI

### Phase 7 : Optimisations & monitoring
- [ ] Métriques performance (temps réponse, coûts API)
- [ ] Cache intelligent pour requêtes similaires
- [ ] Limitation rate limiting par utilisateur
- [ ] Logging détaillé pour debugging
- [ ] Monitoring qualité réponses via feedback

## Questions en suspens
1. Titre conversation : auto-généré ou saisi utilisateur ?
2. Format sources : "page 5" ou snippet texte ?
3. Feedback : juste boolean ou commentaire libre ?
4. Limite messages par conversation ?

## Décisions techniques
- ✅ Conversations avec historique (pas de sessions persistantes pour v1)
- ✅ Top-k et seuil configurable
- ✅ Pondération équitable OCR/descriptions pour v1
- ✅ Agent refuse questions hors-domaine
- ✅ Sources mentionnées dans réponse
- ✅ Feedback utilisateur simple (satisfait/non satisfait)