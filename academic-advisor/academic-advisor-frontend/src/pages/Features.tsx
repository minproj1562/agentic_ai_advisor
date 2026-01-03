// src/pages/Features.tsx
import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence, useScroll, useTransform } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import {
  Sparkles,
  Brain,
  BarChart3,
  Users,
  Shield,
  Zap,
  Globe,
  Clock,
  Trophy,
  Target,
  Layers,
  Code,
  Database,
  Cloud,
  Lock,
  Smartphone,
  Monitor,
  Wifi,
  Battery,
  Cpu,
  HardDrive,
  Server,
  GitBranch,
  Terminal,
  Package,
  Puzzle,
  Workflow,
  Activity,
  TrendingUp,
  PieChart,
  Calendar,
  Bell,
  MessageSquare,
  Video,
  Mic,
  Camera,
  Share2,
  Download,
  Upload,
  FileText,
  BookOpen,
  GraduationCap,
  Award,
  Medal,
  Flag,
  Rocket,
  Lightbulb,
  Eye,
  Search,
  Filter,
  Settings,
  Palette,
  Brush,
  PenTool,
  Layout,
  Grid,
  List,
  Map,
  Navigation,
  Compass,
  MapPin,
  Route,
  Send,
  Inbox,
  Archive,
  Trash,
  Edit,
  Copy,
  Clipboard,
  Link,
  ExternalLink,
  Anchor,
  Command,
  Terminal as TerminalIcon,
  Code2,
  Binary,
  Hash,
  Variable,
  Braces,
  Brackets,
  FileCode,
  FolderOpen,
  Save,
  RefreshCw,
  RotateCw,
  Loader,
  CheckCircle,
  XCircle,
  AlertCircle,
  Info,
  HelpCircle,
  Plus,
  Minus,
  X,
  Check,
  ChevronRight,
  ChevronLeft,
  ChevronUp,
  ChevronDown,
  ChevronsRight,
  ChevronsLeft,
  ArrowRight,
  ArrowLeft,
  ArrowUp,
  ArrowDown,
  Maximize,
  Minimize,
  Expand,
  Shrink,
  Move,
  MoreVertical,
  MoreHorizontal,
  Menu,
  Sidebar,
  Columns,
  Square,
  Circle,
  Triangle,
  Hexagon,
  Octagon,
  Star,
  Heart,
  ThumbsUp,
  ThumbsDown,
  Bookmark,
  Tag,
  Hash as HashIcon,
  AtSign,
  DollarSign,
  Percent,
  Calculator,
  Gauge,
  Thermometer,
  Droplet,
  Flame,
  Wind,
  CloudRain,
  Sun,
  Moon,
  Stars,
  Sunrise,
  Sunset,
  Music,
  Radio,
  Podcast,
  Voicemail,
  PhoneCall,
  PhoneIncoming,
  PhoneOutgoing,
  PhoneMissed,
  PhoneOff,
  Video as VideoIcon,
  VideoOff,
  Airplay,
  Cast,
  Tv,
  Speaker,
  Volume,
  Volume1,
  Volume2,
  VolumeX,
  Headphones,
  Bluetooth,
  WifiOff,
  Signal,
  Smartphone as SmartphoneIcon,
  Tablet,
  Laptop,
  Monitor as MonitorIcon,
  Watch,
  Gamepad,
  Keyboard,
  Mouse,
  HardDrive as HardDriveIcon,
  Disc,
  Printer,
  Camera as CameraIcon,
  Image,
  Film,
  FileImage,
  Aperture,
  Sliders,
  Crosshair,
  ZoomIn,
  ZoomOut,
  Search as SearchIcon,
  Eye as EyeIcon,
  EyeOff,
  Microscope,
  Telescope,
  Glasses,
  Accessibility,
  UserCheck,
  UserPlus,
  UserMinus,
  UserX,
  Users as UsersIcon,
  Building,
  Home,
  Store,
  ShoppingCart,
  ShoppingBag,
  Package as PackageIcon,
  Gift,
  CreditCard,
  Wallet,
  Receipt,
  Banknote,
  Coins,
  PiggyBank,
  Vault,
  Scale,
  Gavel,
  Handshake,
  Briefcase,
  Backpack,
  Luggage,
  Plane,
  Train,
  Car,
  Bus,
  Bike,
  Ship,
  Anchor as AnchorIcon,
  Compass as CompassIcon,
  Map as MapIcon,
  Navigation2,
  Milestone,
  Signpost,
  Construction,
  Hammer,
  Wrench,
  PaintBucket,
  Paintbrush,
  Ruler,
  PencilRuler,
  Eraser,
  Scissors,
  Paperclip,
  Pin,
  Stamp,
  Ticket,
  Tag as TagIcon,
  Badge,
  Medal as MedalIcon,
  Trophy as TrophyIcon,
  Crown,
  Gem,
  Sparkle,
  Wand,
  Zap as ZapIcon,
  Flashlight,
  Lightbulb as LightbulbIcon,
  Lamp,
  Flame as FlameIcon,
  Snowflake,
  Cloud as CloudIcon,
  CloudRain as CloudRainIcon,
  CloudSnow,
  CloudLightning,
  Rainbow,
  Umbrella,
  Waves,
  Wind as WindIcon,
  Tornado,
  Sunrise as SunriseIcon,
  Sunset as SunsetIcon,
  Mountain,
  TreePine,
  Trees,
  Palmtree as PalmTree,
  Flower,
  Flower2,
  Leaf,
  Feather,
  Bird,
  Fish,
  Bug,
  Cat,
  Dog,
  Rabbit,
  Turtle,
  Squirrel,
  Bone,
  Egg,
  Apple,
  Cherry,
  Grape,
  Banana,
  Carrot,
  Wheat,
  Croissant,
  Pizza,
  Sandwich,
  Candy,
  Coffee,
  Milk,
  Beer,
  Wine,
  Martini,
  Utensils,
  Microwave,
  Refrigerator,
  Scale as ScaleIcon,
  Play // Added Play icon which was missing
} from 'lucide-react';
import CTALink from '../components/common/CTALink';
import { useAnalytics } from '../hooks/useAnalytics';
import toast from 'react-hot-toast';

