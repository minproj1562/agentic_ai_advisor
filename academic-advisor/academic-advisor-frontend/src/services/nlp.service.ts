// src/services/nlp.service.ts
import { ExtractedSkills } from '../types/cv.types';

export class NLPService {
  private skillSynonyms: Map<string, string[]> = new Map([
    ['javascript', ['js', 'ecmascript']],
    ['typescript', ['ts']],
    ['python', ['py']],
    ['react', ['reactjs', 'react.js']],
    ['node', ['nodejs', 'node.js']],
    ['html', ['html5']],
    ['css', ['css3']],
    ['aws', ['amazon web services']],
    ['azure', ['microsoft azure']],
    ['gcp', ['google cloud platform']],
  ]);

  private skillCategories: Map<string, string> = new Map([
    // Programming Languages
    ['javascript', 'Programming Language'],
    ['typescript', 'Programming Language'],
    ['python', 'Programming Language'],
    ['java', 'Programming Language'],
    ['c++', 'Programming Language'],
    ['c#', 'Programming Language'],
    ['go', 'Programming Language'],
    ['rust', 'Programming Language'],
    ['swift', 'Programming Language'],
    ['kotlin', 'Programming Language'],
    
    // Frontend Frameworks
    ['react', 'Frontend Framework'],
    ['angular', 'Frontend Framework'],
    ['vue', 'Frontend Framework'],
    ['svelte', 'Frontend Framework'],
    
    // Backend Frameworks
    ['node', 'Backend Framework'],
    ['express', 'Backend Framework'],
    ['django', 'Backend Framework'],
    ['flask', 'Backend Framework'],
    ['spring', 'Backend Framework'],
    ['laravel', 'Backend Framework'],
    
    // Databases
    ['mysql', 'Database'],
    ['postgresql', 'Database'],
    ['mongodb', 'Database'],
    ['redis', 'Database'],
    ['sqlite', 'Database'],
    ['oracle', 'Database'],
    
    // Tools & Platforms
    ['docker', 'DevOps'],
    ['kubernetes', 'DevOps'],
    ['aws', 'Cloud Platform'],
    ['azure', 'Cloud Platform'],
    ['gcp', 'Cloud Platform'],
    ['git', 'Version Control'],
    ['jenkins', 'CI/CD'],
  ]);

  async enhanceSkills(skills: ExtractedSkills[], context: string): Promise<ExtractedSkills[]> {
    const enhancedSkills: ExtractedSkills[] = [];

    for (const skill of skills) {
      // Create a new skill object to avoid mutation
      const enhancedSkill: ExtractedSkills = {
        name: skill.name,
        category: skill.category || this.categorizeSkill(skill.name),
        confidence: this.calculateConfidence(skill.name, context, skill.confidence),
      };

      // Add metadata if we have synonyms or other enhancements
      const synonyms = this.getSynonyms(enhancedSkill.name);
      if (synonyms.length > 0) {
        enhancedSkill.metadata = {
          synonyms,
          occurrences: this.countOccurrences(enhancedSkill.name, context),
          context: this.extractSkillContext(enhancedSkill.name, context)
        };
      }

      enhancedSkills.push(enhancedSkill);
    }

    return enhancedSkills;
  }

