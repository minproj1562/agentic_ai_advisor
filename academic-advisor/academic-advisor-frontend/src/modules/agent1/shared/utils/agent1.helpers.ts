// modules/agent1/shared/utils/agent1.helpers.ts
// FIXED: Create local types since the import is missing
interface PerformanceTrend {
  studentId: string;
  dataPoints: Array<{
    date: string;
    gpa: number;
    percentile?: number;
    improvement?: number;
    confidence?: number;
  }>;
  currentGPA?: number;
  percentile?: number;
  subjects?: SubjectData[];
  lastUpdated?: string;
  projection?: any[];
}

interface SubjectData {
  id: string;
  name: string;
  category: string;
  credits: number;
  currentGrade: number;
  previousGrade?: number;
  classAverage?: number;
  rank?: number;
  totalStudents?: number;
  attendance?: number;
  completedAssignments?: number;
  totalAssignments?: number;
  weakTopics?: string[];
  recommendation?: string;
  trend: number;
}

interface WeakArea {
  id: string;
  name: string;
  currentScore: number;
  targetScore: number;
  classAverage?: number;
  credits?: number;
  impactOnGPA?: number;
  difficulty?: number;
  severity?: 'low' | 'medium' | 'high' | 'critical';
  estimatedImprovementTime?: string;
  potentialImprovement?: number;
  subject?: string;
  priority?: number;
}

// FIXED: Create local formatter functions since the import is missing
const formatGPA = (value: number | undefined | null): string => {
  if (value === undefined || value === null) return 'N/A';
  return value.toFixed(2);
};

const formatPercentage = (value: number | undefined | null, decimals: number = 1): string => {
  if (value === undefined || value === null) return 'N/A';
  return `${value.toFixed(decimals)}%`;
};

/**
 * Calculate overall performance score
 */
export function calculatePerformanceScore(performance: PerformanceTrend): number {
  if (!performance.dataPoints || performance.dataPoints.length === 0) return 0;

  const factors = {
    currentGPA: (performance.currentGPA || 0) / 4 * 0.4,
    trend: calculateTrendScore(performance) * 0.3,
    consistency: calculateConsistencyScore(performance) * 0.2,
    improvement: calculateImprovementScore(performance) * 0.1
  };

  return Object.values(factors).reduce((sum, score) => sum + score, 0) * 100;
}

/**
 * Calculate trend score
 */
function calculateTrendScore(performance: PerformanceTrend): number {
  if (!performance.dataPoints || performance.dataPoints.length < 2) return 0.5;

  const recent = performance.dataPoints.slice(-5);
  const trend = recent[recent.length - 1].gpa - recent[0].gpa;
  
  return Math.min(Math.max((trend + 0.5) / 1, 0), 1);
}

/**
 * Calculate consistency score
 */
function calculateConsistencyScore(performance: PerformanceTrend): number {
  if (!performance.dataPoints || performance.dataPoints.length < 2) return 0.5;

  const gpas = performance.dataPoints.map(d => d.gpa);
  const mean = gpas.reduce((sum: number, gpa: number) => sum + gpa, 0) / gpas.length;
  const variance = gpas.reduce((sum: number, gpa: number) => sum + Math.pow(gpa - mean, 2), 0) / gpas.length;
  const stdDev = Math.sqrt(variance);
  
  return Math.max(0, 1 - stdDev);
}

/**
 * Calculate improvement score
 */
function calculateImprovementScore(performance: PerformanceTrend): number {
  if (!performance.dataPoints || performance.dataPoints.length < 2) return 0.5;

  const first = performance.dataPoints[0].gpa;
  const last = performance.dataPoints[performance.dataPoints.length - 1].gpa;
  const improvement = (last - first) / first;
  
  return Math.min(Math.max((improvement + 0.2) / 0.4, 0), 1);
}

/**
 * Generate performance summary
 */
export function generatePerformanceSummary(performance: PerformanceTrend): string {
  const score = calculatePerformanceScore(performance);
  const gpa = performance.currentGPA || 0;
  const percentile = performance.percentile || 50;

  if (score >= 80) {
    return `Excellent performance! You're in the top ${100 - percentile}% with a ${formatGPA(gpa)} GPA.`;
  } else if (score >= 60) {
    return `Good progress! Your current GPA is ${formatGPA(gpa)}, ranking at ${percentile}th percentile.`;
  } else if (score >= 40) {
    return `You're making steady progress with a ${formatGPA(gpa)} GPA. Focus on consistency.`;
  } else {
    return `Your current GPA is ${formatGPA(gpa)}. Let's work on improvement strategies.`;
  }
}

