# Exemple pour plus tard : vraie analyse vision avec LangChain

def _analyze_page_real(self, image_data):
    """Version réelle avec modèle vision (à utiliser plus tard)"""
    from langchain_core.messages import HumanMessage
    
    prompt = """Analyse cette page de règles de jeu:
    1. Extrait le texte intégral
    2. Identifie les schémas/diagrammes et décrit-les précisément
    3. Identifie les éléments de jeu (cartes, pions, plateaux)
    4. Structure l'information par sections logiques
    
    Réponds en JSON structuré."""
    
    message = HumanMessage(content=[
        {"type": "text", "text": prompt},
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_data['data']}"}
        }
    ])
    
    response = self.vision_model.invoke([message])
    return response.content