"use client";
import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
    // State pour stocker les informations du formulaire
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const router = useRouter();

    // Fonction pour gérer la soumission du formulaire
    const handleSubmit = async (event: React.FormEvent) => {
  event.preventDefault();
  setIsLoading(true);
  setError('');

  const formData = new URLSearchParams();
  formData.append('grant_type', 'password'); // Champ requis par la documentation
  formData.append('username', email);
  formData.append('password', password);
  formData.append('scope', ''); // Champ requis par la documentation
  formData.append('client_id', ''); // Champ requis par la documentation
  formData.append('client_secret', ''); // Champ requis par la documentation

  try {
    const response = await fetch('https://gameadvisor-api-containerapp.purpleplant-bc5dabd4.francecentral.azurecontainerapps.io/auth/login', {
      method: 'POST',
      headers: {
        // NOUVEAU: Le Content-Type correct
        'Content-Type': 'application/x-www-form-urlencoded',
      },

      body: formData,
    });

        // On attend la réponse de l'API
       const data = await response.json();

      if (!response.ok) {
        // Si l'API renvoie une erreur (ex: 401, 404), on la traite ici
        // On utilise le message de l'API s'il existe, sinon un message par défaut
        throw new Error(data.message || 'Email ou mot de passe incorrect.');
      }

      // 1. On stocke le token d'accès dans le sessionStorage

      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);


      console.log('Connexion réussie, redirection...');

      // 2. On redirige l'utilisateur vers la page de chat
      router.push('/chat');
      // Si tout s'est bien passé
      console.log('Connexion réussie !', data);


  } catch (err: any) {
    console.error(err);
    setError(err.message);
  } finally {
    setIsLoading(false);
  }
};

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-100">
      <div className="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md">
        <h1 className="text-2xl font-bold text-center text-gray-900">
          Se connecter
        </h1>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Champ pour l'Email */}
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-700"
            >
              Adresse e-mail
            </label>
            <input
              id="email"
              name="email"
              type="email"
              required
              className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="vous@exemple.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          {/* Champ pour le Mot de passe */}
          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-gray-700"
            >
              Mot de passe
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="********"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
            />
          </div>
             {/* NOUVEAU: Affichage du message d'erreur s'il y en a un */}
          {error && (
            <p className="text-sm text-center text-gray-900">{error}</p>
          )}

          {/* Bouton de connexion */}
          <div>
            <button
              type="submit"
              className="w-full px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Se connecter
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}