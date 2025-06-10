// src/content/content.ts
import React from 'react';
import { createRoot, Root } from 'react-dom/client';

let overlayRoot: HTMLDivElement | null = null;
let reactRoot: Root | null = null;
let isOverlayVisible = false;

// CommandPalette Component (integrated directly)
const CommandPalette: React.FC = () => {
  const [isOpen, setIsOpen] = React.useState(true); // Start open when created
  const [activeTab, setActiveTab] = React.useState(2);
  const [highlightedIndex, setHighlightedIndex] = React.useState(0);
  const [query, setQuery] = React.useState("");
  const [position, setPosition] = React.useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = React.useState(false);
  const [dragStart, setDragStart] = React.useState({ x: 0, y: 0 });

  const tabs = ["Memory", "Ask", "Chat"];
  const inputRef = React.useRef<HTMLInputElement>(null);
  const paletteRef = React.useRef<HTMLDivElement>(null);

  const askItems = [
    "Ask AI: How do I center a div?",
    "Search documentation", 
    "Search Stack Overflow",
    "Find React best practices",
    "Explain this code pattern"
  ];

  const items = activeTab === 0 ? askItems : askItems;

  // Handle keyboard shortcuts
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + K to toggle
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsOpen((prev) => !prev);
        if (!isOpen) {
          setTimeout(() => inputRef.current?.focus(), 100);
        }
      }
      
      if (e.key === "Escape") {
        setIsOpen(false);
      }
      
      if (!isOpen) return;

      // Check if input is focused
      const isInputFocused = document.activeElement === inputRef.current;

      // Tab switching with numbers 1-3
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

      // Tab navigation
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
  }, [isOpen, items.length, activeTab]);

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

  const handleMouseMove = React.useCallback((e: MouseEvent) => {
    if (isDragging) {
      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  }, [isDragging, dragStart]);

  const handleMouseUp = React.useCallback(() => {
    setIsDragging(false);
  }, []);

  React.useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  // Focus input when opening
  React.useEffect(() => {
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
    }
  };

  const handleClose = () => {
    hideOverlay();
  };

  // Show trigger hint when closed
  if (!isOpen) {
    return React.createElement('div', {
      style: {
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        zIndex: 2147483647,
        pointerEvents: 'auto'
      }
    }, [
      React.createElement('div', {
        key: 'hint',
        style: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          color: 'white',
          padding: '8px 16px',
          borderRadius: '8px',
          fontSize: '14px',
          backdropFilter: 'blur(4px)',
          cursor: 'pointer'
        },
        onClick: () => setIsOpen(true)
      }, 'Command Palette Available - Press ⌘K')
    ]);
  }

  // Main palette UI
  return React.createElement('div', {
    style: {
      position: 'fixed',
      inset: '0',
      zIndex: 2147483647,
      backgroundColor: 'rgba(0, 0, 0, 0.1)',
      backdropFilter: 'blur(1px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '16px'
    },
    onClick: handleBackdropClick
  }, [
    // Shortcuts at top
    React.createElement('div', {
      key: 'shortcuts',
      style: {
        position: 'fixed',
        top: '16px',
        left: '16px',
        zIndex: 2147483648,
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        color: 'white',
        padding: '8px 16px',
        borderRadius: '8px',
        fontSize: '12px',
        backdropFilter: 'blur(4px)',
        border: '1px solid rgba(255, 255, 255, 0.2)'
      }
    }, '1-3: tabs • ↑↓: navigate • Ctrl+↑↓←→: move • Ctrl+R: reset • Esc: close'),

    // Main palette
    React.createElement('div', {
      key: 'palette',
      ref: paletteRef,
      style: {
        width: '100%',
        maxWidth: '32rem',
        backgroundColor: 'rgba(255, 255, 255, 0.4)',
        backdropFilter: 'blur(24px)',
        borderRadius: '16px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        border: '1px solid rgba(255, 255, 255, 0.3)',
        overflow: 'hidden',
        transform: `translate(${position.x}px, ${position.y}px)`,
        transition: isDragging ? 'none' : 'transform 0.2s ease-out',
        cursor: isDragging ? 'grabbing' : 'grab'
      },
      onMouseDown: handleMouseDown
    }, [
      // Header
      React.createElement('div', {
        key: 'header',
        style: {
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid rgba(255, 255, 255, 0.3)',
          backgroundColor: 'rgba(249, 250, 251, 0.2)',
          backdropFilter: 'blur(4px)',
          padding: '12px 16px'
        }
      }, [
        React.createElement('div', {
          key: 'header-left',
          style: { display: 'flex', alignItems: 'center', gap: '12px' }
        }, [
          // Drag handle
          React.createElement('div', {
            key: 'drag-handle',
            className: 'drag-handle',
            style: {
              color: '#9CA3AF',
              cursor: 'grab'
            }
          }, '⋮⋮'),
          
          // Tabs
          React.createElement('div', {
            key: 'tabs',
            style: { display: 'flex', gap: '4px' }
          }, tabs.map((tab, index) => 
            React.createElement('button', {
              key: tab,
              onClick: () => handleTabClick(index),
              style: {
                padding: '8px 16px',
                borderRadius: '8px',
                fontWeight: '500',
                fontSize: '14px',
                border: 'none',
                cursor: 'pointer',
                transition: 'all 0.2s',
                backgroundColor: index === activeTab 
                  ? 'rgba(255, 255, 255, 0.6)' 
                  : 'transparent',
                color: index === activeTab ? '#111827' : '#6B7280'
              }
            }, `${tab} ${index + 1}`)
          ))
        ]),
        
        // Close button
        React.createElement('button', {
          key: 'close',
          onClick: handleClose,
          style: {
            color: '#9CA3AF',
            padding: '4px',
            borderRadius: '8px',
            border: 'none',
            backgroundColor: 'transparent',
            cursor: 'pointer',
            fontSize: '20px'
          }
        }, '×')
      ]),

      // Content
      React.createElement('div', {
        key: 'content',
        style: { padding: '24px' }
      }, [
        activeTab === 2 
          ? React.createElement('div', {
              key: 'chat',
              style: {
                textAlign: 'center',
                padding: '48px 0',
                color: '#6B7280'
              }
            }, [
              React.createElement('div', { key: 'icon', style: { fontSize: '48px', marginBottom: '16px' } }, '💬'),
              React.createElement('p', { key: 'text' }, 'Chat functionality coming soon!')
            ])
          : React.createElement('div', { key: 'search-content' }, [
              // Search Input
              React.createElement('div', {
                key: 'search',
                style: { position: 'relative', marginBottom: '24px' }
              }, [
                React.createElement('div', {
                  key: 'search-icon',
                  style: {
                    position: 'absolute',
                    left: '12px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: '#9CA3AF',
                    pointerEvents: 'none'
                  }
                }, '🔍'),
                
                React.createElement('input', {
                  key: 'search-input',
                  ref: inputRef,
                  type: 'text',
                  disabled: activeTab === 0,
                  value: query,
                  onChange: (e: React.ChangeEvent<HTMLInputElement>) => setQuery(e.target.value),
                  placeholder: activeTab === 0 
                    ? "Viewing memory from this page..." 
                    : "Ask a question or search...",
                  style: {
                    width: '100%',
                    paddingLeft: '40px',
                    paddingRight: '16px',
                    paddingTop: '12px',
                    paddingBottom: '12px',
                    borderRadius: '12px',
                    border: '1px solid rgba(209, 213, 219, 0.3)',
                    backdropFilter: 'blur(4px)',
                    backgroundColor: activeTab === 0 
                      ? 'rgba(243, 244, 246, 0.4)' 
                      : 'rgba(255, 255, 255, 0.4)',
                    color: activeTab === 0 ? '#6B7280' : '#111827',
                    cursor: activeTab === 0 ? 'not-allowed' : 'text',
                    outline: 'none',
                    fontSize: '14px'
                  }
                })
              ]),

              // Memory Tab Content
              activeTab === 0 
                ? React.createElement('div', {
                    key: 'memory-content',
                    style: {
                      textAlign: 'center',
                      padding: '48px 0',
                      color: '#6B7280'
                    }
                  }, [
                    React.createElement('div', { key: 'memory-icon', style: { fontSize: '48px', marginBottom: '16px' } }, '🧠'),
                    React.createElement('p', { key: 'memory-text' }, 'Memory functionality coming soon!'),
                    React.createElement('p', { key: 'memory-desc', style: { fontSize: '12px', marginTop: '8px' } }, 'Save and search through webpage content')
                  ])
                : React.createElement('ul', {
                    key: 'search-results',
                    style: { listStyle: 'none', padding: '0', margin: '0', gap: '8px', display: 'flex', flexDirection: 'column' }
                  }, items.map((item, index) => 
                    React.createElement('li', {
                      key: index,
                      style: {
                        padding: '16px',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        backgroundColor: index === highlightedIndex 
                          ? '#3B82F6' 
                          : 'rgba(255, 255, 255, 0.1)',
                        color: index === highlightedIndex ? 'white' : '#374151',
                        transition: 'all 0.2s'
                      }
                    }, item)
                  ))
            ])
      ])
    ])
  ]);
};

