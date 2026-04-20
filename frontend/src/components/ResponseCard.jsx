import { useState } from "react";

function ResponseCard({ data }) {
  const [showSources, setShowSources] = useState(false);

  if (!data) return null;

  const {
    overview,
    research_insights = [],
    clinical_trials = [],
    sources = [],
  } = data;

  return (
    <div className="space-y-4 max-w-3xl">
      
      {/* Overview */}
      {overview && (
        <div className="bg-[#111827] p-4 rounded-2xl shadow-lg border border-gray-800">
          <h2 className="text-sm font-semibold text-cyan-400 mb-2">
            🧠 Overview
          </h2>
          <p className="text-sm text-gray-200 leading-relaxed whitespace-pre-wrap">
            {overview}
          </p>
        </div>
      )}

      {/* Insights */}
      {research_insights.length > 0 && (
        <div className="bg-[#111827] p-4 rounded-2xl shadow-lg border border-gray-800">
          <h2 className="text-sm font-semibold text-cyan-400 mb-2">
            🔬 Research Insights
          </h2>
          <ul className="list-disc pl-5 space-y-2 text-sm text-gray-200">
            {research_insights.map((insight, idx) => (
              <li key={idx} className="leading-relaxed">{insight}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Trials - 🔥 NOW SHOWING RICH DATA */}
      {clinical_trials.length > 0 && (
        <div className="bg-[#111827] p-4 rounded-2xl shadow-lg border border-gray-800">
          <h2 className="text-sm font-semibold text-cyan-400 mb-2">
            🧪 Clinical Trials
          </h2>
          <div className="space-y-3">
            {clinical_trials.map((trial, idx) => {
              if (typeof trial === "string") {
                return <div key={idx} className="bg-gray-800/60 p-2 rounded-lg text-sm text-gray-200">{trial}</div>;
              }
              return (
                <div key={idx} className="bg-gray-800/60 p-3 rounded-lg border border-gray-700">
                  <div className="text-sm font-medium text-white mb-1">{trial.title}</div>
                  <div className="flex flex-wrap gap-2 text-xs mb-2">
                    {trial.status && (
                      <span className={`px-2 py-1 rounded-md ${trial.status.toLowerCase().includes('recruiting') ? 'bg-emerald-900/50 text-emerald-400' : 'bg-gray-700 text-gray-300'}`}>
                        {trial.status}
                      </span>
                    )}
                    {trial.location && (
                      <span className="px-2 py-1 rounded-md bg-blue-900/50 text-blue-400">
                        📍 {trial.location}
                      </span>
                    )}
                  </div>
                  {trial.url && (
                    <a
                      href={trial.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-cyan-400 hover:underline"
                    >
                      🔗 View Trial Details
                    </a>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Sources */}
      {sources.length > 0 && (
        <div className="bg-[#111827] p-4 rounded-2xl shadow-lg border border-gray-800">
          
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-sm font-semibold text-cyan-400">
              📚 Sources
            </h2>

            <button
              onClick={() => setShowSources(!showSources)}
              className="text-xs text-emerald-400 hover:underline px-2 py-1 rounded hover:bg-gray-800 transition"
            >
              {showSources ? "Hide Sources" : "View Sources"}
            </button>
          </div>

          {showSources && (
            <div className="space-y-3 max-h-64 overflow-y-auto pr-2 custom-scrollbar">
              {sources.map((src, idx) => (
                <div
                  key={idx}
                  className="bg-gray-800/60 p-3 rounded-lg text-sm border border-gray-700"
                >
                  <div className="font-medium text-white mb-1">
                    [{idx + 1}] {src.title}
                  </div>

                  <div className="text-xs text-gray-400 mb-2 font-medium">
                    {src.authors} • {src.year} • <span className="text-purple-400">{src.platform}</span>
                  </div>

                  {src.snippet && (
                    <div className="text-xs text-gray-300 mb-2 line-clamp-3 italic">
                      "{src.snippet}"
                    </div>
                  )}

                  <a
                    href={src.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-emerald-400 hover:underline"
                  >
                    🔗 Read Full Paper
                  </a>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ResponseCard;