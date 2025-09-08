from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, delete
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

  async def search_by_embedding_type(
      self,
      game_id: UUID,
      query_embedding: List[float],
      embedding_type: str,  # "ocr" | "description" | "labels" - SEULEMENT pour la recherche
      limit: int = 10,
      similarity_threshold: float = 0.7
  ) -> List[GameVector]:
      """
      Recherche vectorielle découplée - utilise seulement embedding_type pour la similarité
      Retourne TOUT le contenu pour que l'agent puisse choisir ses champs
      """
      from sqlalchemy import text
      from app.domain.entities.vector_search_types import VectorSearchMethod
      import json
      
      # Validation et conversion du type de recherche
      try:
          search_enum = VectorSearchMethod(embedding_type)
      except ValueError:
          raise ValueError(f"Type de recherche non supporté: {embedding_type}")
      
      # Récupération SEULEMENT de la colonne embedding (découplée du contenu)
      embedding_column = search_enum.get_embedding_column()
      not_null_condition = search_enum.get_not_null_condition()
      
      print(f"🔍 DEBUG REPO DÉCOUPLÉ: embedding_type='{embedding_type}' -> embedding_column='{embedding_column}'")

      # Requête SQL découplée - on récupère TOUT le contenu
      stmt = text(f"""
          SELECT id, game_id, image_id,
                 ocr_content, description_content, labels_content,
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

      # Conversion avec tout le contenu disponible
      vectors = []
      for row in result:
          vector = GameVector(
              id=row.id,
              game_id=row.game_id,
              image_id=row.image_id if row.image_id else None,
              
              # TOUT le contenu pour l'agent (découplé de la recherche)
              ocr_content=row.ocr_content,
              ocr_embedding=None,  # Pas besoin des embeddings dans les résultats
              description_content=row.description_content,
              description_embedding=None,
              labels_content=row.labels_content,
              labels_embedding=None,
              
              page_number=row.page_number,
              created_at=row.created_at,
              similarity_score=float(row.similarity_score)
          )
          vectors.append(vector)

      return vectors

  # Gardons l'ancienne méthode pour la compatibilité pendant la transition
  async def search_by_vector_type(
      self,
      game_id: UUID,
      query_embedding: List[float],
      search_type: str,
      limit: int = 10,
      similarity_threshold: float = 0.7
  ) -> List[GameVector]:
      """DEPRECATED: Utiliser search_by_embedding_type à la place"""
      return await self.search_by_embedding_type(
          game_id, query_embedding, search_type, limit, similarity_threshold
      )

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