import React from 'react';
import { ScrapedMemory } from '../functionality/types';

interface ContentPreviewProps {
  memory: ScrapedMemory;
}

export const ContentPreview: React.FC<ContentPreviewProps> = ({ memory }) => (
  <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 sm:p-6 border">
    <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
      Preview: {memory.title}
    </h3>
    <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
      {memory.type === 'pdf' ? '📋 PDF Document' : '🌐 Web Page'}
      {memory.pageCount && ` • ${memory.pageCount} pages`}
    </div>
    <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-3">
      {memory.bodyText}
    </p>
    {memory.type === 'pdf' && (
      <div className="mt-2 text-xs text-blue-600 dark:text-blue-400">
        Click "Extract & Embed PDF" to process and store in vector database
      </div>
    )}
  </div>
);