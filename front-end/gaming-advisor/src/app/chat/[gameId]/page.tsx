"use client";

import { useState, useEffect, FormEvent, useRef } from 'react';
import { useRouter, useParams, useSearchParams } from 'next/navigation';
import { fetchWithAuth, uploadFileWithAuth } from '@/utils/api';
import Link from 'next/link';

// --- TYPES ---
type Message = {
  id: number;
  text: string;
  sender: 'user' | 'bot';
};

type UploadStatus = {
  status: 'processing' | 'completed' | 'failed';
  progress: number;
  totalImages?: number;
};

export default function ChatPage() {
  // --- HOOKS ---
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // --- LOGIQUE DE LA PAGE ---
  const gameId = params.gameId as string;
  // On détermine si l'utilisateur est le propriétaire directement depuis l'URL
  const isUserOwner = searchParams.get('owner') === 'true';
  const gameTitle = searchParams.get('title');



  // --- ÉTATS ---
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isAiTyping, setIsAiTyping] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<Record<string, UploadStatus>>({});




  // --- EFFETS ---
  useEffect(() => {
  const token = localStorage.getItem('access_token');
  if (!token) {
    router.push('/login');
    return;
  }

  const initializeConversation = async () => {
    try {
      // 1. On récupère les conversations pour le jeu
      const { response: convResponse } = await fetchWithAuth(`https://gameadvisor-api-containerapp.purpleplant-bc5dabd4.francecentral.azurecontainerapps.io/chat/games/${gameId}/conversations`);
      const conversationsData = await convResponse.json();
      let currentConversationId: string | null = null;

      if (convResponse.ok && conversationsData.conversations.length > 0) {
        // Cas A : Une conversation existe
        currentConversationId = conversationsData.conversations[0].id;
        console.log("conv exist currentconvid : ",currentConversationId)
        setConversationId(currentConversationId);
      } else {
        // Cas B : On en crée une nouvelle
        const { response: createConvResponse } = await fetchWithAuth('https://gameadvisor-api-containerapp.purpleplant-bc5dabd4.francecentral.azurecontainerapps.io/chat/conversations', {
          method: 'POST',
          body: JSON.stringify({ game_id: gameId, title: gameTitle }),
        });
        const newConversation = await createConvResponse.json();
        if (!createConvResponse.ok) throw new Error('Impossible de créer une conversation.');
        currentConversationId = newConversation.id;
        console.log("conv not exist currentconvid : ",currentConversationId)
        setConversationId(currentConversationId);
      }

      // 2. Si on a un ID de conversation, on charge son historique
      if (currentConversationId) {
        const { response: historyResponse } = await fetchWithAuth(`https://gameadvisor-api-containerapp.purpleplant-bc5dabd4.francecentral.azurecontainerapps.io/chat/conversations/${currentConversationId}/history`);
        if (!historyResponse.ok) {
          throw new Error("Impossible de charger l'historique de la conversation.");
        }
        const historyData = await historyResponse.json();

        // On transforme les messages de l'API au format de notre front-end
        const formattedMessages: Message[] = historyData.messages.map((msg: any) => ({
          id: msg.id,
          text: msg.content,
          sender: msg.role,
        }));

        setMessages(formattedMessages);
      }

    } catch (error) {
      console.error("Erreur d'initialisation de la conversation:", error);
    } finally {
      setIsLoading(false);
    }
  };

  initializeConversation();
}, [router, gameId, gameTitle]);

  // --- GESTIONNAIRES D'ÉVÉNEMENTS ---
  const handleSendMessage = async (event: FormEvent) => {
    event.preventDefault();
    if (currentMessage.trim() === '' || !conversationId) return;

    const userMessage: Message = { id: Date.now(), text: currentMessage, sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    setCurrentMessage('');
    setIsAiTyping(true);

    try {
      const { response } = await fetchWithAuth('https://gameadvisor-api-containerapp.purpleplant-bc5dabd4.francecentral.azurecontainerapps.io/chat/messages', {
        method: 'POST',
        body: JSON.stringify({ conversation_id: conversationId, content: userMessage.text }),
      });
      if (!response.ok) throw new Error("L'API a renvoyé une erreur");
      const data = await response.json();
      const botResponseText = data.assistant_message.content;

      const botMessage: Message = {
      id: Date.now() + 1,
      text: botResponseText,
      sender: 'bot'
    };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage: Message = { id: Date.now() + 1, text: "Désolé, une erreur est survenue.", sender: 'bot' };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsAiTyping(false);
    }
  };

const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    try {
      const uploadUrl = `https://gameadvisor-api-containerapp.purpleplant-bc5dabd4.francecentral.azurecontainerapps.io/images/games/${gameId}/batch-upload`;
      const response = await uploadFileWithAuth(uploadUrl, files);
      const data = await response.json();

      if (!response.ok) throw new Error(data.detail || "Erreur lors de l'envoi.");

      const batchId = data.batch_id;

      // On initialise la progression
      setUploadProgress(prev => ({
        ...prev,
        [batchId]: { status: 'processing', progress: 0, totalImages: files.length }
      }));

      pollBatchStatus(batchId);

    } catch (err: any) {
      console.error("L'envoi a échoué:", err.message);
    }
  };

  const pollBatchStatus = (batchId: string) => {
    const intervalId = setInterval(async () => {
      try {
        const { response } = await fetchWithAuth(`https://gameadvisor-api-containerapp.purpleplant-bc5dabd4.francecentral.azurecontainerapps.io/images/batches/${batchId}/status`);
        const data = await response.json();

        if (response.ok) {
          setUploadProgress(prev => ({
            ...prev,
            [batchId]: { ...prev[batchId], status: data.status, progress: data.completion_percentage },
          }));

          // On arrête le polling
          if (data.status === 'completed' || data.status === 'failed') {
            clearInterval(intervalId);
          }
        } else {
          clearInterval(intervalId);
          setUploadProgress(prev => ({ ...prev, [batchId]: { ...prev[batchId], status: 'failed' } }));
        }
      } catch (error) {
        clearInterval(intervalId);
        setUploadProgress(prev => ({ ...prev, [batchId]: { ...prev[batchId], status: 'failed' } }));
      }
    }, 5000);
  };

  const handleAttachClick = () => fileInputRef.current?.click();
  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_id');
    router.push('/login');
  };

  if (isLoading) {
    return <div className="flex h-screen items-center justify-center bg-gray-900 text-white">Initialisation de la conversation...</div>;
  }

  // --- JSX ---
  return (
    <div className="flex flex-col h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
                <Link href="/games">
                    <h1 className="text-xl font-bold text-gray-100 cursor-pointer hover:text-gray-300 transition-colors">
                        Gaming Advisor
                    </h1>
                </Link>
                <div className="flex items-center gap-x-4">
                    <Link href="/account" className="p-2 text-gray-400 hover:text-white" title="Mon Compte">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
                    </Link>
                    <button onClick={handleLogout} className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-500">
                        Déconnexion
                    </button>
                </div>
            </div>
        </div>
      </header>

      {/* Main */}
      <main className="flex-grow p-4 overflow-y-auto">
        <div className="space-y-4">
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-xs md:max-w-md p-3 rounded-lg ${message.sender === 'user' ? 'bg-indigo-600 text-white' : 'bg-gray-700 text-gray-200'}`}>
                <p className="text-sm">{message.text}</p>
              </div>
            </div>
          ))}
          {isAiTyping && (
            <div className="flex justify-start">
              <div className="max-w-xs md:max-w-md p-3 rounded-lg bg-gray-700 text-gray-400">
                <p className="animate-pulse">...</p>
              </div>
            </div>
          )}
        </div>
       {/* Section pour les notifications de progression */}
<div className="fixed bottom-24 right-8 w-72 space-y-4">
  {Object.entries(uploadProgress).map(([batchId, { status, progress, totalImages }]) => (
    <div key={batchId} className="bg-gray-700 p-3 rounded-lg shadow-lg border border-gray-600">

      {/* Affichage conditionnel en fonction du statut */}
      {status === 'processing' && (
        <>
          <p className="text-sm font-medium text-gray-200 mb-2">
            Traitement de {totalImages} images...
          </p>
          <div className="w-full bg-gray-600 rounded-full h-2.5">
            <div
              className="bg-indigo-600 h-2.5 rounded-full transition-all duration-300"
              style={{ width: `${progress || 0}%` }}
            ></div>
          </div>
        </>
      )}

      {status === 'completed' && (
        <p className="text-sm font-medium text-green-400">
          ✅ Traitement terminé ({totalImages} images traitées).
        </p>
      )}

      {status === 'failed' && (
        <p className="text-sm font-medium text-red-400">
          ❌ Le traitement a échoué.
        </p>
      )}

    </div>
  ))}
</div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 border-t border-gray-700 p-4">
        <form onSubmit={handleSendMessage} className="flex items-center space-x-3">
          {isUserOwner && (
            <button type="button" onClick={handleAttachClick} className="p-2 text-gray-400 hover:text-white rounded-full hover:bg-gray-700">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" /></svg>
            </button>
          )}
          <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" multiple />
          <input type="text" className="flex-grow w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-full focus:outline-none focus:ring-2 focus:ring-indigo-500 text-gray-100 placeholder-gray-400"
            placeholder="Écrivez votre message..." value={currentMessage} onChange={(e) => setCurrentMessage(e.target.value)} />
          <button type="submit" className="p-2 bg-indigo-600 text-white rounded-full hover:bg-indigo-500 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" /></svg>
          </button>
        </form>
      </footer>
    </div>
  );
}