import pdfToText from "react-pdftotext";
import { ScrapedMemory } from './types';

export async function extractText(file: File): Promise<string> {
  try {
    const text = await pdfToText(file);
    return text;
  } catch (error) {
    console.error("Error extracting text from PDF:", error);
    throw new Error("Failed to extract text from PDF");
  }
}

const getCleanText = (element: Element): string => {
  const excludeSelectors = [
    'script', 'style', 'nav', 'header', 'footer', '.navigation',
    '.menu', '.sidebar', '.ads', '.advertisement', '[class*="overlay"]',
    '[class*="modal"]', '[class*="popup"]', '[class*="extension"]',
    '.chrome-extension', '[data-extension]', '.social-share',
    '.comments', '.related-posts'
  ];

  const clone = element.cloneNode(true) as Element;
  excludeSelectors.forEach(selector => {
    clone.querySelectorAll(selector).forEach(el => el.remove());
  });

  return (clone.textContent || '')
    .replace(/\s+/g, ' ')
    .replace(/\n\s*\n/g, '\n')
    .trim();
};

const extractWebpageContent = () => {
  const title = document.title || 
    document.querySelector('h1')?.textContent?.trim() ||
    document.querySelector('meta[property="og:title"]')?.getAttribute('content') ||
    "Untitled Page";

  const contentSelectors = [
    'article', 'main', '[role="main"]', '.content', '.post-content',
    '.entry-content', '.article-body', '#content', '.main-content'
  ];

  let mainContent = '';
  for (const selector of contentSelectors) {
    const element = document.querySelector(selector);
    if (element) {
      mainContent = getCleanText(element);
      if (mainContent.length > 200) break;
    }
  }

  if (!mainContent || mainContent.length < 100) {
    mainContent = getCleanText(document.body);
  }

  const links = Array.from(document.links)
    .map(link => link.href)
    .filter(href => href?.startsWith('http'))
    .slice(0, 50);

  return {
    title: title.slice(0, 200),
    bodyText: mainContent.slice(0, 2000),
    links,
    metadata: { wordCount: mainContent.split(/\s+/).length }
  };
};

export const scrapePage = (): ScrapedMemory => {
  const currentUrl = window.location.href;
  
  // Check for PDF
  const selectors = ["iframe[src$='.pdf']", "embed[src$='.pdf']", "object[data$='.pdf']"];
  let pdfUrl: string | null = null;
  
  for (const selector of selectors) {
    const el = document.querySelector(selector) as HTMLElement | null;
    if (el) {
      pdfUrl = el.getAttribute('src') || el.getAttribute('data');
      if (pdfUrl) break;
    }
  }

  const isPdfUrl = currentUrl.toLowerCase().includes('.pdf');
  if (isPdfUrl && !pdfUrl) pdfUrl = currentUrl;

  if (pdfUrl || isPdfUrl) {
    return {
      title: document.title || "PDF Document",
      bodyText: `PDF document detected at: ${pdfUrl || currentUrl}`,
      links: [],
      url: currentUrl,
      timestamp: Date.now(),
      type: 'pdf',
      pdfUrl: pdfUrl || currentUrl,
    };
  }

  const extractedData = extractWebpageContent();
  return {
    ...extractedData,
    url: currentUrl,
    timestamp: Date.now(),
    type: 'webpage',
  };
};
