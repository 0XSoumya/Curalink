import { useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import ChatBox from "./components/ChatBox";
import ResponseCard from "./components/ResponseCard";
import { sendMessage, createSession } from "./services/api";

function App() {
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(false);

  // Create session on load
  useEffect(() => {
    const initSession = async () => {
      const res = await createSession();
      setSessionId(res.session_id);
    };
    initSession();
  }, []);

  // Send message
  const handleSend = async (query) => {
    if (!query || loading) return;

    const userMessage = {
      type: "user",
      text: query,
    };

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
    const res = await createSession();
    setSessionId(res.session_id);
    setMessages([]);
  };

  return (
    <div className="flex h-screen bg-[#0b1220] text-gray-100">
      
      {/* Sidebar */}
      <Sidebar onNewChat={handleNewChat} />

      {/* Main Area */}
      <div className="flex flex-col flex-1">
        
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
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
            <div className="text-sm text-gray-400 animate-pulse">
              Generating research-backed answer...
            </div>
          )}
        </div>

        {/* Input */}
        <div className="border-t border-gray-800 p-4">
          <ChatBox onSend={handleSend} disabled={loading} />
        </div>
      </div>
    </div>
  );
}

export default App;