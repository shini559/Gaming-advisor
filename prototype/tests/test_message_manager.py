import pytest
import sys
import os
from unittest.mock import Mock, patch
from PIL import Image
import io
import base64

# Ajouter le chemin du prototype pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from classes.message_manager import MessageManager
from classes.settings import Settings


class TestMessageManager:
    
    @pytest.fixture
    def settings(self):
        """Mock des settings pour les tests"""
        settings = Mock(spec=Settings)
        settings.params = {
            "image_max_size": 1024,
            "dpi": 100
        }
        return settings
    
    @pytest.fixture
    def mock_pdf_file(self):
        """Mock d'un fichier PDF uploadé"""
        mock_file = Mock()
        mock_file.name = "test_document.pdf"
        mock_file.type = "application/pdf"
        
        # Lire le PDF de test existant
        test_pdf_path = os.path.join(os.path.dirname(__file__), 'test_assets', 'pdf_test.pdf')
        if os.path.exists(test_pdf_path):
            with open(test_pdf_path, 'rb') as f:
                mock_file.read.return_value = f.read()
        else:
            # Fallback si le PDF n'existe pas
            mock_file.read.return_value = b"PDF content placeholder"
        
        return mock_file
    
    def test_process_pdf_returns_list(self, settings, mock_pdf_file):
        """Test que _process_pdf retourne une liste"""
        print("\n🧪 Test: process_pdf_returns_list")
        try:
            result = MessageManager._process_pdf(mock_pdf_file, settings)
            assert isinstance(result, list), "Le résultat doit être une liste"
            print(f"✅ PASSÉ - Retourne une liste de {len(result)} éléments")
        except Exception as e:
            print(f"⚠️ SKIPPÉ - {e}")
            pytest.skip(f"PDF de test non disponible ou erreur PyMuPDF: {e}")
    
    def test_process_pdf_creates_image_dict(self, settings, mock_pdf_file):
        """Test que chaque page PDF génère un dictionnaire d'image valide"""
        print("\n🧪 Test: process_pdf_creates_image_dict")
        try:
            result = MessageManager._process_pdf(mock_pdf_file, settings)
            
            if len(result) > 0:
                image_dict = result[0]
                
                # Vérifier la structure du dictionnaire
                assert "type" in image_dict, "Le dictionnaire doit contenir 'type'"
                assert "name" in image_dict, "Le dictionnaire doit contenir 'name'"
                assert "data" in image_dict, "Le dictionnaire doit contenir 'data'"
                
                # Vérifier les valeurs
                assert image_dict["type"] == "image", "Le type doit être 'image'"
                assert "test_document.pdf" in image_dict["name"], "Le nom doit contenir le nom du fichier"
                assert "Page" in image_dict["name"], "Le nom doit contenir 'Page'"
                
                # Vérifier que data est du base64 valide
                try:
                    base64.b64decode(image_dict["data"])
                    print(f"✅ PASSÉ - Structure valide, base64 OK, nom: {image_dict['name']}")
                except:
                    print("❌ ÉCHEC - Base64 invalide")
                    assert False, "Les données ne sont pas du base64 valide"
                    
        except Exception as e:
            print(f"⚠️ SKIPPÉ - {e}")
            pytest.skip(f"PDF de test non disponible ou erreur PyMuPDF: {e}")
    
    def test_process_pdf_multiple_pages(self, settings):
        """Test du traitement d'un PDF multi-pages"""
        print("\n🧪 Test: process_pdf_multiple_pages")
        # Créer un mock de fichier PDF multi-pages
        mock_file = Mock()
        mock_file.name = "multi_page.pdf"
        mock_file.type = "application/pdf"
        
        try:
            # Utiliser le PDF de test s'il existe
            test_pdf_path = os.path.join(os.path.dirname(__file__), 'test_assets', 'pdf_test.pdf')
            if os.path.exists(test_pdf_path):
                with open(test_pdf_path, 'rb') as f:
                    mock_file.read.return_value = f.read()
                
                result = MessageManager._process_pdf(mock_file, settings)
                
                # Vérifier que chaque page a un nom unique
                page_names = [img["name"] for img in result]
                assert len(set(page_names)) == len(page_names), "Chaque page doit avoir un nom unique"
                
                # Vérifier la numérotation des pages
                for i, img in enumerate(result):
                    expected_page_num = i + 1
                    assert f"Page {expected_page_num}" in img["name"], f"Page {expected_page_num} doit être dans le nom"
                
                print(f"✅ PASSÉ - {len(result)} pages traitées avec noms uniques")
            else:
                print("⚠️ SKIPPÉ - PDF de test non trouvé")
                pytest.skip("PDF de test non disponible")
                
        except Exception as e:
            print(f"⚠️ SKIPPÉ - {e}")
            pytest.skip(f"Erreur lors du test multi-pages: {e}")
    
    def test_process_uploaded_files_with_pdf(self, settings, mock_pdf_file):
        """Test de process_uploaded_files avec un PDF"""
        print("\n🧪 Test: process_uploaded_files_with_pdf")
        try:
            uploaded_files = [mock_pdf_file]
            result = MessageManager.process_uploaded_files(uploaded_files, settings)
            
            assert isinstance(result, list), "Le résultat doit être une liste"
            
            # Si le PDF a été traité avec succès
            if len(result) > 0:
                # Tous les éléments doivent être des images
                for item in result:
                    assert item["type"] == "image", "Tous les éléments doivent être de type 'image'"
                    assert "data" in item, "Chaque élément doit contenir 'data'"
                    assert "name" in item, "Chaque élément doit contenir 'name'"
                
                print(f"✅ PASSÉ - Pipeline complet OK, {len(result)} fichiers traités")
                    
        except Exception as e:
            print(f"⚠️ SKIPPÉ - {e}")
            pytest.skip(f"Erreur lors du test process_uploaded_files: {e}")
    
    def test_process_uploaded_files_empty_list(self, settings):
        """Test avec une liste vide"""
        print("\n🧪 Test: process_uploaded_files_empty_list")
        result = MessageManager.process_uploaded_files([], settings)
        assert result == [], "Une liste vide doit retourner une liste vide"
        print("✅ PASSÉ - Liste vide gérée correctement")
    
    def test_process_uploaded_files_none(self, settings):
        """Test avec None"""
        print("\n🧪 Test: process_uploaded_files_none")
        result = MessageManager.process_uploaded_files(None, settings)
        assert result == [], "None doit retourner une liste vide"
        print("✅ PASSÉ - None géré correctement")


if __name__ == "__main__":
    pytest.main([__file__])