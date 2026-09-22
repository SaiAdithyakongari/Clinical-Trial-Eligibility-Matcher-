import React from "react";
import { X, Terminal, Copy, Check, ExternalLink } from "lucide-react";

interface LocalRunModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const LocalRunModal: React.FC<LocalRunModalProps> = ({ isOpen, onClose }) => {
  const [copiedIndex, setCopiedIndex] = React.useState<number | null>(null);

  if (!isOpen) return null;

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const steps = [
    {
      title: "1. Install Python Dependencies",
      cmd: "pip install -r requirements.txt"
    },
    {
      title: "2. Set Gemini / LLM API Key (Optional)",
      cmd: "export GEMINI_API_KEY=\"your-api-key-here\""
    },
    {
      title: "3. Run End-to-End Test Suite",
      cmd: "python3 test_pipeline.py"
    },
    {
      title: "4. Launch Streamlit Web Application",
      cmd: "streamlit run app.py"
    }
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="bg-white rounded-2xl max-w-xl w-full border border-slate-200 shadow-xl overflow-hidden">
        <div className="flex items-center justify-between p-5 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-teal-600/10 text-teal-700 flex items-center justify-center">
              <Terminal className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 m-0">
                Run Streamlit App Locally
              </h3>
              <p className="text-xs text-slate-500 m-0">
                Python GenAI & RAG adjudication pipeline
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 flex items-center justify-center transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-6 space-y-4 max-h-[75vh] overflow-y-auto">
          <p className="text-xs text-slate-600 m-0 leading-relaxed">
            The project includes a complete Python Streamlit application in <code>app.py</code> with unified LLM abstraction, PDF protocol chunking, vector database, and report exports.
          </p>

          <div className="space-y-3">
            {steps.map((st, idx) => (
              <div key={idx} className="space-y-1">
                <div className="text-xs font-semibold text-slate-700">{st.title}</div>
                <div className="flex items-center justify-between bg-slate-900 text-slate-100 font-mono text-xs p-2.5 rounded-lg border border-slate-800">
                  <span className="truncate mr-2">{st.cmd}</span>
                  <button
                    onClick={() => copyToClipboard(st.cmd, idx)}
                    className="text-slate-400 hover:text-white shrink-0 transition-colors p-1"
                    title="Copy command"
                  >
                    {copiedIndex === idx ? (
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="p-3 bg-teal-50 rounded-xl border border-teal-200 text-xs text-teal-900 space-y-1">
            <div className="font-bold">✨ Local Heuristic Fallback Engine</div>
            <p className="text-teal-800 m-0">
              If run without an API key, the system automatically uses its high-fidelity deterministic clinical rules engine and dense semantic vectorizer with zero crashes.
            </p>
          </div>
        </div>

        <div className="p-4 bg-slate-50 border-t border-slate-100 flex justify-end">
          <button
            onClick={onClose}
            className="bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold px-4 py-2 rounded-lg transition-colors"
          >
            Got it, Close
          </button>
        </div>
      </div>
    </div>
  );
};
