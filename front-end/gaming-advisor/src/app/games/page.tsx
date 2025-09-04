"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { fetchWithAuth } from '@/utils/api';

// --- TYPES ---
type Game = {
  game_id: string;
  title: string;
  is_public: boolean;
  owner_id: string;
  created_by: string | null;
};

export default function GamesPage() {
  const router = useRouter();
  const [games, setGames] = useState<Game[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const userId = typeof window !== 'undefined' ? localStorage.getItem('user_id') : null;


  useEffect(() => {
  const getGames = async () => {
    try {
      const { response } = await fetchWithAuth('https://gameadvisor-api-containerapp.purpleplant-bc5dabd4.francecentral.azurecontainerapps.io/games');
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Impossible de charger la liste des jeux.');
      }

      if (data.games && Array.isArray(data.games)) {
        setGames(data.games);
      } else {
        console.error("La clé 'games' n'est pas un tableau dans la réponse de l'API:", data);
        throw new Error("Le format des données reçues est incorrect.");
      }

    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  getGames();
}, []);

  if (isLoading) {
    return <div className="flex h-screen items-center justify-center bg-gray-900 text-white">Chargement des jeux...</div>;
  }

  if (error) {
    return <div className="flex h-screen items-center justify-center bg-gray-900 text-red-500">{error}</div>;
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">Sélectionnez un jeu</h1>
          <Link
            href="/games/create"
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
          >
            Créer un nouveau jeu
          </Link>
        </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {games.map((game) => {
        // On détermine si l'utilisateur est le propriétaire
        const isOwner = game.created_by === userId;
        const encodedTitle = encodeURIComponent(game.title);
        const href = `/chat/${game.game_id}?owner=${isOwner}&title=${encodedTitle}`;


        return (
          <Link
              href={`/chat/${game.game_id}?owner=${isOwner}&title=${encodedTitle}`}
            key={game.game_id}
            className="block p-6 bg-gray-800 rounded-lg shadow-lg border border-gray-700 hover:border-indigo-500 transition-colors"
          >
            <h2 className="text-xl font-bold mb-2">{game.title}</h2>
            <p className={`text-sm ${game.is_public ? 'text-teal-400' : 'text-amber-400'}`}>
              {game.is_public ? 'Jeu Public' : 'Votre jeu privé'}
            </p>
          </Link>
        );
      })}

    </div>

      </div>
      {/* footer */}
      <footer className="w-full bg-gray-900 border-t border-gray-800 py-6">
        <div className="max-w-4xl mx-auto flex flex-wrap justify-center items-center gap-x-6 gap-y-2 text-sm text-gray-400">
          <Link href="/legal" className="hover:text-white transition-colors">Mentions légales</Link>
          <Link href="/privacy" className="hover:text-white transition-colors">Politique de confidentialité</Link>
          <Link href="/terms" className="hover:text-white transition-colors">Conditions d'utilisation</Link>
        </div>
      </footer>
    </div>
  );
}