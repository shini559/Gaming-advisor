"use client";

import { useState, useEffect, FormEvent, useRef} from 'react';
import { useRouter } from 'next/navigation';
import { fetchWithAuth } from '@/utils/api';
import Link from 'next/link';

// Le type Message ne change pas
type Message = {
  id: number;
  text: string;
  sender: 'user' | 'bot';
};

export default function ChatPage() {
  const router = useRouter();
  const [isVerified, setIsVerified] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isAiTyping, setIsAiTyping] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
    } else {
      setIsVerified(true);
    }
  }, [router]);

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

      const { response } = await fetchWithAuth(urlWithQuery, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error("L'API du chatbot a renvoyé une erreur");
      }

      const data = await response.json();
      const botResponseText = data.response;

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

  const handleAttachClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      console.log('Fichier sélectionné :', file.name);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    router.push('/login');
  };

  if (!isVerified) {
    // Message de chargement stylisé pour le thème sombre
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-900">
        <p className="text-lg text-gray-400">Vérification...</p>
      </div>
    );
  }

  return (
    // Fond général sombre
    <div className="flex flex-col h-screen bg-gray-900 text-white">
      {/* Header sombre avec bordure discrète */}
      <header className="bg-gray-800 border-b border-gray-700 shadow-md">
  {/* Le conteneur intérieur qui s'aligne avec le reste de la page */}
  <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

    {/* Conteneur Flexbox principal */}
    <div className="flex justify-between items-center h-16">

      {/* 1. Bloc de gauche : Le titre */}
      <div>
        <h1 className="text-xl font-bold text-gray-100">
          Gaming Advisor
        </h1>
      </div>

      {/* 2. Bloc de droite : Les actions */}
      <div className="flex items-center gap-x-4">
        <Link href="/account" className="p-2 text-gray-400 hover:text-white" title="Mon Compte">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </Link>

        <button
            onClick={handleLogout}
            className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md shadow-sm hover:bg-red-500"
        >
            Déconnexion
        </button>
      </div>

    </div>
  </div>
</header>


      {/* Zone de chat principale */}
      <main className="flex-grow p-4 overflow-y-auto">
  <div className="space-y-4">
    {messages.map((message) => (
      <div
        key={message.id}
        className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
      >
        <div
          className={`max-w-xs md:max-w-md p-3 rounded-lg ${
            message.sender === 'user' 
              ? 'bg-indigo-600 text-white' 
              : 'bg-gray-700 text-gray-200' // <-- Ces classes s'appliquent maintenant au bot
          }`}
        >
          <p className="text-sm">{message.text}</p>
        </div>
      </div>
    ))}

    {/* L'indicateur "en train d'écrire" ne change pas */}
    {isAiTyping && (
      <div className="flex justify-start">
        <div className="max-w-xs md:max-w-md p-3 rounded-lg bg-gray-700 text-gray-400">
          <p className="animate-pulse">...</p>
        </div>
      </div>
    )}
  </div>
</main>

      {/* Footer sombre avec bordure */}
      <footer className="bg-gray-800 border-t border-gray-700 p-4">
        <form onSubmit={handleSendMessage} className="flex items-center space-x-3">
          <button type="button" onClick={handleAttachClick} className="p-2 text-gray-400 hover:text-white rounded-full hover:bg-gray-700">
            {/* SVG trombone */}
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" /></svg>
          </button>

          <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" />

          {/* Champ de saisie adapté au thème sombre */}
          <input
            type="text"
            className="flex-grow w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-full focus:outline-none focus:ring-2 focus:ring-indigo-500 text-gray-100 placeholder-gray-400"
            placeholder="Écrivez votre message..."
            value={currentMessage}
            onChange={(e) => setCurrentMessage(e.target.value)}
          />
          <button type="submit" className="p-2 bg-indigo-600 text-white rounded-full hover:bg-indigo-500 transition-colors">
            {/* SVG flèche */}
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" /></svg>
          </button>
        </form>
      </footer>
    </div>
  );
}