// Updated OverlayComponent to use CommandPalette
const OverlayComponent: React.FC = () => {
  return React.createElement(CommandPalette);
};

function createOverlay(): void {
  if (overlayRoot && isOverlayVisible) {
    console.log('🔄 Overlay already visible');
    return;
  }
  
  // Clean up any existing overlay first
  if (overlayRoot) {
    hideOverlay();
  }
  
  try {
    overlayRoot = document.createElement('div');
    overlayRoot.id = 'code-pipes-overlay-root';
    overlayRoot.style.cssText = 'all: initial; pointer-events: auto; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;';
    
    // Ensure we can append to body
    if (!document.body) {
      console.error('❌ Document body not available');
      return;
    }
    
    document.body.appendChild(overlayRoot);
    
    reactRoot = createRoot(overlayRoot);
    reactRoot.render(React.createElement(OverlayComponent));
    
    isOverlayVisible = true;
    console.log('✅ Command Palette overlay created successfully');
  } catch (error) {
    console.error('❌ Error creating overlay:', error);
    // Clean up on error
    if (overlayRoot && overlayRoot.parentNode) {
      overlayRoot.parentNode.removeChild(overlayRoot);
    }
    overlayRoot = null;
    reactRoot = null;
    isOverlayVisible = false;
  }
}