// Feature categories
const featureCategories = [
  {
    id: 'ai-powered',
    name: 'AI-Powered Intelligence',
    description: 'Advanced artificial intelligence capabilities',
    icon: <Brain className="h-6 w-6" />,
    color: 'from-purple-500 to-pink-600'
  },
  {
    id: 'analytics',
    name: 'Real-Time Analytics',
    description: 'Comprehensive data insights and reporting',
    icon: <BarChart3 className="h-6 w-6" />,
    color: 'from-blue-500 to-cyan-600'
  },
  {
    id: 'collaboration',
    name: 'Collaboration Tools',
    description: 'Seamless team collaboration features',
    icon: <Users className="h-6 w-6" />,
    color: 'from-green-500 to-emerald-600'
  },
  {
    id: 'security',
    name: 'Security & Privacy',
    description: 'Enterprise-grade security measures',
    icon: <Shield className="h-6 w-6" />,
    color: 'from-red-500 to-orange-600'
  },
  {
    id: 'integration',
    name: 'Integrations',
    description: 'Connect with your favorite tools',
    icon: <Puzzle className="h-6 w-6" />,
    color: 'from-indigo-500 to-purple-600'
  },
  {
    id: 'mobile',
    name: 'Mobile Experience',
    description: 'Optimized for all devices',
    icon: <Smartphone className="h-6 w-6" />,
    color: 'from-yellow-500 to-orange-600'
  }
];

