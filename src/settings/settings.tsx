import '../index.css';
import React from 'react';
import { createRoot } from 'react-dom/client';

const Settings = () => {
  return (
    <div className="min-w-[300px] max-w-sm p-4 bg-zinc-900 text-white rounded-xl shadow-lg font-sans">
      <h1 className="text-xl font-bold text-center mb-4 bg-gradient-to-r from-blue-400 to-teal-400 bg-clip-text text-transparent">
        Settings
      </h1>

      <div className="space-y-4">
        <div>
          <label className="block text-sm text-zinc-300 mb-1" htmlFor="theme">
            Theme
          </label>
          <select
            id="theme"
            className="w-full bg-zinc-800 border border-zinc-700 rounded-lg p-2 text-sm text-white"
          >
            <option>Dark</option>
            <option>Light</option>
            <option>System</option>
          </select>
        </div>

        <div>
          <label className="block text-sm text-zinc-300 mb-1" htmlFor="overlay">
            Default Overlay Position
          </label>
          <select
            id="overlay"
            className="w-full bg-zinc-800 border border-zinc-700 rounded-lg p-2 text-sm text-white"
          >
            <option>Bottom Right</option>
            <option>Bottom Left</option>
            <option>Top Right</option>
            <option>Top Left</option>
          </select>
        </div>

        <button className="w-full py-2 px-4 rounded-lg bg-gradient-to-r from-green-500 to-emerald-500 hover:from-emerald-500 hover:to-green-500 transition duration-300 font-semibold shadow-md">
          Save Settings
        </button>
      </div>
    </div>
  );
};

const container = document.createElement('div');
document.body.appendChild(container);
const root = createRoot(container);
root.render(<Settings />);
