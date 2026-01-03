// src/services/parser.service.ts
import { ParsedCV, CVParseOptions } from '.././types/cv.types';

export class ParserService {
  async parse(file: File, options?: CVParseOptions): Promise<ParsedCV> {
    return new Promise((resolve, reject) => {
      // Simulate progress
      if (options?.onProgress) {
        let progress = 0;
        const interval = setInterval(() => {
          progress += 10;
          options.onProgress!(progress);
          if (progress >= 90) {
            clearInterval(interval);
          }
        }, 100);
      }

      // Simulate file reading and parsing
      setTimeout(() => {
        const reader = new FileReader();
        
        reader.onload = (e) => {
          try {
            const content = e.target?.result as string;
            
            // Mock parsed data
            const parsedData: ParsedCV = {
              content: content.substring(0, 1000), // Limit content for demo
              skills: [],
              metadata: {
                fileName: file.name,
                fileSize: file.size,
                uploadedAt: new Date(),
                mimeType: file.type
              },
              personalInfo: {
                name: 'John Doe',
                email: 'john.doe@example.com',
                phone: '+1234567890',
                location: 'New York, NY'
              },
              education: [
                {
                  institution: 'University of Example',
                  degree: 'Bachelor of Science',
                  field: 'Computer Science',
                  startDate: '2018-09',
                  endDate: '2022-05',
                  gpa: 3.8
                }
              ],
              experience: [
                {
                  company: 'Tech Corp',
                  position: 'Software Engineer',
                  startDate: '2022-06',
                  description: 'Developed web applications using React and Node.js',
                  technologies: ['React', 'Node.js', 'TypeScript']
                }
              ]
            };

            if (options?.onProgress) {
              options.onProgress(100);
            }

            resolve(parsedData);
          } catch (error) {
            reject(new Error(`Failed to parse file: ${error}`));
          }
        };

        reader.onerror = () => {
          reject(new Error('Failed to read file'));
        };

        // For demo purposes, we'll just read as text
        // In a real implementation, you'd use proper PDF/text parsing
        reader.readAsText(file);
      }, 1000);
    });
  }

  async parsePDF(file: File): Promise<string> {
    // Mock PDF parsing
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(`Mock PDF content from ${file.name}. This would contain the actual text extracted from the PDF file.`);
      }, 500);
    });
  }

  async parseDOC(file: File): Promise<string> {
    // Mock DOC parsing
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(`Mock DOC content from ${file.name}. This would contain the actual text extracted from the Word document.`);
      }, 500);
    });
  }
}