// src/pages/Resources.tsx
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import {
  BookOpen,
  Video,
  FileText,
  Headphones,
  Download,
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize,
  Minimize,
  Search,
  Filter,
  Grid,
  List,
  Clock,
  Calendar,
  User,
  Star,
  Heart,
  Share2,
  Bookmark,
  Eye,
  TrendingUp,
  Award,
  CheckCircle,
  Lock,
  Unlock,
  AlertCircle,
  Info,
  HelpCircle,
  ChevronRight,
  ChevronLeft,
  ChevronDown,
  ChevronUp,
  ArrowRight,
  ArrowLeft,
  ArrowUp,
  ArrowDown,
  Plus,
  Minus,
  X,
  Menu,
  MoreVertical,
  MoreHorizontal,
  ExternalLink,
  Link,
  Copy,
  Clipboard,
  Save,
  Edit,
  Trash2,
  RefreshCw,
  RotateCw,
  Loader,
  Zap,
  Sparkles,
  Trophy,
  Target,
  Flag,
  Rocket,
  Lightbulb,
  Brain,
  Cpu,
  Database,
  Code,
  Terminal,
  GitBranch,
  Package,
  Layers,
  Layout,
  PenTool,
  Palette,
  Brush,
  Camera,
  Image,
  Film,
  Music,
  Mic,
  Speaker,
  Wifi,
  Cloud,
  Server,
  HardDrive,
  Monitor,
  Smartphone,
  Tablet,
  Laptop,
  Watch,
  Printer,
  //Scanner,
  Keyboard,
  Mouse,
  Gamepad,
  Battery,
  BatteryCharging,
  Power,
  Plug,
  Flashlight,
  Sun,
  Moon,
  CloudRain,
  Wind,
  Droplet,
  Flame,
  Snowflake,
  Thermometer,
  Compass,
  Map,
  Navigation,
  MapPin,
  Globe,
  Home,
  Building,
  Store,
  ShoppingCart,
  ShoppingBag,
  Gift,
  CreditCard,
  Wallet,
  DollarSign,
  Percent,
  Calculator,
  BarChart3,
  PieChart,
  TrendingDown,
  Activity,
 // Pulse,
  //Heartbeat,
  Shield,
  ShieldCheck,
  ShieldAlert,
  Bell,
  BellOff,
  BellRing,
  Inbox,
  Send,
  Mail,
  MessageSquare,
  MessageCircle,
  MessagesSquare,
  Phone,
  PhoneCall,
  PhoneIncoming,
  PhoneOutgoing,
  PhoneMissed,
  PhoneOff,
  Voicemail,
  VideoIcon,
  VideoOff,
  Airplay,
  Cast,
  Tv,
  Radio,
  Podcast,
  Rss,
  WifiOff,
  Signal,
  Bluetooth,
  Usb,
  Disc,
  Archive,
  Box,
  Package2,
  Folder,
  FolderOpen,
  FolderPlus,
  FolderMinus,
  FolderCheck,
  FolderX,
  File,
  FilePlus,
  FileMinus,
  FileCheck,
  FileX,
  FileSearch,
  FileCode,
  FileImage,
  FileVideo,
  FileAudio,
  FileArchive,
  FileSpreadsheet,
  FileJson,
  FileKey,
  FileLock,
  FileOutput,
  FileInput,
  Paperclip,
  Link2,
  Unlink,
  Anchor,
  Hash,
  AtSign,
  Tag,
  Tags,
  Badge,
  Medal,
  Crown,
  Gem,
  Diamond,
  Coins,
  Banknote,
  Receipt,
  Ticket,
 //Label,
  Stamp,
  Users,
  Route,

  Bookmark as BookmarkIcon
} from 'lucide-react';
import CTALink from '../components/common/CTALink';
import { useAuth } from '../hooks/useAuth';
import { useAnalytics } from '../hooks/useAnalytics';
import toast from 'react-hot-toast';

// Types
interface Resource {
  id: string;
  title: string;
  description: string;
  type: 'video' | 'document' | 'tutorial' | 'template' | 'tool' | 'guide' | 'course' | 'webinar';
  category: string;
  subcategory: string;
  format: string;
  duration?: string;
  size?: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  author: {
    name: string;
    avatar: string;
    role: string;
  };
  thumbnail: string;
  url: string;
  downloadUrl?: string;
  tags: string[];
  rating: number;
  reviews: number;
  views: number;
  downloads: number;
  bookmarks: number;
  publishedDate: Date;
  lastUpdated: Date;
  isPremium: boolean;
  isNew: boolean;
  isTrending: boolean;
  isFeatured: boolean;
  prerequisites: string[];
  learningOutcomes: string[];
  relatedResources: string[];
  attachments: {
    name: string;
    url: string;
    size: string;
  }[];
  progress?: number;
  completed?: boolean;
  bookmarked?: boolean;
  certificate?: boolean;
}

