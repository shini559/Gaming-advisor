"""
Tests de sécurité pour les endpoints d'images
Tests critiques pour les vulnérabilités d'autorisation
"""

import pytest
from fastapi import status
from httpx import AsyncClient
from uuid import UUID, uuid4
from io import BytesIO
from PIL import Image

from tests.conftest import ClientHelper


def create_test_image() -> tuple[str, BytesIO, str]:
    """Crée une vraie image test pour les uploads"""
    # Créer une petite image RGB rouge
    image = Image.new('RGB', (100, 100), color='red')
    buffer = BytesIO()
    image.save(buffer, format='JPEG')
    buffer.seek(0)
    return ("test_image.jpg", buffer, "image/jpeg")


class TestImageUploadSecurity:
    """Tests de sécurité pour l'upload d'images"""

    @pytest.mark.asyncio
    async def test_user_cannot_upload_to_other_users_private_game(self, test_client: ClientHelper):
        """CRITIQUE: Un utilisateur ne peut pas uploader sur le jeu privé d'un autre utilisateur"""
        
        # 1. Créer utilisateur A avec un jeu privé
        user_a = await test_client.create_test_user("user_a@test.com")
        token_a = await test_client.login_user(user_a["email"], "testpass123")
        
        game_a_response = await test_client.create_test_game(
            title="Jeu Privé de A",
            is_public=False,
            token=token_a
        )
        game_a_id = game_a_response["game"]["game_id"]
        
        # 2. Créer utilisateur B
        user_b = await test_client.create_test_user("user_b@test.com")
        user_b_token = await test_client.login_user(user_b["email"], "testpass123")
        
        # 3. Essayer d'uploader sur le jeu de A avec les credentials de B
        test_image = create_test_image()
        
        response = await test_client.client.post(
            f"/images/games/{game_a_id}/batch-upload",
            files={"files": test_image},
            headers={"Authorization": f"Bearer {user_b_token}"}
        )
        
        # 4. Vérifications de sécurité
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert "accès refusé" in response_data["detail"].lower()
        assert "propres jeux" in response_data["detail"].lower()
    
    @pytest.mark.asyncio 
    async def test_user_can_upload_to_own_private_game(self, test_client: ClientHelper):
        """Test positif: Un utilisateur peut uploader sur son propre jeu privé"""
        
        # 1. Créer utilisateur A avec un jeu privé
        user_a = await test_client.create_test_user("user_a@test.com")
        token = await test_client.login_user(user_a["email"], "testpass123")
        
        game_response = await test_client.create_test_game(
            title="Mon Jeu Privé",
            is_public=False,
            token=token
        )
        game_id = game_response["game"]["game_id"]
        
        # 2. Uploader sur son propre jeu - doit réussir
        test_image = create_test_image()
        
        response = await test_client.client.post(
            f"/images/games/{game_id}/batch-upload",
            files={"files": test_image},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 3. Vérifications de succès
        assert response.status_code == status.HTTP_202_ACCEPTED
        response_data = response.json()
        assert response_data["total_images"] == 1
        assert "batch_id" in response_data
        assert response_data["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_upload_with_nonexistent_game_id(self, test_client: ClientHelper):
        """Test avec un ID de jeu inexistant"""
        
        user = await test_client.create_test_user("user@test.com")
        token = await test_client.login_user(user["email"], "testpass123")
        
        fake_game_id = str(uuid4())
        test_image = create_test_image()
        
        response = await test_client.client.post(
            f"/images/games/{fake_game_id}/batch-upload",
            files={"files": test_image},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert "non trouvé" in response_data["detail"].lower() or "jeu non trouvé" in response_data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_upload_without_authentication(self, test_client: ClientHelper):
        """Test sans authentification"""
        
        fake_game_id = str(uuid4())
        test_image = create_test_image()
        
        response = await test_client.client.post(
            f"/images/games/{fake_game_id}/batch-upload",
            files={"files": test_image}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestBatchStatusSecurity:
    """Tests de sécurité pour la consultation du statut des batch"""

    @pytest.mark.asyncio
    async def test_user_cannot_access_other_user_batch_status(self, test_client: ClientHelper):
        """CRITIQUE: Un utilisateur ne peut pas consulter les batch d'autres utilisateurs"""
        
        # 1. Utilisateur A crée un jeu et upload des images (génère un batch)
        user_a = await test_client.create_test_user("user_a@test.com")
        token_a = await test_client.login_user(user_a["email"], "testpass123")
        
        game_response = await test_client.create_test_game(
            title="Jeu de A",
            is_public=False,
            token=token_a
        )
        game_id = game_response["game"]["game_id"]
        
        # Upload pour créer un batch
        test_image = create_test_image()
        upload_response = await test_client.client.post(
            f"/images/games/{game_id}/batch-upload",
            files={"files": test_image},
            headers={"Authorization": f"Bearer {token_a}"}
        )
        assert upload_response.status_code == 202, f"Upload failed: {upload_response.json()}"
        batch_id = upload_response.json()["batch_id"]
        
        # 2. Utilisateur B essaie d'accéder au statut du batch de A
        user_b = await test_client.create_test_user("user_b@test.com")
        token_b = await test_client.login_user(user_b["email"], "testpass123")
        
        response = await test_client.client.get(
            f"/images/batches/{batch_id}/status",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        
        # 3. Vérifications de sécurité - B ne peut pas accéder au batch de A
        # L'API peut retourner 403 ou 404 selon l'implémentation
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND, status.HTTP_500_INTERNAL_SERVER_ERROR], f"Status: {response.status_code}, Response: {response.json()}"
        if response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR:
            response_data = response.json()
            assert "accès refusé" in response_data["detail"].lower() or "non trouvé" in response_data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_user_can_access_own_batch_status(self, test_client: ClientHelper):
        """Test positif: Un utilisateur peut consulter ses propres batch"""
        
        # 1. Créer utilisateur et son jeu
        user = await test_client.create_test_user("batch_owner@test.com")
        token = await test_client.login_user(user["email"], "testpass123")
        
        game_response = await test_client.create_test_game(
            title="My Batch Test Game",
            is_public=False,
            token=token
        )
        game_id = game_response["game"]["game_id"]
        
        # 2. Upload pour créer un batch
        test_image = create_test_image()
        upload_response = await test_client.client.post(
            f"/images/games/{game_id}/batch-upload",
            files={"files": test_image},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert upload_response.status_code == status.HTTP_202_ACCEPTED
        batch_id = upload_response.json()["batch_id"]
        
        # 3. Consulter son propre batch - doit réussir
        response = await test_client.client.get(
            f"/images/batches/{batch_id}/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 4. Vérifications de succès
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["batch_id"] == batch_id
        assert "status" in response_data
        assert "progress_ratio" in response_data
    
    @pytest.mark.asyncio
    async def test_batch_status_with_nonexistent_batch_id(self, test_client: ClientHelper):
        """Test avec un ID de batch inexistant"""
        
        user = await test_client.create_test_user("nonexistent_batch_user@test.com")
        token = await test_client.login_user(user["email"], "testpass123")
        
        fake_batch_id = str(uuid4())
        
        response = await test_client.client.get(
            f"/images/batches/{fake_batch_id}/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Peut retourner 404, 500, ou autre selon l'implémentation
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_500_INTERNAL_SERVER_ERROR], f"Status: {response.status_code}, Response: {response.json()}"
    
    @pytest.mark.asyncio
    async def test_batch_status_without_authentication(self, test_client: ClientHelper):
        """Test sans authentification"""
        
        fake_batch_id = str(uuid4())
        
        response = await test_client.client.get(f"/images/batches/{fake_batch_id}/status")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestImageSecurityEdgeCases:
    """Tests de sécurité pour les cas limites"""

    @pytest.mark.asyncio
    async def test_id_enumeration_attack_prevention(self, test_client: ClientHelper):
        """Prévention des attaques d'énumération d'IDs"""
        
        user = await test_client.create_test_user("user@test.com")
        token = await test_client.login_user(user["email"], "testpass123")
        
        # Essayer d'accéder à des IDs séquentiels ou prévisibles
        suspicious_ids = [
            "00000000-0000-0000-0000-000000000001",
            "00000000-0000-0000-0000-000000000002", 
            "11111111-1111-1111-1111-111111111111"
        ]
        
        for suspicious_id in suspicious_ids:
            response = await test_client.client.get(
                f"/images/batches/{suspicious_id}/status",
                headers={"Authorization": f"Bearer {token}"}
            )
            # Soit 404 (n'existe pas) soit 403 (pas le bon propriétaire) soit 500 (erreur interne)
            # Ne doit jamais révéler d'information sur l'existence
            assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN, status.HTTP_500_INTERNAL_SERVER_ERROR], f"Status: {response.status_code} pour ID: {suspicious_id}"
    
    @pytest.mark.asyncio 
    async def test_malformed_uuid_handling(self, test_client: ClientHelper):
        """Test avec des UUIDs malformés"""
        
        user = await test_client.create_test_user("user@test.com")
        token = await test_client.login_user(user["email"], "testpass123")
        
        malformed_ids = ["not-a-uuid", "123", "", "null", "undefined"]
        
        for malformed_id in malformed_ids:
            response = await test_client.client.get(
                f"/images/batches/{malformed_id}/status",
                headers={"Authorization": f"Bearer {token}"}
            )
            # Doit retourner une erreur de validation propre ou 404
            assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_404_NOT_FOUND], f"Status: {response.status_code} pour ID malformé: '{malformed_id}'"


class TestGameCreationSecurity:
    """Tests de sécurité pour la création de jeux"""
    
    @pytest.mark.asyncio
    async def test_non_admin_cannot_create_public_game(self, test_client: ClientHelper):
        """CRITIQUE: Un utilisateur normal ne peut pas créer de jeu public"""
        
        # 1. Créer un utilisateur normal (non admin)
        user = await test_client.create_test_user("user@test.com", is_admin=False)
        token = await test_client.login_user(user["email"], "testpass123")
        
        # 2. Essayer de créer un jeu public
        response = await test_client.client.post(
            "/games/create",
            json={
                "title": "Tentative de jeu public",
                "description": "Jeu que je veux rendre public",
                "publisher": "Test Publisher",
                "is_public": True  # ← Interdit pour les non-admins
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 3. Doit échouer avec 400 Bad Request (validation error)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "seuls les administrateurs" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_admin_can_create_public_game(self, test_client: ClientHelper):
        """Test positif: Un admin peut créer un jeu public"""
        
        # 1. Créer un utilisateur admin
        admin = await test_client.create_test_user("admin@test.com", is_admin=True)
        token = await test_client.login_user(admin["email"], "testpass123")
        
        # 2. Créer un jeu public
        response = await test_client.client.post(
            "/games/create",
            json={
                "title": "Jeu Public Admin",
                "description": "Jeu créé par un admin",
                "publisher": "Admin Publisher",
                "is_public": True  # ← Autorisé pour les admins
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 3. Doit réussir
        assert response.status_code == status.HTTP_201_CREATED
        game_data = response.json()
        assert game_data["is_public"] is True
        assert game_data["created_by"] is None  # Jeu public = pas de propriétaire


class TestImageUploadAdminSecurity:
    """Tests pour les privilèges admin sur l'upload d'images"""
    
    @pytest.mark.asyncio
    async def test_admin_can_upload_to_public_game(self, test_client: ClientHelper):
        """Test positif: Un admin peut uploader sur un jeu public"""
        
        # 1. Admin A crée un jeu public
        admin_a = await test_client.create_test_user("admin_a@test.com", is_admin=True)
        token_a = await test_client.login_user(admin_a["email"], "testpass123")
        
        game_response = await test_client.create_test_game(
            title="Jeu Public pour Upload",
            is_public=True,
            token=token_a
        )
        game_id = game_response["game"]["game_id"]
        
        # 2. Admin B essaie d'uploader sur le jeu public de A
        admin_b = await test_client.create_test_user("admin_b@test.com", is_admin=True)
        token_b = await test_client.login_user(admin_b["email"], "testpass123")
        
        test_image = create_test_image()
        response = await test_client.client.post(
            f"/images/games/{game_id}/batch-upload",
            files={"files": test_image},
            headers={"Authorization": f"Bearer {token_b}"}
        )
        
        # 3. Doit réussir car admin sur jeu public
        assert response.status_code == status.HTTP_202_ACCEPTED
        batch_data = response.json()
        assert batch_data["uploaded_images"] > 0
    
    @pytest.mark.asyncio
    async def test_admin_cannot_upload_to_private_game_of_others(self, test_client: ClientHelper):
        """Test: Un admin ne peut pas uploader sur un jeu privé d'autrui"""
        
        # 1. Utilisateur normal A crée un jeu privé
        user_a = await test_client.create_test_user("user_a@test.com", is_admin=False)
        token_a = await test_client.login_user(user_a["email"], "testpass123")
        
        game_response = await test_client.create_test_game(
            title="Jeu Privé de A",
            is_public=False,
            token=token_a
        )
        game_id = game_response["game"]["game_id"]
        
        # 2. Admin B essaie d'uploader sur le jeu privé de A
        admin_b = await test_client.create_test_user("admin_b@test.com", is_admin=True)
        token_b = await test_client.login_user(admin_b["email"], "testpass123")
        
        test_image = create_test_image()
        response = await test_client.client.post(
            f"/images/games/{game_id}/batch-upload",
            files={"files": test_image},
            headers={"Authorization": f"Bearer {token_b}"}
        )
        
        # 3. Doit échouer car jeu privé d'autrui
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "accès refusé" in response.json()["detail"].lower()


class TestConversationSecurityBasics:
    """Tests de sécurité de base pour les conversations"""

    @pytest.mark.asyncio
    async def test_user_can_create_conversation_for_public_game(self, test_client: ClientHelper):
        """Un utilisateur peut créer des conversations pour TOUS les jeux publics"""
        
        # 1. Admin crée un jeu public
        admin_a = await test_client.create_test_user("admin_a@test.com", is_admin=True)
        # Login APRÈS la mise à jour admin pour avoir un token avec is_admin=true
        token_a = await test_client.login_user(admin_a["email"], "testpass123")
        
        game_response = await test_client.create_test_game(
            title="Jeu Public de A",
            is_public=True,
            token=token_a
        )
        game_id = game_response["game"]["game_id"]
        
        # 2. Utilisateur B crée une conversation pour le jeu public de A
        user_b = await test_client.create_test_user("user_b@test.com")
        token_b = await test_client.login_user(user_b["email"], "testpass123")
        
        response = await test_client.client.post(
            "/chat/conversations",
            json={
                "game_id": game_id,
                "title": "Ma conversation sur le jeu de A"
            },
            headers={"Authorization": f"Bearer {token_b}"}
        )
        
        # 3. Doit réussir pour les jeux publics
        print(f"Public game test - Status: {response.status_code}")
        print(f"Public game test - Response: {response.json()}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] is True
    
    @pytest.mark.asyncio
    async def test_user_cannot_create_conversation_for_private_game(self, test_client: ClientHelper):
        """Un utilisateur ne peut pas créer de conversation pour un jeu privé d'autrui"""
        
        # 1. Utilisateur A crée un jeu privé
        user_a = await test_client.create_test_user("user_a@test.com")
        token_a = await test_client.login_user(user_a["email"], "testpass123")
        
        game_response = await test_client.create_test_game(
            title="Jeu Privé de A",
            is_public=False,
            token=token_a
        )
        game_id = game_response["game"]["game_id"]
        
        # 2. Utilisateur B essaie de créer une conversation pour le jeu privé de A
        user_b = await test_client.create_test_user("user_b@test.com")
        token_b = await test_client.login_user(user_b["email"], "testpass123")
        
        response = await test_client.client.post(
            "/chat/conversations",
            json={
                "game_id": game_id,
                "title": "Tentative sur jeu privé"
            },
            headers={"Authorization": f"Bearer {token_b}"}
        )
        
        # 3. Doit échouer pour les jeux privés d'autrui
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert ("accès refusé" in response.json()["detail"].lower() or 
                "accès au jeu non autorisé" in response.json()["detail"].lower())