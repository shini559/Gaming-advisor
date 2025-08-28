// Fichier: src/app/chat/page.tsx

"use client";

import { useState, useEffect, FormEvent, useRef} from 'react';
import { useRouter } from 'next/navigation';
// On importe notre client API
import { fetchWithAuth } from '@/utils/api';


// Le type Message ne change pas
type Message = {
  id: number;
  text: string;
  sender: 'user' | 'bot';
};


export default function ChatPage() {
  const router = useRouter(); // On initialise le router pour la redirection
  // État pour gérer le chargement de la vérification
  const [isVerified, setIsVerified] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  // On crée une référence pour notre input de fichier
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isAiTyping, setIsAiTyping] = useState(false);

  // Le hook useEffect pour la vérification
  useEffect(() => {
    // On cherche le token dans le localStorage
    const token = localStorage.getItem('access_token');
    // Si le token n'existe pas, on redirige vers la page de connexion
    if (!token) {
      router.push('/login');
    } else {
      // Si le token existe, l'utilisateur est autorisé. On peut afficher la page.
      setIsVerified(true);
    }
  }, [router]); // L'effet se redéclenchera si le router change

   // MODIFIÉ: La fonction d'envoi de message pour appeler la VRAIE API
  const handleSendMessage = async (event: FormEvent) => {
    event.preventDefault();
    if (currentMessage.trim() === '' || isAiTyping) return;

    const userMessage: Message = {
      id: Date.now(),
      text: currentMessage,
      sender: 'user',
    };
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setCurrentMessage('');
    setIsAiTyping(true);

    try {


      const endpoint = 'https://gameadvisor-api-containerapp.purpleplant-bc5dabd4.francecentral.azurecontainerapps.io/test-delay';
    const messageParam = encodeURIComponent(userMessage.text);
    const urlWithQuery = `${endpoint}?message=${messageParam}`;

    // 2. On appelle fetchWithAuth avec la nouvelle URL,
   const { response } = await fetchWithAuth(urlWithQuery, {
      method: 'POST',
    });

      if (!response.ok) {
        throw new Error("L'API du chatbot a renvoyé une erreur");
      }

      const data = await response.json();

      // 2. On extrait la réponse

      const botResponseText = data.reply;

      const botMessage: Message = {
        id: Date.now() + 1,
        text: botResponseText,
        sender: 'bot',
      };

      setMessages(prevMessages => [...prevMessages, botMessage]);

    } catch (error) {
      console.error("Erreur lors de l'appel à l'API du chatbot:", error);
      const errorMessage: Message = {
        id: Date.now() + 1,
        text: "Désolé, une erreur est survenue.",
        sender: 'bot',
      };
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setIsAiTyping(false);
    }
  };

  //  Fonction pour déclencher le clic sur l'input de fichier
  const handleAttachClick = () => {
    // On utilise la référence pour cliquer sur l'input caché
    fileInputRef.current?.click();
  };

  // NOUVEAU: Fonction qui s'exécute quand un fichier est sélectionné
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]; // On récupère le premier fichier
    if (file) {
      // Pour l'instant, on affiche juste son nom dans la console
      console.log('Fichier sélectionné :', file.name);
      // TODO: Logique pour prévisualiser l'image ou envoyer le fichier
    }
  };

  const handleLogout = () => {
    // On supprime les tokens du stockage
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');

    // On redirige vers la page de connexion
    router.push('/login');
  };

   //  On n'affiche le contenu de la page QUE si la vérification est passée
  if (!isVerified) {
    // On peut afficher un message de chargement ou simplement rien
    return
  }


  return (
    <div className="flex flex-col h-screen bg-gray-100">
      <header className="bg-white shadow-md p-4">
        <h1 className="text-xl font-bold text-gray-800 text-center">Gaming Advisor</h1>
        <button onClick={handleLogout}
                className={"px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"}
                >Déconnexion
        </button>
      </header>

      <main className="flex-grow p-4 overflow-y-auto">
        <div className="space-y-4">
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-xs md:max-w-md p-3 rounded-lg ${message.sender === 'user' ? 'bg-indigo-500 text-white' : 'bg-white text-gray-800'}`}>
                <p>{message.text}</p>
              </div>
            </div>
          ))}

          {/* Indicateur "en train d'écrire" */}
          {isAiTyping && (
            <div className="flex justify-start">
              <div className="max-w-xs md:max-w-md p-3 rounded-lg bg-white text-gray-500">
                <p className="animate-pulse">...</p>
              </div>
            </div>
          )}
        </div>
      </main>

      <footer className="bg-white border-t border-gray-200 p-4">
        {/* L'attribut onSubmit est maintenant sur le footer pour englober l'input de fichier */}
        <form onSubmit={handleSendMessage} className="flex items-center space-x-2">
          {/* NOUVEAU: On connecte le bouton à notre fonction handleAttachClick */}
          <button type="button" onClick={handleAttachClick} className="p-2 text-gray-500 hover:text-indigo-600 rounded-full hover:bg-gray-100">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
            </svg>
          </button>

          {/* NOUVEAU: L'input de type "file", caché mais fonctionnel */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            className="hidden" // Classe Tailwind pour le cacher
          />

          <input
            type="text"
            className="flex-grow w-full px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-indigo-400 text-gray-900"
            placeholder="Écrivez votre message..."
            value={currentMessage}
            onChange={(e) => setCurrentMessage(e.target.value)}
          />
          <button type="submit" className="p-2 bg-indigo-600 text-white rounded-full hover:bg-indigo-700">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
        </form>
      </footer>
    </div>
  );
}