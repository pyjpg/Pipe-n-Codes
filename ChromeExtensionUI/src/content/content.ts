import React from 'react';
import { createRoot, Root } from 'react-dom/client';
import App from '../components/App';

let overlayRoot: HTMLDivElement | null = null;
let reactRoot: Root | null = null;
let isOverlayVisible = false;

// Simple overlay component that renders the main App
const OverlayComponent: React.FC = () => {
  return React.createElement(App);
};

function createOverlay(): void {
  if (overlayRoot && isOverlayVisible) {
    console.log('🔄 Overlay already visible');
    return;
  }
  
  if (overlayRoot) {
    hideOverlay();
  }
  
  try {
    overlayRoot = document.createElement('div');
    overlayRoot.id = 'code-pipes-overlay-root';
    overlayRoot.style.cssText = 'all: initial; pointer-events: auto; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;';
    
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

// Expose hideOverlay globally so components can access it
declare global {
  interface Window {
    codePipesContentScriptReady?: boolean;
    hideOverlay?: () => void;
  }
}

window.hideOverlay = hideOverlay;

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

// Keyboard shortcut listener
document.addEventListener('keydown', (event: KeyboardEvent) => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault();
    event.stopPropagation();
    console.log('⌨️ Command Palette keyboard shortcut triggered');
    toggleOverlay();
  }
});

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

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeContentScript);
} else {
  initializeContentScript();
}