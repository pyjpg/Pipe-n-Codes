import { ScrapedMemory, APIResponse } from './types';

export const saveMemoryToAPI = async (memory: ScrapedMemory): Promise<APIResponse> => {
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
        timestamp: memory.timestamp,
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
    return {
      status: "success",
      message: `Memory saved and embedded! ${result.embedding_info ? 
        `Created ${result.embedding_info.chunks_created} chunks with ${result.embedding_info.vector_dimension}D vectors.` : 
        'Successfully processed and stored in vector database.'}`,
      memory_id: result.memory_id,
      embedding_info: result.embedding_info
    };
    
  } catch (error: any) {
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
