// src/app/page.tsx

import Link from 'next/link';

export default function HomePage() {
  return (
    // On change le fond pour un gris très foncé et le texte par défaut en clair
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-900 text-center p-8">
      <div className="max-w-2xl">

        {/* Le titre est maintenant en blanc pour un contraste maximal */}
        <h1 className="text-4xl font-bold tracking-tight text-white sm:text-6xl">
          Bienvenue sur Gaming Advisor 🤖
        </h1>
        {/* Le texte de description est en gris clair pour être plus doux */}
        <p className="mt-6 text-lg leading-8 text-gray-300">
          Votre assistant personnel pour installer n'importe quel jeu de société en un clin d'œil. Posez vos questions, envoyez une photo de la boîte, et laissez-vous guider.
        </p>

        <div className="mt-10 flex items-center justify-center gap-x-6">
          {/* Le bouton principal reste d'une couleur vive (indigo) pour ressortir */}
          <Link
            href="/signup"
            className="rounded-md bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
          >
            Commencer
          </Link>
          {/* Le lien secondaire est maintenant en blanc également */}
          <Link
            href="/login"
            className="text-sm font-semibold leading-6 text-white px-3.5 py-2.5"
          >
            Déjà un compte ? <span aria-hidden="true">→</span>
          </Link>
        </div>

      </div>
    </main>
  );
}