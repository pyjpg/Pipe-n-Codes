import { useState, useRef } from 'react';
import { ScrapedMemory, APIResponse } from '../functionality/types';
import { extractText } from '../functionality/scraper';
import { saveMemoryToAPI } from '../functionality/api';

export const useMemorySaver = (scrapedPreview: ScrapedMemory | null) => {
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "success" | "error">("idle");
  const [saveMessage, setSaveMessage] = useState("");
  const [savedItems, setSavedItems] = useState<ScrapedMemory[]>([]);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const [apiResponse, setApiResponse] = useState<APIResponse | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const resetStatus = () => {
    setTimeout(() => {
      setSaveStatus("idle");
      setSaveMessage("");
      setApiResponse(null);
    }, 5000);
  };

  const addSavedItem = (item: ScrapedMemory) => {
    setSavedItems((prev) => {
      const alreadyExists = prev.some(
        (existing) => existing.url === item.url && Math.abs(existing.timestamp - item.timestamp) < 5000
      );
      return alreadyExists ? prev : [item, ...prev];
    });
  };

  const handleSave = async () => {
    if (!scrapedPreview) return;
    
    setSaveStatus("saving");
    setSaveMessage("Processing...");
    setApiResponse(null);

    try {
      let finalPreview = scrapedPreview;
      const isPdf = scrapedPreview.type === "pdf" || scrapedPreview.type === "application/pdf";
      
      if (isPdf) {
        const pdfUrlToFetch = scrapedPreview.pdfUrl || scrapedPreview.url;
        setSaveMessage("Fetching PDF content...");
        
        try {
          const response = await fetch(pdfUrlToFetch, {
            mode: 'cors',
            headers: { 'Accept': 'application/pdf' }
          });
          
          if (!response.ok) {
            throw new Error(`Failed to fetch PDF: ${response.status} ${response.statusText}`);
          }
          
          setSaveMessage("Extracting text from PDF...");
          const blob = await response.blob();
          const file = new File([blob], "document.pdf", { type: "application/pdf" });
          const extractedText = await extractText(file);
          
          finalPreview = {
            ...scrapedPreview,
            bodyText: extractedText || "Could not extract readable text from PDF",
            title: extractedText ? 
              (extractedText.split('\n').find(line => line.trim().length > 0) || scrapedPreview.title).slice(0, 100) : 
              scrapedPreview.title
          };
          
        } catch (pdfError) {
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
        addSavedItem(finalPreview);
      }
    } catch (error: any) {
      setSaveStatus("error");
      setSaveMessage(`Error: ${error.message}`);
    } finally {
      resetStatus();
    }
  };

  const handlePDFUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || file.type !== 'application/pdf') {
      alert('Please select a PDF file');
      return;
    }

    setSaveStatus("saving");
    setSaveMessage("Extracting text from PDF...");
    setApiResponse(null);
    
    try {
      const text = await extractText(file);
      const pdfMemory: ScrapedMemory = {
        title: file.name.replace('.pdf', ''),
        bodyText: text || "Could not extract readable text from this PDF",
        links: [],
        url: `file://${file.name}`,
        timestamp: Date.now(),
        type: 'pdf',
      };

      setSaveMessage("PDF text extracted! Now embedding in vector database...");
      const res = await saveMemoryToAPI(pdfMemory);
      
      setSaveStatus(res.status === "success" ? "success" : "error");
      setSaveMessage(res.message);
      setApiResponse(res);
      
      if (res.status === "success") {
        addSavedItem(pdfMemory);
      }
    } catch (error) {
      setSaveStatus("error");
      setSaveMessage("Failed to process PDF");
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return {
    saveStatus,
    saveMessage,
    savedItems,
    expandedIndex,
    apiResponse,
    fileInputRef,
    setExpandedIndex,
    handleSave,
    handlePDFUpload,
  };
};