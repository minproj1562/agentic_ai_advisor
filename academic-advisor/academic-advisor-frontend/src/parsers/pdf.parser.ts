// src/parsers/pdf.parser.ts

export interface PDFParseResult {
  text: string;
  metadata: {
    pages: number;
    title?: string;
    author?: string;
    subject?: string;
    [key: string]: any;
  };
}

interface PDFInfo {
  Title?: string;
  Author?: string;
  Subject?: string;
  Creator?: string;
  Producer?: string;
  CreationDate?: string;
  ModDate?: string;
}

export class PDFParser {
  constructor() {
    // We'll lazy load PDF.js to avoid bundle size issues
  }

  private async loadPDFJS() {
    // Dynamic import to reduce bundle size
    const pdfjsLib = await import('pdfjs-dist');
    // Set up worker
    const pdfjsWorker = await import('pdfjs-dist/build/pdf.worker.min?url');
    pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorker.default;
    return pdfjsLib;
  }

  async parse(
    file: File,
    options?: { onProgress?: (progress: number) => void }
  ): Promise<PDFParseResult> {
    const pdfjsLib = await this.loadPDFJS();
    
    try {
      const arrayBuffer = await file.arrayBuffer();
      const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
      
      let fullText = '';
      const metadata: any = {
        numPages: pdf.numPages,
        fileName: file.name,
        fileSize: file.size
      };

      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const textContent = await page.getTextContent();
        
        const pageText = textContent.items
          .map((item: any) => item.str)
          .join(' ');
        
        fullText += pageText + '\n';
        
        if (options?.onProgress) {
          const progress = Math.round((i / pdf.numPages) * 100);
          options.onProgress(progress);
        }
      }

      // Extract PDF metadata
      try {
        const info = await pdf.getMetadata();
        if (info.metadata) {
          metadata.title = info.metadata.get('dc:title') || info.metadata.get('Title');
          metadata.author = info.metadata.get('dc:creator') || info.metadata.get('Author');
          metadata.subject = info.metadata.get('dc:subject') || info.metadata.get('Subject');
          metadata.creationDate = info.metadata.get('CreationDate');
          metadata.modificationDate = info.metadata.get('ModDate');
        }
        
        if (info.info) {
          // Type-safe access to info properties
          const pdfInfo = info.info as PDFInfo;
          metadata.title = metadata.title || pdfInfo.Title;
          metadata.author = metadata.author || pdfInfo.Author;
          metadata.subject = metadata.subject || pdfInfo.Subject;
          metadata.creator = pdfInfo.Creator;
          metadata.producer = pdfInfo.Producer;
        }
      } catch (metadataError) {
        console.warn('Failed to extract PDF metadata:', metadataError);
      }

      return { 
        text: fullText.trim(), 
        metadata 
      };
    } catch (error) {
      console.error('PDF parsing error:', error);
      throw new Error(`Failed to parse PDF: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  // Alternative method for URL-based PDFs
  async parseFromURL(url: string, options?: { onProgress?: (progress: number) => void }): Promise<PDFParseResult> {
    const pdfjsLib = await this.loadPDFJS();
    
    try {
      const pdf = await pdfjsLib.getDocument(url).promise;
      
      let fullText = '';
      const metadata: any = {
        numPages: pdf.numPages
      };

      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const textContent = await page.getTextContent();
        
        const pageText = textContent.items
          .map((item: any) => item.str)
          .join(' ');
        
        fullText += pageText + '\n';
        
        if (options?.onProgress) {
          const progress = Math.round((i / pdf.numPages) * 100);
          options.onProgress(progress);
        }
      }

      // Extract metadata
      try {
        const info = await pdf.getMetadata();
        if (info.metadata) {
          metadata.title = info.metadata.get('dc:title');
          metadata.author = info.metadata.get('dc:creator');
          metadata.subject = info.metadata.get('dc:subject');
        }
        
        if (info.info) {
          const pdfInfo = info.info as PDFInfo;
          metadata.title = metadata.title || pdfInfo.Title;
          metadata.author = metadata.author || pdfInfo.Author;
          metadata.subject = metadata.subject || pdfInfo.Subject;
        }
      } catch (metadataError) {
        console.warn('Failed to extract PDF metadata:', metadataError);
      }

      return { 
        text: fullText.trim(), 
        metadata 
      };
    } catch (error) {
      console.error('PDF URL parsing error:', error);
      throw new Error(`Failed to parse PDF from URL: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }
}