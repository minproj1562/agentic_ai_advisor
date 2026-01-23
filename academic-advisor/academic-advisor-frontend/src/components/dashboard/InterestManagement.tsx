// src/components/dashboard/InterestManagement.tsx

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Heart,
  Plus,
  X,
  Save,
  Sparkles,
  Target,
  Briefcase,
  Code,
  Brain,
  Loader2,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  BookOpen,
  Award
} from 'lucide-react';
import { mlService, InterestProfile } from '../../services/ml.service';
import { useAuth } from '../../contexts/AuthContext';
import toast from 'react-hot-toast';

interface InterestManagementProps {
  onInterestsUpdated?: () => void;
}

// Available interest options
const INTEREST_OPTIONS = [
  { category: 'AI & ML', items: ['Artificial Intelligence', 'Machine Learning', 'Deep Learning', 'Natural Language Processing', 'Computer Vision'] },
  { category: 'Web Development', items: ['Frontend Development', 'Backend Development', 'Full Stack Development', 'Web Design', 'Progressive Web Apps'] },
  { category: 'Data', items: ['Data Science', 'Data Analytics', 'Big Data', 'Data Engineering', 'Business Intelligence'] },
  { category: 'Cloud & DevOps', items: ['Cloud Computing', 'DevOps', 'Kubernetes', 'Docker', 'Microservices'] },
  { category: 'Mobile', items: ['Mobile Development', 'Android Development', 'iOS Development', 'Flutter', 'React Native'] },
  { category: 'Security', items: ['Cybersecurity', 'Ethical Hacking', 'Network Security', 'Cryptography'] },
  { category: 'Emerging Tech', items: ['Blockchain', 'IoT', 'AR/VR', 'Quantum Computing', 'Edge Computing'] },
  { category: 'Other', items: ['Game Development', 'Robotics', 'Embedded Systems', 'System Design', 'Competitive Programming'] }
];

const CAREER_GOAL_OPTIONS = [
  'Software Engineer',
  'ML Engineer',
  'Data Scientist',
  'Full Stack Developer',
  'Cloud Architect',
  'DevOps Engineer',
  'Security Engineer',
  'Product Manager',
  'Technical Lead',
  'Research Scientist',
  'Startup Founder',
  'Freelancer'
];

const SKILL_OPTIONS = [
  'Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'Go', 'Rust',
  'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask', 'Spring',
  'TensorFlow', 'PyTorch', 'Scikit-learn', 'Pandas', 'NumPy',
  'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes',
  'MongoDB', 'PostgreSQL', 'MySQL', 'Redis',
  'Git', 'Linux', 'SQL', 'GraphQL', 'REST APIs'
];