/**
 * Identify critical areas
 */
export function identifyCriticalAreas(subjects: SubjectData[]): SubjectData[] {
  return subjects
    .filter(s => s.currentGrade < 60 || (s.classAverage && s.currentGrade < s.classAverage * 0.8))
    .sort((a, b) => (a.credits * (100 - a.currentGrade)) - (b.credits * (100 - b.currentGrade)));
}

/**
 * Calculate potential GPA impact
 */
export function calculateGPAImpact(
  currentGPA: number,
  totalCredits: number,
  subjectCredits: number,
  currentGrade: number,
  targetGrade: number
): number {
  const currentPoints = currentGPA * totalCredits;
  const currentSubjectPoints = (currentGrade / 25) * subjectCredits;
  const targetSubjectPoints = (targetGrade / 25) * subjectCredits;
  
  const newPoints = currentPoints - currentSubjectPoints + targetSubjectPoints;
  const newGPA = newPoints / totalCredits;
  
  return newGPA - currentGPA;
}

/**
 * Generate improvement roadmap
 */
export function generateImprovementRoadmap(weakAreas: WeakArea[]): any[] {
  const roadmap = [];
  
  // Sort by priority
  const sorted = [...weakAreas].sort((a, b) => (b.priority || 0) - (a.priority || 0));
  
  // Group into phases
  const phases = {
    immediate: sorted.slice(0, 2),
    shortTerm: sorted.slice(2, 5),
    longTerm: sorted.slice(5)
  };
  
  if (phases.immediate.length > 0) {
    roadmap.push({
      phase: 'Immediate Action (Week 1-2)',
      areas: phases.immediate,
      focus: 'Critical weak areas requiring urgent attention'
    });
  }
  
  if (phases.shortTerm.length > 0) {
    roadmap.push({
      phase: 'Short-term Goals (Week 3-6)',
      areas: phases.shortTerm,
      focus: 'Build foundation and improve core competencies'
    });
  }
  
  if (phases.longTerm.length > 0) {
    roadmap.push({
      phase: 'Long-term Development (Week 7+)',
      areas: phases.longTerm,
      focus: 'Sustained improvement and mastery'
    });
  }
  
  return roadmap;
}

/**
 * Calculate study time allocation
 */
export function calculateStudyTimeAllocation(
  subjects: SubjectData[],
  totalAvailableHours: number
): Record<string, number> {
  const allocation: Record<string, number> = {};
  
  // Calculate weight for each subject based on credits and performance gap
  const weights = subjects.map(subject => {
    const performanceGap = Math.max(0, 85 - subject.currentGrade); // Target 85%
    const weight = subject.credits * (1 + performanceGap / 100);
    return { id: subject.id, weight };
  });
  
  const totalWeight = weights.reduce((sum, w) => sum + w.weight, 0);
  
  // Allocate hours proportionally
  weights.forEach(({ id, weight }) => {
    allocation[id] = Math.round((weight / totalWeight) * totalAvailableHours * 10) / 10;
  });
  
  return allocation;
}

/**
 * Generate study schedule
 */
export function generateStudySchedule(
  subjects: SubjectData[],
  hoursPerDay: number,
  daysPerWeek: number = 7
): any[] {
  // FIXED: Properly typed schedule array
  const schedule: any[] = [];
  const totalHours = hoursPerDay * daysPerWeek;
  const allocation = calculateStudyTimeAllocation(subjects, totalHours);
  
  let currentDay = 0;
  let currentDayHours = 0;
  
  Object.entries(allocation).forEach(([subjectId, hours]) => {
    const subject = subjects.find(s => s.id === subjectId);
    if (!subject) return;
    
    let remainingHours = hours;
    
    while (remainingHours > 0) {
      const availableToday = hoursPerDay - currentDayHours;
      const hoursToday = Math.min(remainingHours, availableToday);
      
      if (hoursToday > 0) {
        schedule.push({
          day: currentDay + 1,
          subject: subject.name,
          hours: hoursToday,
          focus: subject.weakTopics?.[0] || 'General review'
        });
        
        currentDayHours += hoursToday;
        remainingHours -= hoursToday;
      }
      
      if (currentDayHours >= hoursPerDay) {
        currentDay++;
        currentDayHours = 0;
      }
    }
  });
  
  return schedule;
}

