import '../index.css';
import React from 'react';
import { createRoot } from 'react-dom/client';

const App = () => {
  return (
    <div className="min-w-[300px] max-w-sm p-4 bg-zinc-900 text-white rounded-xl shadow-lg font-sans">
      <h1 className="text-2xl font-bold mb-2 text-center text-gradient bg-gradient-to-r from-purple-400 via-pink-500 to-red-500 bg-clip-text text-transparent">
        Code n' Pipes
      </h1>
      <p className="text-sm text-zinc-300 text-center mb-4">
        Build, run, and inject terminal overlays into any site.
      </p>
      
      <div className="space-y-2">
        <button className="w-full py-2 px-4 rounded-lg bg-gradient-to-r from-purple-600 to-pink-600 hover:from-pink-600 hover:to-purple-600 transition duration-300 font-semibold shadow-md">
          Launch Terminal
        </button>
        <button className="w-full py-2 px-4 rounded-lg bg-zinc-800 hover:bg-zinc-700 transition duration-300 font-medium border border-zinc-600">
          Settings
        </button>
      </div>
    </div>
  );
};

const container = document.createElement('div');
document.body.appendChild(container);
const root = createRoot(container);
root.render(<App />);