interface LearningPath {
  id: string;
  title: string;
  description: string;
  category: string;
  thumbnail: string;
  duration: string;
  difficulty: string;
  modules: {
    id: string;
    title: string;
    description: string;
    resources: string[];
    duration: string;
    completed: boolean;
  }[];
  enrolledCount: number;
  rating: number;
  instructor: {
    name: string;
    avatar: string;
    bio: string;
  };
  skills: string[];
  certificate: boolean;
  price: number;
  progress: number;
  enrolled: boolean;
}

interface Workshop {
  id: string;
  title: string;
  description: string;
  instructor: string;
  date: Date;
  time: string;
  duration: string;
  venue: string;
  mode: 'online' | 'offline' | 'hybrid';
  capacity: number;
  enrolled: number;
  thumbnail: string;
  topics: string[];
  prerequisites: string[];
  materials: string[];
  recording: boolean;
  certificate: boolean;
  fee: number;
  registered: boolean;
}

// Mock data
const resourcesData: Resource[] = [
  {
    id: '1',
    title: 'Complete Web Development Course',
    description: 'Learn full-stack web development from scratch with hands-on projects',
    type: 'course',
    category: 'Programming',
    subcategory: 'Web Development',
    format: 'Video Course',
    duration: '40 hours',
    difficulty: 'beginner',
    author: {
      name: 'John Doe',
      avatar: 'https://ui-avatars.com/api/?name=John+Doe&background=6366f1&color=fff',
      role: 'Senior Developer'
    },
    thumbnail: 'https://images.unsplash.com/photo-1517180102446-f3ece451e9d8?w=400',
    url: '/resources/web-dev-course',
    downloadUrl: '/downloads/web-dev-course.zip',
    tags: ['HTML', 'CSS', 'JavaScript', 'React', 'Node.js'],
    rating: 4.8,
    reviews: 342,
    views: 15234,
    downloads: 8934,
    bookmarks: 1234,
    publishedDate: new Date('2023-09-15'),
    lastUpdated: new Date('2024-01-10'),
    isPremium: false,
    isNew: false,
    isTrending: true,
    isFeatured: true,
    prerequisites: ['Basic computer skills', 'Internet connection'],
    learningOutcomes: [
      'Build responsive websites',
      'Create dynamic web applications',
      'Deploy projects to production',
      'Work with databases'
    ],
    relatedResources: ['2', '3', '4'],
    attachments: [
      { name: 'Course Outline.pdf', url: '/files/outline.pdf', size: '2.3 MB' },
      { name: 'Project Files.zip', url: '/files/projects.zip', size: '45 MB' }
    ],
    progress: 65,
    completed: false,
    bookmarked: true,
    certificate: true
  },
  {
    id: '2',
    title: 'Data Science Fundamentals',
    description: 'Master the basics of data science and machine learning',
    type: 'tutorial',
    category: 'Data Science',
    subcategory: 'Machine Learning',
    format: 'Interactive Tutorial',
    duration: '20 hours',
    difficulty: 'intermediate',
    author: {
      name: 'Sarah Johnson',
      avatar: 'https://ui-avatars.com/api/?name=Sarah+Johnson&background=6366f1&color=fff',
      role: 'Data Scientist'
    },
    thumbnail: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400',
    url: '/resources/data-science',
    tags: ['Python', 'Statistics', 'ML', 'Data Analysis'],
    rating: 4.9,
    reviews: 567,
    views: 23456,
    downloads: 12345,
    bookmarks: 2345,
    publishedDate: new Date('2023-11-20'),
    lastUpdated: new Date('2024-01-15'),
    isPremium: true,
    isNew: true,
    isTrending: true,
    isFeatured: false,
    prerequisites: ['Python basics', 'Mathematics'],
    learningOutcomes: [
      'Understand ML algorithms',
      'Perform data analysis',
      'Build predictive models'
    ],
    relatedResources: ['1', '3'],
    attachments: [],
    progress: 30,
    completed: false,
    bookmarked: false,
    certificate: true
  }
];

