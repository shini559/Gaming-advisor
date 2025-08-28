from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.models.game_vector import GameVectorModel
from app.domain.entities.game_vector import GameVector
from app.domain.ports.repositories.game_vector_repository import IGameVectorRepository


class GameVectorRepository(IGameVectorRepository):
  def __init__(self, session: AsyncSession):
      self._session = session

  async def create(self, vector: GameVector) -> GameVector:
      """Crée un nouveau vecteur en base"""
      model = GameVectorModel(
          id=vector.id,
          game_id=vector.game_id,
          image_id=vector.image_id,
          
          # Architecture 3-paires
          ocr_content=vector.ocr_content,
          ocr_embedding=vector.ocr_embedding,
          description_content=vector.description_content,
          description_embedding=vector.description_embedding,
          labels_content=vector.labels_content,
          labels_embedding=vector.labels_embedding,
          
          page_number=vector.page_number,
          created_at=vector.created_at
      )

      self._session.add(model)
      await self._session.flush()
      return self._model_to_entity(model)

  async def get_by_id(self, vector_id: UUID) -> Optional[GameVector]:
      """Récupère un vecteur par son ID"""
      stmt = select(GameVectorModel).where(GameVectorModel.id == vector_id)
      result = await self._session.execute(stmt)
      model = result.scalar_one_or_none()
      return self._model_to_entity(model) if model else None

  async def get_by_game_id(self, game_id: UUID) -> List[GameVector]:
      """Récupère tous les vecteurs d'un jeu"""
      stmt = select(GameVectorModel).where(
          GameVectorModel.game_id == game_id
      ).order_by(GameVectorModel.created_at.desc())

      result = await self._session.execute(stmt)
      models = result.scalars().all()
      return [self._model_to_entity(model) for model in models]

  async def get_by_image_id(self, image_id: UUID) -> List[GameVector]:
      """Récupère tous les vecteurs d'une image"""
      stmt = select(GameVectorModel).where(
          GameVectorModel.image_id == image_id
      ).order_by(GameVectorModel.created_at.asc())

      result = await self._session.execute(stmt)
      models = result.scalars().all()
      return [self._model_to_entity(model) for model in models]

  async def search_similar(
      self,
      game_id: UUID,
      query_vector: List[float],
      limit: int = 10
  ) -> List[GameVector]:
      """Recherche de vecteurs similaires pour un jeu donné avec pgvector"""
      # Utilisation de pgvector pour la recherche de similarité cosinus
      stmt = text("""
          SELECT id, game_id, image_id, vector_embedding, extracted_text, page_number, created_at
          FROM game_vectors
          WHERE game_id = :game_id
          ORDER BY vector_embedding <=> :query_vector::vector
          LIMIT :limit
      """)

      result = await self._session.execute(
          stmt,
          {
              "game_id": str(game_id),
              "query_vector": str(query_vector),
              "limit": limit
          }
      )

      vectors = []
      for row in result:
          vectors.append(GameVector(
              id=UUID(row.id),
              game_id=UUID(row.game_id),
              image_id=UUID(row.image_id),
              vector_embedding=row.vector_embedding,
              extracted_text=row.extracted_text,
              page_number=row.page_number,
              created_at=row.created_at
          ))

      return vectors

  async def search_similar_vectors(
      self,
      game_id: UUID,
      query_embedding: List[float],
      limit: int = 10,
      similarity_threshold: float = 0.7
  ) -> List[GameVector]:
      """Recherche de vecteurs similaires avec seuil de similarité"""
      from sqlalchemy import text

      stmt = text("""
          SELECT id, game_id, image_id, vector_embedding, extracted_text, page_number, created_at,
                 1 - (vector_embedding <=> :query_vector) as similarity_score
          FROM game_vectors
          WHERE game_id = :game_id
            AND 1 - (vector_embedding <=> :query_vector) >= :similarity_threshold
          ORDER BY similarity_score DESC
          LIMIT :limit
      """)

      # Convertir l'embedding en format pgvector (string JSON array)
      import json
      query_vector_str = json.dumps(query_embedding)
      
      result = await self._session.execute(
          stmt,
          {
              "game_id": str(game_id),
              "query_vector": query_vector_str,  # Format pgvector : "[0.1,0.2,0.3]"
              "similarity_threshold": similarity_threshold,
              "limit": limit
          }
      )

      vectors = []
      for row in result:
          vectors.append(GameVector(
              id=row.id,  # PostgreSQL retourne déjà un UUID
              game_id=row.game_id,  # PostgreSQL retourne déjà un UUID
              image_id=row.image_id if row.image_id else None,  # PostgreSQL retourne déjà un UUID
              vector_embedding=row.vector_embedding,
              extracted_text=row.extracted_text,
              page_number=row.page_number,
              created_at=row.created_at,
              similarity_score=float(row.similarity_score)  # Score calculé par PostgreSQL
          ))

      return vectors

  async def search_by_vector_type(
      self,
      game_id: UUID,
      query_embedding: List[float],
      search_type: str,  # "ocr" | "description" | "labels"
      limit: int = 10,
      similarity_threshold: float = 0.7
  ) -> List[GameVector]:
      """
      Recherche vectorielle type-safe avec architecture 3-paires
      Utilise l'enum VectorSearchType pour la sélection des colonnes
      """
      from sqlalchemy import text
      from app.domain.entities.vector_search_types import VectorSearchType
      import json
      
      # Validation et conversion du type
      try:
          search_enum = VectorSearchType(search_type)
      except ValueError:
          raise ValueError(f"Type de recherche non supporté: {search_type}")
      
      # Récupération des colonnes via l'enum (type-safe)
      embedding_column = search_enum.get_embedding_column()
      content_column = search_enum.get_content_column()
      not_null_condition = search_enum.get_not_null_condition()
      
      print(f"🔍 DEBUG REPO: search_type='{search_type}' -> embedding_column='{embedding_column}'")

      # Requête SQL avec architecture 3-paires
      stmt = text(f"""
          SELECT id, game_id, image_id, 
                 ocr_content, ocr_embedding,
                 description_content, description_embedding,
                 labels_content, labels_embedding,
                 page_number, created_at,
                 1 - ({embedding_column} <=> :query_vector) as similarity_score
          FROM game_vectors
          WHERE game_id = :game_id
            AND 1 - ({embedding_column} <=> :query_vector) >= :similarity_threshold
            {not_null_condition}
          ORDER BY similarity_score DESC
          LIMIT :limit
      """)

      # Exécution avec paramètres typés
      query_vector_str = json.dumps(query_embedding)
      result = await self._session.execute(
          stmt,
          {
              "game_id": str(game_id),
              "query_vector": query_vector_str,
              "similarity_threshold": similarity_threshold,
              "limit": limit
          }
      )

      # Conversion avec architecture 3-paires
      vectors = []
      for row in result:
          vector = GameVector(
              id=row.id,
              game_id=row.game_id,
              image_id=row.image_id if row.image_id else None,
              
              # Architecture 3-paires complète
              ocr_content=row.ocr_content,
              ocr_embedding=row.ocr_embedding,
              description_content=row.description_content,
              description_embedding=row.description_embedding,
              labels_content=row.labels_content,
              labels_embedding=row.labels_embedding,
              
              page_number=row.page_number,
              created_at=row.created_at,
              similarity_score=float(row.similarity_score)
          )
          vectors.append(vector)

      return vectors

  async def delete(self, vector_id: UUID) -> bool:
      """Supprime un vecteur"""
      stmt = select(GameVectorModel).where(GameVectorModel.id == vector_id)
      result = await self._session.execute(stmt)
      model = result.scalar_one_or_none()

      if model:
          await self._session.delete(model)
          return True
      return False

  async def delete_by_image_id(self, image_id: UUID) -> int:
      """Supprime tous les vecteurs d'une image"""
      stmt = delete(GameVectorModel).where(GameVectorModel.image_id == image_id)
      result = await self._session.execute(stmt)
      return result.rowcount

  def _model_to_entity(self, model: GameVectorModel) -> GameVector:
      """Convertit un modèle en entité"""
      return GameVector(
          id=model.id,
          game_id=model.game_id,
          image_id=model.image_id,
          
          # Architecture 3-paires
          ocr_content=model.ocr_content,
          ocr_embedding=model.ocr_embedding,
          description_content=model.description_content,
          description_embedding=model.description_embedding,
          labels_content=model.labels_content,
          labels_embedding=model.labels_embedding,
          
          page_number=model.page_number,
          created_at=model.created_at
      )