// Detailed features data
const featuresData = [
  {
    id: '1',
    category: 'ai-powered',
    title: 'Smart Academic Advisor',
    description: 'AI-powered personalized academic guidance and course recommendations',
    icon: <Brain className="h-8 w-8" />,
    benefits: [
      'Personalized course recommendations',
      'Career path guidance',
      'Performance predictions',
      'Study schedule optimization'
    ],
    stats: {
      accuracy: '98%',
      timesSaved: '10 hours/week',
      satisfaction: '4.9/5'
    },
    demo: {
      type: 'interactive',
      url: '/demo/academic-advisor'
    },
    testimonial: {
      text: 'The AI advisor helped me choose the perfect courses for my career goals.',
      author: 'Sarah Johnson',
      role: 'Computer Science Student'
    }
  },
  {
    id: '2',
    category: 'ai-powered',
    title: 'Intelligent Content Recommendations',
    description: 'Get personalized learning materials based on your progress and interests',
    icon: <Sparkles className="h-8 w-8" />,
    benefits: [
      'Adaptive learning paths',
      'Content difficulty adjustment',
      'Topic recommendations',
      'Resource suggestions'
    ],
    stats: {
      engagement: '+45%',
      completion: '85%',
      improvement: '+32%'
    },
    demo: {
      type: 'video',
      url: 'https://www.youtube.com/watch?v=demo'
    }
  },
  {
    id: '3',
    category: 'analytics',
    title: 'Performance Analytics Dashboard',
    description: 'Real-time insights into academic performance and progress tracking',
    icon: <BarChart3 className="h-8 w-8" />,
    benefits: [
      'Real-time grade tracking',
      'Performance trends',
      'Comparative analysis',
      'Predictive insights'
    ],
    stats: {
      dataPoints: '500+',
      updateFrequency: 'Real-time',
      accuracy: '99.9%'
    },
    demo: {
      type: 'screenshot',
      images: ['/images/dashboard1.png', '/images/dashboard2.png']
    }
  },
  {
    id: '4',
    category: 'analytics',
    title: 'Attendance & Engagement Tracking',
    description: 'Automated attendance tracking with engagement metrics',
    icon: <Activity className="h-8 w-8" />,
    benefits: [
      'Automatic attendance marking',
      'Engagement scoring',
      'Participation tracking',
      'Alert notifications'
    ],
    stats: {
      accuracy: '99.5%',
      timeSaved: '5 min/class',
      adoption: '95%'
    }
  },
  {
    id: '5',
    category: 'collaboration',
    title: 'Virtual Study Groups',
    description: 'Create and join study groups with video conferencing and collaboration tools',
    icon: <Users className="h-8 w-8" />,
    benefits: [
      'HD video conferencing',
      'Screen sharing',
      'Collaborative whiteboard',
      'File sharing'
    ],
    stats: {
      activeGroups: '1000+',
      dailyMeetings: '500+',
      satisfaction: '4.8/5'
    }
  },
  {
    id: '6',
    category: 'collaboration',
    title: 'Smart Messaging System',
    description: 'Integrated messaging with AI-powered assistance and translation',
    icon: <MessageSquare className="h-8 w-8" />,
    benefits: [
      'Real-time messaging',
      'AI chat assistant',
      'Auto-translation',
      'File attachments'
    ],
    stats: {
      messages: '1M+/day',
      responseTime: '<1s',
      languages: '50+'
    }
  },
  {
    id: '7',
    category: 'security',
    title: 'Biometric Authentication',
    description: 'Secure login with fingerprint and facial recognition',
    icon: <Shield className="h-8 w-8" />,
    benefits: [
      'Fingerprint login',
      'Face recognition',
      'Two-factor authentication',
      'Device management'
    ],
    stats: {
      security: '99.99%',
      loginTime: '<2s',
      breaches: '0'
    }
  },
  {
    id: '8',
    category: 'security',
    title: 'Data Encryption & Privacy',
    description: 'End-to-end encryption for all data and communications',
    icon: <Lock className="h-8 w-8" />,
    benefits: [
      '256-bit encryption',
      'GDPR compliant',
      'Regular security audits',
      'Privacy controls'
    ],
    stats: {
      encryption: 'AES-256',
      compliance: '100%',
      uptime: '99.99%'
    }
  },
  {
    id: '9',
    category: 'integration',
    title: 'LMS Integration',
    description: 'Seamless integration with popular Learning Management Systems',
    icon: <Puzzle className="h-8 w-8" />,
    benefits: [
      'Canvas integration',
      'Moodle support',
      'Blackboard sync',
      'Google Classroom'
    ],
    stats: {
      integrations: '20+',
      syncTime: 'Real-time',
      compatibility: '100%'
    }
  },
  {
    id: '10',
    category: 'mobile',
    title: 'Native Mobile Apps',
    description: 'Fully-featured iOS and Android applications',
    icon: <Smartphone className="h-8 w-8" />,
    benefits: [
      'Offline mode',
      'Push notifications',
      'Native performance',
      'Biometric login'
    ],
    stats: {
      downloads: '500K+',
      rating: '4.8★',
      crashRate: '<0.1%'
    }
  }
];

