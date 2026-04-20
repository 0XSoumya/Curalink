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
          <p className="text-sm text-gray-200 leading-relaxed">
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
              <li key={idx}>{insight}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Trials */}
      {clinical_trials.length > 0 && (
        <div className="bg-[#111827] p-4 rounded-2xl shadow-lg border border-gray-800">
          <h2 className="text-sm font-semibold text-cyan-400 mb-2">
            🧪 Clinical Trials
          </h2>
          <ul className="space-y-2 text-sm text-gray-200">
            {clinical_trials.map((trial, idx) => (
              <li key={idx} className="bg-gray-800/60 p-2 rounded-lg">
                {typeof trial === "string" ? trial : trial.title}
              </li>
            ))}
          </ul>
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
              className="text-xs text-emerald-400 hover:underline"
            >
              {showSources ? "Hide" : "Show"}
            </button>
          </div>

          {showSources && (
            <div className="space-y-3 max-h-64 overflow-y-auto pr-1">
              {sources.map((src, idx) => (
                <div
                  key={idx}
                  className="bg-gray-800/60 p-3 rounded-lg text-sm"
                >
                  <div className="font-medium text-white mb-1">
                    [{idx + 1}] {src.title}
                  </div>

                  <div className="text-xs text-gray-400 mb-1">
                    {src.authors} • {src.year} • {src.platform}
                  </div>

                  {src.snippet && (
                    <div className="text-xs text-gray-300 mb-2 line-clamp-3">
                      {src.snippet}
                    </div>
                  )}

                  <a
                    href={src.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-emerald-400 hover:underline"
                  >
                    🔗 View Paper
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