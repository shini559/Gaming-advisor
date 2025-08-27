"use client";
import { useState } from 'react';

export default function SignupPage() {

  const [nom, setNom] = useState('');
  const [prenom, setPrenom] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

    // Fonction pour gérer la soumission du formulaire
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError('');

    // Étape 1 : Vérification côté client (front-end)
    if (password !== confirmPassword) {
      setError("Les mots de passe ne correspondent pas.");
      return; // On arrête l'exécution
    }

    setIsLoading(true); // Début du chargement

    // Étape 2 : Appel à l'API
    try {
      const response = await fetch('https://gameadvisor-api-containerapp.purpleplant-bc5dabd4.francecentral.azurecontainerapps.io/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
       body: JSON.stringify({
          first_name: prenom,
          last_name: nom,
          username,
          email,
          password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        // L'API renvoie une erreur (ex: email déjà pris)
        throw new Error(data.message || 'Une erreur est survenue lors de l\'inscription.');
      }

      console.log('Inscription réussie !', data);
      // TODO: Rediriger l'utilisateur vers la page de connexion ou directement au chat

    } catch (err: any) {
      console.error(err);
      setError(err.message);
    } finally {
      setIsLoading(false); // Fin du chargement
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-100">
      <div className="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md">
        <h1 className="text-2xl efont-bold text-center text-gray-900">
          Créer un compte
        </h1>
        <form onSubmit={handleSubmit} className="space-y-6">

           <div className="flex gap-4">
            <div className="w-1/2">
              <label htmlFor="prenom" className="block text-sm font-medium text-gray-700">Prénom</label>
              <input id="prenom" type="text" required value={prenom} onChange={(e) => setPrenom(e.target.value)} className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="John"/>
            </div>
            <div className="w-1/2">
              <label htmlFor="nom" className="block text-sm font-medium text-gray-700">Nom</label>
              <input id="nom" type="text" required value={nom} onChange={(e) => setNom(e.target.value)} className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Doe"/>
            </div>
          </div>

          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700">Nom d'utilisateur</label>
            <input id="username" type="text" required value={username} onChange={(e) => setUsername(e.target.value)} className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="johndoe123"
            />
          </div>

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

          {/* Champ de confirmation du mot de passe */}
          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700" >Confirmer le mot de passe</label>
            <input id="confirmPassword" type="password" required value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" placeholder="********" />
          </div>

          {/* Affichage du message d'erreur */}
          {error && (
            <p className="text-sm text-center text-gray-900">{error}</p>
          )}


          {/* Bouton d'inscription */}
          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="w-full px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              {isLoading ? 'Création du compte...' : 'S\'inscrire'}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}