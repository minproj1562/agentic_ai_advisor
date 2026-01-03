// src/pages/ProgramsList.tsx
import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import {
  GraduationCap,
  Clock,
  Users,
  Star,
  Filter,
  Search,
  ChevronRight,
  Award,
  BookOpen,
  Briefcase,
  TrendingUp,
  Calendar,
  MapPin,
  DollarSign,
  Globe,
  Zap,
  Target,
  BarChart3,
  Code,
  Cpu,
  Atom,
  Palette,
  Heart,
  Building,
  Download,
  Share2,
  Bookmark,
  Info,
  ArrowUpRight,
  CheckCircle,
  X,
  Phone,
  MessageSquare,
 // Users,
} from 'lucide-react';
import CTALink from '../components/common/CTALink';
import { useAnalytics } from '../hooks/useAnalytics';
import toast from 'react-hot-toast';

// Comprehensive programs data
const programsData = [
  {
    id: 'cs-btech',
    name: 'B.Tech Computer Science & Engineering',
    category: 'Engineering',
    duration: '4 Years',
    degree: 'Bachelor of Technology',
    students: 500,
    faculty: 45,
    rating: 4.8,
    accreditation: 'NAAC A++',
    image: 'https://images.unsplash.com/photo-1517077304055-6e89abbf09b0?w=800',
    description: 'Cutting-edge computer science program with specializations in AI, ML, and Cloud Computing',
    highlights: ['AI/ML Focus', 'Industry Partnerships', '95% Placement'],
    specializations: [
      'Artificial Intelligence',
      'Machine Learning',
      'Data Science',
      'Cybersecurity',
      'Cloud Computing',
      'Blockchain'
    ],
    careerProspects: {
      averagePackage: '₹12 LPA',
      highestPackage: '₹45 LPA',
      topRecruiters: ['Google', 'Microsoft', 'Amazon', 'Adobe', 'Flipkart'],
      placementRate: '95%'
    },
    admissionCriteria: {
      examAccepted: ['JEE Main', 'SAT', 'State CET'],
      minimumPercentage: '75% in 12th',
      requiredSubjects: ['Physics', 'Chemistry', 'Mathematics']
    },
    fees: {
      tuition: '₹2,00,000/year',
      hostel: '₹80,000/year',
      total: '₹2,80,000/year',
      scholarships: 'Up to 100% for meritorious students'
    },
    curriculum: {
      totalCredits: 180,
      coreSubjects: 45,
      electives: 20,
      projects: 5,
      internships: 2
    },
    infrastructure: [
      'State-of-art Labs',
      'AI Research Center',
      'Innovation Hub',
      'Startup Incubator',
      '24/7 Computing Facility'
    ],
    achievements: [
      'Ranked #1 in State',
      '100+ Research Papers',
      '50+ Patents Filed',
      '20+ Startups Incubated'
    ]
  },
  {
    id: 'mba',
    name: 'Master of Business Administration',
    category: 'Business',
    duration: '2 Years',
    degree: 'MBA',
    students: 300,
    faculty: 30,
    rating: 4.7,
    accreditation: 'AACSB',
    image: 'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800',
    description: 'Global MBA program with focus on entrepreneurship and innovation',
    highlights: ['Global Exposure', 'Entrepreneurship', 'Case Studies'],
    specializations: [
      'Finance',
      'Marketing',
      'Operations',
      'HR Management',
      'International Business',
      'Analytics'
    ],
    careerProspects: {
      averagePackage: '₹15 LPA',
      highestPackage: '₹35 LPA',
      topRecruiters: ['McKinsey', 'BCG', 'Deloitte', 'Goldman Sachs', 'JP Morgan'],
      placementRate: '98%'
    },
    admissionCriteria: {
      examAccepted: ['CAT', 'GMAT', 'GRE'],
      minimumPercentage: '60% in Graduation',
      workExperience: '2 years preferred'
    },
    fees: {
      tuition: '₹4,00,000/year',
      hostel: '₹1,00,000/year',
      total: '₹5,00,000/year',
      scholarships: 'Merit & Need-based available'
    },
    curriculum: {
      totalCredits: 120,
      coreSubjects: 30,
      electives: 15,
      projects: 3,
      internships: 1
    },
    infrastructure: [
      'Bloomberg Terminal',
      'Case Study Rooms',
      'Executive Lounge',
      'Simulation Lab',
      'Conference Center'
    ],
    achievements: [
      'Top 10 B-School',
      '500+ Alumni CEOs',
      '₹1Cr+ Average Package',
      'Global Rankings'
    ]
  },
  {
    id: 'medical-mbbs',
    name: 'Bachelor of Medicine & Surgery',
    category: 'Medicine',
    duration: '5.5 Years',
    degree: 'MBBS',
    students: 200,
    faculty: 80,
    rating: 4.9,
    accreditation: 'MCI Approved',
    image: 'https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=800',
    description: 'Premier medical program with state-of-the-art hospital facilities',
    highlights: ['1000+ Bed Hospital', 'Research Focus', 'Global Recognition'],
    specializations: [
      'General Medicine',
      'Surgery',
      'Pediatrics',
      'Cardiology',
      'Neurology',
      'Oncology'
    ],
    careerProspects: {
      averagePackage: '₹10 LPA',
      highestPackage: '₹30 LPA',
      topRecruiters: ['AIIMS', 'Apollo', 'Fortis', 'Max Healthcare'],
      placementRate: '100%'
    },
    admissionCriteria: {
      examAccepted: ['NEET UG'],
      minimumPercentage: '50% in 12th PCB',
      requiredSubjects: ['Physics', 'Chemistry', 'Biology']
    },
    fees: {
      tuition: '₹5,00,000/year',
      hostel: '₹1,00,000/year',
      total: '₹6,00,000/year',
      scholarships: 'Government & Private scholarships'
    },
    curriculum: {
      totalCredits: 250,
      clinicalRotations: 12,
      researchProjects: 3,
      internship: '1 Year'
    },
    infrastructure: [
      'Super-specialty Hospital',
      'Research Labs',
      'Anatomy Museum',
      'Simulation Center',
      'Medical Library'
    ],
    achievements: [
      '100% NEET Success',
      '50+ Specializations',
      'International Collaborations',
      'Research Grants'
    ]
  },
  // Add more programs...
];