const learningPathsData: LearningPath[] = [
  {
    id: '1',
    title: 'Full-Stack Developer Path',
    description: 'Become a full-stack developer with comprehensive training',
    category: 'Programming',
    thumbnail: 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=400',
    duration: '6 months',
    difficulty: 'Intermediate',
    modules: [
      {
        id: 'm1',
        title: 'Frontend Fundamentals',
        description: 'HTML, CSS, JavaScript basics',
        resources: ['1', '2'],
        duration: '4 weeks',
        completed: true
      },
      {
        id: 'm2',
        title: 'React Development',
        description: 'Build modern React applications',
        resources: ['3', '4'],
        duration: '6 weeks',
        completed: false
      }
    ],
    enrolledCount: 1234,
    rating: 4.7,
    instructor: {
      name: 'Michael Chen',
      avatar: 'https://ui-avatars.com/api/?name=Michael+Chen&background=6366f1&color=fff',
      bio: '10+ years of development experience'
    },
    skills: ['HTML/CSS', 'JavaScript', 'React', 'Node.js', 'MongoDB'],
    certificate: true,
    price: 0,
    progress: 35,
    enrolled: true
  }
];

const workshopsData: Workshop[] = [
  {
    id: '1',
    title: 'AI & Machine Learning Workshop',
    description: 'Hands-on workshop on implementing ML algorithms',
    instructor: 'Dr. Robert Williams',
    date: new Date('2024-02-15'),
    time: '10:00 AM - 5:00 PM',
    duration: '7 hours',
    venue: 'Tech Lab, Building A',
    mode: 'hybrid',
    capacity: 50,
    enrolled: 42,
    thumbnail: 'https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=400',
    topics: ['Neural Networks', 'Deep Learning', 'Computer Vision'],
    prerequisites: ['Python knowledge', 'Basic ML concepts'],
    materials: ['Laptop required', 'Python installed'],
    recording: true,
    certificate: true,
    fee: 500,
    registered: false
  }
];

