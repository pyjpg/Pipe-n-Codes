import React from 'react';
import { APIResponse } from '../functionality/types';

interface StatusMessageProps {
  message: string;
  status: "idle" | "saving" | "success" | "error";
  apiResponse: APIResponse | null;
}

export const StatusMessage: React.FC<StatusMessageProps> = ({ message, status, apiResponse }) => {
  if (!message) return null;

  const getStyle = () => {
    switch (status) {
      case "success": return "bg-green-50 text-green-800 border border-green-200";
      case "error": return "bg-red-50 text-red-800 border border-red-200";
      default: return "bg-blue-50 text-blue-800 border border-blue-200";
    }
  };

  return (
    <div className={`p-3 rounded-lg text-sm ${getStyle()}`}>
      {message}
      {apiResponse?.embedding_info && (
        <div className="mt-2 text-xs">
          <strong>Vector Details:</strong> {apiResponse.embedding_info.chunks_created} chunks, 
          {apiResponse.embedding_info.vector_dimension}D embeddings
          {apiResponse.memory_id && <span className="ml-2"><strong>ID:</strong> {apiResponse.memory_id}</span>}
        </div>
      )}
    </div>
  );
};