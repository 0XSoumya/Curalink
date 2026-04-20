import { Plus } from "lucide-react";

function Sidebar({ onNewChat }) {
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

      <div className="flex-1 flex items-center justify-center text-xs text-gray-500 px-4 text-center">
        No chat history yet
      </div>

      <div className="p-4 border-t border-gray-800 text-xs text-gray-500">
        Clinical Research Assistant ⚕️
      </div>
    </div>
  );
}

export default Sidebar;