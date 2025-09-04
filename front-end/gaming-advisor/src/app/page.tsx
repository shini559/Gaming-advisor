"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { SparklesIcon, PuzzlePieceIcon, UserGroupIcon } from '@heroicons/react/24/outline';

export default function HomePage() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // On vérifie si un token existe dans le localStorage
    const token = localStorage.getItem('access_token');
    if (token) {
      setIsLoggedIn(true);
    }
    setIsLoading(false);
  }, []);

  return (
    <div className="flex flex-col min-h-screen bg-gray-900 text-white">
      <main className="flex-grow flex flex-col items-center justify-center p-8">
        <div className="max-w-4xl text-center">

          {/* Section de présentation  */}
          <h1 className="text-5xl font-extrabold tracking-tight sm:text-6xl mb-6">
            Gaming Advisor 🤖
          </h1>
          <p className="text-xl text-gray-300 leading-relaxed mb-10">
            Votre copilote IA pour les jeux de société. Oubliez les règles complexes et les setups interminables, Gaming Advisor vous guide pas à pas.
          </p>

          {/* Boutons d'action */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16 h-12">
            {!isLoading && (
              isLoggedIn ? (
                <Link
                  href="/games"
                  className="w-full sm:w-auto rounded-md bg-teal-600 px-8 py-3 text-lg font-semibold text-white shadow-lg hover:bg-teal-500 transition"
                >
                  Accéder à mes jeux
                </Link>
              ) : (
                <>
                  <Link
                    href="/signup"
                    className="w-full sm:w-auto rounded-md bg-indigo-600 px-8 py-3 text-lg font-semibold text-white shadow-lg hover:bg-indigo-500 transition"
                  >
                    Commencer à discuter
                  </Link>
                  <Link
                    href="/login"
                    className="w-full sm:w-auto text-lg font-semibold leading-6 text-gray-300 hover:text-white transition"
                  >
                    Déjà un compte ? <span aria-hidden="true">→</span>
                  </Link>
                </>
              )
            )}
          </div>

          {/* Section des avantages / cas d'usage */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-left mt-12">
            <div className="bg-gray-800 p-6 rounded-lg shadow-xl border border-gray-700">
              <SparklesIcon className="h-10 w-10 text-indigo-400 mb-4" />
              <h3 className="text-xl font-bold mb-2">Règles simplifiées</h3>
              <p className="text-gray-400">
                Fini les manuels de 50 pages ! Posez vos questions, Gaming Advisor vous explique les règles complexes en un instant.
              </p>
            </div>
            <div className="bg-gray-800 p-6 rounded-lg shadow-xl border border-gray-700">
              <PuzzlePieceIcon className="h-10 w-10 text-teal-400 mb-4" />
              <h3 className="text-xl font-bold mb-2">Setup rapide</h3>
              <p className="text-gray-400">
                Envoyez une photo de votre boîte de jeu et recevez des instructions pas à pas pour la mise en place.
              </p>
            </div>
            <div className="bg-gray-800 p-6 rounded-lg shadow-xl border border-gray-700">
              <UserGroupIcon className="h-10 w-10 text-orange-400 mb-4" />
              <h3 className="text-xl font-bold mb-2">Conseils personnalisés</h3>
              <p className="text-gray-400">
                Besoin d'une stratégie ? Gaming Advisor vous donne des astuces pour optimiser votre jeu et surprendre vos amis.
              </p>
            </div>
          </div>
        </div>
      </main>

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