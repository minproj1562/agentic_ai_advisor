// src/components/dashboard/InterestManagement.tsx
// FIXED VERSION - localStorage persistence + correct event dispatch + reliable save order

import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Heart, Plus, X, Save, Sparkles, Target, Briefcase, Code, Brain,
  Loader2, CheckCircle, AlertCircle, TrendingUp, BookOpen, Award,
  RefreshCw, AlertTriangle,
} from 'lucide-react';
import { mlService, InterestProfile } from '../../services/ml.service';
import { getWeaknessService } from '../../services/weakness.service';
import { useAuth } from '../../contexts/AuthContext';
import { useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

// ✅ Use the SAME localStorage key as the dashboard
const INTERESTS_STORAGE_KEY = 'academic_advisor_interests';

interface InterestManagementProps {
  onInterestsUpdated?: () => void;
}

// localStorage helpers
const loadFromStorage = (): {
  interests: string[];
  careerGoals: string[];
  skills: string[];
  electives: string[];
  honours: string[];
} => {
  try {
    const stored = localStorage.getItem(INTERESTS_STORAGE_KEY);
    if (stored) {
      const data = JSON.parse(stored);
      if (Date.now() - (data.timestamp || 0) < 86400000) {
        return {
          interests: data.interests || [],
          careerGoals: data.careerGoals || data.career_goals || [],
          skills: data.skills || [],
          electives: data.electives || [],
          honours: data.honours || [],
        };
      }
    }
  } catch (error) {
    console.error('Error loading interests from storage:', error);
  }
  return { interests: [], careerGoals: [], skills: [], electives: [], honours: [] };
};

const saveToStorage = (data: {
  interests: string[];
  careerGoals: string[];
  skills: string[];
  electives: string[];
  honours: string[];
}) => {
  try {
    localStorage.setItem(
      INTERESTS_STORAGE_KEY,
      JSON.stringify({
        interests: data.interests,
        careerGoals: data.careerGoals,
        skills: data.skills,
        electives: data.electives,
        honours: data.honours,
        timestamp: Date.now(),
      })
    );
    console.log('💾 Interests saved to localStorage');
  } catch (error) {
    console.error('Error saving interests to storage:', error);
  }
};

const INTEREST_OPTIONS = [
  { category: 'AI & ML', items: ['Artificial Intelligence', 'Machine Learning', 'Deep Learning', 'Natural Language Processing', 'Computer Vision'] },
  { category: 'Web Development', items: ['Frontend Development', 'Backend Development', 'Full Stack Development', 'Web Design', 'Progressive Web Apps'] },
  { category: 'Data', items: ['Data Science', 'Data Analytics', 'Big Data', 'Data Engineering', 'Business Intelligence'] },
  { category: 'Cloud & DevOps', items: ['Cloud Computing', 'DevOps', 'Kubernetes', 'Docker', 'Microservices'] },
  { category: 'Mobile', items: ['Mobile Development', 'Android Development', 'iOS Development', 'Flutter', 'React Native'] },
  { category: 'Security', items: ['Cybersecurity', 'Ethical Hacking', 'Network Security', 'Cryptography'] },
  { category: 'Emerging Tech', items: ['Blockchain', 'IoT', 'AR/VR', 'Quantum Computing', 'Edge Computing'] },
  { category: 'Other', items: ['Game Development', 'Robotics', 'Embedded Systems', 'System Design', 'Competitive Programming'] },
];

const CAREER_GOAL_OPTIONS = [
  'Software Engineer', 'ML Engineer', 'Data Scientist', 'Full Stack Developer',
  'Cloud Architect', 'DevOps Engineer', 'Security Engineer', 'Product Manager',
  'Technical Lead', 'Research Scientist', 'Startup Founder', 'Freelancer',
];

const SKILL_OPTIONS = [
  'Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'Go', 'Rust',
  'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask', 'Spring',
  'TensorFlow', 'PyTorch', 'Scikit-learn', 'Pandas', 'NumPy',
  'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes',
  'MongoDB', 'PostgreSQL', 'MySQL', 'Redis',
  'Git', 'Linux', 'SQL', 'GraphQL', 'REST APIs',
];

export const InterestManagement: React.FC<InterestManagementProps> = ({ onInterestsUpdated }) => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [profile, setProfile] = useState<InterestProfile | null>(null);

  // Initialize from localStorage so data survives tab switches
  const cachedData = useRef(loadFromStorage());

  const [selectedInterests, setSelectedInterests] = useState<string[]>(cachedData.current.interests);
  const [selectedCareerGoals, setSelectedCareerGoals] = useState<string[]>(cachedData.current.careerGoals);
  const [selectedSkills, setSelectedSkills] = useState<string[]>(cachedData.current.skills);

  // Preserve electives and honours (edited elsewhere, not here)
  const [preservedElectives, setPreservedElectives] = useState<string[]>(cachedData.current.electives);
  const [preservedHonours, setPreservedHonours] = useState<string[]>(cachedData.current.honours);

  const [customInterest, setCustomInterest] = useState('');
  const [customSkill, setCustomSkill] = useState('');

  const [activeSection, setActiveSection] = useState<'interests' | 'careers' | 'skills'>('interests');
  const [showRecommendations, setShowRecommendations] = useState(false);
  const [syncStatus, setSyncStatus] = useState<'synced' | 'failed' | 'unknown' | null>(null);
  const [backendHasData, setBackendHasData] = useState(false);

  // Track unsaved changes
  const [isDirty, setIsDirty] = useState(false);
  const lastSavedRef = useRef<{
    interests: string[];
    goals: string[];
    skills: string[];
  }>({
    interests: cachedData.current.interests,
    goals: cachedData.current.careerGoals,
    skills: cachedData.current.skills,
  });

  const checkDirty = useCallback(
    (interests: string[], goals: string[], skills: string[]) => {
      const saved = lastSavedRef.current;
      const dirty =
        JSON.stringify([...interests].sort()) !== JSON.stringify([...saved.interests].sort()) ||
        JSON.stringify([...goals].sort()) !== JSON.stringify([...saved.goals].sort()) ||
        JSON.stringify([...skills].sort()) !== JSON.stringify([...saved.skills].sort());
      setIsDirty(dirty);
    },
    []
  );

  // Local completeness calculation
  const localCompleteness = useMemo(() => {
    let score = 0;
    if (selectedInterests.length >= 3) score += 40;
    else if (selectedInterests.length >= 1) score += Math.round((selectedInterests.length / 3) * 40);
    if (selectedCareerGoals.length >= 1) score += 30;
    if (selectedSkills.length >= 3) score += 30;
    else if (selectedSkills.length >= 1) score += Math.round((selectedSkills.length / 3) * 30);
    return Math.min(score, 100);
  }, [selectedInterests, selectedCareerGoals, selectedSkills]);

  const displayCompleteness =
    profile?.profile_completeness && profile.profile_completeness > 0
      ? profile.profile_completeness
      : localCompleteness;

  // Save to localStorage whenever selections change
  useEffect(() => {
    saveToStorage({
      interests: selectedInterests,
      careerGoals: selectedCareerGoals,
      skills: selectedSkills,
      electives: preservedElectives,
      honours: preservedHonours,
    });
    checkDirty(selectedInterests, selectedCareerGoals, selectedSkills);
  }, [selectedInterests, selectedCareerGoals, selectedSkills, preservedElectives, preservedHonours, checkDirty]);

  // Warn before page unload if unsaved
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault();
        e.returnValue = 'You have unsaved interest changes.';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isDirty]);

  // Fetch on mount
  useEffect(() => {
    if (user?.uid) {
      fetchInterestProfile();
    } else {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.uid]);

  // ✅ FIXED: Rewritten retrieval logic
  // Priority: Weakness service (canonical) > ML service (supplementary) > localStorage (fallback)
  const fetchInterestProfile = async () => {
    try {
      setLoading(true);

      const localData = loadFromStorage();
      const hasLocalData = localData.interests.length > 0 || localData.skills.length > 0;

      // Accumulator — we merge from multiple sources
      let bestInterests: string[] = [];
      let bestCareerGoals: string[] = [];
      let bestSkills: string[] = [];
      let bestElectives: string[] = localData.electives;
      let bestHonours: string[] = localData.honours;
      let backendLoaded = false;

      // ═══════════════════════════════════════════════════════
      // 1. PRIMARY: Weakness service (canonical source of truth)
      //    This is where PUT/POST endpoints actually save to.
      //    Collection: student_interests — has ALL fields.
      // ═══════════════════════════════════════════════════════
      if (user?.uid) {
        try {
          const weaknessService = getWeaknessService();
          const interestProfile = await weaknessService.getInterests(user.uid);

          if (
            interestProfile.interests?.length > 0 ||
            interestProfile.career_goals?.length > 0 ||
            interestProfile.skills?.length > 0
          ) {
            bestInterests = interestProfile.interests || [];
            bestCareerGoals = interestProfile.career_goals || [];
            bestSkills = interestProfile.skills || [];
            backendLoaded = true;
            console.log('✅ Loaded from weakness service (primary):', {
              interests: bestInterests.length,
              careerGoals: bestCareerGoals.length,
              skills: bestSkills.length,
            });

            if (interestProfile.preferred_electives?.length) {
              bestElectives = interestProfile.preferred_electives;
            }
            if (interestProfile.honours_minors_interest?.length) {
              bestHonours = interestProfile.honours_minors_interest;
            }
          }
        } catch (e) {
          console.warn('⚠️ Weakness service not available:', e);
        }
      }

      // ═══════════════════════════════════════════════════════
      // 2. SUPPLEMENTARY: ML service (fill EMPTY gaps only)
      //    Only fills fields that weakness service didn't provide.
      // ═══════════════════════════════════════════════════════
      try {
        const data = await mlService.getInterestProfile();
        if (data) {
          setProfile(data);

          // Only fill in fields that are EMPTY from the primary source
          if (bestInterests.length === 0 && data.declared_interests?.length > 0) {
            bestInterests = data.declared_interests;
            console.log('📡 Filled interests from ML service');
          }
          if (bestCareerGoals.length === 0 && data.career_goals?.length > 0) {
            bestCareerGoals = data.career_goals;
            console.log('📡 Filled career_goals from ML service');
          }
          if (bestSkills.length === 0 && data.skills?.length > 0) {
            bestSkills = data.skills;
            console.log('📡 Filled skills from ML service');
          }

          if (bestInterests.length > 0 || bestCareerGoals.length > 0 || bestSkills.length > 0) {
            backendLoaded = true;
          }
        }
      } catch (error) {
        console.warn('⚠️ ML interest profile not available:', error);
      }

      // ═══════════════════════════════════════════════════════
      // 3. FALLBACK: localStorage (if ALL APIs failed)
      // ═══════════════════════════════════════════════════════
      if (!backendLoaded && hasLocalData) {
        console.log('📦 Using cached interests from localStorage');
        bestInterests = localData.interests;
        bestCareerGoals = localData.careerGoals;
        bestSkills = localData.skills;
        bestElectives = localData.electives;
        bestHonours = localData.honours;
        setSyncStatus('unknown');
        setBackendHasData(false);
      } else if (backendLoaded) {
        setSyncStatus('synced');
        setBackendHasData(true);
      } else {
        console.log('No saved interests found — user needs to select interests');
        setSyncStatus('unknown');
        setBackendHasData(false);
      }

      // Apply the best data we found
      setSelectedInterests(bestInterests);
      setSelectedCareerGoals(bestCareerGoals);
      setSelectedSkills(bestSkills);
      setPreservedElectives(bestElectives);
      setPreservedHonours(bestHonours);

      // Mark as clean
      lastSavedRef.current = {
        interests: bestInterests,
        goals: bestCareerGoals,
        skills: bestSkills,
      };
      setIsDirty(false);
    } catch (error) {
      console.error('Error fetching interest profile:', error);
      setSyncStatus('unknown');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (selectedInterests.length === 0) {
      toast.error('Please select at least one interest');
      return;
    }

    try {
      setSaving(true);
      let savedToBackend = false;

      // ════════════════════════════════════════════════════════
      // 1. PRIMARY: Save via weakness service PUT
      // ════════════════════════════════════════════════════════
      if (user?.uid) {
        try {
          const weaknessService = getWeaknessService();
          await weaknessService.updateInterests(user.uid, {
            interests: selectedInterests,
            career_goals: selectedCareerGoals,
            skills: selectedSkills,
            skill_levels: {},
            interest_levels: {},
            preferred_electives: preservedElectives,
            honours_minors_interest: preservedHonours,
          });
          savedToBackend = true;
          console.log('✅ Saved via PUT /weakness/{id}/interests (primary)');
        } catch (putError) {
          console.warn('⚠️ PUT failed, trying POST fallback:', putError);

          // ════════════════════════════════════════════════════════
          // 2. FALLBACK: Save via weakness service POST
          // ════════════════════════════════════════════════════════
          try {
            const weaknessService = getWeaknessService();
            await weaknessService.saveInterests(
              user.uid,
              selectedInterests,
              selectedCareerGoals,
              selectedSkills
            );
            savedToBackend = true;
            console.log('✅ Saved via POST /weakness/{id}/interests (fallback)');
          } catch (postError) {
            console.error('❌ POST fallback also failed:', postError);
          }
        }
      }

      // ════════════════════════════════════════════════════════
      // 3. SECONDARY: Also save to ML service (non-blocking)
      // ════════════════════════════════════════════════════════
      try {
        await mlService.updateInterests(selectedInterests, selectedCareerGoals, selectedSkills);
        console.log('✅ Also saved to ML service (secondary)');
      } catch (mlError) {
        console.warn('⚠️ ML service save failed (non-critical):', mlError);
      }

      // ════════════════════════════════════════════════════════
      // 4. ALWAYS: Save to localStorage
      // ════════════════════════════════════════════════════════
      saveToStorage({
        interests: selectedInterests,
        careerGoals: selectedCareerGoals,
        skills: selectedSkills,
        electives: preservedElectives,
        honours: preservedHonours,
      });

      // Update sync status
      if (savedToBackend) {
        setSyncStatus('synced');
        setBackendHasData(true);
      } else {
        setSyncStatus('failed');
        toast('Saved locally. Will sync when connection is restored.', { icon: '💾' });
      }

      // Mark as clean
      lastSavedRef.current = {
        interests: [...selectedInterests],
        goals: [...selectedCareerGoals],
        skills: [...selectedSkills],
      };
      setIsDirty(false);

      // Invalidate caches
      queryClient.invalidateQueries({ queryKey: ['weakness-analysis'] });
      queryClient.invalidateQueries({ queryKey: ['student-interests'] });
      queryClient.invalidateQueries({ queryKey: ['performance-metrics'] });
      queryClient.invalidateQueries({ queryKey: ['study-resources'] });
      queryClient.invalidateQueries({ queryKey: ['elective-recommendations'] });

      toast.success('Interests saved successfully!');

      // Dispatch event with ALL fields
      window.dispatchEvent(
        new CustomEvent('interestsUpdated', {
          detail: {
            interests: selectedInterests,
            careerGoals: selectedCareerGoals,
            skills: selectedSkills,
            electives: preservedElectives,
            honours: preservedHonours,
          },
        })
      );
      console.log('📡 Dispatched interestsUpdated with all 5 fields');

      // Notify parent
      if (onInterestsUpdated) onInterestsUpdated();
      setShowRecommendations(true);

      // Delayed re-fetch to confirm what was saved
      setTimeout(async () => {
        try {
          const data = await mlService.getInterestProfile();
          if (data) setProfile(data);
        } catch {
          // Non-critical
        }
      }, 2000);
    } catch (error) {
      console.error('Error saving interests:', error);
      toast.error('Failed to save interests');
      setSyncStatus('failed');
    } finally {
      setSaving(false);
    }
  };

  const handleForceSync = async () => {
    if (!user?.uid) return;
    setSyncing(true);
    try {
      const weaknessService = getWeaknessService();
      const result = await weaknessService.syncInterests(user.uid);

      if (result.status === 'success' && result.interests?.length) {
        setSelectedInterests(result.interests);
        if (result.career_goals?.length) {
          setSelectedCareerGoals(result.career_goals);
        }
        if (result.skills?.length) {
          setSelectedSkills(result.skills);
        }
        if (result.preferred_electives?.length) {
          setPreservedElectives(result.preferred_electives);
        }
        if (result.honours_minors_interest?.length) {
          setPreservedHonours(result.honours_minors_interest);
        }
        setSyncStatus('synced');
        setBackendHasData(true);

        lastSavedRef.current = {
          interests: result.interests,
          goals: result.career_goals || selectedCareerGoals,
          skills: result.skills || selectedSkills,
        };
        setIsDirty(false);

        toast.success(
          `Synced ${result.interests.length} interests from ${result.sources?.join(', ') || 'all sources'}`
        );
        queryClient.invalidateQueries({ queryKey: ['weakness-analysis'] });
        queryClient.invalidateQueries({ queryKey: ['student-interests'] });
      } else if (result.status === 'no_interests') {
        toast('No interests found in any source. Please select your interests above.', {
          icon: 'ℹ️',
        });
      } else {
        toast.error('Sync failed. Please save your interests first.');
      }
    } catch (error) {
      console.error('Sync error:', error);
      toast.error('Failed to sync interests');
    } finally {
      setSyncing(false);
    }
  };

  const toggleInterest = (interest: string) => {
    setSelectedInterests((prev) =>
      prev.includes(interest) ? prev.filter((i) => i !== interest) : [...prev, interest]
    );
  };

  const toggleCareerGoal = (goal: string) => {
    setSelectedCareerGoals((prev) =>
      prev.includes(goal)
        ? prev.filter((g) => g !== goal)
        : prev.length < 3
        ? [...prev, goal]
        : prev
    );
  };

  const toggleSkill = (skill: string) => {
    setSelectedSkills((prev) =>
      prev.includes(skill) ? prev.filter((s) => s !== skill) : [...prev, skill]
    );
  };

  const addCustomInterest = () => {
    if (customInterest.trim() && !selectedInterests.includes(customInterest.trim())) {
      setSelectedInterests((prev) => [...prev, customInterest.trim()]);
      setCustomInterest('');
    }
  };

  const addCustomSkill = () => {
    if (customSkill.trim() && !selectedSkills.includes(customSkill.trim())) {
      setSelectedSkills((prev) => [...prev, customSkill.trim()]);
      setCustomSkill('');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
        <span className="ml-3 text-gray-600">Loading your interests...</span>
      </div>
    );
  }

  const getSyncDisplay = () => {
    if (isDirty) {
      return {
        text: 'Unsaved changes — click Save to sync',
        color: 'text-yellow-200',
        icon: AlertCircle,
      };
    }
    if (syncStatus === 'synced') {
      return {
        text: 'Interests synced to all services',
        color: 'text-green-200',
        icon: CheckCircle,
      };
    }
    if (syncStatus === 'failed') {
      return {
        text: 'Sync incomplete — save again to retry',
        color: 'text-yellow-200',
        icon: AlertCircle,
      };
    }
    if (selectedInterests.length === 0) {
      return {
        text: 'Select interests to get started',
        color: 'text-purple-200',
        icon: Sparkles,
      };
    }
    return null;
  };

  const syncDisplay = getSyncDisplay();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Heart className="w-7 h-7" />
              Your Interests & Goals
            </h2>
            <p className="text-purple-100 mt-1">
              Tell us what excites you for personalized recommendations
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleForceSync}
              disabled={syncing}
              className="px-3 py-2 bg-white/20 rounded-lg hover:bg-white/30 flex items-center gap-2 text-sm transition-colors"
              title="Sync interests from all sources"
            >
              <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
              {syncing ? 'Syncing...' : 'Sync'}
            </button>
            <div className="bg-white/20 rounded-lg p-3">
              <div className="text-center">
                <p className="text-xs text-purple-100">Profile Complete</p>
                <p className="text-2xl font-bold">{displayCompleteness}%</p>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-4">
          <div className="w-full bg-white/20 rounded-full h-2">
            <div
              className="bg-white h-2 rounded-full transition-all duration-500"
              style={{ width: `${displayCompleteness}%` }}
            />
          </div>
        </div>

        {syncDisplay && (
          <div className={`mt-3 flex items-center gap-2 text-sm ${syncDisplay.color}`}>
            <syncDisplay.icon className="w-4 h-4" />
            {syncDisplay.text}
          </div>
        )}
      </div>

      {/* Unsaved changes warning banner */}
      <AnimatePresence>
        {isDirty && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-center justify-between"
          >
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
              <span className="text-sm text-amber-800 font-medium">
                You have unsaved changes. Click "Save" to persist your selections.
              </span>
            </div>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-3 py-1.5 bg-amber-600 text-white text-xs font-medium rounded-lg hover:bg-amber-700 transition-colors flex-shrink-0"
            >
              {saving ? 'Saving...' : 'Save Now'}
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Section Tabs */}
      <div className="bg-white rounded-xl shadow-sm border p-2">
        <div className="flex space-x-2">
          <button
            onClick={() => setActiveSection('interests')}
            className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
              activeSection === 'interests'
                ? 'bg-purple-600 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            Interests ({selectedInterests.length})
          </button>
          <button
            onClick={() => setActiveSection('careers')}
            className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
              activeSection === 'careers'
                ? 'bg-purple-600 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Briefcase className="w-4 h-4" />
            Career Goals ({selectedCareerGoals.length}/3)
          </button>
          <button
            onClick={() => setActiveSection('skills')}
            className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
              activeSection === 'skills'
                ? 'bg-purple-600 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Code className="w-4 h-4" />
            Skills ({selectedSkills.length})
          </button>
        </div>
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {activeSection === 'interests' && (
          <motion.div
            key="interests"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-white rounded-xl shadow-sm border p-6"
          >
            <h3 className="text-lg font-semibold mb-4">What are you interested in?</h3>
            {selectedInterests.length > 0 && (
              <div className="mb-6">
                <p className="text-sm text-gray-600 mb-2">Selected Interests:</p>
                <div className="flex flex-wrap gap-2">
                  {selectedInterests.map((interest, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm flex items-center gap-2"
                    >
                      {interest}
                      <button onClick={() => toggleInterest(interest)} className="hover:text-purple-900">
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            )}
            <div className="space-y-4">
              {INTEREST_OPTIONS.map((category, catIndex) => (
                <div key={catIndex}>
                  <p className="text-sm font-medium text-gray-700 mb-2">{category.category}</p>
                  <div className="flex flex-wrap gap-2">
                    {category.items.map((interest, index) => (
                      <button
                        key={index}
                        onClick={() => toggleInterest(interest)}
                        className={`px-3 py-1 rounded-full text-sm transition-all ${
                          selectedInterests.includes(interest)
                            ? 'bg-purple-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {interest}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-6 pt-4 border-t">
              <p className="text-sm text-gray-600 mb-2">Add custom interest:</p>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={customInterest}
                  onChange={(e) => setCustomInterest(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addCustomInterest()}
                  placeholder="Enter interest and press Enter"
                  className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none"
                />
                <button
                  onClick={addCustomInterest}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                >
                  <Plus className="w-5 h-5" />
                </button>
              </div>
            </div>
          </motion.div>
        )}

        {activeSection === 'careers' && (
          <motion.div
            key="careers"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-white rounded-xl shadow-sm border p-6"
          >
            <h3 className="text-lg font-semibold mb-2">What do you want to become?</h3>
            <p className="text-sm text-gray-600 mb-4">Select up to 3 career goals</p>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {CAREER_GOAL_OPTIONS.map((goal, index) => (
                <button
                  key={index}
                  onClick={() => toggleCareerGoal(goal)}
                  disabled={!selectedCareerGoals.includes(goal) && selectedCareerGoals.length >= 3}
                  className={`p-4 rounded-lg border text-left transition-all ${
                    selectedCareerGoals.includes(goal)
                      ? 'border-purple-600 bg-purple-50 text-purple-700'
                      : selectedCareerGoals.length >= 3
                      ? 'border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed'
                      : 'border-gray-200 hover:border-purple-300 hover:bg-purple-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{goal}</span>
                    {selectedCareerGoals.includes(goal) && (
                      <CheckCircle className="w-5 h-5 text-purple-600" />
                    )}
                  </div>
                </button>
              ))}
            </div>
          </motion.div>
        )}

        {activeSection === 'skills' && (
          <motion.div
            key="skills"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-white rounded-xl shadow-sm border p-6"
          >
            <h3 className="text-lg font-semibold mb-2">What skills do you have?</h3>
            <p className="text-sm text-gray-600 mb-4">Select all that apply</p>
            {selectedSkills.length > 0 && (
              <div className="mb-6">
                <p className="text-sm text-gray-600 mb-2">Your Skills ({selectedSkills.length}):</p>
                <div className="flex flex-wrap gap-2">
                  {selectedSkills.map((skill, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm flex items-center gap-2"
                    >
                      {skill}
                      <button onClick={() => toggleSkill(skill)}>
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            )}
            <div className="flex flex-wrap gap-2 mb-6">
              {SKILL_OPTIONS.map((skill, index) => (
                <button
                  key={index}
                  onClick={() => toggleSkill(skill)}
                  className={`px-3 py-1 rounded-full text-sm transition-all ${
                    selectedSkills.includes(skill)
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {skill}
                </button>
              ))}
            </div>
            <div className="pt-4 border-t">
              <p className="text-sm text-gray-600 mb-2">Add custom skill:</p>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={customSkill}
                  onChange={(e) => setCustomSkill(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addCustomSkill()}
                  placeholder="Enter skill and press Enter"
                  className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none"
                />
                <button
                  onClick={addCustomSkill}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  <Plus className="w-5 h-5" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-2">
          <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
          <div>
            <p className="font-medium text-blue-900">How interests affect your dashboard</p>
            <ul className="mt-1 text-sm text-blue-700 space-y-1">
              <li>• <strong>Weakness Analysis:</strong> Shows gaps in subjects required for your interests</li>
              <li>• <strong>Readiness Analysis:</strong> Scores how prepared you are for chosen electives/honours</li>
              <li>• <strong>AI Recommendations:</strong> Suggests electives and career paths matching your interests</li>
              <li>• <strong>Study Resources:</strong> Curated materials for your weak areas</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saving || selectedInterests.length === 0}
          className={`px-6 py-3 rounded-lg font-medium transition-all flex items-center gap-2 disabled:opacity-50 ${
            isDirty
              ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white hover:shadow-lg animate-pulse'
              : 'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:shadow-lg'
          }`}
        >
          {saving ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" /> Saving & Syncing...
            </>
          ) : (
            <>
              <Save className="w-5 h-5" />
              {isDirty ? 'Save Changes' : 'Save Interests & Get Recommendations'}
            </>
          )}
        </button>
      </div>

      {/* Recommendations Preview */}
      {showRecommendations && profile?.recommendations && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl border border-purple-200 p-6"
        >
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Brain className="w-5 h-5 text-purple-600" />
            AI Recommendations Based on Your Interests
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-lg p-4">
              <h4 className="font-medium mb-3 flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-blue-600" /> Recommended Electives
              </h4>
              <div className="space-y-2">
                {profile.recommendations.electives?.slice(0, 3).map((elective: any, index: number) => (
                  <div key={index} className="text-sm">
                    <p className="font-medium">{elective.elective_name}</p>
                    <p className="text-gray-600 text-xs">{elective.match_score}% match</p>
                  </div>
                )) || <p className="text-sm text-gray-500">Add more interests to get recommendations</p>}
              </div>
            </div>
            <div className="bg-white rounded-lg p-4">
              <h4 className="font-medium mb-3 flex items-center gap-2">
                <Award className="w-4 h-4 text-purple-600" /> Honours/Minor Programs
              </h4>
              <div className="space-y-2">
                {profile.recommendations.honours_programs?.slice(0, 3).map((program: any, index: number) => (
                  <div key={index} className="text-sm">
                    <p className="font-medium">{program.program}</p>
                    <p className="text-gray-600 text-xs">{program.type}</p>
                  </div>
                )) || <p className="text-sm text-gray-500">Add interests for programme recommendations</p>}
              </div>
            </div>
            <div className="bg-white rounded-lg p-4">
              <h4 className="font-medium mb-3 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-green-600" /> Career Paths
              </h4>
              <div className="space-y-2">
                {profile.topDomains?.slice(0, 3).map((domain: any, index: number) => (
                  <div key={index} className="text-sm">
                    <p className="font-medium">{domain.name}</p>
                    <p className="text-gray-600 text-xs">{domain.strength}% strength</p>
                  </div>
                )) || <p className="text-sm text-gray-500">Complete your profile for career insights</p>}
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default InterestManagement;