/**
 * Calculate success probability
 */
export function calculateSuccessProbability(
  currentGPA: number,
  targetGPA: number,
  timeframe: number, // weeks
  currentTrend: number
): number {
  const requiredImprovement = targetGPA - currentGPA;
  const requiredWeeklyRate = requiredImprovement / timeframe;
  
  // Compare required rate with current trend
  const probabilityFactor = currentTrend / requiredWeeklyRate;
  
  // Adjust for difficulty
  const difficulty = requiredImprovement / currentGPA;
  const difficultyAdjustment = Math.max(0, 1 - difficulty);
  
  // Calculate probability
  let probability = probabilityFactor * difficultyAdjustment;
  
  // Clamp between 0 and 1
  probability = Math.min(Math.max(probability, 0), 1);
  
  return probability;
}

/**
 * Generate motivational message
 */
export function generateMotivationalMessage(
  performance: PerformanceTrend,
  improvement: number
): string {
  const messages = {
    highImprovement: [
      "Outstanding progress! You're on fire! 🔥",
      "Incredible improvement! Keep up the amazing work! 🌟",
      "You're crushing it! This is what dedication looks like! 💪"
    ],
    moderateImprovement: [
      "Great job! You're moving in the right direction! 📈",
      "Nice progress! Keep pushing forward! 👍",
      "You're doing well! Stay consistent! ⭐"
    ],
    lowImprovement: [
      "Every step counts! Keep going! 🚀",
      "Progress is progress! Stay focused! 💡",
      "You've got this! One day at a time! 🌱"
    ],
    declining: [
      "Don't give up! Let's turn this around together! 💪",
      "It's okay to struggle. Let's make a plan! 📝",
      "You can do this! Let's find what works for you! 🎯"
    ]
  };
  
  let category: keyof typeof messages;
  if (improvement > 10) category = 'highImprovement';
  else if (improvement > 5) category = 'moderateImprovement';
  else if (improvement >= 0) category = 'lowImprovement';
  else category = 'declining';
  
  const categoryMessages = messages[category];
  return categoryMessages[Math.floor(Math.random() * categoryMessages.length)];
}

/**
 * Calculate streak
 */
export function calculateStreak(dataPoints: any[]): number {
  if (!dataPoints || dataPoints.length < 2) return 0;
  
  let streak = 0;
  for (let i = dataPoints.length - 1; i > 0; i--) {
    if (dataPoints[i].gpa > dataPoints[i - 1].gpa) {
      streak++;
    } else {
      break;
    }
  }
  
  return streak;
}

/**
 * Determine risk level
 */
export function determineRiskLevel(
  gpa: number,
  trend: number,
  attendance: number
): 'low' | 'medium' | 'high' | 'critical' {
  let riskScore = 0;
  
  // GPA factor
  if (gpa < 2.0) riskScore += 3;
  else if (gpa < 2.5) riskScore += 2;
  else if (gpa < 3.0) riskScore += 1;
  
  // Trend factor
  if (trend < -0.2) riskScore += 2;
  else if (trend < 0) riskScore += 1;
  
  // Attendance factor
  if (attendance < 70) riskScore += 2;
  else if (attendance < 85) riskScore += 1;
  
  if (riskScore >= 5) return 'critical';
  if (riskScore >= 3) return 'high';
  if (riskScore >= 1) return 'medium';
  return 'low';
}

/**
 * Format time to target
 */
export function formatTimeToTarget(weeks: number): string {
  if (weeks < 1) return 'Less than a week';
  if (weeks === 1) return '1 week';
  if (weeks < 4) return `${weeks} weeks`;
  
  const months = Math.round(weeks / 4);
  if (months === 1) return '1 month';
  if (months < 12) return `${months} months`;
  
  const years = Math.round(months / 12);
  return `${years} ${years === 1 ? 'year' : 'years'}`;
}