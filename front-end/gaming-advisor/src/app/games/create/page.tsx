// src/app/games/create/page.tsx
"use client";

import { useState, useEffect, FormEvent, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
// Note: fetchWithAuth n'est pas utilisé ici car FormData est un cas spécial
// On utilise fetch directement pour que le navigateur gère bien les en-têtes.

export default function CreateGamePage() {
  const router = useRouter();
  // Référence pour l'input file caché
  const fileInputRef = useRef<HTMLInputElement>(null);

  // États pour les champs du formulaire
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [publisher, setPublisher] = useState('');
  const [avatar, setAvatar] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // États pour la logique de la page
  const [isVerified, setIsVerified] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');

  // Vérification de l'authentification au chargement
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
    } else {
      setIsVerified(true);
    }
  }, [router]);

  // Gère la soumission du formulaire avec FormData
  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setIsLoading(true);
    setMessage('');

    try {
      const formData = new FormData();
      formData.append('title', title);
      formData.append('description', description);
      formData.append('publisher', publisher);
      formData.append('is_public', 'false'); // FormData envoie les valeurs en texte
      if (avatar) {
        formData.append('avatar', avatar);
      }

      const accessToken = localStorage.getItem('access_token');
      const response = await fetch('https://gameadvisor-api-containerapp.purpleplant-bc5dabd4.francecentral.azurecontainerapps.io/games/create', {
        method: 'POST',
        headers: {
          // IMPORTANT: Ne pas mettre 'Content-Type'. Le navigateur le fait pour nous avec FormData.
          'Authorization': `Bearer ${accessToken}`,
        },
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        // Logique pour gérer les erreurs de l'API
        let errorMessage = "Erreur lors de la création du jeu.";
        if (data.detail && Array.isArray(data.detail)) {
          errorMessage = data.detail.map((err: { msg: string, loc: string[] }) => `Le champ '${err.loc[1]}' est manquant ou invalide.`).join(' ');
        } else if (data.detail) {
          errorMessage = data.detail;
        }
        throw new Error(errorMessage);
      }

      setMessage('Jeu créé avec succès ! Redirection...');
      setTimeout(() => {
        router.push('/games');
      }, 2000);

    } catch (err: any) {
      setMessage(`Erreur : ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Gère la sélection et l'aperçu de l'image
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] || null;
    setAvatar(file);

    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewUrl(reader.result as string);
      };
      reader.readAsDataURL(file);
    } else {
      setPreviewUrl(null);
    }
  };

  const handleChooseFileClick = () => {
    fileInputRef.current?.click();
  };

  if (!isVerified) {
    return <div className="flex h-screen items-center justify-center bg-gray-900 text-white">Vérification...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-2xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">Créer un nouveau jeu</h1>
          <Link href="/games" className="text-sm text-indigo-400 hover:text-indigo-300">
            &larr; Retour à la liste
          </Link>
        </div>

        <div className="bg-gray-800 p-8 rounded-xl shadow-lg border border-gray-700">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-300">Titre du jeu</label>
              <input id="title" type="text" required value={title} onChange={(e) => setTitle(e.target.value)} className="mt-1 w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" />
            </div>
            <div>
              <label htmlFor="publisher" className="block text-sm font-medium text-gray-300">Éditeur</label>
              <input id="publisher" type="text" value={publisher} onChange={(e) => setPublisher(e.target.value)} className="mt-1 w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" />
            </div>
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-300">Description</label>
              <textarea id="description" rows={4} value={description} onChange={(e) => setDescription(e.target.value)} className="mt-1 w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" />
            </div>

            {/* --- SECTION AVATAR AVEC LE NOUVEAU DESIGN --- */}
            <div>
              <label className="block text-sm font-medium text-gray-300">Avatar du jeu</label>
              <div
                className="mt-2 flex justify-center items-center px-6 pt-5 pb-6 border-2 border-gray-600 border-dashed rounded-md cursor-pointer hover:border-indigo-500 transition-colors"
                onClick={handleChooseFileClick}
              >
                <div className="space-y-1 text-center">
                  {previewUrl ? (
                    <img src={previewUrl} alt="Aperçu de l'avatar" className="mx-auto h-24 w-24 object-cover rounded-md" />
                  ) : (
                    <svg className="mx-auto h-12 w-12 text-gray-500" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
                      <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                  <div className="flex text-sm text-gray-500">
                    <p className="pl-1">
                      {avatar ? avatar.name : "Cliquez pour choisir une image"}
                    </p>
                  </div>
                  {!avatar && <p className="text-xs text-gray-600">PNG, JPG, GIF jusqu'à 10MB</p>}
                </div>
              </div>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                className="hidden"
                accept="image/*"
              />
            </div>

            <div>
              <button type="submit" disabled={isLoading} className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50">
                {isLoading ? 'Création en cours...' : 'Créer le jeu'}
              </button>
            </div>
            {message && <p className={`text-center text-sm mt-4 ${message.startsWith('Erreur') ? 'text-red-400' : 'text-green-400'}`}>{message}</p>}
          </form>
        </div>
      </div>
    </div>
  );
}