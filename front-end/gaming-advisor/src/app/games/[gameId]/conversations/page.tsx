"use client";

import { useState, useEffect } from 'react';
import { useRouter, useParams, useSearchParams} from 'next/navigation';
import Link from 'next/link';
import { fetchWithAuth } from '@/utils/api';

type Conversation = {
  id: string;
  title: string;
  created_at: string;
};

export default function ConversationsPage() {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const gameId = params.gameId as string;
  const gameTitle = searchParams.get('title') ? decodeURIComponent(searchParams.get('title')!) : 'ce jeu';

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!gameId) return;

    const getConversations = async () => {
      try {
        const { response } = await fetchWithAuth(`https://gameadvisor-api-containerapp.purpleplant-bc5dabd4.francecentral.azurecontainerapps.io/chat/games/${gameId}/conversations`);
        if (!response.ok) throw new Error('Impossible de charger les conversations.');

        const data = await response.json();
        setConversations(data.conversations || []);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };
    getConversations();
  }, [gameId]);

  const handleCreateConversation = async () => {
    try {
      // On génère un titre plus simple
      const newTitle = `Discussion ${conversations.length + 1} pour ${gameTitle}`;

      const { response } = await fetchWithAuth('https://gameadvisor-api-containerapp.purpleplant-bc5dabd4.francecentral.azurecontainerapps.io/chat/conversations', {
        method: 'POST',
        body: JSON.stringify({ game_id: gameId, title: newTitle }),
      });
      const newConversationData = await response.json();
      if (!response.ok) throw new Error('Impossible de créer la conversation.');

      const newConversation = newConversationData.conversation;
      router.push(`/chat/${newConversation.id}`);
    } catch (err: any) {
      setError(err.message);
    }
  };

  if (isLoading) return <div className="flex h-screen items-center justify-center bg-gray-900 text-white">Chargement...</div>;
  if (error) return <div className="flex h-screen items-center justify-center bg-gray-900 text-red-500">{error}</div>;


  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          {/* On affiche le nom du jeu dans le titre */}
          <h1 className="text-3xl font-bold">Discussions pour {gameTitle}</h1>
          <button
            onClick={handleCreateConversation}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
          >
            Nouvelle discussion
          </button>
        </div>
        <div className="space-y-4">
          {conversations.length > 0 ? (
            conversations.map((conv) => (
              <Link
                href={`/chat/${conv.id}`}
                key={conv.id}
                className="block p-6 bg-gray-800 rounded-lg shadow-lg border border-gray-700 hover:border-indigo-500 transition-colors"
              >
                <h2 className="text-xl font-bold">{conv.title}</h2>
                <p className="text-sm text-gray-400">
                  Créée le: {new Date(conv.created_at).toLocaleDateString()}
                </p>
              </Link>
            ))
          ) : (
            <p className="text-center text-gray-400">Aucune discussion pour ce jeu. Créez-en une !</p>
          )}
        </div>
      </div>
    </div>
  );
}