// Comparison data
const competitorComparison = [
  { feature: 'AI-Powered Recommendations', smartCampus: true, competitorA: false, competitorB: true },
  { feature: 'Real-time Analytics', smartCampus: true, competitorA: true, competitorB: false },
  { feature: 'Biometric Authentication', smartCampus: true, competitorA: false, competitorB: false },
  { feature: 'Virtual Study Groups', smartCampus: true, competitorA: true, competitorB: true },
  { feature: 'Mobile Apps', smartCampus: true, competitorA: true, competitorB: true },
  { feature: 'LMS Integration', smartCampus: true, competitorA: false, competitorB: true },
  { feature: 'Offline Mode', smartCampus: true, competitorA: false, competitorB: false },
  { feature: '24/7 Support', smartCampus: true, competitorA: false, competitorB: true },
  { feature: 'Custom Branding', smartCampus: true, competitorA: true, competitorB: false },
  { feature: 'API Access', smartCampus: true, competitorA: false, competitorB: true }
];

// Pricing tiers
const pricingTiers = [
  {
    name: 'Basic',
    price: 'Free',
    period: '',
    description: 'Perfect for individual students',
    features: [
      'Access to basic features',
      '5GB storage',
      'Basic analytics',
      'Email support',
      'Mobile app access'
    ],
    limitations: [
      'Limited AI features',
      'Basic integrations',
      'Standard support'
    ],
    cta: 'Get Started',
    popular: false
  },
  {
    name: 'Pro',
    price: '$9.99',
    period: '/month',
    description: 'Ideal for serious students',
    features: [
      'All Basic features',
      '100GB storage',
      'Advanced analytics',
      'Priority support',
      'AI-powered features',
      'Unlimited study groups',
      'Advanced integrations'
    ],
    limitations: [
      'Standard API limits'
    ],
    cta: 'Start Free Trial',
    popular: true
  },
  {
    name: 'Institution',
    price: 'Custom',
    period: '',
    description: 'For educational institutions',
    features: [
      'All Pro features',
      'Unlimited storage',
      'Custom branding',
      'Dedicated support',
      'API access',
      'Custom integrations',
      'Advanced security',
      'Admin dashboard',
      'Bulk user management'
    ],
    limitations: [],
    cta: 'Contact Sales',
    popular: false
  }
];

