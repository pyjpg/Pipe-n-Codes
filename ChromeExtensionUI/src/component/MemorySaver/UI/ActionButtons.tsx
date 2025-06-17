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
      case "saving": return "bg-gray-400 text-white";
      case "success": return "bg-green-500 text-white";
      case "error": return "bg-red-500 text-white";
      default: return "bg-blue-600 text-white hover:bg-blue-700 hover:shadow-lg";
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
        className={`px-4 sm:px-6 py-3 rounded-xl font-medium transition-all duration-200 ${getButtonStyle()}`}
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
        <button className="w-full px-6 py-3 rounded-lg font-medium bg-purple-600 text-white hover:bg-purple-700 hover:shadow-lg transition-all">
          📋 Upload & Embed PDF
        </button>
      </div>
    </div>
  );
};