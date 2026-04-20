import { useState } from "react";
import { Send } from "lucide-react";

function ChatBox({ onSend, disabled }) {
  const [input, setInput] = useState("");

  const handleSubmit = () => {
    if (!input.trim() || disabled) return;
    onSend(input.trim());
    setInput("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex items-center gap-3">
      
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask a medical research question..."
        rows={1}
        disabled={disabled}
        className="flex-1 resize-none bg-[#111827] border border-gray-700 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none px-4 py-2 rounded-xl text-sm text-white placeholder-gray-500 transition"
      />

      <button
        onClick={handleSubmit}
        disabled={disabled}
        className={`p-2 rounded-lg transition ${
          disabled
            ? "bg-gray-700 cursor-not-allowed"
            : "bg-emerald-500 hover:bg-emerald-400 text-black"
        }`}
      >
        <Send size={18} />
      </button>
    </div>
  );
}

export default ChatBox;