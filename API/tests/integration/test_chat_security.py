"""
Tests de sécurité pour les endpoints de chat/conversation
Tests pour valider les règles d'autorisation des conversations
"""

import pytest
from fastapi import status
from uuid import uuid4

from tests.conftest import ClientHelper


class TestConversationSecurity:
    """Tests de sécurité pour les conversations"""

    @pytest.mark.asyncio
    async def test_user_cannot_send_message_to_other_conversation(self, test_client: ClientHelper):
        """CRITIQUE: Un utilisateur ne peut pas envoyer de messages dans les conversations d'autrui"""
        
        # 1. Utilisateur A crée un jeu et une conversation
        user_a = await test_client.create_test_user("user_a@test.com")
        token_a = await test_client.login_user(user_a["email"], "testpass123")
        
        game_response = await test_client.create_test_game("Jeu de A", is_public=False, token=token_a)
        game_id = game_response["game"]["game_id"]
        
        # Créer conversation de A
        conv_response = await test_client.client.post(
            "/chat/conversations",
            json={"game_id": game_id, "title": "Conversation de A"},
            headers={"Authorization": f"Bearer {token_a}"}
        )
        conversation_id = conv_response.json()["conversation"]["id"]
        
        # 2. Utilisateur B essaie d'envoyer un message dans la conversation de A
        user_b = await test_client.create_test_user("user_b@test.com")
        token_b = await test_client.login_user(user_b["email"], "testpass123")
        
        response = await test_client.client.post(
            "/chat/messages",
            json={
                "conversation_id": conversation_id,
                "content": "Message non autorisé de B"
            },
            headers={"Authorization": f"Bearer {token_b}"}
        )
        
        # 3. Doit échouer
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non trouvée ou accès refusé" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_user_cannot_access_other_conversation_history(self, test_client: ClientHelper):
        """CRITIQUE: Un utilisateur ne peut pas consulter l'historique d'autres conversations"""
        
        # 1. Utilisateur A crée une conversation avec des messages
        user_a = await test_client.create_test_user("user_a@test.com")
        token_a = await test_client.login_user(user_a["email"], "testpass123")
        
        game_response = await test_client.create_test_game("Jeu de A", is_public=False, token=token_a)
        game_id = game_response["game"]["game_id"]
        
        conv_response = await test_client.client.post(
            "/chat/conversations",
            json={"game_id": game_id, "title": "Conversation privée de A"},
            headers={"Authorization": f"Bearer {token_a}"}
        )
        conversation_id = conv_response.json()["conversation"]["id"]
        
        # 2. Utilisateur B essaie d'accéder à l'historique de la conversation de A
        user_b = await test_client.create_test_user("user_b@test.com")
        token_b = await test_client.login_user(user_b["email"], "testpass123")
        
        response = await test_client.client.get(
            f"/chat/conversations/{conversation_id}/history",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        
        # 3. Doit échouer
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non trouvée ou accès refusé" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_user_cannot_feedback_other_conversation_messages(self, test_client: ClientHelper):
        """CRITIQUE: Un utilisateur ne peut pas évaluer les messages d'autres conversations"""
        
        # 1. Utilisateur A crée une conversation avec un message
        user_a = await test_client.create_test_user("user_a@test.com")
        token_a = await test_client.login_user(user_a["email"], "testpass123")
        
        game_response = await test_client.create_test_game("Jeu de A", is_public=False, token=token_a)
        game_id = game_response["game"]["game_id"]
        
        conv_response = await test_client.client.post(
            "/chat/conversations",
            json={"game_id": game_id, "title": "Conversation de A"},
            headers={"Authorization": f"Bearer {token_a}"}
        )
        conversation_id = conv_response.json()["conversation"]["id"]
        
        # Envoyer un message pour avoir une réponse de l'assistant à évaluer
        msg_response = await test_client.client.post(
            "/chat/messages",
            json={
                "conversation_id": conversation_id,
                "content": "Question test"
            },
            headers={"Authorization": f"Bearer {token_a}"}
        )
        assistant_message_id = msg_response.json()["assistant_message"]["id"]
        
        # 2. Utilisateur B essaie de donner un feedback sur le message de A
        user_b = await test_client.create_test_user("user_b@test.com")
        token_b = await test_client.login_user(user_b["email"], "testpass123")
        
        response = await test_client.client.post(
            f"/chat/messages/{assistant_message_id}/feedback",
            json={
                "feedback_type": "positive",
                "comment": "Feedback non autorisé de B"
            },
            headers={"Authorization": f"Bearer {token_b}"}
        )
        
        # 3. Doit échouer
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "accès à la conversation refusé" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_user_only_sees_own_conversations_for_game(self, test_client: ClientHelper):
        """CRITIQUE: Un utilisateur ne voit que ses propres conversations pour un jeu"""
        
        # 1. Admin crée un jeu public pour que deux utilisateurs puissent créer des conversations
        admin = await test_client.create_test_user("admin@test.com", is_admin=True)
        admin_token = await test_client.login_user(admin["email"], "testpass123")
        
        game_response = await test_client.create_test_game("Jeu Public", is_public=True, token=admin_token)
        game_id = game_response["game"]["game_id"]
        
        # 2. Utilisateur A crée une conversation sur le jeu public
        user_a = await test_client.create_test_user("user_a@test.com")
        token_a = await test_client.login_user(user_a["email"], "testpass123")
        
        await test_client.client.post(
            "/chat/conversations",
            json={"game_id": game_id, "title": "Conversation de A"},
            headers={"Authorization": f"Bearer {token_a}"}
        )
        
        # 3. Utilisateur B crée aussi une conversation sur le même jeu public
        user_b = await test_client.create_test_user("user_b@test.com")
        token_b = await test_client.login_user(user_b["email"], "testpass123")
        
        await test_client.client.post(
            "/chat/conversations",
            json={"game_id": game_id, "title": "Conversation de B"},
            headers={"Authorization": f"Bearer {token_b}"}
        )
        
        # 3. Utilisateur A liste les conversations pour ce jeu
        response_a = await test_client.client.get(
            f"/chat/games/{game_id}/conversations",
            headers={"Authorization": f"Bearer {token_a}"}
        )
        
        # 4. Utilisateur B liste les conversations pour ce jeu  
        response_b = await test_client.client.get(
            f"/chat/games/{game_id}/conversations",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        
        # 5. Chaque utilisateur ne voit que sa propre conversation
        conversations_a = response_a.json()["conversations"]
        conversations_b = response_b.json()["conversations"]
        
        assert len(conversations_a) == 1
        assert len(conversations_b) == 1
        assert conversations_a[0]["title"] == "Conversation de A"
        assert conversations_b[0]["title"] == "Conversation de B"
        
        # Les IDs des conversations doivent être différents
        assert conversations_a[0]["id"] != conversations_b[0]["id"]

    @pytest.mark.asyncio
    async def test_user_can_create_conversation_for_public_game(self, test_client: ClientHelper):
        """Test positif: Un utilisateur peut créer des conversations pour TOUS les jeux publics"""
        
        # 1. Admin crée un jeu public
        admin = await test_client.create_test_user("admin@test.com", is_admin=True)
        admin_token = await test_client.login_user(admin["email"], "testpass123")
        
        game_response = await test_client.create_test_game("Jeu Public Admin", is_public=True, token=admin_token)
        game_id = game_response["game"]["game_id"]
        
        # 2. Utilisateur B crée une conversation pour le jeu public de l'admin
        user_b = await test_client.create_test_user("user_b@test.com")
        token_b = await test_client.login_user(user_b["email"], "testpass123")
        
        response = await test_client.client.post(
            "/chat/conversations",
            json={
                "game_id": game_id,
                "title": "Ma conversation sur le jeu public de l'admin"
            },
            headers={"Authorization": f"Bearer {token_b}"}
        )
        
        # 3. Doit réussir pour les jeux publics
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] is True
        assert response.json()["conversation"]["title"] == "Ma conversation sur le jeu public de l'admin"

    @pytest.mark.asyncio
    async def test_user_cannot_create_conversation_for_private_game(self, test_client: ClientHelper):
        """Test critique: Un utilisateur ne peut pas créer de conversation pour un jeu privé d'autrui"""
        
        # 1. Utilisateur A crée un jeu privé
        user_a = await test_client.create_test_user("user_a@test.com")
        token_a = await test_client.login_user(user_a["email"], "testpass123")
        
        game_response = await test_client.create_test_game("Jeu Privé de A", is_public=False, token=token_a)
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


class TestConversationPositiveFlows:
    """Tests des flux positifs pour s'assurer que les fonctionnalités marchent"""

    @pytest.mark.asyncio
    async def test_complete_positive_flow_own_game(self, test_client: ClientHelper):
        """Test du flux complet sur son propre jeu"""
        
        # 1. Créer utilisateur et jeu
        user = await test_client.create_test_user("user@test.com")
        token = await test_client.login_user(user["email"], "testpass123")
        
        game_response = await test_client.create_test_game("Mon Jeu", is_public=False, token=token)
        game_id = game_response["game"]["game_id"]
        
        # 2. Créer conversation
        conv_response = await test_client.client.post(
            "/chat/conversations",
            json={"game_id": game_id, "title": "Ma Conversation"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert conv_response.status_code == status.HTTP_200_OK
        conversation_id = conv_response.json()["conversation"]["id"]
        
        # 3. Envoyer message (skip car nécessite l'agent IA)
        # msg_response = await test_client.client.post(...)
        
        # 4. Consulter historique
        history_response = await test_client.client.get(
            f"/chat/conversations/{conversation_id}/history",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert history_response.status_code == status.HTTP_200_OK
        
        # 5. Lister conversations pour ce jeu
        list_response = await test_client.client.get(
            f"/chat/games/{game_id}/conversations",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert list_response.status_code == status.HTTP_200_OK
        conversations = list_response.json()["conversations"]
        assert len(conversations) == 1
        assert conversations[0]["title"] == "Ma Conversation"


class TestConversationEdgeCases:
    """Tests des cas limites"""

    @pytest.mark.asyncio
    async def test_conversation_with_nonexistent_game(self, test_client: ClientHelper):
        """Test création conversation avec jeu inexistant"""
        
        user = await test_client.create_test_user("user@test.com")
        token = await test_client.login_user(user["email"], "testpass123")
        
        fake_game_id = str(uuid4())
        
        response = await test_client.client.post(
            "/chat/conversations",
            json={
                "game_id": fake_game_id,
                "title": "Conversation pour jeu inexistant"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "jeu non trouvé" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_access_nonexistent_conversation_history(self, test_client: ClientHelper):
        """Test accès historique conversation inexistante"""
        
        user = await test_client.create_test_user("user@test.com")
        token = await test_client.login_user(user["email"], "testpass123")
        
        fake_conversation_id = str(uuid4())
        
        response = await test_client.client.get(
            f"/chat/conversations/{fake_conversation_id}/history",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non trouvée ou accès refusé" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_feedback_nonexistent_message(self, test_client: ClientHelper):
        """Test feedback sur message inexistant"""
        
        user = await test_client.create_test_user("user@test.com")
        token = await test_client.login_user(user["email"], "testpass123")
        
        fake_message_id = str(uuid4())
        
        response = await test_client.client.post(
            f"/chat/messages/{fake_message_id}/feedback",
            json={
                "feedback_type": "positive",
                "comment": "Test sur message inexistant"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "message non trouvé" in response.json()["detail"].lower()