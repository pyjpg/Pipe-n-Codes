import React, { useEffect, useState, useRef } from "react";
import pdfToText from "react-pdftotext";
import '../index.css';

type ScrapedMemory = {
  title: string;
  bodyText: string;
  links: string[];
  url: string;
  timestamp: number;
  type: 'webpage' | 'pdf' | 'application/pdf';
  pdfUrl?: string;
  pageCount?: number;
};

// API response types
type APIResponse = {
  status: string;
  message: string;
  memory_id?: string;
  embedding_info?: {
    chunks_created: number;
    vector_dimension: number;
  };
};

async function extractText(file: File): Promise<string> {
    try {
      const text = await pdfToText(file);
      console.log("Extracted text:", text);
      return text;
    } catch (error) {
      console.error("Error extracting text from PDF:", error);
      throw new Error("Failed to extract text from PDF");
    }
}

const scrapePage = (): ScrapedMemory => {
  // Try to find embedded PDF URL in iframe or embed tags or object tags
  const selectors = ["iframe[src$='.pdf']", "embed[src$='.pdf']", "object[data$='.pdf']"];
  let pdfUrl: string | null = null;
  
  for (const selector of selectors) {
    const el = document.querySelector(selector) as HTMLElement | null;
    if (el) {
      pdfUrl = el.getAttribute('src') || el.getAttribute('data');
      if (pdfUrl) break;
    }
  }

  // Check if the current URL is directly a PDF
  const currentUrl = window.location.href;
  const isPdfUrl = currentUrl.toLowerCase().includes('.pdf');
  
  if (isPdfUrl && !pdfUrl) {
    pdfUrl = currentUrl;
  }

  // Get page content, but exclude extension overlays and common overlay selectors
  let bodyText = '';
  
  if (pdfUrl || isPdfUrl) {
    // For PDF pages, don't try to extract text from DOM since it's likely a PDF viewer
    bodyText = `PDF document detected at: ${pdfUrl || currentUrl}`;
  } else {
    // For regular webpages, get text but exclude overlays
    const excludeSelectors = [
      '[class*="overlay"]',
      '[class*="modal"]', 
      '[class*="popup"]',
      '[class*="extension"]',
      '[id*="overlay"]',
      '[id*="modal"]',
      '[id*="extension"]',
      '.chrome-extension',
      '[data-extension]'
    ];
    
    // Clone the body to avoid modifying the original
    const bodyClone = document.body.cloneNode(true) as HTMLElement;
    
    // Remove overlay elements
    excludeSelectors.forEach(selector => {
      const elements = bodyClone.querySelectorAll(selector);
      elements.forEach(el => el.remove());
    });
    
    bodyText = bodyClone.innerText.slice(0, 1000);
  }

  return {
    title: document.title || "Untitled Page",
    bodyText: bodyText,
    links: Array.from(document.links).map(link => link.href),
    url: currentUrl,
    timestamp: Date.now(),
    type: pdfUrl || isPdfUrl ? 'pdf' : 'webpage',
    ...(pdfUrl ? { pdfUrl } : {}),
  };
};

