// src/app/account/page.tsx
"use client";

import { useState, useEffect, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { fetchWithAuth } from '@/utils/api';
import Link from 'next/link';

export default function AccountPage() {
  const router = useRouter();

  // États pour les informations du profil
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');

  // États pour le changement de mot de passe
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // États pour les retours utilisateur
  const [profileMessage, setProfileMessage] = useState('');
  const [passwordMessage, setPasswordMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  // Au chargement, on récupère les infos via /auth/me
  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const { response } = await fetchWithAuth('https://gameadvisor-api-containerapp.purpleplant-bc5dabd4.francecentral.azurecontainerapps.io/auth/me');
        if (!response.ok) throw new Error('Failed to fetch user data');

        const data = await response.json();
        setEmail(data.mail || '');
        setUsername(data.username || '');
        setFirstName(data.first_name || '');
        setLastName(data.last_name || '');
      } catch (error) {
        console.error(error);
        router.push('/login');
      } finally {
        setIsLoading(false);
      }
    };
    fetchUserData();
  }, [router]);

  const handleProfileUpdate = async (event: FormEvent) => {
    event.preventDefault();
    alert('Fonctionnalité non disponible : endpoint API manquant.');
    setProfileMessage('Cette fonctionnalité n\'est pas encore active.');
  };

  const handlePasswordChange = async (event: FormEvent) => {
    event.preventDefault();
    if (newPassword !== confirmPassword) {
      setPasswordMessage('Les nouveaux mots de passe ne correspondent pas.');
      return;
    }
    alert('Fonctionnalité non disponible : endpoint API manquant.');
    setPasswordMessage('Cette fonctionnalité n\'est pas encore active.');
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-900">
        <p className="text-lg text-gray-400">Chargement de votre compte...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 p-6 sm:p-8 flex items-center justify-center">
      <div className="max-w-3xl w-full mx-auto space-y-8">
        {/* Header (reprise de celui du chat pour la cohérence) */}
        <header className="bg-gray-900 border-b border-b-gray-900 shadow-md fixed top-0 left-0 right-0 z-10">
  <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    {/* On utilise flex et justify-center pour centrer le titre */}
    <div className="flex justify-center items-center h-16">
      <Link href="/chat" title="Retour au Chat">
        <h1 className="text-xl font-bold text-gray-100 cursor-pointer hover:text-gray-300 transition-colors">
          Gaming Advisor
        </h1>
      </Link>
    </div>
  </div>
</header>

        <div className="pt-24"> {/* Padding pour éviter que le contenu ne passe sous le header fixe */}
            <h1 className="text-4xl font-extrabold text-white text-center mb-10">Mon Compte</h1>

            {/* Section 1: Informations du Profil */}
            <div className="bg-gray-800 p-8 rounded-xl shadow-lg border border-gray-700 mb-4">
              <h2 className="text-2xl font-bold text-gray-100 mb-6">Informations du profil</h2>
              <form onSubmit={handleProfileUpdate} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label htmlFor="firstName" className="block text-sm font-medium text-gray-400 mb-1">Prénom</label>
                    <input type="text" id="firstName" value={firstName} onChange={e => setFirstName(e.target.value)} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-indigo-500 focus:border-indigo-500" />
                  </div>
                  <div>
                    <label htmlFor="lastName" className="block text-sm font-medium text-gray-400 mb-1">Nom</label>
                    <input type="text" id="lastName" value={lastName} onChange={e => setLastName(e.target.value)} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-indigo-500 focus:border-indigo-500" />
                  </div>
                </div>
                <div>
                  <label htmlFor="username" className="block text-sm font-medium text-gray-400 mb-1">Nom d'utilisateur</label>
                  <input type="text" id="username" value={username} onChange={e => setUsername(e.target.value)} className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-indigo-500 focus:border-indigo-500" />
                </div>
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-400 mb-1">Adresse e-mail</label>
                  <input type="email" id="email" value={email} onChange={e => setEmail(e.target.value)} required className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-indigo-500 focus:border-indigo-500" />
                </div>
                <button type="submit" className="w-full py-2 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 transition duration-150 ease-in-out">
                  Enregistrer les modifications
                </button>
                {profileMessage && <p className="mt-4 text-center text-sm text-gray-500">{profileMessage}</p>}
              </form>
            </div>

            {/* Section 2: Changer le mot de passe */}
            <div className="bg-gray-800 p-8 rounded-xl shadow-lg border border-gray-700">
              <h2 className="text-2xl font-bold text-gray-100 mb-6">Changer le mot de passe</h2>
              <form onSubmit={handlePasswordChange} className="space-y-6">
                <div>
                  <label htmlFor="currentPassword" className="block text-sm font-medium text-gray-400 mb-1">Mot de passe actuel</label>
                  <input type="password" id="currentPassword" value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} required className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-red-500 focus:border-red-500" />
                </div>
                <div>
                  <label htmlFor="newPassword" className="block text-sm font-medium text-gray-400 mb-1">Nouveau mot de passe</label>
                  <input type="password" id="newPassword" value={newPassword} onChange={e => setNewPassword(e.target.value)} required className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-red-500 focus:border-red-500" />
                </div>
                <div>
                  <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-400 mb-1">Confirmer le nouveau mot de passe</label>
                  <input type="password" id="confirmPassword" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-red-500 focus:border-red-500" />
                </div>
                <button type="submit" className="w-full py-2 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 transition duration-150 ease-in-out">
                  Changer le mot de passe
                </button>
                {passwordMessage && <p className="mt-4 text-center text-sm text-gray-500">{passwordMessage}</p>}
              </form>
            </div>
        </div>
      </div>
    </div>
  );
}