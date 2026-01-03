// src/parsers/text.parser.ts

export class TextParser {
  async parse(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (event) => {
        try {
          const content = event.target?.result as string;
          resolve(content);
        } catch (error) {
          reject(new Error(`Failed to parse text file: ${error}`));
        }
      };
      
      reader.onerror = () => {
        reject(new Error(`Failed to read file: ${file.name}`));
      };
      
      reader.readAsText(file);
    });
  }

  extractSections(content: string): Record<string, string> {
    const sections: Record<string, string> = {};
    const lines = content.split('\n');
    
    let currentSection = 'general';
    let sectionContent: string[] = [];

    for (const line of lines) {
      const trimmedLine = line.trim();
      
      // Check for section headers
      const sectionMatch = this.detectSectionHeader(trimmedLine);
      if (sectionMatch) {
        // Save previous section
        if (sectionContent.length > 0) {
          sections[currentSection] = sectionContent.join('\n').trim();
          sectionContent = [];
        }
        currentSection = sectionMatch;
      } else if (trimmedLine) {
        sectionContent.push(trimmedLine);
      }
    }

    // Save the last section
    if (sectionContent.length > 0) {
      sections[currentSection] = sectionContent.join('\n').trim();
    }

    return sections;
  }

  private detectSectionHeader(line: string): string | null {
    const sectionPatterns: Record<string, RegExp> = {
      education: /^(education|academic background|qualifications)$/i,
      experience: /^(work experience|employment history|experience|professional experience)$/i,
      skills: /^(skills|technical skills|competencies)$/i,
      projects: /^(projects|personal projects|project experience)$/i,
      certifications: /^(certifications|certificates|licenses)$/i,
      summary: /^(summary|about|profile)$/i,
      contact: /^(contact information|contact details)$/i
    };

    for (const [section, pattern] of Object.entries(sectionPatterns)) {
      if (pattern.test(line)) {
        return section;
      }
    }

    return null;
  }
}