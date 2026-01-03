// src/services/extraction.service.ts
import { SkillExtractor } from '../parsers/skill.extractor';
import { ExtractedSkills, Experience } from '../types/cv.types';
import { NLPService } from './nlp.service';

export class ExtractionService {
  private skillExtractor: SkillExtractor;
  private nlpService: NLPService;

  constructor() {
    this.skillExtractor = new SkillExtractor();
    this.nlpService = new NLPService();
  }

  async extractSkills(text: string): Promise<ExtractedSkills[]> {
    try {
      // Extract skills using pattern matching
      const patternSkills = this.skillExtractor.extract(text);
      
      // Enhance with NLP if available
      const nlpEnhanced = await this.nlpService.enhanceSkills(patternSkills, text);
      
      // Deduplicate and score
      return this.processSkills(nlpEnhanced);
    } catch (error) {
      console.error('Skill extraction error:', error);
      // Fallback to basic extraction
      return this.skillExtractor.extract(text);
    }
  }

  async extractExperience(text: string): Promise<Experience[]> {
    const experiences: Experience[] = [];
    
    // Pattern for extracting experience entries
    const experiencePattern = /(\d{4})\s*[-–]\s*(\d{4}|present|current)[\s\S]*?(?=\d{4}\s*[-–]|$)/gi;
    const matches = text.matchAll(experiencePattern);

    for (const match of matches) {
      const [fullMatch, startYear, endYear] = match;
      
      // Extract company and position
      const lines = fullMatch.split('\n').filter(l => l.trim());
      if (lines.length >= 2) {
        const endDate = endYear === 'present' || endYear === 'current' ? undefined : `${endYear}-12-31`;
        
        experiences.push({
          startDate: `${startYear}-01-01`,
          endDate: endDate,
          company: lines[0].trim(),
          position: lines[1].trim(), // Use 'position' instead of 'role'
          description: lines.slice(2).join(' ').trim(),
          technologies: [] // You can extract technologies separately if needed
        });
      }
    }

    return experiences;
  }

  private processSkills(skills: ExtractedSkills[]): ExtractedSkills[] {
    // Remove duplicates
    const uniqueSkills = new Map<string, ExtractedSkills>();
    
    for (const skill of skills) {
      const key = skill.name.toLowerCase();
      if (!uniqueSkills.has(key) || skill.confidence > (uniqueSkills.get(key)?.confidence || 0)) {
        uniqueSkills.set(key, skill);
      }
    }

    // Sort by confidence
    return Array.from(uniqueSkills.values())
      .sort((a, b) => b.confidence - a.confidence);
  }
}