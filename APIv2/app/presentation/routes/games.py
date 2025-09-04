from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form
from starlette import status
from typing import Optional
from uuid import UUID

from app.dependencies import get_create_game_use_case, get_current_user
from app.dependencies.use_cases import get_list_user_accessible_games_use_case, get_list_user_games_use_case, get_update_game_use_case
from app.domain.entities.user import User
from app.domain.use_cases.games import CreateGameUseCase, CreateGameRequest
from app.domain.use_cases.games.create_game import GameAlreadyExistsError
from app.domain.use_cases.games.update_game import UpdateGameUseCase, UpdateGameRequest
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
      413: {"model": ErrorResponse, "description": "Avatar file too large"},
      415: {"model": ErrorResponse, "description": "Unsupported avatar file type"},
      500: {"model": ErrorResponse, "description": "Internal server error"}
  },
  summary="Create a new game",
  description="Create a new game with title, public status and optional avatar image"
)
async def create_game(
  title: str = Form(..., description="Game title"),
  publisher: Optional[str] = Form(None, description="Game publisher"),
  description: Optional[str] = Form(None, description="Game description"),
  series_id: Optional[UUID] = Form(None, description="Game series ID"),
  is_expansion: bool = Form(False, description="Is this an expansion"),
  base_game_id: Optional[UUID] = Form(None, description="Base game ID if expansion"),
  is_public: Optional[bool] = Form(None, description="Is game public (admin only)"),
  avatar: Optional[UploadFile] = File(None, description="Game avatar image"),
  current_user: User = Depends(get_current_user),
  use_case: CreateGameUseCase = Depends(get_create_game_use_case)
) -> GameResponse:
  """Créer un nouveau jeu avec avatar optionnel"""
  try:
      # Validation et traitement de l'avatar
      avatar_content = None
      avatar_filename = None
      
      if avatar:
          # Validation du type de fichier
          allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
          if avatar.content_type not in allowed_types:
              raise HTTPException(
                  status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                  detail=f"Unsupported file type. Allowed: {', '.join(allowed_types)}"
              )
          
          # Validation de la taille (limite à 5 MB)
          max_size = 5 * 1024 * 1024  # 5 MB
          avatar_content = await avatar.read()
          if len(avatar_content) > max_size:
              raise HTTPException(
                  status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                  detail="Avatar file too large. Maximum size: 5 MB"
              )
          
          avatar_filename = avatar.filename
      
      # Convertir en requête use case
      use_case_request = CreateGameRequest(
          title=title,
          publisher=publisher,
          description=description,
          series_id=series_id,
          is_expansion=is_expansion,
          base_game_id=base_game_id,
          is_public=is_public,
          created_by=current_user.id,
          user_is_admin=current_user.is_admin,
          avatar_content=avatar_content,
          avatar_filename=avatar_filename
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
          created_by=response.game.created_by,
          avatar=response.game.avatar
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
                created_by=game.created_by,
                avatar=game.avatar
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
                created_by=game.created_by,
                avatar=game.avatar
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


@router.put(
    "/{game_id}/update",
    response_model=GameResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
        404: {"model": ErrorResponse, "description": "Game not found"},
        413: {"model": ErrorResponse, "description": "Avatar file too large"},
        415: {"model": ErrorResponse, "description": "Unsupported avatar file type"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Update a game",
    description="Update game information and optionally change avatar image"
)
async def update_game(
    game_id: UUID,
    title: Optional[str] = Form(None, description="Game title"),
    publisher: Optional[str] = Form(None, description="Game publisher"),
    description: Optional[str] = Form(None, description="Game description"),
    series_id: Optional[str] = Form(None, description="Game series ID (optional)"),
    is_expansion: bool = Form(False, description="Is this an expansion"),
    base_game_id: Optional[str] = Form(None, description="Base game ID if expansion"),
    is_public: Optional[bool] = Form(None, description="Is game public (admin only)"),
    avatar: Optional[UploadFile] = File(None, description="New game avatar image (optional)"),
    current_user: User = Depends(get_current_user),
    use_case: UpdateGameUseCase = Depends(get_update_game_use_case)
) -> GameResponse:
    """Mettre à jour les informations d'un jeu avec avatar optionnel"""
    try:
        # Validation et traitement de l'avatar
        avatar_content = None
        avatar_filename = None
        
        if avatar:
            # Validation du type de fichier
            allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
            if avatar.content_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail=f"Unsupported file type. Allowed: {', '.join(allowed_types)}"
                )
            
            # Validation de la taille (limite à 5 MB)
            max_size = 5 * 1024 * 1024  # 5 MB
            avatar_content = await avatar.read()
            if len(avatar_content) > max_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Avatar file too large. Maximum size: 5 MB"
                )
            
            avatar_filename = avatar.filename
        
        # Nettoyer et valider les champs UUID optionnels
        def clean_uuid_field(value: Optional[str]) -> Optional[UUID]:
            """Convertit chaîne vide en None, ou parse l'UUID si valide"""
            if not value or value.strip() == "":
                return None
            try:
                return UUID(value.strip())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid UUID format: {value}"
                )
        
        # Nettoyer les UUIDs
        cleaned_series_id = clean_uuid_field(series_id)
        cleaned_base_game_id = clean_uuid_field(base_game_id)
        
        # Règle métier: si is_expansion=False, alors base_game_id doit être None
        if not is_expansion:
            cleaned_base_game_id = None
        
        # Convertir en requête use case
        use_case_request = UpdateGameRequest(
            game_id=game_id,
            user_id=current_user.id,
            user_is_admin=current_user.is_admin,
            title=title,
            publisher=publisher,
            description=description,
            series_id=cleaned_series_id,
            is_expansion=is_expansion,
            base_game_id=cleaned_base_game_id,
            is_public=is_public,
            avatar_content=avatar_content,
            avatar_filename=avatar_filename
        )

        # Exécuter le use case
        response = await use_case.execute(use_case_request)

        if not response.success:
            # Gestion spécifique des erreurs
            if "not found" in response.message.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=response.message
                )
            elif "permission denied" in response.message.lower():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=response.message
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=response.message
                )

        if not response.game:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Game update succeeded but game object is None"
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
            created_by=response.game.created_by,
            avatar=response.game.avatar
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during update"
        )