const Resources: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useAuth();
  const { trackEvent } = useAnalytics();

  // State
  const [resources, setResources] = useState(resourcesData);
  const [learningPaths, setLearningPaths] = useState(learningPathsData);
  const [workshops, setWorkshops] = useState(workshopsData);
  const [selectedTab, setSelectedTab] = useState('resources');
  const [selectedResource, setSelectedResource] = useState<Resource | null>(null);
  const [showResourceModal, setShowResourceModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState(searchParams.get('q') || '');
  const [filters, setFilters] = useState({
    category: 'all',
    type: 'all',
    difficulty: 'all',
    format: 'all',
    isPremium: false
  });
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [sortBy, setSortBy] = useState('relevance');
  const [bookmarkedResources, setBookmarkedResources] = useState<string[]>([]);
  const [downloadHistory, setDownloadHistory] = useState<string[]>([]);
  const [enrolledPaths, setEnrolledPaths] = useState<string[]>(['1']);
  const [registeredWorkshops, setRegisteredWorkshops] = useState<string[]>([]);
  const [showFilters, setShowFilters] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 12;

  // Categories
  const categories = [
    { id: 'all', name: 'All Resources', icon: <Grid />, count: 234 },
    { id: 'programming', name: 'Programming', icon: <Code />, count: 89 },
    { id: 'data-science', name: 'Data Science', icon: <Database />, count: 56 },
    { id: 'design', name: 'Design', icon: <Palette />, count: 34 },
    { id: 'business', name: 'Business', icon: <TrendingUp />, count: 45 },
    { id: 'marketing', name: 'Marketing', icon: <Target />, count: 23 },
    { id: 'languages', name: 'Languages', icon: <Globe />, count: 12 }
  ];

  // Load saved data
  useEffect(() => {
    const savedBookmarks = localStorage.getItem('bookmarkedResources');
    if (savedBookmarks) {
      setBookmarkedResources(JSON.parse(savedBookmarks));
    }

    const savedHistory = localStorage.getItem('downloadHistory');
    if (savedHistory) {
      setDownloadHistory(JSON.parse(savedHistory));
    }
  }, []);

  // Filter resources
  const filteredResources = resources.filter(resource => {
    if (searchQuery && !resource.title.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !resource.description.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !resource.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))) {
      return false;
    }

    if (filters.category !== 'all' && resource.category.toLowerCase() !== filters.category) {
      return false;
    }

    if (filters.type !== 'all' && resource.type !== filters.type) {
      return false;
    }

    if (filters.difficulty !== 'all' && resource.difficulty !== filters.difficulty) {
      return false;
    }

    if (filters.isPremium && !resource.isPremium) {
      return false;
    }

    return true;
  });

  // Sort resources
  const sortedResources = [...filteredResources].sort((a, b) => {
    switch (sortBy) {
      case 'newest':
        return b.publishedDate.getTime() - a.publishedDate.getTime();
      case 'popular':
        return b.views - a.views;
      case 'rating':
        return b.rating - a.rating;
      case 'trending':
        return (b.isTrending ? 1 : 0) - (a.isTrending ? 1 : 0);
      default:
        return 0;
    }
  });

  // Paginate
  const paginatedResources = sortedResources.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );
  const totalPages = Math.ceil(sortedResources.length / itemsPerPage);

  // Handlers
  const handleResourceClick = (resource: Resource) => {
    setSelectedResource(resource);
    setShowResourceModal(true);
    trackEvent('resource_viewed', {
      resourceId: resource.id,
      resourceTitle: resource.title,
      resourceType: resource.type
    });
  };

  const handleDownload = async (resource: Resource) => {
    if (resource.isPremium && user?.role !== 'admin') { 
      toast.error('Premium subscription required');
      navigate('/pricing');
      return;
    }

    try {
      const updatedHistory = [...downloadHistory, resource.id];
      setDownloadHistory(updatedHistory);
      localStorage.setItem('downloadHistory', JSON.stringify(updatedHistory));
      
      trackEvent('resource_downloaded', {
        resourceId: resource.id,
        resourceTitle: resource.title
      });
      
      toast.success(`Downloaded: ${resource.title}`);
      
      // Simulate download
      if (resource.downloadUrl) {
        window.open(resource.downloadUrl, '_blank');
      }
    } catch (error) {
      toast.error('Download failed');
    }
  };

  const toggleBookmark = (resourceId: string) => {
    const updated = bookmarkedResources.includes(resourceId)
      ? bookmarkedResources.filter(id => id !== resourceId)
      : [...bookmarkedResources, resourceId];
    
    setBookmarkedResources(updated);
    localStorage.setItem('bookmarkedResources', JSON.stringify(updated));
    
    toast.success(
      bookmarkedResources.includes(resourceId)
        ? 'Removed from bookmarks'
        : 'Added to bookmarks'
    );
    
    trackEvent('resource_bookmarked', {
      resourceId,
      action: bookmarkedResources.includes(resourceId) ? 'remove' : 'add'
    });
  };

  const handleEnrollPath = (pathId: string) => {
    const updated = enrolledPaths.includes(pathId)
      ? enrolledPaths.filter(id => id !== pathId)
      : [...enrolledPaths, pathId];
    
    setEnrolledPaths(updated);
    
    toast.success(
      enrolledPaths.includes(pathId)
        ? 'Unenrolled from learning path'
        : 'Enrolled in learning path'
    );
    
    trackEvent('learning_path_enrolled', {
      pathId,
      action: enrolledPaths.includes(pathId) ? 'unenroll' : 'enroll'
    });
  };

  const handleRegisterWorkshop = (workshopId: string) => {
    const workshop = workshops.find(w => w.id === workshopId);
    if (!workshop) return;

    if (workshop.enrolled >= workshop.capacity) {
      toast.error('Workshop is full');
      return;
    }

    const updated = registeredWorkshops.includes(workshopId)
      ? registeredWorkshops.filter(id => id !== workshopId)
      : [...registeredWorkshops, workshopId];
    
    setRegisteredWorkshops(updated);
    
    toast.success(
      registeredWorkshops.includes(workshopId)
        ? 'Unregistered from workshop'
        : 'Registered for workshop'
    );
    
    trackEvent('workshop_registered', {
      workshopId,
      action: registeredWorkshops.includes(workshopId) ? 'unregister' : 'register'
    });
  };

  // Render resource card
  const renderResourceCard = (resource: Resource) => (
    <motion.div
      key={resource.id}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -5 }}
      className="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-2xl transition-all group cursor-pointer"
      onClick={() => handleResourceClick(resource)}
    >
      {/* Thumbnail */}
      <div className="relative h-48 overflow-hidden bg-gradient-to-br from-gray-100 to-gray-200">
        <img
          src={resource.thumbnail}
          alt={resource.title}
          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
        />
        
        {/* Badges */}
        <div className="absolute top-3 left-3 flex flex-wrap gap-2">
          {resource.isNew && (
            <span className="px-2 py-1 bg-green-500 text-white text-xs font-bold rounded-full">
              NEW
            </span>
          )}
          {resource.isTrending && (
            <span className="px-2 py-1 bg-orange-500 text-white text-xs font-bold rounded-full flex items-center">
              <TrendingUp className="h-3 w-3 mr-1" />
              TRENDING
            </span>
          )}
          {resource.isPremium && (
            <span className="px-2 py-1 bg-purple-600 text-white text-xs font-bold rounded-full flex items-center">
              <Crown className="h-3 w-3 mr-1" />
              PREMIUM
            </span>
          )}
        </div>

        {/* Type Icon */}
        <div className="absolute bottom-3 right-3 h-10 w-10 bg-white/90 backdrop-blur-sm rounded-xl flex items-center justify-center">
          {resource.type === 'video' && <Video className="h-5 w-5 text-gray-700" />}
          {resource.type === 'document' && <FileText className="h-5 w-5 text-gray-700" />}
          {resource.type === 'course' && <BookOpen className="h-5 w-5 text-gray-700" />}
          {resource.type === 'tutorial' && <Lightbulb className="h-5 w-5 text-gray-700" />}
        </div>

        {/* Progress Bar */}
        {resource.progress !== undefined && (
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200">
            <div
              className="h-full bg-gradient-to-r from-green-500 to-emerald-500"
              style={{ width: `${resource.progress}%` }}
            />
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-5">
        <div className="flex items-start justify-between mb-2">
          <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs font-medium rounded-full">
            {resource.category}
          </span>
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
            resource.difficulty === 'beginner' ? 'bg-green-100 text-green-700' :
            resource.difficulty === 'intermediate' ? 'bg-yellow-100 text-yellow-700' :
            resource.difficulty === 'advanced' ? 'bg-orange-100 text-orange-700' :
            'bg-red-100 text-red-700'
          }`}>
            {resource.difficulty.charAt(0).toUpperCase() + resource.difficulty.slice(1)}
          </span>
        </div>

        <h3 className="font-bold text-gray-900 mb-2 line-clamp-2 group-hover:text-purple-600 transition-colors">
          {resource.title}
        </h3>
        
        <p className="text-sm text-gray-600 mb-3 line-clamp-2">
          {resource.description}
        </p>

        {/* Author */}
        <div className="flex items-center mb-3">
          <img
            src={resource.author.avatar}
            alt={resource.author.name}
            className="h-6 w-6 rounded-full mr-2"
          />
          <span className="text-sm text-gray-600">{resource.author.name}</span>
        </div>

        {/* Stats */}
        <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
          <span className="flex items-center">
            <Clock className="h-3 w-3 mr-1" />
            {resource.duration || resource.size}
          </span>
          <span className="flex items-center">
            <Eye className="h-3 w-3 mr-1" />
            {resource.views.toLocaleString()}
          </span>
          <span className="flex items-center">
            <Star className="h-3 w-3 mr-1 text-yellow-500" />
            {resource.rating}
          </span>
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-1 mb-4">
          {resource.tags.slice(0, 3).map((tag, index) => (
            <span
              key={index}
              className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full"
            >
              {tag}
            </span>
          ))}
          {resource.tags.length > 3 && (
            <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
              +{resource.tags.length - 3}
            </span>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between">
          <div className="flex space-x-2">
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleBookmark(resource.id);
              }}
              className={`p-2 rounded-lg transition-colors ${
                bookmarkedResources.includes(resource.id)
                  ? 'bg-purple-100 text-purple-600'
                  : 'hover:bg-gray-100 text-gray-600'
              }`}
            >
              <BookmarkIcon className={`h-4 w-4 ${
                bookmarkedResources.includes(resource.id) ? 'fill-current' : ''
              }`} />
            </button>
            
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleDownload(resource);
              }}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-600"
            >
              <Download className="h-4 w-4" />
            </button>
            
            <button
              onClick={(e) => {
                e.stopPropagation();
                // Share logic
              }}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-600"
            >
              <Share2 className="h-4 w-4" />
            </button>
          </div>
          
          <CTALink
            to={resource.url}
            variant="primary"
            size="sm"
            onClick={() => {}}
          >
            {resource.type === 'video' ? 'Watch' :
             resource.type === 'course' ? 'Enroll' :
             'View'}
          </CTALink>
        </div>
      </div>
    </motion.div>
  );

  return (
    <>
      <Helmet>
        <title>Learning Resources - Smart Campus</title>
        <meta name="description" content="Access comprehensive learning resources, tutorials, and tools" />
      </Helmet>

      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
        {/* Header */}
        <section className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center"
            >
              <h1 className="text-4xl lg:text-5xl font-bold mb-4">Learning Resources</h1>
              <p className="text-xl text-white/90 max-w-3xl mx-auto">
                Explore our comprehensive collection of learning materials, tutorials, and tools to enhance your skills
              </p>
              
              {/* Search Bar */}
              <div className="max-w-2xl mx-auto mt-8">
                <div className="relative">
                  <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search resources, courses, tutorials..."
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      setSearchParams({ q: e.target.value });
                    }}
                    className="w-full pl-12 pr-4 py-4 bg-white text-gray-900 rounded-2xl focus:outline-none focus:ring-4 focus:ring-white/30"
                  />
                </div>
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
                {[
                  { icon: <BookOpen />, value: '500+', label: 'Resources' },
                  { icon: <Video />, value: '200+', label: 'Video Tutorials' },
                  { icon: <Users />, value: '10K+', label: 'Active Learners' },
                  { icon: <Award />, value: '50+', label: 'Certificates' }
                ].map((stat, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="bg-white/10 backdrop-blur-sm rounded-xl p-4"
                  >
                    {React.cloneElement(stat.icon, { className: 'h-6 w-6 mx-auto mb-2 text-white/80' })}
                    <div className="text-2xl font-bold">{stat.value}</div>
                    <div className="text-sm text-white/80">{stat.label}</div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </div>
        </section>

        {/* Navigation Tabs */}
        <div className="bg-white border-b sticky top-0 z-30">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between">
              <nav className="flex space-x-1">
                {[
                  { id: 'resources', label: 'All Resources', icon: <Grid /> },
                  { id: 'paths', label: 'Learning Paths', icon: <Route /> },
                  { id: 'workshops', label: 'Workshops', icon: <Calendar /> },
                  { id: 'bookmarks', label: 'My Bookmarks', icon: <BookmarkIcon /> },
                  { id: 'history', label: 'History', icon: <Clock /> }
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setSelectedTab(tab.id)}
                    className={`flex items-center space-x-2 px-4 py-3 font-medium transition-all border-b-2 ${
                      selectedTab === tab.id
                        ? 'text-purple-600 border-purple-600'
                        : 'text-gray-600 border-transparent hover:text-gray-900'
                    }`}
                  >
                    {React.cloneElement(tab.icon, { className: 'h-4 w-4' })}
                    <span>{tab.label}</span>
                  </button>
                ))}
              </nav>

              <div className="flex items-center space-x-3">
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className="flex items-center space-x-2 px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  <Filter className="h-4 w-4" />
                  <span>Filters</span>
                </button>
                
                <button
                  onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  {viewMode === 'grid' ? <List className="h-5 w-5" /> : <Grid className="h-5 w-5" />}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex gap-8">
            {/* Sidebar */}
            <aside className={`w-64 flex-shrink-0 ${showFilters ? 'block' : 'hidden lg:block'}`}>
              <div className="bg-white rounded-2xl p-6 shadow-lg sticky top-24">
                <h3 className="font-bold text-gray-900 mb-4">Categories</h3>
                
                <div className="space-y-2 mb-6">
                  {categories.map((category) => (
                    <button
                      key={category.id}
                      onClick={() => setFilters({ ...filters, category: category.id })}
                      className={`w-full flex items-center justify-between px-3 py-2 rounded-lg transition-all ${
                        filters.category === category.id
                          ? 'bg-purple-100 text-purple-700'
                          : 'hover:bg-gray-100 text-gray-700'
                      }`}
                    >
                      <span className="flex items-center">
                        {React.cloneElement(category.icon, { className: 'h-4 w-4 mr-2' })}
                        {category.name}
                      </span>
                      <span className="text-sm">{category.count}</span>
                    </button>
                  ))}
                </div>

                <h3 className="font-bold text-gray-900 mb-4">Filters</h3>
                
                {/* Type Filter */}
                <div className="mb-4">
                  <label className="text-sm font-medium text-gray-700 mb-2 block">Type</label>
                  <select
                    value={filters.type}
                    onChange={(e) => setFilters({ ...filters, type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="all">All Types</option>
                    <option value="video">Videos</option>
                    <option value="document">Documents</option>
                    <option value="course">Courses</option>
                    <option value="tutorial">Tutorials</option>
                  </select>
                </div>

                {/* Difficulty Filter */}
                <div className="mb-4">
                  <label className="text-sm font-medium text-gray-700 mb-2 block">Difficulty</label>
                  <select
                    value={filters.difficulty}
                    onChange={(e) => setFilters({ ...filters, difficulty: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="all">All Levels</option>
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced</option>
                    <option value="expert">Expert</option>
                  </select>
                </div>

                {/* Sort By */}
                <div className="mb-4">
                  <label className="text-sm font-medium text-gray-700 mb-2 block">Sort By</label>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="relevance">Relevance</option>
                    <option value="newest">Newest First</option>
                    <option value="popular">Most Popular</option>
                    <option value="rating">Highest Rated</option>
                    <option value="trending">Trending</option>
                  </select>
                </div>

                {/* Premium Filter */}
                <label className="flex items-center space-x-2 mb-6">
                  <input
                    type="checkbox"
                    checked={filters.isPremium}
                    onChange={(e) => setFilters({ ...filters, isPremium: e.target.checked })}
                    className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                  />
                  <span className="text-sm text-gray-700">Premium Only</span>
                </label>

                {/* Clear Filters */}
                <button
                  onClick={() => {
                    setFilters({
                      category: 'all',
                      type: 'all',
                      difficulty: 'all',
                      format: 'all',
                      isPremium: false
                    });
                    setSortBy('relevance');
                  }}
                  className="w-full py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
                >
                  Clear All Filters
                </button>
              </div>
            </aside>

            {/* Main Content Area */}
            <div className="flex-1">
              {selectedTab === 'resources' && (
                <>
                  {/* Results Header */}
                  <div className="flex items-center justify-between mb-6">
                    <p className="text-gray-600">
                      Found <span className="font-semibold">{sortedResources.length}</span> resources
                    </p>
                  </div>

                  {/* Resources Grid/List */}
                  {viewMode === 'grid' ? (
                    <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-6">
                      {paginatedResources.map(renderResourceCard)}
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {paginatedResources.map((resource) => (
                        <motion.div
                          key={resource.id}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          className="bg-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-all flex items-start space-x-6"
                        >
                          <img
                            src={resource.thumbnail}
                            alt={resource.title}
                            className="w-40 h-32 object-cover rounded-lg"
                          />
                          <div className="flex-1">
                            <div className="flex items-start justify-between mb-2">
                              <div>
                                <h3 className="text-xl font-bold text-gray-900 mb-1">{resource.title}</h3>
                                <p className="text-gray-600">{resource.description}</p>
                              </div>
                              <div className="flex items-center space-x-2">
                                {resource.isNew && (
                                  <span className="px-2 py-1 bg-green-500 text-white text-xs font-bold rounded-full">NEW</span>
                                )}
                                {resource.isTrending && (
                                  <span className="px-2 py-1 bg-orange-500 text-white text-xs font-bold rounded-full">TRENDING</span>
                                )}
                              </div>
                            </div>
                            
                            <div className="flex items-center space-x-6 text-sm text-gray-600 mb-3">
                              <span className="flex items-center">
                                <Clock className="h-4 w-4 mr-1" />
                                {resource.duration || resource.size}
                              </span>
                              <span className="flex items-center">
                                <Eye className="h-4 w-4 mr-1" />
                                {resource.views.toLocaleString()} views
                              </span>
                              <span className="flex items-center">
                                <Star className="h-4 w-4 mr-1 text-yellow-500" />
                                {resource.rating} ({resource.reviews} reviews)
                              </span>
                            </div>
                            
                            <div className="flex items-center justify-between">
                              <div className="flex flex-wrap gap-2">
                                {resource.tags.map((tag, index) => (
                                  <span
                                    key={index}
                                    className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full"
                                  >
                                    {tag}
                                  </span>
                                ))}
                              </div>
                              
                              <div className="flex items-center space-x-3">
                                <button
                                  onClick={() => toggleBookmark(resource.id)}
                                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                                >
                                  <BookmarkIcon className={`h-5 w-5 ${
                                    bookmarkedResources.includes(resource.id) ? 'text-purple-600 fill-current' : 'text-gray-500'
                                  }`} />
                                </button>
                                <CTALink
                                  to={resource.url}
                                  variant="primary"
                                  size="sm"
                                >
                                  Access Resource
                                </CTALink>
                              </div>
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  )}

                  {/* Pagination */}
                  {totalPages > 1 && (
                    <div className="flex items-center justify-center space-x-2 mt-8">
                      <button
                        onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                        disabled={currentPage === 1}
                        className="p-2 hover:bg-gray-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <ChevronLeft className="h-5 w-5" />
                      </button>
                      
                      {[...Array(Math.min(5, totalPages))].map((_, index) => {
                        const pageNum = index + 1;
                        return (
                          <button
                            key={pageNum}
                            onClick={() => setCurrentPage(pageNum)}
                            className={`px-4 py-2 rounded-lg font-medium ${
                              currentPage === pageNum
                                ? 'bg-purple-600 text-white'
                                : 'hover:bg-gray-100 text-gray-700'
                            }`}
                          >
                            {pageNum}
                          </button>
                        );
                      })}
                      
                      <button
                        onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                        disabled={currentPage === totalPages}
                        className="p-2 hover:bg-gray-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <ChevronRight className="h-5 w-5" />
                      </button>
                    </div>
                  )}
                </>
              )}

              {selectedTab === 'paths' && (
                <div className="space-y-6">
                  {learningPaths.map((path) => (
                    <motion.div
                      key={path.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="bg-white rounded-2xl shadow-lg p-6"
                    >
                      <div className="flex items-start space-x-6">
                        <img
                          src={path.thumbnail}
                          alt={path.title}
                          className="w-48 h-32 object-cover rounded-xl"
                        />
                        <div className="flex-1">
                          <div className="flex items-start justify-between mb-3">
                            <div>
                              <h3 className="text-2xl font-bold text-gray-900 mb-1">{path.title}</h3>
                              <p className="text-gray-600">{path.description}</p>
                            </div>
                            {path.enrolled && (
                              <span className="px-3 py-1 bg-green-100 text-green-700 text-sm font-medium rounded-full">
                                Enrolled
                              </span>
                            )}
                          </div>
                          
                          <div className="flex items-center space-x-6 text-sm text-gray-600 mb-4">
                            <span className="flex items-center">
                              <Clock className="h-4 w-4 mr-1" />
                              {path.duration}
                            </span>
                            <span className="flex items-center">
                              <Users className="h-4 w-4 mr-1" />
                              {path.enrolledCount} enrolled
                            </span>
                            <span className="flex items-center">
                              <Star className="h-4 w-4 mr-1 text-yellow-500" />
                              {path.rating}
                            </span>
                            <span className="flex items-center">
                              <Award className="h-4 w-4 mr-1" />
                              Certificate
                            </span>
                          </div>
                          
                          <div className="mb-4">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-sm font-medium text-gray-700">Progress</span>
                              <span className="text-sm font-bold text-purple-600">{path.progress}%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div
                                className="h-2 bg-gradient-to-r from-purple-600 to-pink-600 rounded-full"
                                style={{ width: `${path.progress}%` }}
                              />
                            </div>
                          </div>
                          
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <img
                                src={path.instructor.avatar}
                                alt={path.instructor.name}
                                className="h-8 w-8 rounded-full"
                              />
                              <div>
                                <p className="text-sm font-medium text-gray-900">{path.instructor.name}</p>
                                <p className="text-xs text-gray-500">{path.instructor.bio}</p>
                              </div>
                            </div>
                            
                            <CTALink
                              to={`/learning-paths/${path.id}`}
                              variant={path.enrolled ? 'secondary' : 'primary'}
                              size="sm"
                            >
                              {path.enrolled ? 'Continue Learning' : 'Enroll Now'}
                            </CTALink>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}

              {selectedTab === 'workshops' && (
                <div className="grid md:grid-cols-2 gap-6">
                  {workshops.map((workshop) => (
                    <motion.div
                      key={workshop.id}
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="bg-white rounded-2xl shadow-lg overflow-hidden"
                    >
                      <div className="h-48 overflow-hidden">
                        <img
                          src={workshop.thumbnail}
                          alt={workshop.title}
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <div className="p-6">
                        <div className="flex items-start justify-between mb-3">
                          <h3 className="text-xl font-bold text-gray-900">{workshop.title}</h3>
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                            workshop.mode === 'online' ? 'bg-blue-100 text-blue-700' :
                            workshop.mode === 'offline' ? 'bg-gray-100 text-gray-700' :
                            'bg-purple-100 text-purple-700'
                          }`}>
                            {workshop.mode.toUpperCase()}
                          </span>
                        </div>
                        
                        <p className="text-gray-600 mb-4">{workshop.description}</p>
                        
                        <div className="space-y-2 text-sm text-gray-600 mb-4">
                          <div className="flex items-center">
                            <Calendar className="h-4 w-4 mr-2" />
                            {workshop.date.toLocaleDateString()}
                          </div>
                          <div className="flex items-center">
                            <Clock className="h-4 w-4 mr-2" />
                            {workshop.time}
                          </div>
                          <div className="flex items-center">
                            <MapPin className="h-4 w-4 mr-2" />
                            {workshop.venue}
                          </div>
                          <div className="flex items-center">
                            <Users className="h-4 w-4 mr-2" />
                            {workshop.enrolled}/{workshop.capacity} seats filled
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-between">
                          <div>
                            {workshop.fee > 0 ? (
                              <span className="text-lg font-bold text-gray-900">₹{workshop.fee}</span>
                            ) : (
                              <span className="text-lg font-bold text-green-600">FREE</span>
                            )}
                          </div>
                          
                          <button
                            onClick={() => handleRegisterWorkshop(workshop.id)}
                            className={`px-4 py-2 rounded-lg font-medium transition-all ${
                              registeredWorkshops.includes(workshop.id)
                                ? 'bg-gray-200 text-gray-700'
                                : 'bg-purple-600 text-white hover:bg-purple-700'
                            }`}
                          >
                            {registeredWorkshops.includes(workshop.id) ? 'Registered' : 'Register Now'}
                          </button>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Resources;