class RAGRetriever:
    def retrieve_relevant_rules(self, user_query, game_context=None):
        """Recherche intelligente dans les règles"""

        # 1. Embedding de la question
        query_embedding = self.embeddings.embed_query(user_query)

        # 2. Recherche par similarité
        similar_chunks = self.vector_store.similarity_search(
            user_query,
            k=5,
            filter={"game": game_context} if game_context else None
        )

        # 3. Re-ranking par pertinence contextuelle
        relevant_rules = self._rerank_by_context(similar_chunks, user_query)

        return relevant_rules

    def _rerank_by_context(self, chunks, query):
        """Re-classe selon le type de question (setup, scoring, etc.)"""
        # Logique de classification et re-ranking
        pass
