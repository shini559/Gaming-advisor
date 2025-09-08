"use client";

import { useState, useEffect, FormEvent, useRef } from 'react';
import {useRouter, useParams, useSearchParams} from 'next/navigation';
import { fetchWithAuth, uploadFileWithAuth} from '@/utils/api';
import Link from 'next/link';

// --- TYPES ---
type Message = {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  feedback?: 'positive' | 'negative' | null;
};

type UploadStatus = {
  status: 'processing' | 'completed' | 'failed';
  progress: number;
  totalImages?: number;
  imageUrls?: string[];
};

export default function ChatPage() {
  // --- HOOKS ---
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const conversationId = params.conversationId as string;
  const gameId = searchParams.get('gameId');
  const isUserOwner = searchParams.get('owner') === 'true';
  const fileInputRef = useRef<HTMLInputElement>(null);


  // --- ÉTATS ---
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isAiTyping, setIsAiTyping] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [uploadProgress, setUploadProgress] = useState<Record<string, UploadStatus>>({});

  // --- EFFETS ---
  useEffect(() => {
    if (!conversationId) return;

    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }

    const loadChatHistory = async () => {
      setIsLoading(true);
      try {
        const { response } = await fetchWithAuth(`https://gameadvisor-api-containerapp.purpleplant-bc5dabd4.francecentral.azurecontainerapps.io/chat/conversations/${conversationId}/history?limit=100`);
        if (!response.ok) throw new Error("Impossible de charger l'historique de la conversation.");

        const historyData = await response.json();
        const formattedMessages: Message[] = historyData.messages.map((msg: any) => {
          let feedbackStatus: 'positive' | 'negative' | null = null;
          if (msg.is_useful === true) feedbackStatus = 'positive';
          else if (msg.is_useful === false) feedbackStatus = 'negative';

          return {
            id: msg.id,
            text: msg.content,
            sender: msg.role === 'assistant' ? 'bot' : 'user',
            feedback: feedbackStatus,
          };
        });
        setMessages(formattedMessages);
      } catch (error) {
        console.error("Erreur lors du chargement de l'historique:", error);
      } finally {
        setIsLoading(false);
      }
    };

    loadChatHistory();
  }, [conversationId, router]);

  // --- GESTIONNAIRES D'ÉVÉNEMENTS ---
  const handleSendMessage = async (event: FormEvent) => {
    event.preventDefault();
    if (currentMessage.trim() === '' || isAiTyping) return;

    const tempId = `temp-${Date.now()}`;
    const userMessage: Message = { id: tempId, text: currentMessage, sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    setCurrentMessage('');
    setIsAiTyping(true);

    try {
      const { response } = await fetchWithAuth('https://gameadvisor-api-containerapp.purpleplant-bc5dabd4.francecentral.azurecontainerapps.io/chat/messages', {
        method: 'POST',
        body: JSON.stringify({ conversation_id: conversationId, content: currentMessage }),
      });
      if (!response.ok) throw new Error("L'API a renvoyé une erreur");

      const data = await response.json();

      setMessages(prev => prev.map(msg => msg.id === tempId ? { ...msg, id: data.user_message.id } : msg));

      const botMessage: Message = {
        id: data.assistant_message.id,
        text: data.assistant_message.content,
        sender: 'bot',
        feedback: null,
      };
      setMessages(prev => [...prev, botMessage]);

    } catch (error) {
      const errorMessage: Message = { id: `err-${Date.now()}`, text: "Désolé, une erreur est survenue.", sender: 'bot' };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsAiTyping(false);
    }
  };

  const handleFeedback = async (messageId: string, feedbackType: 'positive' | 'negative') => {
    setMessages(prev => prev.map(msg => msg.id === messageId ? { ...msg, feedback: feedbackType } : msg));
    try {
      await fetchWithAuth(`https://gameadvisor-api-containerapp.purpleplant-bc5dabd4.francecentral.azurecontainerapps.io/chat/messages/${messageId}/feedback`, {
        method: 'POST', body: JSON.stringify({ feedback_type: feedbackType }),
      });
    } catch (error) {
      console.error("Erreur lors de l'envoi du feedback:", error);
      setMessages(prev => prev.map(msg => msg.id === messageId ? { ...msg, feedback: null } : msg));
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
      setUploadProgress(prev => ({ ...prev, [batchId]: { status: 'processing', progress: 0, totalImages: files.length } }));
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
          setUploadProgress(prev => {
            const currentBatch = prev[batchId];
            return {
              ...prev,
              [batchId]: {
                ...currentBatch,
                status: data.status,
                progress: data.completion_percentage,
                imageUrls: data.status === 'completed' ? data.image_urls : currentBatch.imageUrls,
              },
            };
          });
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
    }, 2000);
  };

  const handleAttachClick = () => fileInputRef.current?.click();

  const handleLogout = () => {
    localStorage.clear();
    router.push('/login');
  };

  if (isLoading) {
    return <div className="flex h-screen items-center justify-center bg-gray-900 text-white">Chargement de la discussion...</div>;
  }

  // --- JSX ---
  return (
    <div className="flex flex-col h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 border-b border-gray-700 shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center h-16">
                <Link href="/games"><h1 className="text-xl font-bold text-gray-100 cursor-pointer hover:text-gray-300 transition-colors">Gaming Advisor</h1></Link>
                <div className="flex-grow"></div>
                <div className="flex items-center gap-x-4">
                    <Link href="/account" className="p-2 text-gray-400 hover:text-white" title="Mon Compte"><svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg></Link>
                    <button onClick={handleLogout} className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-500">Déconnexion</button>
                </div>
            </div>
        </div>
      </header>

      <main className="flex-grow p-4 overflow-y-auto">
        <div className="space-y-4">
          {messages.map((message) => (
            <div key={message.id}>
              <div className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-xs md:max-w-md p-3 rounded-lg ${message.sender === 'user' ? 'bg-indigo-600 text-white' : 'bg-gray-700 text-gray-200'}`}>
                  <p className="text-sm">{message.text}</p>
                </div>
              </div>
              {message.sender === 'bot' && (
                <div className="flex justify-start mt-2 ml-2 space-x-2">
                  <button onClick={() => handleFeedback(message.id, 'positive')} disabled={message.feedback === 'positive'} className={`p-1 rounded-full ${message.feedback === 'positive' ? 'text-indigo-400 cursor-not-allowed' : 'text-gray-500 hover:text-indigo-400'}`}><svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.562 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.821 2.333l-.414.622a2 2 0 00-.342 1.258V10.333z" /></svg></button>
                  <button onClick={() => handleFeedback(message.id, 'negative')} disabled={message.feedback === 'negative'} className={`p-1 rounded-full ${message.feedback === 'negative' ? 'text-red-400 cursor-not-allowed' : 'text-gray-500 hover:text-red-400'}`}><svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M18 9.5a1.5 1.5 0 11-3 0v-6a1.5 1.5 0 013 0v6zM14 9.667v-5.43a2 2 0 00-1.106-1.79l-.05-.025A4 4 0 0011.057 2H5.642a2 2 0 00-1.962 1.608l-1.2 6A2 2 0 004.438 12H8v4a2 2 0 002 2 1 1 0 001-1v-.667a4 4 0 01.821-2.333l.414.622a2 2 0 00.342-1.258V9.667z" /></svg></button>
                </div>
              )}
            </div>
          ))}
          {isAiTyping && (<div className="flex justify-start"><div className="max-w-xs md:max-w-md p-3 rounded-lg bg-gray-700 text-gray-400"><p className="animate-pulse">...</p></div></div>)}
        </div>
        <div className="fixed bottom-24 right-8 w-80 space-y-4">
          {Object.entries(uploadProgress).map(([batchId, { status, progress, totalImages, imageUrls }]) => (
            <div key={batchId} className="bg-gray-700 p-4 rounded-lg shadow-lg border border-gray-600">
              {status === 'processing' && (<><p className="text-sm font-medium text-gray-200 mb-2">Traitement de {totalImages} images... ({Math.round(progress || 0)}%)</p><div className="w-full bg-gray-600 rounded-full h-2.5"><div className="bg-indigo-600 h-2.5 rounded-full" style={{ width: `${progress || 0}%` }}></div></div></>)}
              {status === 'completed' && (<div><p className="text-sm font-medium text-green-400 mb-3">✅ Traitement terminé. Images ajoutées :</p><div className="grid grid-cols-3 gap-2">{imageUrls?.map((url, index) => (<img key={index} src={url} alt={`Image traitée ${index + 1}`} className="w-full h-20 object-cover rounded-md"/>))}</div></div>)}
              {status === 'failed' && (<p className="text-sm font-medium text-red-400">❌ Le traitement a échoué.</p>)}
            </div>
          ))}
        </div>
      </main>

      <footer className="bg-gray-800 border-t border-gray-700 p-4">
        <form onSubmit={handleSendMessage} className="flex items-center space-x-3">
          {isUserOwner && (<button type="button" onClick={handleAttachClick} className="p-2 text-gray-400 hover:text-white rounded-full hover:bg-gray-700"><svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" /></svg></button>)}
          <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" multiple />
          <input type="text" disabled={!conversationId || isAiTyping} className="flex-grow w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-full focus:outline-none focus:ring-2 focus:ring-indigo-500 text-gray-100 placeholder-gray-400"
            placeholder={!conversationId ? "Chargement..." : "Écrivez votre message..."} value={currentMessage} onChange={(e) => setCurrentMessage(e.target.value)} />
          <button type="submit" disabled={!conversationId || isAiTyping} className="p-2 bg-indigo-600 text-white rounded-full hover:bg-indigo-500 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" /></svg>
          </button>
        </form>
      </footer>
    </div>
  );
}