const Features: React.FC = () => {
  const navigate = useNavigate();
  const { trackEvent } = useAnalytics();
  const { scrollY } = useScroll();
  
  // State
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedFeature, setSelectedFeature] = useState<any>(null);
  const [showDemo, setShowDemo] = useState(false);
  const [showComparison, setShowComparison] = useState(false);
  const [showPricing, setShowPricing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [expandedFeatures, setExpandedFeatures] = useState<string[]>([]);
  
  // Parallax effects
  const heroY = useTransform(scrollY, [0, 500], [0, 150]);
  const heroOpacity = useTransform(scrollY, [0, 300], [1, 0]);
  
  // Filter features
  const filteredFeatures = featuresData.filter(feature => {
    if (selectedCategory !== 'all' && feature.category !== selectedCategory) {
      return false;
    }
    if (searchQuery && !feature.title.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !feature.description.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    return true;
  });

  // Handlers
  const handleFeatureClick = (feature: any) => {
    setSelectedFeature(feature);
    setShowDemo(true);
    trackEvent('feature_viewed', {
      featureId: feature.id,
      featureTitle: feature.title,
      category: feature.category
    });
  };

  const handleCategoryChange = (category: string) => {
    setSelectedCategory(category);
    trackEvent('feature_category_selected', { category });
  };

  const toggleFeatureExpansion = (featureId: string) => {
    setExpandedFeatures(prev =>
      prev.includes(featureId)
        ? prev.filter(id => id !== featureId)
        : [...prev, featureId]
    );
  };

  const handleRequestDemo = () => {
    trackEvent('demo_requested', { source: 'features_page' });
    navigate('/demo');
  };

  const handleStartTrial = (tier: string) => {
    trackEvent('trial_started', { tier, source: 'features_page' });
    navigate('/register');
  };

  // Render feature card
  const renderFeatureCard = (feature: any) => {
    const isExpanded = expandedFeatures.includes(feature.id);
    
    return (
      <motion.div
        key={feature.id}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={{ y: -5 }}
        className="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-2xl transition-all group"
      >
        {/* Header */}
        <div className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className={`h-14 w-14 bg-gradient-to-r ${
              featureCategories.find(c => c.id === feature.category)?.color
            } rounded-xl flex items-center justify-center text-white shadow-lg`}>
              {feature.icon}
            </div>
            
            <button
              onClick={() => toggleFeatureExpansion(feature.id)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              {isExpanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
            </button>
          </div>

          <h3 className="text-xl font-bold text-gray-900 mb-2">{feature.title}</h3>
          <p className="text-gray-600 mb-4">{feature.description}</p>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-3 mb-4">
            {Object.entries(feature.stats).slice(0, 3).map(([key, value]: [string, any]) => (
              <div key={key} className="text-center">
                <div className="text-lg font-bold text-purple-600">{value}</div>
                <div className="text-xs text-gray-500 capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}</div>
              </div>
            ))}
          </div>

          {/* Benefits (shown when expanded) */}
          <AnimatePresence>
            {isExpanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3 }}
              >
                <div className="pt-4 border-t">
                  <h4 className="font-semibold text-gray-900 mb-3">Key Benefits</h4>
                  <ul className="space-y-2">
                    {feature.benefits.map((benefit: string, index: number) => (
                      <li key={index} className="flex items-start">
                        <CheckCircle className="h-5 w-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                        <span className="text-sm text-gray-600">{benefit}</span>
                      </li>
                    ))}
                  </ul>
                  
                  {feature.testimonial && (
                    <div className="mt-4 p-4 bg-gray-50 rounded-xl">
                      <p className="text-sm text-gray-600 italic mb-2">"{feature.testimonial.text}"</p>
                      <p className="text-xs text-gray-500">
                        — {feature.testimonial.author}, {feature.testimonial.role}
                      </p>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Actions */}
          <div className="flex space-x-3 mt-4">
            <button
              onClick={() => handleFeatureClick(feature)}
              className="flex-1 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg transition-all"
            >
              View Demo
            </button>
            <button
              onClick={() => {
                toast.success(`Learning more about ${feature.title}`);
                trackEvent('feature_learn_more', { featureId: feature.id });
              }}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors"
            >
              Learn More
            </button>
          </div>
        </div>
      </motion.div>
    );
  };

  return (
    <>
      <Helmet>
        <title>Platform Features - Smart Campus</title>
        <meta name="description" content="Explore the powerful features of Smart Campus platform" />
      </Helmet>

      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
        {/* Hero Section */}
        <section className="relative bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white overflow-hidden">
          <motion.div
            style={{ y: heroY, opacity: heroOpacity }}
            className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24"
          >
            <div className="text-center">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 200 }}
                className="inline-flex items-center px-6 py-3 bg-white/20 backdrop-blur-xl rounded-full mb-8"
              >
                <Sparkles className="h-5 w-5 mr-2" />
                <span className="font-semibold">Discover What Makes Us Different</span>
              </motion.div>
              
              <motion.h1
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-5xl lg:text-6xl font-bold mb-6"
              >
                Powerful Features for
                <span className="block mt-2 bg-gradient-to-r from-yellow-300 to-orange-300 bg-clip-text text-transparent">
                  Modern Education
                </span>
              </motion.h1>
              
              <motion.p
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="text-xl text-white/90 mb-8 max-w-3xl mx-auto"
              >
                Experience the future of education with our comprehensive suite of AI-powered tools,
                real-time analytics, and collaboration features designed to enhance learning outcomes.
              </motion.p>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="flex flex-col sm:flex-row gap-4 justify-center"
              >
                <CTALink
                  to="/demo"
                  variant="secondary"
                  size="lg"
                  icon={<Play className="h-5 w-5" />}
                  analyticsEvent="features_hero_demo"
                >
                  Watch Demo
                </CTALink>
                <CTALink
                  to="/register"
                  variant="primary"
                  size="lg"
                  className="!bg-white !text-purple-600 hover:!bg-gray-100"
                  analyticsEvent="features_hero_trial"
                >
                  Start Free Trial
                </CTALink>
              </motion.div>

              {/* Feature highlights */}
              <motion.div
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
                className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-16"
              >
                {[
                  { icon: <Zap />, label: 'Lightning Fast', value: '<100ms' },
                  { icon: <Shield />, label: 'Secure', value: '99.99%' },
                  { icon: <Users />, label: 'Active Users', value: '50K+' },
                  { icon: <Trophy />, label: 'Satisfaction', value: '4.9/5' }
                ].map((stat, index) => (
                  <div key={index} className="bg-white/10 backdrop-blur-xl rounded-xl p-4">
                    <div className="flex items-center justify-center mb-2 text-white/80">
                      {React.cloneElement(stat.icon, { className: 'h-6 w-6' })}
                    </div>
                    <div className="text-2xl font-bold">{stat.value}</div>
                    <div className="text-sm text-white/80">{stat.label}</div>
                  </div>
                ))}
              </motion.div>
            </div>
          </motion.div>

          {/* Animated background elements */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
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
              className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-r from-purple-400 to-pink-400 opacity-20 rounded-full"
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
              className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-gradient-to-r from-blue-400 to-cyan-400 opacity-20 rounded-full"
            />
          </div>
        </section>

        {/* Category Navigation */}
        <section className="sticky top-0 z-30 bg-white border-b shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between py-4">
              <div className="flex items-center space-x-2 overflow-x-auto">
                <button
                  onClick={() => handleCategoryChange('all')}
                  className={`px-4 py-2 rounded-full font-medium whitespace-nowrap transition-all ${
                    selectedCategory === 'all'
                      ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  All Features
                </button>
                {featureCategories.map((category) => (
                  <button
                    key={category.id}
                    onClick={() => handleCategoryChange(category.id)}
                    className={`px-4 py-2 rounded-full font-medium whitespace-nowrap transition-all flex items-center space-x-2 ${
                      selectedCategory === category.id
                        ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {React.cloneElement(category.icon, { className: 'h-4 w-4' })}
                    <span>{category.name}</span>
                  </button>
                ))}
              </div>

              <div className="flex items-center space-x-3">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search features..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                
                <button
                  onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  {viewMode === 'grid' ? <List className="h-5 w-5" /> : <Grid className="h-5 w-5" />}
                </button>
                
                <button
                  onClick={() => setShowComparison(true)}
                  className="px-4 py-2 bg-purple-100 text-purple-700 rounded-lg font-medium hover:bg-purple-200 transition-colors"
                >
                  Compare
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Features Grid/List */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {viewMode === 'grid' ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredFeatures.map((feature, index) => (
                <motion.div
                  key={feature.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  {renderFeatureCard(feature)}
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="space-y-6">
              {filteredFeatures.map((feature, index) => (
                <motion.div
                  key={feature.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-white rounded-2xl shadow-lg p-6 hover:shadow-xl transition-all"
                >
                  <div className="flex items-start space-x-6">
                    <div className={`h-16 w-16 bg-gradient-to-r ${
                      featureCategories.find(c => c.id === feature.category)?.color
                    } rounded-xl flex items-center justify-center text-white shadow-lg flex-shrink-0`}>
                      {feature.icon}
                    </div>
                    
                    <div className="flex-1">
                      <h3 className="text-2xl font-bold text-gray-900 mb-2">{feature.title}</h3>
                      <p className="text-gray-600 mb-4">{feature.description}</p>
                      
                      <div className="flex flex-wrap gap-4 mb-4">
                        {Object.entries(feature.stats).map(([key, value]: [string, any]) => (
                          <div key={key}>
                            <span className="text-2xl font-bold text-purple-600">{value}</span>
                            <span className="ml-2 text-sm text-gray-500 capitalize">
                              {key.replace(/([A-Z])/g, ' $1').trim()}
                            </span>
                          </div>
                        ))}
                      </div>
                      
                      <div className="grid md:grid-cols-2 gap-4 mb-4">
                        {feature.benefits.map((benefit: string, index: number) => (
                          <div key={index} className="flex items-start">
                            <CheckCircle className="h-5 w-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                            <span className="text-sm text-gray-600">{benefit}</span>
                          </div>
                        ))}
                      </div>
                      
                      <div className="flex space-x-3">
                        <button
                          onClick={() => handleFeatureClick(feature)}
                          className="px-6 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg transition-all"
                        >
                          View Demo
                        </button>
                        <button
                          className="px-6 py-2 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors"
                        >
                          Learn More
                        </button>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}

          {filteredFeatures.length === 0 && (
            <div className="text-center py-12">
              <SearchIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-700 mb-2">No features found</h3>
              <p className="text-gray-500">Try adjusting your search or filters</p>
            </div>
          )}
        </section>

        {/* Comparison Table */}
        {showComparison && (
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12"
          >
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-3xl font-bold text-gray-900">Feature Comparison</h2>
                <button
                  onClick={() => setShowComparison(false)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="h-6 w-6 text-gray-500" />
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr>
                      <th className="text-left py-4 px-6 font-semibold text-gray-900">Features</th>
                      <th className="text-center py-4 px-6">
                        <div className="font-semibold text-purple-600">Smart Campus</div>
                        <div className="text-sm text-gray-500">Our Platform</div>
                      </th>
                      <th className="text-center py-4 px-6">
                        <div className="font-semibold text-gray-700">Competitor A</div>
                        <div className="text-sm text-gray-500">Traditional LMS</div>
                      </th>
                      <th className="text-center py-4 px-6">
                        <div className="font-semibold text-gray-700">Competitor B</div>
                        <div className="text-sm text-gray-500">Basic Platform</div>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {competitorComparison.map((row, index) => (
                      <tr key={index} className={index % 2 === 0 ? 'bg-gray-50' : ''}>
                        <td className="py-4 px-6 font-medium text-gray-700">{row.feature}</td>
                        <td className="text-center py-4 px-6">
                          {row.smartCampus ? (
                            <CheckCircle className="h-6 w-6 text-green-500 mx-auto" />
                          ) : (
                            <XCircle className="h-6 w-6 text-gray-300 mx-auto" />
                          )}
                        </td>
                        <td className="text-center py-4 px-6">
                          {row.competitorA ? (
                            <CheckCircle className="h-6 w-6 text-green-500 mx-auto" />
                          ) : (
                            <XCircle className="h-6 w-6 text-gray-300 mx-auto" />
                          )}
                        </td>
                        <td className="text-center py-4 px-6">
                          {row.competitorB ? (
                            <CheckCircle className="h-6 w-6 text-green-500 mx-auto" />
                          ) : (
                            <XCircle className="h-6 w-6 text-gray-300 mx-auto" />
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-8 text-center">
                <CTALink
                  to="/demo"
                  variant="primary"
                  size="lg"
                  showArrow
                  analyticsEvent="comparison_demo_cta"
                >
                  See the Difference in Action
                </CTALink>
              </div>
            </div>
          </motion.section>
        )}

        {/* Pricing Section */}
        <section className="bg-gradient-to-b from-gray-50 to-white py-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
              <h2 className="text-4xl font-bold text-gray-900 mb-4">
                Choose Your Plan
              </h2>
              <p className="text-xl text-gray-600">
                Start free and scale as you grow
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              {pricingTiers.map((tier, index) => (
                <motion.div
                  key={tier.name}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={`relative bg-white rounded-2xl shadow-lg p-8 ${
                    tier.popular ? 'ring-2 ring-purple-600' : ''
                  }`}
                >
                  {tier.popular && (
                    <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                      <span className="px-4 py-1 bg-gradient-to-r from-purple-600 to-pink-600 text-white text-sm font-bold rounded-full">
                        MOST POPULAR
                      </span>
                    </div>
                  )}

                  <div className="text-center mb-6">
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">{tier.name}</h3>
                    <p className="text-gray-600 mb-4">{tier.description}</p>
                    <div className="text-5xl font-bold text-gray-900">
                      {tier.price}
                      <span className="text-lg text-gray-500">{tier.period}</span>
                    </div>
                  </div>

                  <ul className="space-y-3 mb-8">
                    {tier.features.map((feature, i) => (
                      <li key={i} className="flex items-start">
                        <CheckCircle className="h-5 w-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
                        <span className="text-gray-700">{feature}</span>
                      </li>
                    ))}
                    {tier.limitations.map((limitation, i) => (
                      <li key={i} className="flex items-start">
                        <XCircle className="h-5 w-5 text-gray-400 mr-3 flex-shrink-0 mt-0.5" />
                        <span className="text-gray-500">{limitation}</span>
                      </li>
                    ))}
                  </ul>

                  <button
                    onClick={() => handleStartTrial(tier.name)}
                    className={`w-full py-3 rounded-xl font-semibold transition-all ${
                      tier.popular
                        ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:shadow-lg'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {tier.cta}
                  </button>
                </motion.div>
              ))}
            </div>

            <div className="mt-12 text-center">
              <p className="text-gray-600 mb-4">
                All plans include a 14-day free trial. No credit card required.
              </p>
              <div className="flex items-center justify-center space-x-8 text-sm text-gray-500">
                <span className="flex items-center">
                  <Shield className="h-4 w-4 mr-2" />
                  SSL Secured
                </span>
                <span className="flex items-center">
                  <Lock className="h-4 w-4 mr-2" />
                  GDPR Compliant
                </span>
                <span className="flex items-center">
                  <CheckCircle className="h-4 w-4 mr-2" />
                  99.9% Uptime SLA
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white py-20">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h2 className="text-4xl font-bold mb-4">
              Ready to Transform Your Institution?
            </h2>
            <p className="text-xl mb-8 text-white/90">
              Join thousands of institutions already using Smart Campus
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <CTALink
                to="/demo"
                variant="secondary"
                size="lg"
                icon={<Play className="h-5 w-5" />}
                className="!bg-white !text-purple-600 hover:!bg-gray-100"
              >
                Schedule Demo
              </CTALink>
              <CTALink
                to="/contact"
                variant="outline"
                size="lg"
                className="!text-white !border-white hover:!bg-white hover:!text-purple-600"
              >
                Contact Sales
              </CTALink>
            </div>
          </div>
        </section>
      </div>
    </>
  );
};

export default Features;