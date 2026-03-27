// src/utils/interestPersistence.ts
// Shared localStorage utility for interest data persistence
// This ensures data survives tab switches, page refreshes, and API failures

const INTERESTS_STORAGE_KEY = 'academic_advisor_interests';

export interface PersistedInterests {
  interests: string[];
  careerGoals: string[];
  skills: string[];
  electives: string[];
  honours: string[];
  timestamp: number;
}

const DEFAULT_PERSISTED: PersistedInterests = {
  interests: [],
  careerGoals: [],
  skills: [],
  electives: [],
  honours: [],
  timestamp: 0,
};

/**
 * Save interests to localStorage.
 * Merges with existing data so partial updates don't erase other fields.
 */
export const saveInterestsToStorage = (data: Partial<PersistedInterests>): void => {
  try {
    const existing = loadInterestsFromStorage();
    const merged: PersistedInterests = {
      interests: data.interests ?? existing.interests,
      careerGoals: data.careerGoals ?? existing.careerGoals,
      skills: data.skills ?? existing.skills,
      electives: data.electives ?? existing.electives,
      honours: data.honours ?? existing.honours,
      timestamp: Date.now(),
    };
    localStorage.setItem(INTERESTS_STORAGE_KEY, JSON.stringify(merged));
    console.log('💾 Interests saved to localStorage:', {
      interests: merged.interests.length,
      careerGoals: merged.careerGoals.length,
      skills: merged.skills.length,
      electives: merged.electives.length,
      honours: merged.honours.length,
    });
  } catch (error) {
    console.error('Error saving interests to storage:', error);
  }
};

/**
 * Load interests from localStorage.
 * Returns data if less than 24 hours old.
 */
export const loadInterestsFromStorage = (): PersistedInterests => {
  try {
    const stored = localStorage.getItem(INTERESTS_STORAGE_KEY);
    if (stored) {
      const data = JSON.parse(stored) as Partial<PersistedInterests>;
      // Check if data is less than 24 hours old
      if (Date.now() - (data.timestamp || 0) < 86400000) {
        return {
          interests: data.interests || [],
          careerGoals: data.careerGoals || [],
          skills: data.skills || [],
          electives: data.electives || [],
          honours: data.honours || [],
          timestamp: data.timestamp || 0,
        };
      }
    }
  } catch (error) {
    console.error('Error loading interests from storage:', error);
  }
  return { ...DEFAULT_PERSISTED };
};

/**
 * Clear persisted interests
 */
export const clearInterestsFromStorage = (): void => {
  try {
    localStorage.removeItem(INTERESTS_STORAGE_KEY);
  } catch (error) {
    console.error('Error clearing interests from storage:', error);
  }
};

/**
 * Check if there are persisted interests
 */
export const hasPersistedInterests = (): boolean => {
  const data = loadInterestsFromStorage();
  return data.interests.length > 0 || data.skills.length > 0;
};

/**
 * Dispatch interest update event with ALL field names the dashboard expects.
 * Also persists to localStorage before dispatching.
 *
 * The dashboard listens for:
 *   detail.interests  → setStudentInterests
 *   detail.electives  → setStudentElectives
 *   detail.honours    → setStudentHonours
 *   detail.careerGoals → logged / future use
 *   detail.skills     → logged / future use
 */
export const dispatchInterestsUpdatedEvent = (data: {
  interests: string[];
  careerGoals: string[];
  skills: string[];
  electives: string[];
  honours: string[];
}): void => {
  // Save to localStorage immediately
  saveInterestsToStorage(data);

  // Dispatch event with ALL fields
  window.dispatchEvent(
    new CustomEvent('interestsUpdated', {
      detail: {
        interests: data.interests,
        careerGoals: data.careerGoals,
        skills: data.skills,
        electives: data.electives,
        honours: data.honours,
      },
    })
  );

  console.log('📡 Dispatched interestsUpdated event:', {
    interests: data.interests.length,
    careerGoals: data.careerGoals.length,
    skills: data.skills.length,
    electives: data.electives.length,
    honours: data.honours.length,
  });
};