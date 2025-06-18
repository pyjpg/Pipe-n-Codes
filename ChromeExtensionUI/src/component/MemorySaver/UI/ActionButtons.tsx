import React from 'react';

interface ActionButtonsProps {
  onSave: () => void;
  onFileUpload: (event: React.ChangeEvent<HTMLInputElement>) => void;
  saveStatus: "idle" | "saving" | "success" | "error";
  isPdf: boolean;
  fileInputRef: React.RefObject<HTMLInputElement>;
}

export const ActionButtons: React.FC<ActionButtonsProps> = ({
  onSave, onFileUpload, saveStatus, isPdf, fileInputRef
}) => {
 const getButtonStyle = () => {
  switch (saveStatus) {
    case "saving":
      return "bg-gray-400 text-white border border-gray-500";
    case "success":
      return "bg-green-500 text-white border border-green-700";
    case "error":
      return "bg-red-500 text-white border border-red-700";
    default:
      return "bg-blue-600 text-white border border-blue-700 hover:bg-blue-700 hover:shadow-lg";
  }
}; 

  const getButtonText = () => {
    switch (saveStatus) {
      case "saving": return "Processing...";
      case "success": return "Saved to Vector DB!";
      case "error": return "Error";
      default: return isPdf ? "🧠 Extract & Embed PDF" : "🧠 Save to Vector Database";
    }
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
      <button
        onClick={onSave}
        disabled={saveStatus === "saving"}
        className={`inline-flex items-center justify-center px-4 py-5 sm:px-6 rounded-xl font-medium shadow transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${getButtonStyle()}`}
      >
        {getButtonText()}
      </button>

      <div className="relative">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={onFileUpload}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        <button
          className="inline-flex items-center justify-center px-4 py-5 sm:px-6 rounded-xl font-medium shadow transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 border border-purple-700 bg-purple-600 text-white hover:bg-purple-900 hover:shadow-lg cursor-pointer"
        >
          📋 Upload & Embed PDF
        </button>
      </div>
    </div>
  );
};