  async extractEntities(text: string): Promise<{ type: string; text: string; confidence: number }[]> {
    // Mock entity extraction - in real implementation, use a proper NLP library
    const entities: { type: string; text: string; confidence: number }[] = [];
    
    // Extract potential technologies
    const techPatterns = [
      { pattern: /\b(react|angular|vue|svelte)\b/gi, type: 'Frontend Framework' },
      { pattern: /\b(node\.?js|express|django|flask|spring)\b/gi, type: 'Backend Framework' },
      { pattern: /\b(javascript|typescript|python|java|c\+\+|c#|go|rust)\b/gi, type: 'Programming Language' },
      { pattern: /\b(mysql|postgresql|mongodb|redis|sqlite)\b/gi, type: 'Database' },
      { pattern: /\b(docker|kubernetes|aws|azure|gcp|git)\b/gi, type: 'Tool/Platform' },
    ];

    for (const { pattern, type } of techPatterns) {
      const matches = text.match(pattern);
      if (matches) {
        matches.forEach(match => {
          entities.push({
            type,
            text: match.toLowerCase(),
            confidence: 0.8
          });
        });
      }
    }

    return entities;
  }

  async analyzeSentiment(text: string): Promise<{ score: number; magnitude: number }> {
    // Mock sentiment analysis
    const positiveWords = ['excellent', 'great', 'good', 'successful', 'effective', 'efficient'];
    const negativeWords = ['poor', 'bad', 'inefficient', 'failed', 'challenging', 'difficult'];
    
    let score = 0;
    const words = text.toLowerCase().split(/\W+/);
    
    words.forEach(word => {
      if (positiveWords.includes(word)) score += 1;
      if (negativeWords.includes(word)) score -= 1;
    });

    return {
      score: Math.max(-1, Math.min(1, score / 10)),
      magnitude: Math.abs(score) / words.length
    };
  }

  private categorizeSkill(skillName: string): string {
    const normalizedName = skillName.toLowerCase();
    
    for (const [skill, category] of this.skillCategories) {
      if (normalizedName.includes(skill)) {
        return category;
      }
    }

    // Default categories based on common patterns
    if (normalizedName.includes('js') || normalizedName.includes('script')) {
      return 'Programming Language';
    }
    if (normalizedName.includes('sql') || normalizedName.includes('database')) {
      return 'Database';
    }
    if (normalizedName.includes('cloud') || normalizedName.includes('aws') || normalizedName.includes('azure')) {
      return 'Cloud Platform';
    }
    if (normalizedName.includes('tool') || normalizedName.includes('software')) {
      return 'Tool';
    }

    return 'Technical Skill';
  }

  private calculateConfidence(skillName: string, context: string, baseConfidence: number = 0.5): number {
    const normalizedSkill = skillName.toLowerCase();
    const normalizedContext = context.toLowerCase();
    
    let confidence = baseConfidence;
    
    // Increase confidence if skill is mentioned multiple times
    const occurrences = (normalizedContext.match(new RegExp(normalizedSkill, 'g')) || []).length;
    confidence += Math.min(0.3, occurrences * 0.1);
    
    // Increase confidence if skill is near relevant context
    const relevantContext = ['experienced in', 'proficient with', 'skilled in', 'expertise in', 'knowledge of'];
    if (relevantContext.some(ctx => normalizedContext.includes(ctx))) {
      confidence += 0.2;
    }
    
    return Math.min(1, confidence);
  }

  private getSynonyms(skillName: string): string[] {
    const normalizedName = skillName.toLowerCase();
    return this.skillSynonyms.get(normalizedName) || [];
  }

  private countOccurrences(skill: string, text: string): number {
    const pattern = new RegExp(`\\b${skill}\\b`, 'gi');
    const matches = text.match(pattern);
    return matches ? matches.length : 0;
  }

  private extractSkillContext(skill: string, text: string): string {
    const skillIndex = text.toLowerCase().indexOf(skill.toLowerCase());
    if (skillIndex === -1) return '';

    const start = Math.max(0, skillIndex - 30);
    const end = Math.min(text.length, skillIndex + skill.length + 30);
    
    return text.substring(start, end).trim();
  }

  async extractKeyPhrases(text: string): Promise<string[]> {
    // Mock key phrase extraction
    const sentences = text.split(/[.!?]+/);
    const keyPhrases: string[] = [];
    
    sentences.forEach(sentence => {
      const words = sentence.trim().split(/\s+/);
      if (words.length >= 3 && words.length <= 7) {
        // Simple heuristic: medium-length sentences might be key phrases
        keyPhrases.push(sentence.trim());
      }
    });
    
    return keyPhrases.slice(0, 10); // Return top 10
  }
}