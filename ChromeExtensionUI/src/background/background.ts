chrome.runtime.onInstalled.addListener(() => {
  console.log('🚀 Code n\' Pipes extension installed');
});

chrome.bookmarks.onCreated.addListener(() => {
  console.log('📖 Bookmark created');
});

async function sendMessageToActiveTab(message: { action: string }): Promise<any> {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id || !tab.url) {
      console.log('❌ No valid active tab');
      return null;
    }

    // Don't inject into restricted pages
    const restricted = [
      'chrome://', 
      'chrome-extension://', 
      'moz-extension://', 
      'edge://', 
      'about:', 
      'file://',
      'devtools://'
    ];
    
    if (restricted.some((prefix) => tab.url!.startsWith(prefix))) {
      console.warn('🚫 Blocked injection into restricted page:', tab.url);
      return null;
    }

    console.log('📤 Attempting to send message to tab:', tab.id, 'URL:', tab.url);

    // First, try to send the message to existing content script
    try {
      const response = await chrome.tabs.sendMessage(tab.id, message);
      console.log('✅ Message sent to existing content script:', response);
      return response;
    } catch (sendError) {
      console.log('⚠️ Content script not found, attempting injection...');
      
      try {
        // Check if we can inject scripts into this tab
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: () => { 
            console.log('🔍 Testing script injection capability'); 
            return true; 
          }
        });

        // Inject the content script
        console.log('💉 Injecting content script...');
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ['content.js']
        });

        // ✅ Wait for content script to signal readiness
        console.log('⏳ Waiting for content script to signal readiness...');
        const initialized = await new Promise<boolean>((resolve) => {
          const listener = (msg: any, sender: chrome.runtime.MessageSender) => {
            if (msg?.type === 'CONTENT_READY' && sender.tab?.id === tab.id) {
              chrome.runtime.onMessage.removeListener(listener);
              console.log('✅ Received CONTENT_READY message from tab:', tab.id);
              resolve(true);
            }
          };

          chrome.runtime.onMessage.addListener(listener);

          // Timeout in case message isn't received
          setTimeout(() => {
            chrome.runtime.onMessage.removeListener(listener);
            console.error('❌ Timed out waiting for CONTENT_READY');
            resolve(false);
          }, 3000);
        });

        if (!initialized) return null;

        // Send the intended message
        const response = await chrome.tabs.sendMessage(tab.id, message);
        console.log('✅ Message sent successfully after content readiness:', response);
        return response;

      } catch (injectError) {
        console.error('❌ Failed to inject content script:', injectError);
        
        if (injectError instanceof Error && injectError.message.includes('Cannot access')) {
          console.error('🚫 Permission denied - cannot inject into this page');
        }
        
        return null;
      }
    }
  } catch (error) {
    console.error('💥 Unexpected error in sendMessageToActiveTab:', error);
    return null;
  }
}

// Command listener (keyboard shortcuts)
chrome.commands.onCommand.addListener(async (command: string) => {
  console.log('⌨️ Command received:', command);
  if (command === 'toggle-overlay') {
    const result = await sendMessageToActiveTab({ action: 'toggle-overlay' });
    if (result) {
      console.log('✅ Overlay toggled via command');
    } else {
      console.log('❌ Failed to toggle overlay via command');
    }
  }
});

// Extension icon click listener
chrome.action.onClicked.addListener(async (tab: chrome.tabs.Tab) => {
  console.log('🖱️ Extension icon clicked');
  if (tab.id) {
    const result = await sendMessageToActiveTab({ action: 'toggle-overlay' });
    if (result) {
      console.log('✅ Overlay toggled via icon click');
    } else {
      console.log('❌ Failed to toggle overlay via icon click');
    }
  }
});

console.log('🎯 Background script loaded and ready');
