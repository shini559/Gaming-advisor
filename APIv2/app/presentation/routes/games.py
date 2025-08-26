from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from app.dependencies import get_create_game_use_case
from app.domain.use_cases.games import CreateGameUseCase, CreateGameRequest
from app.domain.use_cases.games.create_game import GameAlreadyExistsError
from app.presentation.schemas.auth import ErrorResponse
from app.presentation.schemas.games import GameResponse, GameCreationRequest

router = APIRouter(prefix="/games", tags=["Games"])

@router.post(
  "/create",
  response_model=GameResponse,
  status_code=status.HTTP_201_CREATED,
  responses={
      400: {"model": ErrorResponse, "description": "Validation error"},
      409: {"model": ErrorResponse, "description": "Game already exists"},
      500: {"model": ErrorResponse, "description": "Internal server error"}
  },
  summary="Create a new game",
  description="Create a new game with title and public status"
)
async def create_game(
  request: GameCreationRequest,
  use_case: CreateGameUseCase = Depends(get_create_game_use_case)
) -> GameResponse:
  """Inscrire un nouvel utilisateur"""
  try:
      # Convertir le schéma API en requête use case
      use_case_request = CreateGameRequest(
          title=request.title,
          publisher=request.publisher,
          description=request.description,
          series_id=request.series_id,
          is_expansion=request.is_expansion,
          base_game_id=request.base_game_id,
          is_public=request.is_public,
          created_by=request.created_by
      )

      # Exécuter le use case
      response = await use_case.execute(use_case_request)

      if not response.success:
          raise HTTPException(
              status_code=status.HTTP_400_BAD_REQUEST,
              detail=response.message
          )

      if not response.game:
          raise HTTPException(
              status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
              detail="Game creation succeeded but game object is None"
          )

      # Convertir la réponse use case en schéma API
      return GameResponse(
          game_id=response.game.id,
          title=response.game.title,
          publisher=response.game.publisher,
          description=response.game.description,
          series_id=response.game.series_id,
          is_expansion=response.game.is_expansion,
          base_game_id=response.game.base_game_id,
          is_public=response.game.is_public,
          created_by=response.game.created_by
      )

  except ValueError as e:
      raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail=str(e)
      )
  except GameAlreadyExistsError as e:
      raise HTTPException(
          status_code=status.HTTP_409_CONFLICT,
          detail=str(e)
      )
  except Exception as e:
      raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail="An unexpected error occurred during creation"
      )