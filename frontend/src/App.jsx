import { useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import ChatBox from "./components/ChatBox";
import ResponseCard from "./components/ResponseCard";
import { sendMessage, createSession, getSessions, getSession } from "./services/api";

function App() {
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [recentChats, setRecentChats] = useState([]);

  // Create session and fetch history on load
  useEffect(() => {
    const initApp = async () => {
      try {
        const sessionRes = await createSession();
        setSessionId(sessionRes.session_id);
        fetchSidebarSessions();
      } catch (err) {
        console.error("Failed to initialize:", err);
      }
    };
    initApp();
  }, []);

  // Helper to fetch sidebar data
  const fetchSidebarSessions = async () => {
    try {
      const sessions = await getSessions();
      setRecentChats(sessions);
    } catch (err) {
      console.error("Failed to fetch sessions:", err);
    }
  };

  // Handle clicking an old chat from the sidebar
  const handleSelectChat = async (id) => {
    try {
      const data = await getSession(id);
      setSessionId(id);
      
      // Reconstruct the message UI from the database history
      const loadedMessages = [];
      data.chat_history.forEach((turn) => {
        loadedMessages.push({ type: "user", text: turn.query });
        loadedMessages.push({ 
          type: "assistant", 
          // Use full_data if available, otherwise fallback gracefully
          data: turn.full_data || { 
            overview: turn.response, 
            research_insights: [], 
            clinical_trials: [], 
            sources: [] 
          } 
        });
      });
      setMessages(loadedMessages);
    } catch (err) {
      console.error("Failed to load chat history:", err);
    }
  };

  // Send message
  const handleSend = async (query) => {
    if (!query || loading) return;

    const userMessage = { type: "user", text: query };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const res = await sendMessage({
        session_id: sessionId,
        query: query,
      });

      const botMessage = {
        type: "assistant",
        data: res.data || {
          overview: res.message,
          research_insights: [],
          clinical_trials: [],
          sources: [],
        },
      };

      setMessages((prev) => [...prev, botMessage]);
      setSessionId(res.session_id);
      
      // Update the sidebar list so the new query appears instantly
      fetchSidebarSessions();

    } catch (err) {
      console.error("Error:", err);
      setMessages((prev) => [
        ...prev,
        {
          type: "assistant",
          data: {
            overview: "Something went wrong. Please try again.",
            research_insights: [],
            clinical_trials: [],
            sources: [],
          },
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // New chat
  const handleNewChat = async () => {
    try {
      const res = await createSession();
      setSessionId(res.session_id);
      setMessages([]);
      fetchSidebarSessions();
    } catch (err) {
      console.error("Failed to create new chat:", err);
    }
  };

  return (
    <div className="flex h-screen bg-[#0b1220] text-gray-100">
      
      <Sidebar 
        onNewChat={handleNewChat} 
        recentChats={recentChats}
        onSelectChat={handleSelectChat}
        currentSessionId={sessionId}
      />

      <div className="flex flex-col flex-1">
        
        <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
          {messages.map((msg, idx) => {
            if (msg.type === "user") {
              return (
                <div key={idx} className="flex justify-end">
                  <div className="bg-emerald-500 text-black px-4 py-2 rounded-xl max-w-md">
                    {msg.text}
                  </div>
                </div>
              );
            }

            if (msg.type === "assistant") {
              return <ResponseCard key={idx} data={msg.data} />;
            }

            return null;
          })}

          {loading && (
            <div className="text-sm text-emerald-400 animate-pulse font-medium">
              🧠 Analyzing medical literature and clinical trials...
            </div>
          )}
        </div>

        <div className="border-t border-gray-800 p-4">
          <ChatBox onSend={handleSend} disabled={loading} />
        </div>
      </div>
    </div>
  );
}

export default App;