function hideOverlay(): void {
  if (!overlayRoot) {
    console.log('🔄 No overlay to hide');
    return;
  }
  
  try {
    if (reactRoot) {
      reactRoot.unmount();
    }
    
    if (overlayRoot.parentNode) {
      overlayRoot.parentNode.removeChild(overlayRoot);
    }
    
    console.log('✅ Command Palette overlay hidden successfully');
  } catch (error) {
    console.warn('⚠️ Error cleaning up overlay:', error);
    // Force removal if unmount fails
    try {
      if (overlayRoot.parentNode) {
        overlayRoot.parentNode.removeChild(overlayRoot);
      }
    } catch (removeError) {
      console.error('❌ Failed to force remove overlay:', removeError);
    }
  } finally {
    overlayRoot = null;
    reactRoot = null;
    isOverlayVisible = false;
  }
}

function toggleOverlay(): void {
  console.log('🔄 Toggle Command Palette called, current state:', isOverlayVisible);
  try {
    if (isOverlayVisible) {
      hideOverlay();
    } else {
      createOverlay();
    }
  } catch (error) {
    console.error('❌ Error in toggleOverlay:', error);
  }
}

// Message listener
chrome.runtime.onMessage.addListener((request: any, sender: chrome.runtime.MessageSender, sendResponse: (response: any) => void) => {
  console.log('📨 Content script received message:', request);
  
  if (request.action === 'toggle-overlay') {
    try {
      toggleOverlay();
      sendResponse({ 
        success: true, 
        overlayVisible: isOverlayVisible,
        timestamp: Date.now()
      });
    } catch (error) {
      console.error('❌ Error handling toggle message:', error);
      sendResponse({ 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  } else {
    sendResponse({ success: false, error: 'Unknown action' });
  }
  
  return true;
});

// Keyboard shortcut listener - Updated to use Cmd/Ctrl + K
document.addEventListener('keydown', (event: KeyboardEvent) => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault();
    event.stopPropagation();
    console.log('⌨️ Command Palette keyboard shortcut triggered');
    toggleOverlay();
  }
});

// Signal that the content script is ready
declare global {
  interface Window {
    codePipesContentScriptReady?: boolean;
  }
}

function initializeContentScript() {
  window.codePipesContentScriptReady = true;
  console.log('🚀 Code n\' Pipes content script with Command Palette loaded and ready');
  
  try {
    chrome.runtime.sendMessage({ type: 'CONTENT_READY' }, (response) => {
      if (chrome.runtime.lastError) {
        console.log('📡 Background script not ready yet');
      } else {
        console.log('📡 Background script acknowledged');
      }
    });
  } catch (error) {
    console.log('📡 Could not contact background script:', error);
  }
}

// Initialize immediately if DOM is already loaded, otherwise wait
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeContentScript);
} else {
  initializeContentScript();
}