const saveMemoryToAPI = async (
  memory: ScrapedMemory
): Promise<APIResponse> => {
  console.log('[API] Saving memory to vector database:', memory);
  
  try {
    const response = await fetch('http://127.0.0.1:8000/memory/save', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        title: memory.title,
        bodyText: memory.bodyText,
        url: memory.url,
        content_type: memory.type,
        timestamp: memory.timestamp, // Move timestamp to top level
        metadata: {
          links: memory.links,
          ...(memory.pdfUrl && { pdf_url: memory.pdfUrl }),
          ...(memory.pageCount && { page_count: memory.pageCount }),
        }
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error: ${response.status} ${response.statusText} - ${errorText}`);
    }

    const result = await response.json();
    console.log('[API] Vector database response:', result);
    
    return {
      status: "success",
      message: `Memory saved and embedded! ${result.embedding_info ? 
        `Created ${result.embedding_info.chunks_created} chunks with ${result.embedding_info.vector_dimension}D vectors.` : 
        'Successfully processed and stored in vector database.'}`,
      memory_id: result.memory_id,
      embedding_info: result.embedding_info
    };
    
  } catch (error: any) {
    console.error('[API] Error saving to vector database:', error);
    
    // Check if it's a network error (API server not running)
    if (error.message.includes('fetch')) {
      return {
        status: "error",
        message: "Cannot connect to vector database API. Is the server running on http://127.0.0.1:8000?"
      };
    }
    
    return {
      status: "error",
      message: `Failed to save to vector database: ${error.message}`
    };
  }
};

const MemorySaver: React.FC = () => {
  const [scrapedPreview, setScrapedPreview] = useState<ScrapedMemory | null>(null);
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "success" | "error">("idle");
  const [saveMessage, setSaveMessage] = useState("");
  const [savedItems, setSavedItems] = useState<ScrapedMemory[]>([]);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const [apiResponse, setApiResponse] = useState<APIResponse | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const isPdf = 
     scrapedPreview?.type === "pdf" 
  || scrapedPreview?.type === "application/pdf";
  useEffect(() => {
    const scraped = scrapePage();
    console.log("Scraped current webpage:", scraped);
    setScrapedPreview(scraped);
  }, []);

  const handleSave = async () => {
    if (!scrapedPreview) return;
    setSaveStatus("saving");
    setSaveMessage("Processing...");
    setApiResponse(null);

    try {
      let finalPreview = scrapedPreview;
      console.log("Saving memory:", scrapedPreview);
      
      // Handle PDF extraction
      if (isPdf) {
        let pdfUrlToFetch = scrapedPreview.pdfUrl || scrapedPreview.url;
        
        setSaveMessage("Fetching PDF content...");
        console.log("Fetching PDF from URL:", pdfUrlToFetch);
        
        try {
          const response = await fetch(pdfUrlToFetch, {
            mode: 'cors',
            headers: {
              'Accept': 'application/pdf'
            }
          });
          
          if (!response.ok) {
            throw new Error(`Failed to fetch PDF: ${response.status} ${response.statusText}`);
          }
          
          const contentType = response.headers.get("content-type") || "";
          console.log("PDF content-type:", contentType);
          
          if (!contentType.includes("pdf") && !contentType.includes("application/octet-stream")) {
            throw new Error(`URL does not point to a PDF file, content-type: ${contentType}`);
          }
          
          setSaveMessage("Extracting text from PDF...");
          const blob = await response.blob();
          const file = new File([blob], "document.pdf", { type: "application/pdf" });

          const extractedText = await extractText(file);
          console.log("Extracted text from PDF (first 300 chars):", extractedText.slice(0, 300));
          
          finalPreview = {
            ...scrapedPreview,
            bodyText: extractedText || "Could not extract readable text from PDF",
            title: extractedText ? 
              (extractedText.split('\n').find(line => line.trim().length > 0) || scrapedPreview.title).slice(0, 100) : 
              scrapedPreview.title
          };
          
        } catch (pdfError) {
          console.error("PDF processing error:", pdfError);
          // Fallback: save the PDF reference without extracted text
          finalPreview = {
            ...scrapedPreview,
            bodyText: `PDF document at: ${pdfUrlToFetch}\n\nError extracting text: ${pdfError.message}`,
          };
        }
      }

      setSaveMessage("Embedding content in vector database...");
      const res = await saveMemoryToAPI(finalPreview);
      setSaveStatus(res.status === "success" ? "success" : "error");
      setSaveMessage(res.message);
      setApiResponse(res);

      if (res.status === "success") {
        setSavedItems((prev) => {
          const alreadyExists = prev.some(
            (item) => item.url === finalPreview.url && Math.abs(item.timestamp - finalPreview.timestamp) < 5000
          );
          return alreadyExists ? prev : [finalPreview, ...prev];
        });
      }
    } catch (error: any) {
      console.error("Error saving memory:", error);
      setSaveStatus("error");
      setSaveMessage(`Error: ${error.message}`);
    } finally {
      setTimeout(() => {
        setSaveStatus("idle");
        setSaveMessage("");
        setApiResponse(null);
      }, 5000);
    }
  };

  const handlePDFUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    console.log('[Upload Triggered]', file);
    if (!file || file.type !== 'application/pdf') {
      alert('Please select a PDF file');
      return;
    }

    setSaveStatus("saving");
    setSaveMessage("Extracting text from PDF...");
    setApiResponse(null);
    
    try {
      const text = await extractText(file);
      console.log('[Extracted]', { textSnippet: text.slice(0, 300) });

      const pdfMemory: ScrapedMemory = {
        title: file.name.replace('.pdf', ''),
        bodyText: text || "Could not extract readable text from this PDF",
        links: [],
        url: `file://${file.name}`,
        timestamp: Date.now(),
        type: 'pdf',
      };

      setScrapedPreview(pdfMemory);
      setSaveMessage("PDF text extracted! Now embedding in vector database...");

      // Automatically save to vector database after successful extraction
      const res = await saveMemoryToAPI(pdfMemory);
      console.log('[Save result]', res);
      
      setSaveStatus(res.status === "success" ? "success" : "error");
      setSaveMessage(res.message);
      setApiResponse(res);
      
      if (res.status === "success") {
        setSavedItems((prev) => [pdfMemory, ...prev]);
      }

    } catch (error) {
      console.error('[PDF Processing Error]', error);
      setSaveStatus("error");
      setSaveMessage("Failed to process PDF");
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto p-6">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Memory Saver
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Save web pages and PDFs to vector database for semantic search
        </p>
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <button
          onClick={handleSave}
          disabled={saveStatus === "saving"}
          className={`px-6 py-3 rounded-lg font-medium transition-all ${
            saveStatus === "saving"
              ? "bg-gray-400 text-white"
              : saveStatus === "success"
              ? "bg-green-500 text-white"
              : saveStatus === "error"
              ? "bg-red-500 text-white"
              : "bg-blue-600 text-white hover:bg-blue-700 hover:shadow-lg"
          }`}
        >
          {saveStatus === "saving"
            ? "Processing..."
            : saveStatus === "success"
            ? "Saved to Vector DB!"
            : saveStatus === "error"
            ? "Error"
            : scrapedPreview?.type === 'pdf' ? "🧠 Extract & Embed PDF" : "🧠 Save to Vector Database"}
        </button>

        <div className="relative">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handlePDFUpload}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
          <button className="w-full px-6 py-3 rounded-lg font-medium bg-purple-600 text-white hover:bg-purple-700 hover:shadow-lg transition-all">
            📋 Upload & Embed PDF
          </button>
        </div>
      </div>

      {saveMessage && (
        <div className={`p-3 rounded-lg text-sm ${
          saveStatus === "success" 
            ? "bg-green-50 text-green-800 border border-green-200" 
            : saveStatus === "error"
            ? "bg-red-50 text-red-800 border border-red-200"
            : "bg-blue-50 text-blue-800 border border-blue-200"
        }`}>
          {saveMessage}
          {apiResponse?.embedding_info && (
            <div className="mt-2 text-xs">
              <strong>Vector Details:</strong> {apiResponse.embedding_info.chunks_created} chunks, 
              {apiResponse.embedding_info.vector_dimension}D embeddings
              {apiResponse.memory_id && <span className="ml-2"><strong>ID:</strong> {apiResponse.memory_id}</span>}
            </div>
          )}
        </div>
      )}

      {/* Preview */}
      {scrapedPreview && (
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border">
          <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Preview: {scrapedPreview.title}
          </h3>
          <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
            {scrapedPreview.type === 'pdf' ? '📋 PDF Document' : '🌐 Web Page'}
            {scrapedPreview.pageCount && ` • ${scrapedPreview.pageCount} pages`}
          </div>
          <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-3">
            {scrapedPreview.bodyText}
          </p>
          {scrapedPreview.type === 'pdf' && (
            <div className="mt-2 text-xs text-blue-600 dark:text-blue-400">
              Click "Extract & Embed PDF" to process and store in vector database
            </div>
          )}
        </div>
      )}

      {/* Saved Items List */}
      <div className="space-y-3">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
          Saved Memories ({savedItems.length})
        </h2>
        
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {savedItems.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-400 text-4xl mb-4">🧠</div>
              <p className="text-gray-500 dark:text-gray-400">No saved memories yet.</p>
              <p className="text-sm text-gray-400 mt-2">Save a webpage or upload a PDF to get started!</p>
            </div>
          ) : (
            savedItems.map((item, index) => {
              const isExpanded = index === expandedIndex;
              return (
                <div
                  key={`${item.url}-${item.timestamp}`}
                  className={`rounded-xl transition-all cursor-pointer border-2 ${
                    isExpanded
                      ? "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-700"
                      : "bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 border-gray-200 dark:border-gray-700"
                  }`}
                  onClick={() => setExpandedIndex(isExpanded ? null : index)}
                >
                  <div className="p-4">
                    <div className="flex items-start space-x-3">
                      <div className="text-2xl flex-shrink-0">
                        {item.type === 'pdf' ? '📋' : '🧠'}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-900 dark:text-gray-100 truncate">
                          {item.title}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                          {new Date(item.timestamp).toLocaleString()}
                          {item.type === 'pdf' && item.pageCount && ` • ${item.pageCount} pages`}
                          <span className="ml-2 px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                            ✓ Embedded
                          </span>
                        </div>
                        {!isExpanded && (
                          <div className="text-sm text-gray-600 dark:text-gray-300 mt-2 line-clamp-2">
                            {item.bodyText}
                          </div>
                        )}
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600 space-y-3">
                        <div>
                          <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Content:</h4>
                          <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                            {item.bodyText}
                          </p>
                        </div>

                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          <strong>Source:</strong> {item.url}
                        </div>

                        {item.links.length > 0 && (
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            <strong>Links found ({item.links.length}):</strong>
                            <ul className="list-disc list-inside mt-1 space-y-1">
                              {item.links.slice(0, 5).map((link, i) => (
                                <li key={i} className="truncate">
                                  <a
                                    href={link}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-blue-500 hover:underline"
                                    onClick={(e) => e.stopPropagation()}
                                  >
                                    {link}
                                  </a>
                                </li>
                              ))}
                              {item.links.length > 5 && (
                                <li className="italic text-gray-400">
                                  +{item.links.length - 5} more links
                                </li>
                              )}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};

export default MemorySaver;