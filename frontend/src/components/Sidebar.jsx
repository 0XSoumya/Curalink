import { Plus, MessageSquare } from "lucide-react";

function Sidebar({ onNewChat, recentChats, onSelectChat, currentSessionId }) {
  return (
    <div className="w-64 bg-[#0f172a] border-r border-gray-800 flex flex-col">
      
      <div className="p-4 border-b border-gray-800">
        <h1 className="text-lg font-semibold text-emerald-400">
          🧠 MedResearch AI
        </h1>
      </div>

      <div className="p-4">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-black px-4 py-2 rounded-lg text-sm font-medium transition"
        >
          <Plus size={16} />
          New Chat
        </button>
      </div>

      <div className="px-4 pb-2">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Recent Chats</h2>
      </div>

      <div className="flex-1 overflow-y-auto px-2 space-y-1 custom-scrollbar">
        {!recentChats || recentChats.length === 0 ? (
          <div className="text-xs text-gray-500 text-center mt-4">No chat history yet</div>
        ) : (
          recentChats.map((chat) => (
            <button
              key={chat.session_id}
              onClick={() => onSelectChat(chat.session_id)}
              className={`w-full flex items-center gap-2 text-left p-3 rounded-lg text-sm transition ${
                chat.session_id === currentSessionId
                  ? "bg-gray-800 text-emerald-400"
                  : "text-gray-300 hover:bg-gray-800/50"
              }`}
            >
              <MessageSquare size={14} className="shrink-0" />
              <span className="truncate">{chat.title}</span>
            </button>
          ))
        )}
      </div>

      <div className="p-4 border-t border-gray-800 text-xs text-gray-500 text-center">
        Clinical Research Assistant ⚕️
      </div>
    </div>
  );
}

export default Sidebar;