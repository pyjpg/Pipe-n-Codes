import React, { useState, useEffect } from 'react';
import CommandPalette from '../component/CommandPalette';
import '../index.css';

declare global {
  interface Window {
    hideOverlay?: () => void;
  }
}

const App: React.FC = () => {
  const [isOpen, setIsOpen] = useState(true); // Start with palette open

  const handleCloseOverlay = () => {
    setIsOpen(false);
    // Hide the entire overlay after a brief delay to allow close animation
    setTimeout(() => {
      if (window.hideOverlay) {
        window.hideOverlay();
      }
    }, 200);
  };

  // Handle ESC key to close overlay
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleCloseOverlay();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Don't render anything if closed
  if (!isOpen) {
    return null;
  }

  return (
    <div style={{ 
      position: 'fixed',
      inset: 0,
      zIndex: 2147483647,
      pointerEvents: 'auto',
      fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      <CommandPalette onClose={handleCloseOverlay} />
    </div>
  );
};

export default App;