from fastapi import APIRouter, Depends, HTTPException, Query
from starlette import status

from app.dependencies import get_create_game_use_case, get_current_user
from app.dependencies.use_cases import get_list_user_accessible_games_use_case, get_list_user_games_use_case
from app.domain.entities.user import User
from app.domain.use_cases.games import CreateGameUseCase, CreateGameRequest
from app.domain.use_cases.games.create_game import GameAlreadyExistsError
from app.domain.use_cases.games.list_user_accessible_games import ListUserAccessibleGamesUseCase, ListUserAccessibleGamesRequest
from app.domain.use_cases.games.list_user_games import ListUserGamesUseCase, ListUserGamesRequest
from app.presentation.schemas.auth import ErrorResponse
from app.presentation.schemas.games import GameResponse, GameCreationRequest, GamesListResponse

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
  current_user: User = Depends(get_current_user),
  use_case: CreateGameUseCase = Depends(get_create_game_use_case)
) -> GameResponse:
  """Inscrire un nouvel utilisateur"""
  try:
      # Convertir le schéma API en requête use case
      # Sécurité: is_public=False et created_by=current_user.id forcés
      use_case_request = CreateGameRequest(
          title=request.title,
          publisher=request.publisher,
          description=request.description,
          series_id=request.series_id,
          is_expansion=request.is_expansion,
          base_game_id=request.base_game_id,
          is_public=False,
          created_by=current_user.id
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


@router.get(
    "",
    response_model=GamesListResponse,
    responses={
        200: {"description": "List of accessible games"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Get accessible games",
    description="Get games accessible to the current user (public games + user's private games) with pagination"
)
async def get_accessible_games(
    limit: int = Query(default=20, ge=1, le=100, description="Number of games per page"),
    offset: int = Query(default=0, ge=0, description="Number of games to skip"),
    current_user: User = Depends(get_current_user),
    use_case: ListUserAccessibleGamesUseCase = Depends(get_list_user_accessible_games_use_case)
) -> GamesListResponse:
    """Récupérer les jeux accessibles à l'utilisateur connecté"""
    try:
        # Créer la requête use case
        request = ListUserAccessibleGamesRequest(
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )

        # Exécuter le use case
        response = await use_case.execute(request)

        if not response.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=response.message
            )

        # Convertir les entités en schémas API
        games_response = [
            GameResponse(
                game_id=game.id,
                title=game.title,
                publisher=game.publisher,
                description=game.description,
                series_id=game.series_id,
                is_expansion=game.is_expansion,
                base_game_id=game.base_game_id,
                is_public=game.is_public,
                created_by=game.created_by
            )
            for game in response.games
        ]

        return GamesListResponse(
            games=games_response,
            total_count=response.total_count,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < response.total_count
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve games: {str(e)}"
        )


@router.get(
    "/my",
    response_model=GamesListResponse,
    responses={
        200: {"description": "List of user's own games"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Get user's own games",
    description="Get games created by the current user (only owned games, not public games) with pagination"
)
async def get_my_games(
    limit: int = Query(default=20, ge=1, le=100, description="Number of games per page"),
    offset: int = Query(default=0, ge=0, description="Number of games to skip"),
    current_user: User = Depends(get_current_user),
    use_case: ListUserGamesUseCase = Depends(get_list_user_games_use_case)
) -> GamesListResponse:
    """Récupérer les jeux créés par l'utilisateur connecté"""
    try:
        # Créer la requête use case
        request = ListUserGamesRequest(
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )

        # Exécuter le use case
        response = await use_case.execute(request)

        if not response.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=response.message
            )

        # Convertir les entités en schémas API
        games_response = [
            GameResponse(
                game_id=game.id,
                title=game.title,
                publisher=game.publisher,
                description=game.description,
                series_id=game.series_id,
                is_expansion=game.is_expansion,
                base_game_id=game.base_game_id,
                is_public=game.is_public,
                created_by=game.created_by
            )
            for game in response.games
        ]

        return GamesListResponse(
            games=games_response,
            total_count=response.total_count,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < response.total_count
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user games: {str(e)}"
        )