export const InterestManagement: React.FC<InterestManagementProps> = ({ onInterestsUpdated }) => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [profile, setProfile] = useState<InterestProfile | null>(null);
  
  // Form state
  const [selectedInterests, setSelectedInterests] = useState<string[]>([]);
  const [selectedCareerGoals, setSelectedCareerGoals] = useState<string[]>([]);
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [customInterest, setCustomInterest] = useState('');
  const [customSkill, setCustomSkill] = useState('');
  
  const [activeSection, setActiveSection] = useState<'interests' | 'careers' | 'skills'>('interests');
  const [showRecommendations, setShowRecommendations] = useState(false);

  useEffect(() => {
    if (user?.uid) {
      fetchInterestProfile();
    }
  }, [user]);

  const fetchInterestProfile = async () => {
    try {
      setLoading(true);
      const data = await mlService.getInterestProfile();
      setProfile(data);
      setSelectedInterests(data.declared_interests || []);
      setSelectedCareerGoals(data.career_goals || []);
      setSelectedSkills(data.skills || []);
    } catch (error) {
      console.error('Error fetching interest profile:', error);
      // Initialize with empty values
      setSelectedInterests([]);
      setSelectedCareerGoals([]);
      setSelectedSkills([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      
      await mlService.updateInterests(
        selectedInterests,
        selectedCareerGoals,
        selectedSkills
      );
      
      toast.success('Interests updated successfully!');
      
      // Refresh profile
      await fetchInterestProfile();
      
      // Notify parent
      if (onInterestsUpdated) {
        onInterestsUpdated();
      }
      
      // Show recommendations
      setShowRecommendations(true);
      
    } catch (error) {
      console.error('Error saving interests:', error);
      toast.error('Failed to save interests');
    } finally {
      setSaving(false);
    }
  };

  const toggleInterest = (interest: string) => {
    setSelectedInterests(prev => 
      prev.includes(interest)
        ? prev.filter(i => i !== interest)
        : [...prev, interest]
    );
  };

  const toggleCareerGoal = (goal: string) => {
    setSelectedCareerGoals(prev => 
      prev.includes(goal)
        ? prev.filter(g => g !== goal)
        : prev.length < 3 ? [...prev, goal] : prev
    );
  };

  const toggleSkill = (skill: string) => {
    setSelectedSkills(prev => 
      prev.includes(skill)
        ? prev.filter(s => s !== skill)
        : [...prev, skill]
    );
  };

  const addCustomInterest = () => {
    if (customInterest.trim() && !selectedInterests.includes(customInterest.trim())) {
      setSelectedInterests(prev => [...prev, customInterest.trim()]);
      setCustomInterest('');
    }
  };

  const addCustomSkill = () => {
    if (customSkill.trim() && !selectedSkills.includes(customSkill.trim())) {
      setSelectedSkills(prev => [...prev, customSkill.trim()]);
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
          <div className="bg-white/20 rounded-lg p-3">
            <div className="text-center">
              <p className="text-xs text-purple-100">Profile Complete</p>
              <p className="text-2xl font-bold">{profile?.profile_completeness || 0}%</p>
            </div>
          </div>
        </div>
        
        {/* Progress bar */}
        <div className="mt-4">
          <div className="w-full bg-white/20 rounded-full h-2">
            <div 
              className="bg-white h-2 rounded-full transition-all duration-500"
              style={{ width: `${profile?.profile_completeness || 0}%` }}
            />
          </div>
        </div>
      </div>

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
        {/* Interests Section */}
        {activeSection === 'interests' && (
          <motion.div
            key="interests"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-white rounded-xl shadow-sm border p-6"
          >
            <h3 className="text-lg font-semibold mb-4">What are you interested in?</h3>
            
            {/* Selected Interests */}
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
                      <button
                        onClick={() => toggleInterest(interest)}
                        className="hover:text-purple-900"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            {/* Interest Categories */}
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
            
            {/* Custom Interest */}
            <div className="mt-6 pt-4 border-t">
              <p className="text-sm text-gray-600 mb-2">Add custom interest:</p>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={customInterest}
                  onChange={(e) => setCustomInterest(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addCustomInterest()}
                  placeholder="Enter interest and press Enter"
                  className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
                />
                <button
                  onClick={addCustomInterest}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                >
                  <Plus className="w-5 h-5" />
                </button>
              </div>
            </div>
          </motion.div>
        )}

        {/* Career Goals Section */}
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

        {/* Skills Section */}
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
            
            {/* Selected Skills */}
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
            
            {/* Skill Options */}
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
            
            {/* Custom Skill */}
            <div className="pt-4 border-t">
              <p className="text-sm text-gray-600 mb-2">Add custom skill:</p>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={customSkill}
                  onChange={(e) => setCustomSkill(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addCustomSkill()}
                  placeholder="Enter skill and press Enter"
                  className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-green-500"
                />
                <button
                  onClick={addCustomSkill}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  <Plus className="w-5 h-5" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-medium hover:shadow-lg transition-shadow flex items-center gap-2 disabled:opacity-50"
        >
          {saving ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="w-5 h-5" />
              Save Interests & Get Recommendations
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
            {/* Elective Recommendations */}
            <div className="bg-white rounded-lg p-4">
              <h4 className="font-medium mb-3 flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-blue-600" />
                Recommended Electives
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
            
            {/* Honours Programs */}
            <div className="bg-white rounded-lg p-4">
              <h4 className="font-medium mb-3 flex items-center gap-2">
                <Award className="w-4 h-4 text-purple-600" />
                Honours/Minor Programs
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
            
            {/* Career Paths */}
            <div className="bg-white rounded-lg p-4">
              <h4 className="font-medium mb-3 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-green-600" />
                Career Paths
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