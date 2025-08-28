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
          vector_embedding=vector.vector_embedding,
          extracted_text=vector.extracted_text,
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
          vector_embedding=model.vector_embedding,
          extracted_text=model.extracted_text,
          page_number=model.page_number,
          created_at=model.created_at
      )