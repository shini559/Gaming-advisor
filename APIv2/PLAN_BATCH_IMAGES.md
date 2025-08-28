# Plan d'Implémentation - Système de Batch d'Images

## Spécifications Validées

### Comportement de traitement :
- ✅ **Parallélisme** : Traitement en parallèle des images du batch
- ✅ **Gestion d'erreurs** : Marquer image échouée, continuer le batch, retry des échecs
- ✅ **Retry système** : Maximum X retries défini dans config.py
- ✅ **Pas de limite** : Nombre illimité d'images par batch
- ✅ **Stockage** : Images dans dossier du jeu concerné

## Architecture - Plan d'Implémentation

### Phase 1 : Domain & Configuration ✅ EN COURS
```
📁 app/config.py
  └── Ajouter batch_max_retries, batch_parallel_limit

📁 app/domain/entities/
  └── image_batch.py          # Entité Batch avec statut et ratios

📁 app/domain/ports/repositories/
  └── image_batch_repository.py  # Interface repository
```

### Phase 2 : Database & Infrastructure 
```
📁 migrations/versions/
  └── create_image_batches_table.py  # Migration

📁 app/data/models/
  └── image_batch.py          # Modèle SQLAlchemy

📁 app/data/repositories/  
  └── image_batch_repository.py  # Implémentation repository
```

### Phase 3 : Use Cases & Business Logic
```
📁 app/domain/use_cases/images/
  ├── create_image_batch.py    # Créer batch + upload multiple images
  ├── get_batch_status.py      # Statut avec ratio "processing 5/30"
  ├── retry_failed_images.py   # Retry des images échouées
  └── process_image_batch.py   # Orchestration traitement batch
```

### Phase 4 : API & Presentation
```
📁 app/presentation/routes/images.py
  └── Nouveaux endpoints batch

📁 app/presentation/schemas/images.py
  └── Schémas batch request/response
```

### Phase 5 : Worker & Queue
```
📁 app/services/image_processing_worker.py
  └── Modifier pour traitement parallèle par batch
  
📁 app/services/redis_queue_service.py  
  └── Support des jobs de type batch
```

## Entités Proposées

### ImageBatch Entity
```python
@dataclass
class ImageBatch:
    id: UUID
    game_id: UUID
    total_images: int
    processed_images: int = 0
    failed_images: int = 0
    status: BatchStatus  # PENDING, PROCESSING, COMPLETED, FAILED, RETRYING
    retry_count: int = 0
    max_retries: int
    created_at: datetime
    processing_started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Business methods:
    @property
    def progress_ratio(self) -> str:
        return f"{self.processed_images}/{self.total_images}"
    
    @property
    def completion_percentage(self) -> float:
        return (self.processed_images / self.total_images) * 100 if self.total_images > 0 else 0.0
        
    @property  
    def failed_ratio(self) -> str:
        return f"{self.failed_images}/{self.total_images}"
        
    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries and self.failed_images > 0
        
    def mark_image_processed(self) -> None:
        self.processed_images += 1
        
    def mark_image_failed(self) -> None:
        self.failed_images += 1
```

### BatchStatus Enum
```python
class BatchStatus(str, Enum):
    PENDING = "pending"      # Créé, pas encore commencé
    PROCESSING = "processing" # En cours de traitement
    COMPLETED = "completed"   # Terminé avec succès (toutes images traitées)
    FAILED = "failed"        # Échec définitif (trop de retries)
    RETRYING = "retrying"    # En cours de retry des images échouées
    PARTIALLY_COMPLETED = "partially_completed"  # Terminé avec quelques échecs
```

### Relation avec GameImage
```python
# Ajouter dans GameImage entity:
batch_id: Optional[UUID] = None  # Référence vers le batch parent
```

## API Endpoints Proposés

```
POST /images/games/{game_id}/batch-upload
  - Body: List[UploadFile] 
  - Response: BatchUploadResponse { batch_id, total_images, status }

GET /images/batches/{batch_id}/status  
  - Response: BatchStatusResponse { 
      status: "processing",
      progress: "5/30 images processed", 
      failed: "2/30 images failed",
      percentage: 16.67,
      can_retry: true
    }

GET /images/batches/{batch_id}/images
  - Response: List des images du batch avec leurs statuts individuels

POST /images/batches/{batch_id}/retry
  - Relance le traitement des images échouées
```

## Configuration à Ajouter
```python
# Dans config.py
batch_max_retries: int = 3
batch_parallel_workers: int = 5  # Nombre d'images traitées en parallèle
batch_retry_delay_minutes: int = 5  # Délai avant retry
```

## Workflow de Traitement

1. **Upload Batch** : Créer batch → Upload toutes les images → Créer jobs de traitement
2. **Processing** : Worker traite N images en parallèle du batch
3. **Gestion échecs** : Images échouées marquées, batch continue
4. **Completion** : Batch terminé → Si échecs et retries disponibles → Auto-retry
5. **Status API** : Temps réel du progresso avec ratios

## Ordre d'Implémentation

1. ✅ **Phase 1** : Configuration + Domain entities
2. **Phase 2** : Database models + migration  
3. **Phase 3** : Use cases + business logic
4. **Phase 4** : API endpoints + schemas
5. **Phase 5** : Worker modification + queue support

---

**Status** : Fini - a tester

Tests à effectuer pour valider la robustesse :

  1. Échecs d'upload Azure Blob

  - Tester avec des permissions invalides
  - Vérifier que les autres images continuent

  2. Échecs de traitement IA

  - Images corrompues ou formats non supportés
  - Vérifier l'incrémentation de failed_images

  3. Échecs Redis

  - Déconnexion Redis pendant la création des jobs
  - Vérifier que les images sont bien sauvées

  4. Échecs de base de données

  - Contrainte violée, connexion perdue
  - Vérifier le rollback complet

  5. Worker en panne

  - Arrêt du worker pendant le traitement
  - Redémarrage et reprise des jobs

  Ces tests permettront de valider que :
  - ✅ Aucun job orphelin n'est créé
  - ✅ Les compteurs de batch sont corrects
  - ✅ Les retry fonctionnent
  - ✅ Les statuts sont cohérents