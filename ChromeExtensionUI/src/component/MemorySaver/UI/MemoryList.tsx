import React from 'react';
import { ScrapedMemory } from '../functionality/types';

interface MemoryListProps {
  memories: ScrapedMemory[];
  expandedIndex: number | null;
  onToggleExpanded: (index: number | null) => void;
}

export const MemoryList: React.FC<MemoryListProps> = ({ 
  memories, expandedIndex, onToggleExpanded 
}) => {
  if (memories.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-400 text-4xl mb-4">🧠</div>
        <p className="text-gray-500 dark:text-gray-400">No saved memories yet.</p>
        <p className="text-sm text-gray-400 mt-2">Save a webpage or upload a PDF to get started!</p>
      </div>
    );
  }

  return (
    <div className="space-y-2 max-h-[50vh] sm:max-h-[60vh] overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600 scrollbar-track-transparent">
      {memories.map((item, index) => {
        const isExpanded = index === expandedIndex;
        return (
          <div
            key={`${item.url}-${item.timestamp}`}
            className={`rounded-xl transition-all cursor-pointer border-2 ${
              isExpanded
                ? "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-700"
                : "bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 border-gray-200 dark:border-gray-700"
            }`}
            onClick={() => onToggleExpanded(isExpanded ? null : index)}
          >
            <div className="p-3 sm:p-4">
              <div className="flex items-start space-x-3">
                <div className="text-2xl flex-shrink-0">
                  {item.type === 'pdf' ? '📋' : '🧠'}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-gray-900 dark:text-gray-100 truncate">
                    {item.title}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400 mt-1 flex flex-wrap items-center gap-2">
                    <span>{new Date(item.timestamp).toLocaleDateString()}</span>
                    <span className="hidden sm:inline text-gray-300 dark:text-gray-600">•</span>
                    <span className="hidden sm:inline">{new Date(item.timestamp).toLocaleTimeString()}</span>
                    {item.type === 'pdf' && item.pageCount && (
                      <>
                        <span className="text-gray-300 dark:text-gray-600">•</span>
                        <span>{item.pageCount} pages</span>
                      </>
                    )}
                    <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
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
      })}
    </div>
  );
};
