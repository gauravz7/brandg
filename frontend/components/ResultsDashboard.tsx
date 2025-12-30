import React from 'react';
import { Download, ExternalLink, Image as ImageIcon, Type, FileText, Palette, Code } from 'lucide-react';

interface BrandData {
  title: string;
  description: string;
  url: string;
  screenshot_url?: string;
  assets_urls?: string[];
  fonts?: string[];
}

interface ResultsProps {
  data: {
    brand_data: BrandData;
    guidelines: string;
    report: string;
    pdf_url?: string;
    screenshot_url?: string;
    assets_urls?: string[];
    css_urls?: string[];
  };
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ResultsDashboard({ data }: ResultsProps) {
  const { brand_data, guidelines, pdf_url, screenshot_url, assets_urls, css_urls } = data;

  return (
    <div className="w-full max-w-6xl mx-auto p-6 space-y-8 animate-in fade-in duration-700">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-600">
            {brand_data.title || "Brand Analysis"}
          </h1>
          <p className="text-gray-400 mt-2 max-w-2xl">{brand_data.description}</p>
          <a href={brand_data.url} target="_blank" rel="noreferrer" className="flex items-center gap-2 text-blue-400 mt-2 hover:underline">
            {brand_data.url} <ExternalLink size={14} />
          </a>
        </div>
        {pdf_url && (
            <a 
              href={`${API_BASE}${pdf_url}`} 
              download 
              className="flex items-center gap-2 bg-white text-black px-6 py-3 rounded-full font-bold hover:bg-gray-200 transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
            >
              <Download size={20} />
              Download Report
            </a>
        )}
      </div>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        
        {/* Snapshot */}
        <div className="lg:col-span-2 relative group overflow-hidden rounded-2xl border border-white/10 bg-black/50 backdrop-blur-sm">
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent z-10 opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="p-4 absolute bottom-0 left-0 z-20 opacity-0 group-hover:opacity-100 transition-opacity">
            <h3 className="text-xl font-bold text-white flex items-center gap-2"><ImageIcon size={20} /> Snapshot</h3>
          </div>
          <img 
            src={screenshot_url ? `${API_BASE}${screenshot_url}` : ""} 
            alt="Website Snapshot" 
            className="w-full h-full object-cover object-top transition-transform duration-700 group-hover:scale-105"
          />
        </div>

        {/* Colors & Fonts */}
        <div className="space-y-6">
           {/* Fonts */}
           <div className="p-6 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md">
             <h3 className="text-xl font-bold mb-4 flex items-center gap-2"><Type size={20} className="text-purple-400"/> Typography</h3>
             <ul className="space-y-2">
               {brand_data.fonts?.slice(0, 5).map((font, i) => (
                 <li key={i} className="text-sm text-gray-300 font-mono bg-white/5 p-2 rounded">{font}</li>
               ))}
             </ul>
           </div>

           {/* Guidelines Summary */}
           <div className="p-6 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md h-64 overflow-y-auto custom-scrollbar">
             <h3 className="text-xl font-bold mb-4 flex items-center gap-2"><FileText size={20} className="text-green-400"/> Brand Guidelines</h3>
             <p className="text-sm text-gray-300 whitespace-pre-line leading-relaxed">
               {guidelines ? guidelines.slice(0, 500) + "..." : "No guidelines found."}
             </p>
           </div>
        </div>

        {/* Assets Gallery */}
        <div className="lg:col-span-2 p-6 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md">
             <h3 className="text-xl font-bold mb-6 flex items-center gap-2"><Palette size={20} className="text-yellow-400"/> Brand Assets & Icons</h3>
             <div className="flex flex-wrap gap-4">
               {assets_urls?.map((url, i) => (
                 <div key={i} className="w-24 h-24 p-4 bg-white/10 rounded-xl flex items-center justify-center hover:bg-white/20 transition-colors border border-white/5">
                   <img src={`${API_BASE}${url}`} className="max-w-full max-h-full object-contain" alt="asset" />
                 </div>
               ))}
             </div>
        </div>

        {/* Technical Identity (CSS) */}
        <div className="p-6 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md">
             <h3 className="text-xl font-bold mb-6 flex items-center gap-2"><Code size={20} className="text-blue-400"/> Technical Specs (CSS)</h3>
             <div className="space-y-2">
               {css_urls?.map((url, i) => (
                 <a 
                   key={i} 
                   href={`${API_BASE}${url}`} 
                   target="_blank" 
                   rel="noreferrer"
                   className="text-xs font-mono text-gray-400 hover:text-white flex items-center gap-2 bg-white/5 p-2 rounded truncate"
                 >
                   <Code size={12} /> {url.split('/').pop()}
                 </a>
               ))}
               {(!css_urls || css_urls.length === 0) && <p className="text-xs text-gray-500">No CSS assets captured.</p>}
             </div>
        </div>
      </div>

      {/* Footer / Final CTA */}
      <div className="flex flex-col items-center gap-6 pt-12 border-t border-white/10">
        <h3 className="text-2xl font-bold">Ready to take this further?</h3>
        {pdf_url && (
            <a 
              href={`${API_BASE}${pdf_url}`} 
              download 
              className="flex items-center gap-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white px-10 py-4 rounded-full font-bold hover:scale-105 transition-all shadow-xl hover:shadow-purple-500/20"
            >
              <Download size={24} />
              Download Complete Brand Report (PDF)
            </a>
        )}
      </div>
    </div>
  );
}
