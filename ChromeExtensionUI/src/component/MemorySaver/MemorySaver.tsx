import React, { useEffect, useState } from "react";
import { scrapePage } from "./functionality/scraper";
import { useMemorySaver } from "./hooks/useMemorySaver";
import { ActionButtons } from "./UI/ActionButtons";
import { StatusMessage } from "./UI/StatusMessage";
import { ContentPreview } from "./UI/ContentPreview";
import { MemoryList } from "./UI/MemoryList";
import '../../index.css';

const MemorySaver: React.FC = () => {
  const [scrapedPreview, setScrapedPreview] = useState(null);
  
  const {
    saveStatus,
    saveMessage,
    savedItems,
    expandedIndex,
    apiResponse,
    fileInputRef,
    setExpandedIndex,
    handleSave,
    handlePDFUpload,
  } = useMemorySaver(scrapedPreview);

  useEffect(() => {
    const scraped = scrapePage();
    setScrapedPreview(scraped);
  }, []);

  const isPdf = scrapedPreview?.type === "pdf" || scrapedPreview?.type === "application/pdf";

  return (
    <div className="space-y-4 sm:space-y-6 max-w-4xl mx-auto p-4 sm:p-6 h-full overflow-hidden flex flex-col">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Memory Saver
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Save web pages and PDFs to vector database for semantic search
        </p>
      </div>

      <ActionButtons
        onSave={handleSave}
        onFileUpload={handlePDFUpload}
        saveStatus={saveStatus}
        isPdf={isPdf}
        fileInputRef={fileInputRef}
      />

      <StatusMessage
        message={saveMessage}
        status={saveStatus}
        apiResponse={apiResponse}
      />

      {scrapedPreview && <ContentPreview memory={scrapedPreview} />}

      <div className="flex-1 min-h-0 space-y-3">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
          Saved Memories ({savedItems.length})
        </h2>
        
        <MemoryList
          memories={savedItems}
          expandedIndex={expandedIndex}
          onToggleExpanded={setExpandedIndex}
        />
      </div>
    </div>
  );
};

export default MemorySaver;