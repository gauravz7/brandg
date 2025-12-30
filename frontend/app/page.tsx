"use client";
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Loader2, Sparkles, ArrowRight } from 'lucide-react';
import ResultsDashboard from '../components/ResultsDashboard';

const API_BASE = "http://localhost:8000";

export default function Home() {
  const [url, setUrl] = useState('');
  const [status, setStatus] = useState<'idle' | 'processing' | 'completed' | 'failed'>('idle');
  const [progress, setProgress] = useState(0);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [data, setData] = useState<any>(null);
  const [logs, setLogs] = useState<string[]>([]);

  const startAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;
    
    let targetUrl = url;
    if (!targetUrl.startsWith('http://') && !targetUrl.startsWith('https://')) {
      targetUrl = 'https://' + targetUrl;
      setUrl(targetUrl);
    }
    
    setStatus('processing');
    setProgress(5);
    setLogs(["Starting analysis..."]);
    
    try {
      const res = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: targetUrl })
      });
      const json = await res.json();
      setTaskId(json.task_id);
    } catch (err) {
      console.error(err);
      setStatus('failed');
      setLogs(prev => [...prev, "Failed to start analysis."]);
    }
  };

  useEffect(() => {
    if (status === 'processing' && taskId) {
      const interval = setInterval(async () => {
        try {
          const res = await fetch(`${API_BASE}/status/${taskId}`);
          const json = await res.json();
          
          setProgress(json.progress);
          if (json.logs) setLogs(json.logs);
          
          if (json.status === 'completed') {
            setData(json.data);
            setStatus('completed');
            clearInterval(interval);
          } else if (json.status === 'failed') {
            setStatus('failed');
            clearInterval(interval);
          }
        } catch (err) {
          console.error(err);
        }
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [status, taskId]);

  return (
    <main className="min-h-screen bg-black text-white selection:bg-purple-500/30">
        
        {/* Background Gradients */}
        <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
            <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-purple-900/20 rounded-full blur-[120px]" />
            <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-900/20 rounded-full blur-[120px]" />
        </div>

        <div className="relative z-10 container mx-auto px-4 py-12 md:py-24 flex flex-col items-center min-h-screen">
            
            <AnimatePresence mode="wait">
                {status === 'idle' && (
                    <motion.div 
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="w-full max-w-2xl text-center space-y-8 mt-20"
                        key="idle"
                    >
                        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-sm md:text-base backdrop-blur-sm animate-pulse">
                            <Sparkles size={16} className="text-yellow-400" />
                            <span className="bg-clip-text text-transparent bg-gradient-to-r from-yellow-200 to-yellow-500 font-medium">
                                AI-Powered Brand Analyst
                            </span>
                        </div>
                        
                        <h1 className="text-5xl md:text-7xl font-bold tracking-tight">
                            Decode any <br />
                            <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500">
                                Brand Identity
                            </span>
                        </h1>
                        
                        <p className="text-lg text-gray-400 max-w-lg mx-auto leading-relaxed">
                            Enter a URL to extract logos, fonts, colors, and generate a comprehensive brand guidelines report instantly.
                        </p>

                        <form onSubmit={startAnalysis} className="relative group max-w-lg mx-auto">
                            <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl blur opacity-25 group-hover:opacity-75 transition duration-1000 group-hover:duration-200" />
                            <div className="relative flex items-center bg-black rounded-xl p-1 border border-white/10">
                                <Search className="ml-4 text-gray-500" size={20}/>
                                <input 
                                    type="text" 
                                    placeholder="https://example.com" 
                                    className="w-full bg-transparent border-none focus:ring-0 text-white placeholder-gray-600 px-4 py-3 outline-none"
                                    value={url}
                                    onChange={e => setUrl(e.target.value)}
                                    required
                                />
                                <button type="submit" className="bg-white text-black px-6 py-3 rounded-lg font-bold hover:bg-gray-200 transition-colors flex items-center gap-2">
                                    Analyze <ArrowRight size={16} />
                                </button>
                            </div>
                        </form>
                    </motion.div>
                )}

                {status === 'processing' && (
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="w-full max-w-xl text-center mt-32 space-y-8"
                        key="processing"
                    >
                        <div className="relative w-32 h-32 mx-auto">
                            <div className="absolute inset-0 border-4 border-white/10 rounded-full" />
                            <div className="absolute inset-0 border-t-4 border-blue-500 rounded-full animate-spin" />
                            <div className="absolute inset-0 flex items-center justify-center font-mono text-2xl font-bold">
                                {progress}%
                            </div>
                        </div>
                        
                        <div className="space-y-2">
                            <h3 className="text-2xl font-bold animate-pulse">Analyzing Brand DNA...</h3>
                            <div className="h-6 overflow-hidden">
                                <p className="text-gray-400 font-mono text-sm transition-all duration-300">
                                    {logs[logs.length - 1] || "Initializing..."}
                                </p>
                            </div>
                            <div className="text-xs text-gray-500 font-mono mt-2">
                                Status: <span className="text-blue-400 uppercase">{status}</span>
                            </div>
                        </div>

                        {/* Log Terminal */}
                        <div className="bg-black/80 rounded-xl border border-white/10 p-4 text-left h-48 overflow-y-auto font-mono text-xs text-green-400/80 custom-scrollbar">
                            {logs.map((log, i) => (
                                <div key={i}>&gt; {log}</div>
                            ))}
                            <div className="animate-pulse">&gt; _</div>
                        </div>
                    </motion.div>
                )}

                {status === 'completed' && data && (
                     <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="w-full"
                        key="results"
                     >
                        <div className="mb-8 flex justify-center">
                            <button onClick={() => setStatus('idle')} className="text-sm text-gray-500 hover:text-white transition-colors">
                                ← Analyze another brand
                            </button>
                        </div>
                        <ResultsDashboard data={data} />
                     </motion.div>
                )}

                {status === 'failed' && (
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="w-full max-w-xl text-center mt-32 space-y-8"
                        key="failed"
                    >
                        <div className="relative w-24 h-24 mx-auto text-red-500">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-full h-full">
                              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                            </svg>
                        </div>
                        
                        <div className="space-y-4">
                            <h3 className="text-3xl font-bold text-red-500">Analysis Failed</h3>
                            <p className="text-gray-400">
                                Something went wrong during the analysis.
                            </p>
                            
                            <div className="bg-red-900/20 border border-red-500/20 rounded-lg p-4 text-left font-mono text-sm text-red-300 overflow-x-auto">
                                {logs.map((log, i) => (
                                    <div key={i}>&gt; {log}</div>
                                ))}
                            </div>
                        </div>

                        <button 
                            onClick={() => setStatus('idle')}
                            className="bg-white text-black px-8 py-3 rounded-lg font-bold hover:bg-gray-200 transition-colors"
                        >
                            Try Again
                        </button>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    </main>
  )
}
