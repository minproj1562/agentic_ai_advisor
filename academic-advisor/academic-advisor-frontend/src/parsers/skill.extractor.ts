// src/parsers/skill.extractor.ts
import { ExtractedSkills } from '../types/cv.types';

export class SkillExtractor {
  private skillDatabase: Map<string, { category: string; aliases: string[] }>;

  constructor() {
    this.skillDatabase = this.initializeSkillDatabase();
  }

  extract(text: string): ExtractedSkills[] {
    const extractedSkills: ExtractedSkills[] = [];
    const normalizedText = text.toLowerCase();

    for (const [skill, info] of this.skillDatabase.entries()) {
      let found = false;
      let confidence = 0;

      // Check main skill name
      if (this.findSkillInText(normalizedText, skill)) {
        found = true;
        confidence = this.calculateConfidence(normalizedText, skill);
      }

      // Check aliases
      if (!found) {
        for (const alias of info.aliases) {
          if (this.findSkillInText(normalizedText, alias)) {
            found = true;
            confidence = this.calculateConfidence(normalizedText, alias);
            break;
          }
        }
      }

      if (found) {
        extractedSkills.push({
          name: skill,
          category: info.category,
          confidence,
          metadata: {
            synonyms: info.aliases,
            occurrences: this.countOccurrences(normalizedText, skill, info.aliases),
            context: this.extractContext(text, skill)
          }
        });
      }
    }

    return extractedSkills;
  }

  private findSkillInText(text: string, skill: string): boolean {
    // Use word boundaries to match complete words
    const pattern = new RegExp(`\\b${skill.toLowerCase()}\\b`);
    return pattern.test(text);
  }

  private calculateConfidence(text: string, skill: string): number {
    // Base confidence
    let confidence = 60;

    // Increase confidence based on frequency
    const pattern = new RegExp(`\\b${skill.toLowerCase()}\\b`, 'g');
    const matches = text.match(pattern);
    if (matches) {
      confidence += Math.min(matches.length * 5, 20);
    }

    // Check for proficiency indicators
    const proficiencyPattern = new RegExp(
      `(expert|advanced|proficient|experienced|skilled)\\s+.*?${skill}`, 'i'
    );
    if (proficiencyPattern.test(text)) {
      confidence += 15;
    }

    return Math.min(confidence, 95);
  }

  private extractContext(text: string, skill: string): string {
    const pattern = new RegExp(
      `.{0,50}\\b${skill}\\b.{0,50}`, 'i'
    );
    const match = text.match(pattern);
    return match ? match[0].trim() : '';
  }

  private countOccurrences(text: string, skill: string, aliases: string[]): number {
    let count = 0;
    
    // Count main skill
    const skillPattern = new RegExp(`\\b${skill.toLowerCase()}\\b`, 'g');
    const skillMatches = text.match(skillPattern);
    if (skillMatches) count += skillMatches.length;
    
    // Count aliases
    for (const alias of aliases) {
      const aliasPattern = new RegExp(`\\b${alias.toLowerCase()}\\b`, 'g');
      const aliasMatches = text.match(aliasPattern);
      if (aliasMatches) count += aliasMatches.length;
    }
    
    return count;
  }

  private initializeSkillDatabase(): Map<string, { category: string; aliases: string[] }> {
    return new Map([
      ['Python', { category: 'Programming', aliases: ['python3', 'py'] }],
      ['JavaScript', { category: 'Programming', aliases: ['js', 'es6', 'es2015'] }],
      ['TypeScript', { category: 'Programming', aliases: ['ts'] }],
      ['React', { category: 'Framework', aliases: ['react.js', 'reactjs'] }],
      ['Node.js', { category: 'Framework', aliases: ['node', 'nodejs'] }],
      ['Machine Learning', { category: 'AI/ML', aliases: ['ml'] }],
      ['Deep Learning', { category: 'AI/ML', aliases: ['dl', 'neural networks'] }],
      ['Docker', { category: 'DevOps', aliases: ['containerization'] }],
      ['Kubernetes', { category: 'DevOps', aliases: ['k8s'] }],
      ['AWS', { category: 'Cloud', aliases: ['amazon web services'] }],
      ['Git', { category: 'Tools', aliases: ['github', 'gitlab'] }],
      // Add more skills as needed
    ]);
  }
}