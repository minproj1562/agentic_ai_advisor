import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence, useScroll, useTransform, useInView } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext'; // Adjust the import path as needed
import {
  GraduationCap,
  Brain,
  TrendingUp,
  Users,
  Award,
  BookOpen,
  BarChart3,
  Sparkles,
  Shield,
  Clock,
  Target,
  Zap,
  CheckCircle,
  ArrowRight,
  Menu,
  X,
  ChevronDown,
  Star,
  Globe,
  Cpu,
  FileText,
  MessageSquare,
  Play,
  Calendar,
  Building2,
  Library,
  Microscope,
  PenTool,
  Heart,
  Activity,
  PieChart,
  Settings,
  Search,
  Bell,
  ChevronRight,
  School,
  Trophy,
  Lightbulb,
  Layers,
  GitBranch,
  Code,
  Palette,
  Music,
  Camera,
  Headphones,
  Monitor,
  Smartphone,
  Wifi,
  Coffee,
  MapPin,
  Phone,
  Mail,
  ExternalLink,
  Youtube,
  Instagram,
  Facebook,
  Twitter,
  Linkedin,
  Github,
  ArrowUpRight,
  Rocket,
  Flag,
  UserCheck,
  BookMarked,
  BrainCircuit,
  Calculator,
  FlaskConical,
  Atom,
  Dna,
  Binary,
  CircuitBoard,
  Bot,
  Briefcase
} from 'lucide-react';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { user: currentUser } = useAuth(); // Changed from currentUser to user
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [activeFeature, setActiveFeature] = useState(0);
  const [currentTime, setCurrentTime] = useState(new Date());
  const { scrollY } = useScroll();

  // Parallax transforms
  const heroY = useTransform(scrollY, [0, 500], [0, 150]);
  const heroOpacity = useTransform(scrollY, [0, 300], [1, 0]);
  const heroScale = useTransform(scrollY, [0, 300], [1, 0.8]);

  // Animation refs
  const statsRef = useRef(null);
  const isStatsInView = useInView(statsRef, { once: true });

  // Handle scroll for navbar
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Update time
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Animated text for hero
  const [textIndex, setTextIndex] = useState(0);
  const animatedTexts = [
    { text: 'Academic Excellence', gradient: 'from-blue-600 to-cyan-500' },
    { text: 'Smart Campus Life', gradient: 'from-purple-600 to-pink-500' },
    { text: 'AI-Powered Learning', gradient: 'from-green-600 to-emerald-500' },
    { text: 'Research Innovation', gradient: 'from-orange-600 to-red-500' }
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setTextIndex((prev) => (prev + 1) % animatedTexts.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  // Dynamic features data
  const features = [
    {
      icon: <BrainCircuit className="h-8 w-8" />,
      title: 'AI-Powered Academic Advisor',
      description: 'Get personalized course recommendations, study plans, and career guidance powered by advanced AI.',
      color: 'from-violet-500 to-purple-600',
      stats: '98% Accuracy'
    },
    {
      icon: <BarChart3 className="h-8 w-8" />,
      title: 'Real-Time Performance Analytics',
      description: 'Track SGPI/CGPA trends, identify weak areas, and get actionable insights to improve performance.',
      color: 'from-blue-500 to-cyan-600',
      stats: 'Live Updates'
    },
    {
      icon: <Users className="h-8 w-8" />,
      title: 'Smart Faculty Matching',
      description: 'Connect with the right mentors based on your academic needs, research interests, and career goals.',
      color: 'from-emerald-500 to-green-600',
      stats: '500+ Faculty'
    },
    {
      icon: <Trophy className="h-8 w-8" />,
      title: 'Achievement & Recognition',
      description: 'Earn badges, certificates, and recognition for academic milestones and improvements.',
      color: 'from-amber-500 to-orange-600',
      stats: '1000+ Badges'
    },
    {
      icon: <BookMarked className="h-8 w-8" />,
      title: 'Smart Study Resources',
      description: 'Access curated learning materials, past papers, and video tutorials tailored to your courses.',
      color: 'from-pink-500 to-rose-600',
      stats: '10K+ Resources'
    },
    {
      icon: <Microscope className="h-8 w-8" />,
      title: 'Research Opportunities',
      description: 'Discover and apply for research projects, internships, and collaboration opportunities.',
      color: 'from-indigo-500 to-blue-600',
      stats: '200+ Projects'
    }
  ];

  // Departments data
  const departments = [
    { name: 'Computer Science', icon: <Code className="h-6 w-6" />, students: 1200, faculty: 45, color: 'from-blue-500 to-indigo-600' },
    { name: 'Engineering', icon: <Cpu className="h-6 w-6" />, students: 1500, faculty: 60, color: 'from-orange-500 to-red-600' },
    { name: 'Business', icon: <Briefcase className="h-6 w-6" />, students: 800, faculty: 30, color: 'from-green-500 to-emerald-600' },
    { name: 'Sciences', icon: <Atom className="h-6 w-6" />, students: 900, faculty: 35, color: 'from-purple-500 to-pink-600' },
    { name: 'Arts', icon: <Palette className="h-6 w-6" />, students: 600, faculty: 25, color: 'from-yellow-500 to-amber-600' },
    { name: 'Medicine', icon: <Heart className="h-6 w-6" />, students: 400, faculty: 40, color: 'from-red-500 to-pink-600' }
  ];

  // Campus life features
  const campusLife = [
    { icon: <Library className="h-10 w-10" />, title: '24/7 Digital Library', count: '1M+ Books' },
    { icon: <Wifi className="h-10 w-10" />, title: 'Smart Campus', count: '100% Coverage' },
    { icon: <Coffee className="h-10 w-10" />, title: 'Study Spaces', count: '50+ Zones' },
    { icon: <Users className="h-10 w-10" />, title: 'Student Clubs', count: '100+ Active' }
  ];

  // Success stories
  const successStories = [
    {
      name: 'Priya Sharma',
      department: 'Computer Science',
      achievement: 'Improved SGPI from 7.2 to 9.1',
      story: 'The AI recommendations helped me identify my weak areas and the perfect electives for my career path.',
      image: '👩‍💻',
      badge: 'Top Performer'
    },
    {
      name: 'Rahul Verma',
      department: 'Engineering',
      achievement: 'Published 3 Research Papers',
      story: 'Faculty matching connected me with the perfect mentor who guided my research journey.',
      image: '👨‍🔬',
      badge: 'Research Star'
    },
    {
      name: 'Ananya Patel',
      department: 'Business',
      achievement: 'Landed Dream Internship',
      story: 'CV analysis and personalized guidance helped me secure an internship at a Fortune 500 company.',
      image: '👩‍💼',
      badge: 'Career Ready'
    }
  ];

  // Live stats with animation
  const [stats, setStats] = useState({
    students: 0,
    faculty: 0,
    courses: 0,
    placements: 0
  });

  useEffect(() => {
    if (isStatsInView) {
      const duration = 2000;
      const steps = 60;
      const interval = duration / steps;
      
      const targetStats = {
        students: 15000,
        faculty: 500,
        courses: 1200,
        placements: 95
      };

      let current = 0;
      const timer = setInterval(() => {
        current++;
        const progress = current / steps;
        
        setStats({
          students: Math.floor(targetStats.students * progress),
          faculty: Math.floor(targetStats.faculty * progress),
          courses: Math.floor(targetStats.courses * progress),
          placements: Math.floor(targetStats.placements * progress)
        });

        if (current >= steps) clearInterval(timer);
      }, interval);

      return () => clearInterval(timer);
    }
  }, [isStatsInView]);

  // Manual redirect to dashboard if authenticated (optional button)
  const handleGetStarted = () => {
    if (currentUser) {
      const userRole = currentUser.role || 'student'; // Assume role is stored in user object
      navigate(`/${userRole}/dashboard`);
    } else {
      navigate('/register'); // Redirect to register for unauthenticated users
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 overflow-x-hidden">
      {/* Advanced Navigation Bar */}
      <motion.nav
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ type: 'spring', stiffness: 100 }}
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
          scrolled 
            ? 'bg-white/95 backdrop-blur-xl shadow-2xl border-b border-gray-100' 
            : 'bg-gradient-to-b from-white/80 to-transparent backdrop-blur-sm'
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 lg:h-20">
            {/* Logo with animation */}
            <motion.div 
              className="flex items-center space-x-3 cursor-pointer"
              whileHover={{ scale: 1.05 }}
              onClick={() => navigate('/')}
            >
              <motion.div 
                animate={{ rotate: [0, 360] }}
                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                className="h-12 w-12 bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 rounded-2xl flex items-center justify-center shadow-xl"
              >
                <GraduationCap className="h-7 w-7 text-white" />
              </motion.div>
              <div>
                <span className="text-xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
                  Smart Campus
                </span>
                <p className="text-xs text-gray-500">Powered by AI</p>
              </div>
            </motion.div>

            {/* Desktop Navigation with hover effects */}
            <div className="hidden lg:flex items-center space-x-8">
              <nav className="flex items-center space-x-1">
                {[
                  { name: 'Home', icon: <Building2 className="h-4 w-4" /> },
                  { name: 'Features', icon: <Sparkles className="h-4 w-4" /> },
                  { name: 'Departments', icon: <School className="h-4 w-4" /> },
                  { name: 'Resources', icon: <BookOpen className="h-4 w-4" /> },
                  { name: 'Success Stories', icon: <Trophy className="h-4 w-4" /> }
                ].map((item) => (
                  <motion.a
                    key={item.name}
                    href={`#${item.name.toLowerCase().replace(' ', '-')}`}
                    className="group relative px-4 py-2 rounded-xl transition-all"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <span className="flex items-center space-x-2 font-medium text-gray-700 group-hover:text-purple-600 transition-colors">
                      {item.icon}
                      <span>{item.name}</span>
                    </span>
                    <motion.div
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-indigo-600 to-purple-600"
                      initial={{ scaleX: 0 }}
                      whileHover={{ scaleX: 1 }}
                      transition={{ duration: 0.3 }}
                    />
                  </motion.a>
                ))}
              </nav>
              
              <div className="flex items-center space-x-4">
                {/* Search button */}
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  className="p-2 rounded-xl hover:bg-gray-100 transition-colors"
                >
                  <Search className="h-5 w-5 text-gray-600" />
                </motion.button>

                {/* Notification button */}
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  className="relative p-2 rounded-xl hover:bg-gray-100 transition-colors"
                >
                  <Bell className="h-5 w-5 text-gray-600" />
                  <span className="absolute top-0 right-0 h-2 w-2 bg-red-500 rounded-full animate-pulse"></span>
                </motion.button>

                {/* Login button */}
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => navigate('/login')}
                  className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-xl shadow-lg hover:shadow-xl transition-all relative overflow-hidden btn-gradient"
                >
                  <span className="relative z-10">Student Portal</span>
                  <motion.div
                    className="absolute inset-0 bg-gradient-to-r from-purple-600 to-pink-600"
                    initial={{ x: '100%' }}
                    whileHover={{ x: 0 }}
                    transition={{ duration: 0.3 }}
                  />
                </motion.button>
              </div>
            </div>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-xl hover:bg-gray-100 transition-colors"
            >
              {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu with animations */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="lg:hidden bg-white/95 backdrop-blur-xl border-t"
            >
              <div className="px-4 py-6 space-y-3">
                {['Home', 'Features', 'Departments', 'Resources', 'Success Stories'].map((item, index) => (
                  <motion.a
                    key={item}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    href={`#${item.toLowerCase().replace(' ', '-')}`} // Fixed: toLowercase -> toLowerCase
                    className="block px-4 py-3 text-gray-700 hover:bg-gradient-to-r hover:from-indigo-50 hover:to-purple-50 rounded-xl transition-all"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    {item}
                  </motion.a>
                ))}
                <motion.button
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 }}
                  onClick={() => navigate('/login')}
                  className="w-full px-4 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-medium shadow-lg btn-gradient"
                >
                  Student Portal
                </motion.button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.nav>

      {/* Advanced Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 pt-20 overflow-hidden">
        {/* Animated background elements */}
        <div className="absolute inset-0">
          <motion.div
            animate={{
              scale: [1, 1.2, 1],
              rotate: [0, 180, 360]
            }}
            transition={{
              duration: 20,
              repeat: Infinity,
              ease: "linear"
            }}
            className="absolute top-20 left-20 w-72 h-72 bg-gradient-to-r from-blue-400 to-purple-400 rounded-full mix-blend-multiply filter blur-3xl opacity-20"
          />
          <motion.div
            animate={{
              scale: [1.2, 1, 1.2],
              rotate: [360, 180, 0]
            }}
            transition={{
              duration: 25,
              repeat: Infinity,
              ease: "linear"
            }}
            className="absolute bottom-20 right-20 w-96 h-96 bg-gradient-to-r from-pink-400 to-orange-400 rounded-full mix-blend-multiply filter blur-3xl opacity-20"
          />
          <motion.div
            animate={{
              y: [0, 100, 0],
              x: [0, 50, 0]
            }}
            transition={{
              duration: 30,
              repeat: Infinity,
              ease: "linear"
            }}
            className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-gradient-to-r from-green-400 to-cyan-400 rounded-full mix-blend-multiply filter blur-3xl opacity-20"
          />
        </div>

        <motion.div
          style={{ y: heroY, opacity: heroOpacity, scale: heroScale }}
          className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20"
        >
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Hero Content */}
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
            >
              {/* Badge */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="inline-flex items-center px-6 py-3 bg-white/80 backdrop-blur-xl rounded-full mb-8 shadow-xl"
              >
                <Rocket className="h-5 w-5 text-purple-600 mr-2 animate-pulse" />
                <span className="text-sm font-semibold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                  #1 Smart Campus Platform in India
                </span>
                <span className="ml-2 px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full font-bold">
                  LIVE
                </span>
              </motion.div>

              <h1 className="text-5xl lg:text-7xl font-bold text-gray-900 mb-6 leading-tight">
                Welcome to the
                <span className="block mt-2">
                  Future of
                </span>
                <AnimatePresence mode="wait">
                  <motion.span
                    key={textIndex}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.5 }}
                    className={`block bg-gradient-to-r ${animatedTexts[textIndex].gradient} bg-clip-text text-transparent`}
                  >
                    {animatedTexts[textIndex].text}
                  </motion.span>
                </AnimatePresence>
              </h1>

              <p className="text-xl text-gray-600 mb-8 leading-relaxed">
                Transform your college experience with AI-powered guidance, real-time analytics, 
                and personalized academic support. Join thousands of students achieving excellence.
              </p>

              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 mb-8">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleGetStarted}
                  className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-2xl shadow-xl hover:shadow-2xl transition-all flex items-center justify-center group btn-gradient"
                >
                  <span className="relative z-10 flex items-center">
                    Get Started Now
                    <ArrowRight className="h-5 w-5 ml-2 group-hover:translate-x-1 transition-transform" />
                  </span>
                  <motion.div
                    className="absolute inset-0 bg-gradient-to-r from-purple-600 to-pink-600"
                    initial={{ x: '100%' }}
                    whileHover={{ x: 0 }}
                    transition={{ duration: 0.3 }}
                  />
                </motion.button>
                
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-8 py-4 bg-white/80 backdrop-blur-xl text-gray-700 font-semibold rounded-2xl shadow-lg hover:shadow-xl transition-all flex items-center justify-center border border-gray-200"
                >
                  <Play className="h-5 w-5 mr-2 text-purple-600" />
                  Watch Campus Tour
                  <span className="ml-2 text-xs bg-red-100 text-red-600 px-2 py-1 rounded-full animate-pulse">
                    360°
                  </span>
                </motion.button>
              </div>

              {/* Live Campus Stats */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                {[
                  { icon: <Users className="h-4 w-4" />, value: '2,543', label: 'Online Now' },
                  { icon: <Clock className="h-4 w-4" />, value: currentTime.toLocaleTimeString(), label: 'Campus Time' },
                  { icon: <Wifi className="h-4 w-4" />, value: '100%', label: 'Network' },
                  { icon: <Activity className="h-4 w-4" />, value: '98%', label: 'Uptime' }
                ].map((stat, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5 + index * 0.1 }}
                    className="bg-white/60 backdrop-blur-xl rounded-xl p-3 border border-white/50"
                  >
                    <div className="flex items-center text-purple-600 mb-1">
                      {stat.icon}
                      <span className="ml-2 text-xs font-medium">{stat.label}</span>
                    </div>
                    <p className="text-lg font-bold text-gray-900">{stat.value}</p>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            {/* Interactive Dashboard Preview */}
            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
              className="relative"
            >
              <motion.div
                animate={{ y: [0, -20, 0] }}
                transition={{ duration: 4, repeat: Infinity }}
                className="relative"
              >
                {/* Main Dashboard Card */}
                <div className="bg-white/90 backdrop-blur-xl rounded-3xl shadow-2xl p-6 border border-gray-100">
                  {/* Dashboard Header */}
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center space-x-3">
                      <div className="h-12 w-12 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl flex items-center justify-center">
                        <Brain className="h-7 w-7 text-white" />
                      </div>
                      <div>
                        <p className="font-bold text-gray-900">AI Dashboard</p>
                        <p className="text-xs text-gray-500">Real-time Analytics</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></span>
                      <span className="text-xs text-gray-500">Live</span>
                    </div>
                  </div>

                  {/* Animated Stats Grid */}
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <motion.div
                      whileHover={{ scale: 1.05 }}
                      className="bg-gradient-to-br from-blue-50 to-indigo-100 rounded-2xl p-4"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <TrendingUp className="h-5 w-5 text-blue-600" />
                        <motion.span
                          animate={{ scale: [1, 1.2, 1] }}
                          transition={{ duration: 2, repeat: Infinity }}
                          className="text-xs text-green-600 font-bold"
                        >
                          +15%
                        </motion.span>
                      </div>
                      <p className="text-2xl font-bold text-gray-900">9.2</p>
                      <p className="text-xs text-gray-600">Current SGPI</p>
                    </motion.div>

                    <motion.div
                      whileHover={{ scale: 1.05 }}
                      className="bg-gradient-to-br from-purple-50 to-pink-100 rounded-2xl p-4"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <Award className="h-5 w-5 text-purple-600" />
                        <span className="text-xs text-purple-600 font-bold">Top 5%</span>
                      </div>
                      <p className="text-2xl font-bold text-gray-900">12</p>
                      <p className="text-xs text-gray-600">Achievements</p>
                    </motion.div>
                  </div>

                  {/* Live Performance Chart */}
                  <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl p-4">
                    <div className="flex items-center justify-between mb-3">
                      <p className="text-sm font-bold text-gray-700">Performance Trend</p>
                      <BarChart3 className="h-4 w-4 text-gray-400" />
                    </div>
                    <div className="h-32 flex items-end justify-between space-x-2">
                      {[65, 72, 78, 82, 85, 89, 92].map((height, i) => (
                        <motion.div
                          key={i}
                          initial={{ height: 0 }}
                          animate={{ height: `${height}%` }}
                          transition={{ delay: i * 0.1, duration: 0.5 }}
                          className="flex-1 bg-gradient-to-t from-indigo-600 to-purple-600 rounded-t-lg relative group"
                        >
                          <motion.div
                            className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            {height}%
                          </motion.div>
                        </motion.div>
                      ))}
                    </div>
                    <div className="flex justify-between mt-2 text-xs text-gray-500">
                      <span>Sem 1</span>
                      <span>Sem 7</span>
                    </div>
                  </div>

                  {/* AI Recommendations */}
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 1 }}
                    className="mt-4 p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-2xl"
                  >
                    <div className="flex items-start space-x-3">
                      <Sparkles className="h-5 w-5 text-purple-600 mt-1" />
                      <div>
                        <p className="text-sm font-bold text-gray-900">AI Recommendation</p>
                        <p className="text-xs text-gray-600 mt-1">
                          Focus on Data Structures this week to improve your placement chances by 23%
                        </p>
                      </div>
                    </div>
                  </motion.div>
                </div>

                {/* Floating Feature Cards */}
                <motion.div
                  animate={{ 
                    y: [0, -10, 0],
                    rotate: [-5, 5, -5]
                  }}
                  transition={{ 
                    duration: 4,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                  className="absolute -top-4 -right-4 bg-gradient-to-r from-green-500 to-emerald-500 text-white px-4 py-2 rounded-2xl shadow-xl text-sm font-bold"
                >
                  AI-Powered 🚀
                </motion.div>

                <motion.div
                  animate={{ 
                    y: [0, 10, 0],
                    rotate: [5, -5, 5]
                  }}
                  transition={{ 
                    duration: 4,
                    repeat: Infinity,
                    ease: "easeInOut",
                    delay: 2
                  }}
                  className="absolute -bottom-4 -left-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white px-4 py-2 rounded-2xl shadow-xl text-sm font-bold"
                >
                  Real-time ⚡
                </motion.div>

                <motion.div
                  animate={{ 
                    scale: [1, 1.1, 1],
                    rotate: [0, 360, 0]
                  }}
                  transition={{ 
                    duration: 3,
                    repeat: Infinity,
                    ease: "easeInOut",
                    delay: 1
                  }}
                  className="absolute top-1/2 -right-8 bg-yellow-500 text-white h-12 w-12 rounded-full flex items-center justify-center shadow-xl"
                >
                  <Star className="h-6 w-6" />
                </motion.div>
              </motion.div>
            </motion.div>
          </div>
        </motion.div>

        {/* Scroll Indicator */}
        <motion.div
          animate={{ y: [0, 10, 0] }}
          transition={{ repeat: Infinity, duration: 2 }}
          className="absolute bottom-8 left-1/2 transform -translate-x-1/2"
        >
          <ChevronDown className="h-8 w-8 text-gray-400" />
        </motion.div>
      </section>

      {/* Live Campus Stats Section */}
      <section ref={statsRef} className="py-20 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 relative overflow-hidden">
        {/* Animated background pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }} />
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-4xl lg:text-5xl font-bold text-white mb-4">
              Campus at a Glance
            </h2>
            <p className="text-xl text-white/80">Real-time statistics powered by smart analytics</p>
          </motion.div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              { icon: <Users className="h-8 w-8" />, value: stats.students.toLocaleString(), label: 'Active Students', suffix: '+' },
              { icon: <UserCheck className="h-8 w-8" />, value: stats.faculty, label: 'Expert Faculty', suffix: '+' },
              { icon: <BookOpen className="h-8 w-8" />, value: stats.courses.toLocaleString(), label: 'Courses Offered', suffix: '+' },
              { icon: <Trophy className="h-8 w-8" />, value: stats.placements, label: 'Placement Rate', suffix: '%' }
            ].map((stat, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.5 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1, type: "spring" }}
                viewport={{ once: true }}
                className="text-center"
              >
                <motion.div
                  whileHover={{ scale: 1.1, rotate: 360 }}
                  transition={{ duration: 0.5 }}
                  className="inline-flex items-center justify-center h-20 w-20 bg-white/20 backdrop-blur-xl rounded-2xl mb-4"
                >
                  {React.cloneElement(stat.icon, { className: "h-10 w-10 text-white" })}
                </motion.div>
                <motion.p
                  className="text-5xl lg:text-6xl font-bold text-white mb-2"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: isStatsInView ? 1 : 0 }}
                  transition={{ duration: 0.5 }}
                >
                  {stat.value}{stat.suffix}
                </motion.p>
                <p className="text-white/80 font-medium">{stat.label}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section with Interactive Cards */}
      <section id="features" className="py-20 bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <motion.div
              initial={{ scale: 0 }}
              whileInView={{ scale: 1 }}
              transition={{ type: "spring", duration: 0.5 }}
              className="inline-flex items-center px-4 py-2 bg-purple-100 rounded-full mb-4"
            >
              <Sparkles className="h-4 w-4 text-purple-600 mr-2" />
              <span className="text-sm font-medium text-purple-700">Powered by Advanced AI</span>
            </motion.div>
            
            <h2 className="text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
              Everything You Need for
              <span className="block mt-2 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
                Academic Excellence
              </span>
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Comprehensive suite of AI-powered tools designed to transform your academic journey
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                viewport={{ once: true }}
                onHoverStart={() => setActiveFeature(index)}
                className="group relative"
              >
                <motion.div
                  whileHover={{ y: -10 }}
                  className="h-full bg-white rounded-3xl p-8 shadow-lg hover:shadow-2xl transition-all border border-gray-100 relative overflow-hidden"
                >
                  {/* Background gradient on hover */}
                  <motion.div
                    className={`absolute inset-0 bg-gradient-to-br ${feature.color} opacity-0 group-hover:opacity-5 transition-opacity`}
                  />
                  
                  {/* Icon with animation */}
                  <motion.div
                    whileHover={{ rotate: 360, scale: 1.1 }}
                    transition={{ duration: 0.5 }}
                    className={`h-16 w-16 bg-gradient-to-r ${feature.color} rounded-2xl flex items-center justify-center text-white mb-6 shadow-xl`}
                  >
                    {feature.icon}
                  </motion.div>
                  
                  {/* Content */}
                  <h3 className="text-xl font-bold text-gray-900 mb-3">{feature.title}</h3>
                  <p className="text-gray-600 mb-4 leading-relaxed">{feature.description}</p>
                  
                  {/* Stats badge */}
                  <div className="flex items-center justify-between">
                    <span className="inline-flex items-center px-3 py-1 bg-gray-100 rounded-full text-sm font-medium text-gray-700">
                      {feature.stats}
                    </span>
                    <motion.button
                      whileHover={{ x: 5 }}
                      className="text-purple-600 font-medium flex items-center group"
                    >
                      Learn more
                      <ArrowRight className="h-4 w-4 ml-2 group-hover:translate-x-1 transition-transform" />
                    </motion.button>
                  </div>

                  {/* Animated border on hover */}
                  <motion.div
                    className="absolute inset-0 rounded-3xl border-2 border-transparent group-hover:border-purple-500/20 transition-all"
                    initial={{ scale: 1 }}
                    whileHover={{ scale: 1.02 }}
                  />
                </motion.div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Departments Section */}
      <section id="departments" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
              Academic Departments
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Excellence across diverse fields of study
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {departments.map((dept, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
                viewport={{ once: true }}
                whileHover={{ y: -5 }}
                className="bg-gradient-to-br from-white to-gray-50 rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all border border-gray-100"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className={`h-14 w-14 bg-gradient-to-r ${dept.color} rounded-xl flex items-center justify-center text-white shadow-lg`}>
                    {dept.icon}
                  </div>
                  <motion.div
                    whileHover={{ rotate: 360 }}
                    transition={{ duration: 0.5 }}
                    className="h-8 w-8 bg-gray-100 rounded-full flex items-center justify-center"
                  >
                    <ExternalLink className="h-4 w-4 text-gray-600" />
                  </motion.div>
                </div>
                
                <h3 className="text-lg font-bold text-gray-900 mb-3">{dept.name}</h3>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Students</span>
                    <span className="font-semibold text-gray-900">{dept.students.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Faculty</span>
                    <span className="font-semibold text-gray-900">{dept.faculty}</span>
                  </div>
                </div>

                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="w-full mt-4 py-2 bg-gradient-to-r from-gray-100 to-gray-200 text-gray-700 rounded-xl font-medium hover:from-gray-200 hover:to-gray-300 transition-all"
                >
                  View Programs
                </motion.button>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Campus Life Section */}
      <section className="py-20 bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
              Smart Campus Life
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Experience a digitally-enabled campus with world-class facilities
            </p>
          </motion.div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {campusLife.map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                viewport={{ once: true }}
                whileHover={{ scale: 1.05 }}
                className="bg-white rounded-2xl p-6 shadow-lg text-center"
              >
                <motion.div
                  whileHover={{ rotate: 360 }}
                  transition={{ duration: 0.5 }}
                  className="inline-flex items-center justify-center h-20 w-20 bg-gradient-to-r from-indigo-100 to-purple-100 rounded-2xl mb-4"
                >
                  {React.cloneElement(item.icon, { className: "h-10 w-10 text-purple-600" })}
                </motion.div>
                <h3 className="font-bold text-gray-900 mb-2">{item.title}</h3>
                <p className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  {item.count}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Success Stories Section */}
      <section id="success-stories" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
              Student Success Stories
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Real achievements from our AI-powered academic platform
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {successStories.map((story, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                viewport={{ once: true }}
                className="bg-gradient-to-br from-white to-gray-50 rounded-3xl p-8 shadow-lg hover:shadow-xl transition-all border border-gray-100"
              >
                {/* Badge */}
                <div className="flex justify-between items-start mb-6">
                  <span className="text-4xl">{story.image}</span>
                  <span className="px-3 py-1 bg-gradient-to-r from-green-500 to-emerald-500 text-white text-xs font-bold rounded-full">
                    {story.badge}
                  </span>
                </div>

                {/* Achievement */}
                <div className="mb-4 p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl">
                  <p className="text-lg font-bold text-gray-900">{story.achievement}</p>
                </div>

                {/* Story */}
                <p className="text-gray-600 mb-6 italic">"{story.story}"</p>

                {/* Profile */}
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-bold text-gray-900">{story.name}</p>
                    <p className="text-sm text-gray-500">{story.department}</p>
                  </div>
                  <div className="flex">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} className="h-4 w-4 text-yellow-400 fill-current" />
                    ))}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Resources Section */}
      <section id="resources" className="py-20 bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
              Academic Resources
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Everything you need for academic success at your fingertips
            </p>
          </motion.div>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Resource Categories */}
            {[
              {
                title: 'Digital Library',
                icon: <Library className="h-8 w-8" />,
                items: ['1M+ E-books', '500+ Journals', '24/7 Access', 'AI Search'],
                color: 'from-blue-500 to-indigo-600'
              },
              {
                title: 'Learning Tools',
                icon: <Cpu className="h-8 w-8" />,
                items: ['Virtual Labs', 'Simulations', 'Coding Platforms', 'AI Tutors'],
                color: 'from-purple-500 to-pink-600'
              },
              {
                title: 'Career Support',
                icon: <Briefcase className="h-8 w-8" />,
                items: ['Resume Builder', 'Mock Interviews', 'Job Portal', 'Mentorship'],
                color: 'from-green-500 to-emerald-600'
              }
            ].map((resource, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                viewport={{ once: true }}
                whileHover={{ y: -10 }}
                className="bg-white rounded-3xl p-8 shadow-lg hover:shadow-xl transition-all border border-gray-100"
              >
                <div className={`h-16 w-16 bg-gradient-to-r ${resource.color} rounded-2xl flex items-center justify-center text-white mb-6 shadow-xl`}>
                  {resource.icon}
                </div>
                
                <h3 className="text-xl font-bold text-gray-900 mb-4">{resource.title}</h3>
                
                <ul className="space-y-3 mb-6">
                  {resource.items.map((item, i) => (
                    <li key={i} className="flex items-center text-gray-600">
                      <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>

                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className={`w-full py-3 bg-gradient-to-r ${resource.color} text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all btn-gradient`}
                >
                  Explore Now
                </motion.button>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 relative overflow-hidden">
        {/* Animated background elements */}
        <div className="absolute inset-0">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 50, repeat: Infinity, ease: "linear" }}
            className="absolute -top-1/2 -left-1/2 w-full h-full"
          >
            <div className="h-96 w-96 bg-white/10 rounded-full blur-3xl" />
          </motion.div>
          <motion.div
            animate={{ rotate: -360 }}
            transition={{ duration: 40, repeat: Infinity, ease: "linear" }}
            className="absolute -bottom-1/2 -right-1/2 w-full h-full"
          >
            <div className="h-96 w-96 bg-white/10 rounded-full blur-3xl" />
          </motion.div>
        </div>

        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <motion.div
              initial={{ scale: 0 }}
              whileInView={{ scale: 1 }}
              transition={{ type: "spring" }}
              className="inline-flex items-center px-6 py-3 bg-white/20 backdrop-blur-xl rounded-full mb-8"
            >
              <Rocket className="h-5 w-5 text-white mr-2" />
              <span className="text-white font-semibold">Join 15,000+ Students</span>
            </motion.div>

            <h2 className="text-4xl lg:text-6xl font-bold text-white mb-6">
              Ready to Transform Your
              <span className="block mt-2">Academic Journey?</span>
            </h2>
            
            <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
              Experience the power of AI-driven education and join thousands of students achieving excellence
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleGetStarted}
                className="px-8 py-4 bg-white text-blue-600 font-bold rounded-2xl shadow-xl hover:shadow-2xl transition-all flex items-center justify-center group btn-gradient"
              >
                Get Started Now
                <ArrowRight className="h-5 w-5 ml-2 group-hover:translate-x-1 transition-transform" />
              </motion.button>
              
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="px-8 py-4 bg-transparent text-white font-bold rounded-2xl border-2 border-white hover:bg-white hover:text-blue-600 transition-all flex items-center justify-center"
              >
                <Play className="h-5 w-5 mr-2" />
                Watch Demo
              </motion.button>
            </div>

            {/* Trust Indicators */}
            <div className="mt-12 flex flex-wrap items-center justify-center gap-8 text-white/80">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-5 w-5" />
                <span>No Credit Card Required</span>
              </div>
              <div className="flex items-center space-x-2">
                <Clock className="h-5 w-5" />
                <span>Setup in 2 Minutes</span>
              </div>
              <div className="flex items-center space-x-2">
                <Shield className="h-5 w-5" />
                <span>100% Secure</span>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8 mb-12">
            {/* Logo & Info */}
            <div>
              <div className="flex items-center space-x-3 mb-6">
                <div className="h-12 w-12 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl flex items-center justify-center">
                  <GraduationCap className="h-7 w-7 text-white" />
                </div>
                <div>
                  <span className="text-xl font-bold">Smart Campus</span>
                  <p className="text-xs text-gray-400">AI-Powered Excellence</p>
                </div>
              </div>
              <p className="text-gray-400 mb-6">
                Transforming education with artificial intelligence and smart analytics.
              </p>
              <div className="flex space-x-4">
                {[Facebook, Twitter, Instagram, Linkedin, Youtube].map((Icon, index) => (
                  <motion.a
                    key={index}
                    whileHover={{ scale: 1.2, rotate: 360 }}
                    transition={{ duration: 0.3 }}
                    href="#"
                    className="h-10 w-10 bg-gray-800 rounded-xl flex items-center justify-center hover:bg-gradient-to-r hover:from-blue-600 hover:to-purple-600 transition-all"
                  >
                    <Icon className="h-5 w-5" />
                  </motion.a>
                ))}
              </div>
            </div>

            {/* Quick Links */}
            <div>
              <h3 className="font-bold text-lg mb-4">Quick Links</h3>
              <ul className="space-y-3">
                {['About Us', 'Admissions', 'Academics', 'Research', 'Campus Life'].map((item) => (
                  <li key={item}>
                    <a href="#" className="text-gray-400 hover:text-white transition-colors flex items-center group">
                      <ChevronRight className="h-4 w-4 mr-1 group-hover:translate-x-1 transition-transform" />
                      {item}
                    </a>
                  </li>
                ))}
              </ul>
            </div>

            {/* Resources */}
            <div>
              <h3 className="font-bold text-lg mb-4">Resources</h3>
              <ul className="space-y-3">
                {['Student Portal', 'Faculty Portal', 'Digital Library', 'Career Services', 'Alumni Network'].map((item) => (
                  <li key={item}>
                    <a href="#" className="text-gray-400 hover:text-white transition-colors flex items-center group">
                      <ChevronRight className="h-4 w-4 mr-1 group-hover:translate-x-1 transition-transform" />
                      {item}
                    </a>
                  </li>
                ))}
              </ul>
            </div>

            {/* Contact */}
            <div>
              <h3 className="font-bold text-lg mb-4">Contact Us</h3>
              <ul className="space-y-3">
                <li className="flex items-center space-x-3 text-gray-400">
                  <MapPin className="h-5 w-5 text-purple-500" />
                  <span>123 University Ave, Tech City</span>
                </li>
                <li className="flex items-center space-x-3 text-gray-400">
                  <Phone className="h-5 w-5 text-purple-500" />
                  <span>+91 98765 43210</span>
                </li>
                <li className="flex items-center space-x-3 text-gray-400">
                  <Mail className="h-5 w-5 text-purple-500" />
                  <span>info@smartcampus.edu</span>
                </li>
              </ul>

              {/* Office Hours */}
              <div className="mt-6 p-4 bg-gray-800 rounded-xl">
                <p className="text-sm font-semibold text-white mb-2">Office Hours</p>
                <p className="text-xs text-gray-400">Mon - Fri: 9:00 AM - 6:00 PM</p>
                <p className="text-xs text-gray-400">Sat: 10:00 AM - 4:00 PM</p>
              </div>
            </div>
          </div>

          {/* Bottom Bar */}
          <div className="border-t border-gray-800 pt-8 flex flex-col md:flex-row justify-between items-center">
            <p className="text-gray-400 mb-4 md:mb-0">
              © 2024 Smart Campus. All rights reserved.
            </p>
            <div className="flex space-x-6">
              <a href="#" className="text-gray-400 hover:text-white transition-colors">Privacy Policy</a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors">Terms of Service</a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors">Cookie Policy</a>
            </div>
          </div>
        </div>
      </footer>

      {/* Floating Action Buttons */}
      <div className="fixed bottom-8 right-8 z-40 flex flex-col space-y-4">
        {/* Chat Button */}
        <motion.button
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 1 }}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          className="h-14 w-14 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full shadow-2xl flex items-center justify-center text-white relative"
        >
          <MessageSquare className="h-6 w-6" />
          <span className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full animate-ping"></span>
        </motion.button>

        {/* Back to Top */}
        {scrolled && (
          <motion.button
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            className="h-14 w-14 bg-white shadow-2xl rounded-full flex items-center justify-center text-purple-600 border border-gray-100"
          >
            <ChevronDown className="h-6 w-6 rotate-180" />
          </motion.button>
        )}
      </div>
    </div>
  );
};

export default HomePage;