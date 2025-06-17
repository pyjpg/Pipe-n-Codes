import React, { useState, useEffect, useRef } from "react";
import RagChat from "./RagChat";
import MemorySaver from "./MemorySaver/MemorySaver";
import '../index.css';

interface CommandPaletteProps {
  onClose: () => void;
}

const CommandPalette: React.FC<CommandPaletteProps> = ({ onClose }) => {
  const [isOpen, setIsOpen] = useState(true); // Start open for extension overlay
  const [activeTab, setActiveTab] = useState(0); // Start with Memory tab
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const [query, setQuery] = useState("");
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const tabs = ["Memory", "Ask", "Chat"];
  const inputRef = useRef<HTMLInputElement>(null);
  const paletteRef = useRef<HTMLDivElement>(null);

  const askItems = [
    "Ask AI: How do I center a div?",
    "Search documentation", 
    "Search Stack Overflow",
    "Find React best practices",
    "Explain this code pattern"
  ];

  const items = activeTab === 0 ? askItems : askItems;

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setIsOpen(false);
        onClose();
        return;
      }
      
      if (!isOpen) return;

      // Check if input is focused - if so, don't handle tab switching with numbers
      const isInputFocused = document.activeElement === inputRef.current;

      // Tab switching with numbers 1-3 (only when input is NOT focused)
      if (!isInputFocused && e.key >= "1" && e.key <= "3") {
        e.preventDefault();
        const tabIndex = parseInt(e.key) - 1;
        setActiveTab(tabIndex);
        setHighlightedIndex(0);
      }

      // Movement with Ctrl+Arrow keys
      if (e.ctrlKey) {
        const step = 20;
        switch (e.key) {
          case 'ArrowLeft':
            e.preventDefault();
            setPosition(prev => ({ ...prev, x: prev.x - step }));
            break;
          case 'ArrowRight':
            e.preventDefault();
            setPosition(prev => ({ ...prev, x: prev.x + step }));
            break;
          case 'ArrowUp':
            e.preventDefault();
            setPosition(prev => ({ ...prev, y: prev.y - step }));
            break;
          case 'ArrowDown':
            e.preventDefault();
            setPosition(prev => ({ ...prev, y: prev.y + step }));
            break;
          case 'r':
            e.preventDefault();
            setPosition({ x: 0, y: 0 });
            break;
        }
      }

      // Tab navigation (only when not in Chat tab and input is NOT focused)
      if (activeTab !== 2 && !isInputFocused) {
        if (e.key === "ArrowDown" && items.length > 0) {
          e.preventDefault();
          setHighlightedIndex((prev) => (prev + 1) % items.length);
        }
        if (e.key === "ArrowUp" && items.length > 0) {
          e.preventDefault();
          setHighlightedIndex((prev) => (prev - 1 + items.length) % items.length);
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, items.length, activeTab, onClose]);

  // Mouse drag handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget || (e.target as HTMLElement).closest('.drag-handle')) {
      setIsDragging(true);
      setDragStart({
        x: e.clientX - position.x,
        y: e.clientY - position.y
      });
    }
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (isDragging) {
      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, dragStart]);

  // Focus input when opening
  useEffect(() => {
    if (isOpen && activeTab !== 2) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen, activeTab]);

  const handleTabClick = (index: number) => {
    setActiveTab(index);
    setHighlightedIndex(0);
    setQuery("");
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      setIsOpen(false);
      onClose();
    }
  };

  const handleCloseClick = () => {
    setIsOpen(false);
    onClose();
  };

  // Always render the palette when this component is mounted
  return (
    <>
      {/* Keyboard shortcuts at top - always visible */}
      <div className="fixed top-4 left-4 z-60">
        <div className="bg-black/70 text-white px-4 py-2 rounded-lg text-sm backdrop-blur-sm border border-white/20">
          <div className="flex items-center space-x-4">
            <span><kbd className="bg-white/20 px-1 py-0.5 rounded text-xs">1-3</kbd> tabs</span>
            <span><kbd className="bg-white/20 px-1 py-0.5 rounded text-xs">↑↓</kbd> navigate</span>
            <span><kbd className="bg-white/20 px-1 py-0.5 rounded text-xs">Ctrl+↑↓←→</kbd> move</span>
            <span><kbd className="bg-white/20 px-1 py-0.5 rounded text-xs">Ctrl+R</kbd> reset position</span>
            <span><kbd className="bg-white/20 px-1 py-0.5 rounded text-xs">Esc</kbd> close</span>
          </div>
        </div>
      </div>

      <div 
        className="fixed inset-0 z-50 bg-black/10 backdrop-blur-[1px] flex items-center justify-center p-4"
        onClick={handleBackdropClick}
      >
        <div 
          ref={paletteRef}
          className={`w-full max-w-2xl bg-white/40 dark:bg-gray-900/40 backdrop-blur-xl rounded-2xl shadow-2xl border border-gray-200/30 dark:border-gray-700/30 overflow-hidden animate-in fade-in zoom-in-95 duration-200 ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}`}
          style={{
            transform: `translate(${position.x}px, ${position.y}px)`,
            transition: isDragging ? 'none' : 'transform 0.2s ease-out'
          }}
          onMouseDown={handleMouseDown}
        >
          {/* Header with tabs and drag handle */}
          <div className="flex items-center justify-between border-b border-gray-200/30 dark:border-gray-700/30 bg-gray-50/20 dark:bg-gray-800/20 backdrop-blur-sm px-4 py-3 drag-handle">
            <div className="flex items-center space-x-3">
              {/* Drag handle icon */}
              <div className="text-gray-400 cursor-grab">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                </svg>
              </div>
              
              {/* Tabs */}
              <div className="flex space-x-1">
                {tabs.map((tab, index) => (
                  <button
                    key={tab}
                    onClick={() => handleTabClick(index)}
                    className={`px-4 py-2 rounded-lg font-medium text-sm transition-all ${
                      index === activeTab
                        ? "bg-white/60 dark:bg-gray-700/60 text-gray-900 dark:text-white shadow-sm backdrop-blur-sm"
                        : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-white/20 dark:hover:bg-gray-700/20"
                    }`}
                  >
                    {tab}
                    <span className="ml-2 text-xs text-gray-400">{index + 1}</span>
                  </button>
                ))}
              </div>
            </div>
            
            <button 
              onClick={handleCloseClick}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1 rounded-lg hover:bg-white/20 dark:hover:bg-gray-700/20 transition-all"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="p-6">
            {activeTab === 2 ? (
              <RagChat />
            ) : activeTab === 0 ? (
              <MemorySaver />
            ) : (
              <>
                {/* Search Input for Ask tab */}
                <div className="relative mb-6">
                  <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                    <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                  <input
                    ref={inputRef}
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Ask a question or search..."
                    className="w-full pl-10 pr-4 py-3 rounded-xl border bg-white/40 dark:bg-gray-800/40 border-gray-300/30 dark:border-gray-600/30 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent backdrop-blur-sm transition-all"
                  />
                </div>

                <ul className="space-y-2">
                  {items.map((item, index) => (
                    <li
                      key={index}
                      className={`px-4 py-2 rounded cursor-pointer ${
                        index === highlightedIndex
                          ? "bg-blue-500 text-white"
                          : "hover:bg-gray-200 dark:hover:bg-gray-700"
                      }`}
                    >
                      {item}
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default CommandPalette;