export type ScrapedMemory = {
  title: string;
  bodyText: string;
  links: string[];
  url: string;
  timestamp: number;
  type: 'webpage' | 'pdf' | 'application/pdf';
  pdfUrl?: string;
  pageCount?: number;
  metadata?: {
    description?: string;
    keywords?: string;
    author?: string;
    publishDate?: string;
    wordCount?: number;
  }
};

export type APIResponse = {
  status: string;
  message: string;
  memory_id?: string;
  embedding_info?: {
    chunks_created: number;
    vector_dimension: number;
  };
};