// Filter options
const filterOptions = {
  categories: ['All', 'Engineering', 'Business', 'Medicine', 'Sciences', 'Arts', 'Law'],
  duration: ['All', '2 Years', '3 Years', '4 Years', '5+ Years'],
  degree: ['All', 'Undergraduate', 'Postgraduate', 'Doctoral', 'Diploma'],
  sortBy: ['Popularity', 'Rating', 'Duration', 'Fees (Low to High)', 'Fees (High to Low)']
};

const ProgramsList: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { trackEvent } = useAnalytics();
  
  // State management
  const [programs, setPrograms] = useState(programsData);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState(searchParams.get('search') || '');
  const [selectedCategory, setSelectedCategory] = useState(searchParams.get('category') || 'All');
  const [selectedDuration, setSelectedDuration] = useState('All');
  const [selectedDegree, setSelectedDegree] = useState('All');
  const [sortBy, setSortBy] = useState('Popularity');
  const [showFilters, setShowFilters] = useState(false);
  const [bookmarkedPrograms, setBookmarkedPrograms] = useState<string[]>([]);
  const [compareList, setCompareList] = useState<string[]>([]);
  const [showCompareModal, setShowCompareModal] = useState(false);

  // Load more data on scroll (pagination)
  const [page, setPage] = useState(1);
  const itemsPerPage = 9;

  // Filter and sort programs
  const filteredPrograms = useMemo(() => {
    let filtered = [...programs];

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(program =>
        program.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        program.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        program.specializations.some(spec => 
          spec.toLowerCase().includes(searchQuery.toLowerCase())
        )
      );
    }

    // Category filter
    if (selectedCategory !== 'All') {
      filtered = filtered.filter(program => program.category === selectedCategory);
    }

    // Duration filter
    if (selectedDuration !== 'All') {
      filtered = filtered.filter(program => program.duration === selectedDuration);
    }

    // Degree filter
    if (selectedDegree !== 'All') {
      // Add degree filtering logic
    }

    // Sorting
    switch (sortBy) {
      case 'Rating':
        filtered.sort((a, b) => b.rating - a.rating);
        break;
      case 'Duration':
        filtered.sort((a, b) => parseInt(a.duration) - parseInt(b.duration));
        break;
      case 'Fees (Low to High)':
        filtered.sort((a, b) => 
          parseInt(a.fees.tuition.replace(/[^0-9]/g, '')) - 
          parseInt(b.fees.tuition.replace(/[^0-9]/g, ''))
        );
        break;
      case 'Fees (High to Low)':
        filtered.sort((a, b) => 
          parseInt(b.fees.tuition.replace(/[^0-9]/g, '')) - 
          parseInt(a.fees.tuition.replace(/[^0-9]/g, ''))
        );
        break;
      default:
        // Popularity (default order)
        break;
    }

    return filtered;
  }, [programs, searchQuery, selectedCategory, selectedDuration, selectedDegree, sortBy]);

  // Paginated programs
  const displayedPrograms = filteredPrograms.slice(0, page * itemsPerPage);

  // Update URL params
  useEffect(() => {
    const params = new URLSearchParams();
    if (searchQuery) params.set('search', searchQuery);
    if (selectedCategory !== 'All') params.set('category', selectedCategory);
    setSearchParams(params);
  }, [searchQuery, selectedCategory, setSearchParams]);

  // Handle bookmark
  const toggleBookmark = (programId: string) => {
    setBookmarkedPrograms(prev => {
      const updated = prev.includes(programId)
        ? prev.filter(id => id !== programId)
        : [...prev, programId];
      
      localStorage.setItem('bookmarkedPrograms', JSON.stringify(updated));
      toast.success(prev.includes(programId) ? 'Removed from bookmarks' : 'Added to bookmarks');
      
      trackEvent('program_bookmarked', { programId, action: prev.includes(programId) ? 'remove' : 'add' });
      
      return updated;
    });
  };

  // Handle compare
  const toggleCompare = (programId: string) => {
    setCompareList(prev => {
      if (prev.includes(programId)) {
        return prev.filter(id => id !== programId);
      } else if (prev.length < 3) {
        return [...prev, programId];
      } else {
        toast.error('You can compare up to 3 programs');
        return prev;
      }
    });
  };

  // Download brochure
  const downloadBrochure = (program: typeof programsData[0]) => {
    trackEvent('brochure_downloaded', { programId: program.id });
    toast.success(`Downloading ${program.name} brochure...`);
    // Implement actual download logic
  };

  // Share program
  const shareProgram = async (program: typeof programsData[0]) => {
    const shareData = {
      title: program.name,
      text: program.description,
      url: `${window.location.origin}/programs/${program.id}`
    };

    try {
      if (navigator.share) {
        await navigator.share(shareData);
      } else {
        await navigator.clipboard.writeText(shareData.url);
        toast.success('Link copied to clipboard!');
      }
      trackEvent('program_shared', { programId: program.id });
    } catch (error) {
      toast.error('Failed to share');
    }
  };

  return (
    <>
      <Helmet>
        <title>Academic Programs - Smart Campus</title>
        <meta name="description" content="Explore our comprehensive range of academic programs" />
      </Helmet>

      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
        {/* Hero Section */}
        <section className="relative bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white">
          <div className="absolute inset-0 bg-black/20" />
          <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center"
            >
              <h1 className="text-5xl font-bold mb-6">Academic Programs</h1>
              <p className="text-xl mb-8 max-w-3xl mx-auto">
                Discover world-class programs designed to shape future leaders and innovators
              </p>

              {/* Search Bar */}
              <div className="max-w-2xl mx-auto">
                <div className="relative">
                  <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search programs, specializations, careers..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-12 pr-4 py-4 bg-white text-gray-900 rounded-xl focus:outline-none focus:ring-4 focus:ring-white/30"
                  />
                  <button
                    onClick={() => trackEvent('program_search', { query: searchQuery })}
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 px-6 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-medium hover:shadow-lg transition-all"
                  >
                    Search
                  </button>
                </div>
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-12">
                {[
                  { icon: <GraduationCap />, value: '50+', label: 'Programs' },
                  { icon: <Users />, value: '15,000+', label: 'Students' },
                  { icon: <Award />, value: '95%', label: 'Placement Rate' },
                  { icon: <Globe />, value: '100+', label: 'Global Partners' }
                ].map((stat, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="bg-white/10 backdrop-blur-xl rounded-xl p-4"
                  >
                    <div className="flex items-center justify-center mb-2 text-white/80">
                      {React.cloneElement(stat.icon, { className: 'h-6 w-6' })}
                    </div>
                    <div className="text-2xl font-bold">{stat.value}</div>
                    <div className="text-sm text-white/80">{stat.label}</div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </div>
        </section>

        {/* Filters Section */}
        <section className="sticky top-0 z-30 bg-white border-b shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex flex-wrap items-center justify-between gap-4">
              {/* Category Pills */}
              <div className="flex items-center space-x-2 overflow-x-auto">
                {filterOptions.categories.map((category) => (
                  <button
                    key={category}
                    onClick={() => {
                      setSelectedCategory(category);
                      trackEvent('filter_category', { category });
                    }}
                    className={`px-4 py-2 rounded-full font-medium whitespace-nowrap transition-all ${
                      selectedCategory === category
                        ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {category}
                  </button>
                ))}
              </div>

              {/* Additional Filters */}
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className="flex items-center space-x-2 px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  <Filter className="h-4 w-4" />
                  <span>Filters</span>
                </button>

                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="px-4 py-2 bg-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  {filterOptions.sortBy.map(option => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>

                {compareList.length > 0 && (
                  <button
                    onClick={() => setShowCompareModal(true)}
                    className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                  >
                    <BarChart3 className="h-4 w-4" />
                    <span>Compare ({compareList.length})</span>
                  </button>
                )}
              </div>
            </div>

            {/* Extended Filters */}
            <AnimatePresence>
              {showFilters && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="mt-4 pt-4 border-t"
                >
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <label className="text-sm font-medium text-gray-700 mb-2 block">Duration</label>
                      <select
                        value={selectedDuration}
                        onChange={(e) => setSelectedDuration(e.target.value)}
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                      >
                        {filterOptions.duration.map(option => (
                          <option key={option} value={option}>{option}</option>
                        ))}
                      </select>
                    </div>
                    
                    <div>
                      <label className="text-sm font-medium text-gray-700 mb-2 block">Degree Type</label>
                      <select
                        value={selectedDegree}
                        onChange={(e) => setSelectedDegree(e.target.value)}
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                      >
                        {filterOptions.degree.map(option => (
                          <option key={option} value={option}>{option}</option>
                        ))}
                      </select>
                    </div>

                    <div className="md:col-span-2 flex items-end">
                      <button
                        onClick={() => {
                          setSelectedCategory('All');
                          setSelectedDuration('All');
                          setSelectedDegree('All');
                          setSearchQuery('');
                          setSortBy('Popularity');
                        }}
                        className="px-4 py-2 text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
                      >
                        Clear All Filters
                      </button>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </section>

        {/* Programs Grid */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {/* Results count */}
          <div className="mb-6">
            <p className="text-gray-600">
              Showing <span className="font-semibold">{displayedPrograms.length}</span> of{' '}
              <span className="font-semibold">{filteredPrograms.length}</span> programs
            </p>
          </div>

          {/* Programs Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {displayedPrograms.map((program, index) => (
              <motion.div
                key={program.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-2xl transition-all group"
              >
                {/* Image */}
                <div className="relative h-48 overflow-hidden">
                  <img
                    src={program.image}
                    alt={program.name}
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                  
                  {/* Badges */}
                  <div className="absolute top-4 left-4 flex flex-wrap gap-2">
                    <span className="px-3 py-1 bg-white/90 backdrop-blur-xl text-xs font-semibold rounded-full">
                      {program.category}
                    </span>
                    <span className="px-3 py-1 bg-purple-600 text-white text-xs font-semibold rounded-full">
                      {program.accreditation}
                    </span>
                  </div>

                  {/* Actions */}
                  <div className="absolute top-4 right-4 flex space-x-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleBookmark(program.id);
                      }}
                      className={`p-2 rounded-lg backdrop-blur-xl transition-all ${
                        bookmarkedPrograms.includes(program.id)
                          ? 'bg-purple-600 text-white'
                          : 'bg-white/90 text-gray-700 hover:bg-white'
                      }`}
                    >
                      <Bookmark className={`h-4 w-4 ${bookmarkedPrograms.includes(program.id) ? 'fill-current' : ''}`} />
                    </button>
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleCompare(program.id);
                      }}
                      className={`p-2 rounded-lg backdrop-blur-xl transition-all ${
                        compareList.includes(program.id)
                          ? 'bg-purple-600 text-white'
                          : 'bg-white/90 text-gray-700 hover:bg-white'
                      }`}
                    >
                      <BarChart3 className="h-4 w-4" />
                    </button>
                  </div>

                  {/* Title Overlay */}
                  <div className="absolute bottom-4 left-4 right-4">
                    <h3 className="text-xl font-bold text-white">
                      {program.name}
                    </h3>
                  </div>
                </div>

                {/* Content */}
                <div className="p-6">
                  {/* Description */}
                  <p className="text-gray-600 mb-4 line-clamp-2">
                    {program.description}
                  </p>

                  {/* Key Info */}
                  <div className="grid grid-cols-2 gap-3 mb-4">
                    <div className="flex items-center text-sm text-gray-600">
                      <Clock className="h-4 w-4 mr-2 text-purple-600" />
                      {program.duration}
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <Users className="h-4 w-4 mr-2 text-purple-600" />
                      {program.students} Students
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <DollarSign className="h-4 w-4 mr-2 text-purple-600" />
                      {program.fees.tuition}
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <Star className="h-4 w-4 mr-2 text-yellow-500" />
                      {program.rating}/5.0
                    </div>
                  </div>

                  {/* Highlights */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    {program.highlights.map((highlight, i) => (
                      <span
                        key={i}
                        className="px-3 py-1 bg-purple-100 text-purple-700 text-xs rounded-full font-medium"
                      >
                        {highlight}
                      </span>
                    ))}
                  </div>

                  {/* Career Prospects */}
                  <div className="p-3 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg mb-4">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Avg Package</span>
                      <span className="font-bold text-purple-700">{program.careerProspects.averagePackage}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm mt-1">
                      <span className="text-gray-600">Placement Rate</span>
                      <span className="font-bold text-green-600">{program.careerProspects.placementRate}</span>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex space-x-3">
                    <CTALink
                      to={`/programs/${program.id}`}
                      variant="primary"
                      size="sm"
                      className="flex-1"
                      showArrow
                      analyticsEvent={`program_details_${program.id}`}
                    >
                      View Details
                    </CTALink>
                    
                    <button
                      onClick={() => downloadBrochure(program)}
                      className="p-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                      aria-label="Download brochure"
                    >
                      <Download className="h-4 w-4 text-gray-700" />
                    </button>
                    
                    <button
                      onClick={() => shareProgram(program)}
                      className="p-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                      aria-label="Share program"
                    >
                      <Share2 className="h-4 w-4 text-gray-700" />
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Load More */}
          {displayedPrograms.length < filteredPrograms.length && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center mt-12"
            >
              <button
                onClick={() => setPage(page + 1)}
                className="px-8 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-xl transition-all"
              >
                Load More Programs
              </button>
            </motion.div>
          )}

          {/* Empty State */}
          {filteredPrograms.length === 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-16"
            >
              <GraduationCap className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-700 mb-2">No programs found</h3>
              <p className="text-gray-500 mb-6">Try adjusting your filters or search query</p>
              <button
                onClick={() => {
                  setSearchQuery('');
                  setSelectedCategory('All');
                }}
                className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                Clear Filters
              </button>
            </motion.div>
          )}
        </section>

        {/* Compare Modal */}
        <AnimatePresence>
          {showCompareModal && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
              onClick={() => setShowCompareModal(false)}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                className="bg-white rounded-2xl max-w-6xl w-full max-h-[90vh] overflow-y-auto"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="sticky top-0 bg-white border-b p-6 flex items-center justify-between">
                  <h2 className="text-2xl font-bold">Compare Programs</h2>
                  <button
                    onClick={() => setShowCompareModal(false)}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <X className="h-6 w-6" />
                  </button>
                </div>

                <div className="p-6">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr>
                          <th className="text-left p-4 font-semibold">Features</th>
                          {compareList.map(id => {
                            const program = programs.find(p => p.id === id);
                            return (
                              <th key={id} className="text-left p-4">
                                <div className="font-semibold">{program?.name}</div>
                                <button
                                  onClick={() => toggleCompare(id)}
                                  className="text-sm text-red-600 hover:text-red-700 mt-1"
                                >
                                  Remove
                                </button>
                              </th>
                            );
                          })}
                        </tr>
                      </thead>
                      <tbody>
                        {['duration', 'fees.tuition', 'rating', 'careerProspects.averagePackage', 'careerProspects.placementRate'].map(field => (
                          <tr key={field} className="border-t">
                            <td className="p-4 font-medium capitalize">
                              {field.split('.').pop()?.replace(/([A-Z])/g, ' $1').trim()}
                            </td>
                            {compareList.map(id => {
                              const program = programs.find(p => p.id === id);
                              const value = field.split('.').reduce((obj: any, key) => obj?.[key], program);
                              return (
                                <td key={id} className="p-4">{value}</td>
                              );
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* CTA Section */}
        <section className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white py-16">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h2 className="text-3xl font-bold mb-4">Can't find what you're looking for?</h2>
            <p className="text-xl mb-8">Our admission counselors are here to help you find the perfect program</p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <CTALink
                to="/admissions"
                variant="secondary"
                size="lg"
                icon={<MessageSquare className="h-5 w-5" />}
                analyticsEvent="programs_talk_to_counselor"
              >
                Talk to Counselor
              </CTALink>
              <CTALink
                to="tel:+919876543210"
                variant="outline"
                size="lg"
                external
                icon={<Phone className="h-5 w-5" />}
                className="!text-white !border-white hover:!bg-white hover:!text-purple-600"
              >
                Call: +91 98765 43210
              </CTALink>
            </div>
          </div>
        </section>
      </div>
    </>
  );
};

export default ProgramsList;