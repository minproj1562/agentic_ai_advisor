// src/pages/DigitalLibrary.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import {
  Search,
  Filter,
  Download,
  Bookmark,
  Share2,
  Eye,
  Clock,
  Calendar,
  User,
  Tag,
  FileText,
  Video,
  Headphones,
  Image as ImageIcon,
  BookOpen,
  Library,
  Database,
  Globe,
  Lock,
  Unlock,
  Star,
  TrendingUp,
  BarChart3,
  Grid,
  List,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  X,
  Plus,
  Minus,
  RefreshCw,
  Upload,
  FolderOpen,
  File,
  FileVideo,
  FileAudio,
  FilePlus,
  FileCheck,
  AlertCircle,
  CheckCircle,
  Info,
  HelpCircle,
  Settings,
  Printer,
  Mail,
  MessageSquare,
  ThumbsUp,
  ThumbsDown,
  Heart,
  Award,
  Zap,
  Sparkles,
  BookMarked,
  Microscope,
  Code,
  Terminal,
  Cpu,
  Brain,
  Atom,
  FlaskConical as Flask, 
  Calculator,
  PenTool,
  Palette,
  Music,
  Camera,
  Film,
  Mic,
  Volume2,
  Wifi,
  Cloud,
  Server,
  HardDrive,
  Save,
  Copy,
  Clipboard,
  Link,
  ExternalLink,
  ArrowUp,
  ArrowDown,
  ArrowRight,
  MoreVertical,
  MoreHorizontal,
  Menu,
  Layers,
  Package,
  Archive,
  Trash2,
  Edit,
  GitBranch,
  Binary,
  Hash,
  Key,
  Shield,
  Activity,
  Compass,
  Map,
  Navigation,
  Target,
  Crosshair,
  Move,
  Maximize2,
  Minimize2,
  Square,
  Circle,
  Triangle,
  Hexagon,
  Octagon,
  History,
  RotateCw,
  ZoomIn,
  ZoomOut,
  Expand,
  Shrink,
  Languages,
  Type,
  Bold,
  Italic,
  Underline,
  AlignLeft,
  AlignCenter,
  AlignRight,
  AlignJustify,
  Indent,
  Outdent,
  Quote,
  ListOrdered,
  ListChecks,
  ListTree,
  Table,
  Columns,
  Layout,
  Sidebar,
  PanelLeft,
  PanelRight,
  PanelTop,
  PanelBottom,
  ChevronsLeft,
  ChevronsRight,
  ChevronsUp,
  ChevronsDown,
  ArrowUpCircle,
  ArrowDownCircle,
  ArrowLeftCircle,
  ArrowRightCircle,
  PlayCircle,
  PauseCircle,
  StopCircle,
  SkipBack,
  SkipForward,
  Rewind,
  FastForward,
  Shuffle,
  Repeat,
  Repeat1,
  Cast,
  Airplay,
  Monitor,
  Smartphone,
  Tablet,
  Laptop,
  Tv,
  Radio,
  Speaker,
  Inbox,
  Send,
  ArchiveRestore,
  Reply,
  ReplyAll,
  Forward as ForwardIcon,
  Paperclip as Attachment, 
  FolderPlus,
  FolderMinus,
  FolderCheck,
  FolderX,
  FileSearch,
  FileScan,
  FileDigit,
  FileKey,
  FileLock,
  FileOutput,
  FileInput,
  FileSpreadsheet,
  FileJson,
  FileCode,
  FileArchive,
  FolderArchive,
  Workflow,
  GitPullRequest,
  GitCommit,
  GitBranch as GitBranchIcon,
  GitMerge,
  Github,
  Gitlab,
  Package2,
  Boxes,
  Container,
  Webhook,
  Unplug,
  PlugZap,
  Usb,
  Bluetooth,
  WifiOff,
  Signal,
  Satellite,
  Radar,
  Gauge,
  Thermometer,
  Flame,
  Droplet,
  Wind,
  CloudRain,
  CloudSnow,
  CloudLightning,
  Sun,
  Moon,
  Stars,
  Sunrise,
  Sunset,
  CloudDrizzle,
  CloudHail,
  Tornado,
  Rainbow,
  Waves,
  Anchor,
  Ship,
  Sailboat,
  Mountain,
  TreePine,
  Trees,
  Palmtree as PalmTree, 
  //Cactus,  
  Flower,
  Flower2,
  Leaf,
  Feather,
  Scale,
  Scissors,
  Stamp,
  Highlighter,
  Eraser,
  Ruler,
  PencilRuler,
  Brush,
  PaintBucket,
  Pipette,
  Crop,
  Slice,
  Aperture
} from 'lucide-react';
import CTALink from '../components/common/CTALink';
import { useAuth } from '../hooks/useAuth';
import { useAnalytics } from '../hooks/useAnalytics';
import toast from 'react-hot-toast';
import { Users, FlaskConical, Paperclip, Palmtree } from 'lucide-react';

// Types
interface Resource {
  id: string;
  title: string;
  author: string;
  type: 'book' | 'journal' | 'video' | 'audio' | 'document' | 'dataset' | 'code' | 'image';
  category: string;
  subject: string;
  description: string;
  thumbnail: string;
  fileSize: string;
  format: string;
  language: string;
  publishedDate: Date;
  lastAccessed?: Date;
  downloads: number;
  views: number;
  rating: number;
  reviews: number;
  tags: string[];
  isbn?: string;
  doi?: string;
  url?: string;
  pages?: number;
  duration?: string;
  citations: number;
  isNew: boolean;
  isTrending: boolean;
  isPremium: boolean;
  accessLevel: 'public' | 'students' | 'faculty' | 'premium';
  relatedResources: string[];
}

interface Collection {
  id: string;
  name: string;
  description: string;
  resourceCount: number;
  createdBy: string;
  createdDate: Date;
  isPublic: boolean;
  followers: number;
  thumbnail: string;
  color: string;
}

interface ReadingList {
  id: string;
  name: string;
  courseCode?: string;
  professor?: string;
  resources: string[];
  mandatory: string[];
  supplementary: string[];
  deadline?: Date;
}

interface SearchFilter {
  query: string;
  type: string[];
  category: string[];
  subject: string[];
  language: string;
  publishedAfter?: Date;
  publishedBefore?: Date;
  rating: number;
  accessLevel: string[];
  sortBy: 'relevance' | 'date' | 'rating' | 'downloads' | 'trending';
  viewMode: 'grid' | 'list' | 'compact';
}

// Mock Data
const resourcesData: Resource[] = [
  {
    id: '1',
    title: 'Introduction to Artificial Intelligence',
    author: 'Stuart Russell, Peter Norvig',
    type: 'book',
    category: 'Computer Science',
    subject: 'Artificial Intelligence',
    description: 'The leading textbook in Artificial Intelligence, used in over 1400 universities worldwide.',
    thumbnail: 'https://images.unsplash.com/photo-1532012197267-da84d127e765?w=400',
    fileSize: '45.2 MB',
    format: 'PDF',
    language: 'English',
    publishedDate: new Date('2021-04-28'),
    downloads: 15234,
    views: 45678,
    rating: 4.8,
    reviews: 342,
    tags: ['AI', 'Machine Learning', 'Neural Networks', 'Computer Science'],
    isbn: '978-0136042594',
    pages: 1136,
    citations: 58942,
    isNew: false,
    isTrending: true,
    isPremium: false,
    accessLevel: 'students',
    relatedResources: ['2', '3', '4']
  },
  {
    id: '2',
    title: 'Deep Learning',
    author: 'Ian Goodfellow, Yoshua Bengio, Aaron Courville',
    type: 'book',
    category: 'Computer Science',
    subject: 'Machine Learning',
    description: 'The text offers mathematical and conceptual background on deep learning.',
    thumbnail: 'https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=400',
    fileSize: '38.7 MB',
    format: 'PDF',
    language: 'English',
    publishedDate: new Date('2016-11-18'),
    downloads: 28453,
    views: 67890,
    rating: 4.9,
    reviews: 567,
    tags: ['Deep Learning', 'Neural Networks', 'AI', 'Mathematics'],
    isbn: '978-0262035613',
    pages: 800,
    citations: 45678,
    isNew: false,
    isTrending: true,
    isPremium: false,
    accessLevel: 'public',
    relatedResources: ['1', '3', '5']
  },
  {
    id: '3',
    title: 'Machine Learning Course - Stanford',
    author: 'Andrew Ng',
    type: 'video',
    category: 'Computer Science',
    subject: 'Machine Learning',
    description: 'Complete machine learning course from Stanford University.',
    thumbnail: 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=400',
    fileSize: '12.5 GB',
    format: 'MP4',
    language: 'English',
    publishedDate: new Date('2022-09-01'),
    duration: '64 hours',
    downloads: 45678,
    views: 234567,
    rating: 4.95,
    reviews: 2345,
    tags: ['Machine Learning', 'Video Course', 'Stanford', 'Andrew Ng'],
    isNew: true,
    isTrending: true,
    isPremium: true,
    accessLevel: 'premium',
    relatedResources: ['1', '2', '4'],
    citations: 0
  },
  {
    id: '4',
    title: 'Nature Journal - AI in Healthcare',
    author: 'Various Authors',
    type: 'journal',
    category: 'Medicine',
    subject: 'Healthcare AI',
    description: 'Special issue on applications of AI in healthcare and medicine.',
    thumbnail: 'https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=400',
    fileSize: '18.3 MB',
    format: 'PDF',
    language: 'English',
    publishedDate: new Date('2023-12-15'),
    downloads: 8934,
    views: 23456,
    rating: 4.7,
    reviews: 123,
    tags: ['Healthcare', 'AI', 'Medicine', 'Research'],
    doi: '10.1038/nature.2023.45678',
    pages: 245,
    citations: 1234,
    isNew: true,
    isTrending: false,
    isPremium: true,
    accessLevel: 'faculty',
    relatedResources: ['5', '6']
  },
  {
    id: '5',
    title: 'Data Structures and Algorithms',
    author: 'Thomas H. Cormen',
    type: 'book',
    category: 'Computer Science',
    subject: 'Algorithms',
    description: 'Introduction to fundamental data structures and algorithms.',
    thumbnail: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400',
    fileSize: '28.9 MB',
    format: 'PDF',
    language: 'English',
    publishedDate: new Date('2022-07-31'),
    downloads: 34567,
    views: 89012,
    rating: 4.6,
    reviews: 890,
    tags: ['Algorithms', 'Data Structures', 'Programming', 'Computer Science'],
    isbn: '978-0262033848',
    pages: 1312,
    citations: 78234,
    isNew: false,
    isTrending: false,
    isPremium: false,
    accessLevel: 'students',
    relatedResources: ['1', '6']
  }
];

const collectionsData: Collection[] = [
  {
    id: '1',
    name: 'AI & Machine Learning Essentials',
    description: 'Curated collection of top AI and ML resources',
    resourceCount: 45,
    createdBy: 'Dr. Sarah Johnson',
    createdDate: new Date('2023-09-15'),
    isPublic: true,
    followers: 1234,
    thumbnail: 'https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=400',
    color: 'from-blue-500 to-purple-600'
  },
  {
    id: '2',
    name: 'Research Methods',
    description: 'Essential resources for research methodology',
    resourceCount: 32,
    createdBy: 'Prof. Michael Chen',
    createdDate: new Date('2023-10-20'),
    isPublic: true,
    followers: 876,
    thumbnail: 'https://images.unsplash.com/photo-1532619675605-1ede6c2ed2b0?w=400',
    color: 'from-green-500 to-emerald-600'
  },
  {
    id: '3',
    name: 'Web Development Bootcamp',
    description: 'Complete web development learning path',
    resourceCount: 78,
    createdBy: 'Tech Team',
    createdDate: new Date('2023-11-01'),
    isPublic: true,
    followers: 2345,
    thumbnail: 'https://images.unsplash.com/photo-1517180102446-f3ece451e9d8?w=400',
    color: 'from-orange-500 to-red-600'
  }
];

const readingListsData: ReadingList[] = [
  {
    id: '1',
    name: 'CS301 - Required Reading',
    courseCode: 'CS301',
    professor: 'Dr. Sarah Johnson',
    resources: ['1', '5'],
    mandatory: ['1', '5'],
    supplementary: ['2'],
    deadline: new Date('2024-03-15')
  },
  {
    id: '2',
    name: 'ML Course Materials',
    courseCode: 'CS302',
    professor: 'Prof. Michael Chen',
    resources: ['2', '3'],
    mandatory: ['2'],
    supplementary: ['3'],
    deadline: new Date('2024-04-30')
  }
];

// Resource type icons
const resourceTypeIcons = {
  book: <BookOpen className="h-5 w-5" />,
  journal: <FileText className="h-5 w-5" />,
  video: <Video className="h-5 w-5" />,
  audio: <Headphones className="h-5 w-5" />,
  document: <File className="h-5 w-5" />,
  dataset: <Database className="h-5 w-5" />,
  code: <Code className="h-5 w-5" />,
  image: <ImageIcon className="h-5 w-5" />
};

const DigitalLibrary: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useAuth();
  const { trackEvent } = useAnalytics();

  // State
  const [resources, setResources] = useState(resourcesData);
  const [collections, setCollections] = useState(collectionsData);
  const [readingLists, setReadingLists] = useState(readingListsData);
  const [loading, setLoading] = useState(false);
  const [selectedResource, setSelectedResource] = useState<Resource | null>(null);
  const [showResourceModal, setShowResourceModal] = useState(false);
  const [bookmarkedResources, setBookmarkedResources] = useState<string[]>([]);
  const [downloadHistory, setDownloadHistory] = useState<string[]>([]);
  const [currentTab, setCurrentTab] = useState('browse');
  const [showAdvancedSearch, setShowAdvancedSearch] = useState(false);
  const [pdfViewerOpen, setPdfViewerOpen] = useState(false);
  const [currentPdfUrl, setCurrentPdfUrl] = useState('');
  
  // Filters
  const [filters, setFilters] = useState<SearchFilter>({
    query: searchParams.get('q') || '',
    type: [],
    category: [],
    subject: [],
    language: 'all',
    rating: 0,
    accessLevel: [],
    sortBy: 'relevance',
    viewMode: 'grid'
  });

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 12;

  // Statistics
  const [stats, setStats] = useState({
    totalResources: 1234567,
    totalDownloads: 8901234,
    activeUsers: 5678,
    newThisWeek: 234
  });

  // Filter options
  const filterOptions = {
    types: ['book', 'journal', 'video', 'audio', 'document', 'dataset', 'code', 'image'],
    categories: ['Computer Science', 'Engineering', 'Business', 'Medicine', 'Sciences', 'Arts', 'Mathematics', 'Physics'],
    subjects: ['Artificial Intelligence', 'Machine Learning', 'Data Science', 'Web Development', 'Mobile Development', 'Cybersecurity', 'Cloud Computing', 'Blockchain'],
    languages: ['English', 'Spanish', 'French', 'German', 'Chinese', 'Japanese', 'Hindi', 'Arabic'],
    accessLevels: ['public', 'students', 'faculty', 'premium']
  };

  // Load user data
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
    // Search query
    if (filters.query && !resource.title.toLowerCase().includes(filters.query.toLowerCase()) &&
        !resource.author.toLowerCase().includes(filters.query.toLowerCase()) &&
        !resource.description.toLowerCase().includes(filters.query.toLowerCase()) &&
        !resource.tags.some(tag => tag.toLowerCase().includes(filters.query.toLowerCase()))) {
      return false;
    }

    // Type filter
    if (filters.type.length > 0 && !filters.type.includes(resource.type)) {
      return false;
    }

    // Category filter
    if (filters.category.length > 0 && !filters.category.includes(resource.category)) {
      return false;
    }

    // Subject filter
    if (filters.subject.length > 0 && !filters.subject.includes(resource.subject)) {
      return false;
    }

    // Language filter
    if (filters.language !== 'all' && resource.language !== filters.language) {
      return false;
    }

    // Rating filter
    if (filters.rating > 0 && resource.rating < filters.rating) {
      return false;
    }

    // Access level filter
    if (filters.accessLevel.length > 0 && !filters.accessLevel.includes(resource.accessLevel)) {
      return false;
    }

    return true;
  });

  // Sort resources
  const sortedResources = [...filteredResources].sort((a, b) => {
    switch (filters.sortBy) {
      case 'date':
        return b.publishedDate.getTime() - a.publishedDate.getTime();
      case 'rating':
        return b.rating - a.rating;
      case 'downloads':
        return b.downloads - a.downloads;
      case 'trending':
        return (b.isTrending ? 1 : 0) - (a.isTrending ? 1 : 0);
      default:
        return 0;
    }
  });

  // Paginate resources
  const paginatedResources = sortedResources.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const totalPages = Math.ceil(sortedResources.length / itemsPerPage);

  // Handlers
  const handleSearch = (query: string) => {
    setFilters({ ...filters, query });
    setSearchParams({ q: query });
    setCurrentPage(1);
    trackEvent('library_search', { query });
  };

  const handleFilterChange = (filterType: keyof SearchFilter, value: any) => {
    setFilters({ ...filters, [filterType]: value });
    setCurrentPage(1);
    trackEvent('library_filter_applied', { filterType, value });
  };

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
    // Check access level
   if (resource.accessLevel === 'premium' && user?.role !== 'admin') {
      toast.error('Premium subscription required');
      navigate('/pricing');
      return;
    }

    setLoading(true);
    
    try {
      // Simulate download
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Add to download history
      const updatedHistory = [...downloadHistory, resource.id];
      setDownloadHistory(updatedHistory);
      localStorage.setItem('downloadHistory', JSON.stringify(updatedHistory));
      
      trackEvent('resource_downloaded', {
        resourceId: resource.id,
        resourceTitle: resource.title,
        resourceType: resource.type
      });
      
      toast.success(`Downloaded: ${resource.title}`);
      
      // Open PDF viewer for PDFs
      if (resource.format === 'PDF') {
        setCurrentPdfUrl(`/resources/${resource.id}.pdf`);
        setPdfViewerOpen(true);
      }
    } catch (error) {
      toast.error('Download failed. Please try again.');
    } finally {
      setLoading(false);
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

  const handleShare = async (resource: Resource) => {
    const shareData = {
      title: resource.title,
      text: resource.description,
      url: `${window.location.origin}/library/resource/${resource.id}`
    };

    try {
      if (navigator.share) {
        await navigator.share(shareData);
      } else {
        await navigator.clipboard.writeText(shareData.url);
        toast.success('Link copied to clipboard!');
      }
      trackEvent('resource_shared', { resourceId: resource.id });
    } catch (error) {
      toast.error('Failed to share');
    }
  };

  const handleCiteResource = (resource: Resource) => {
    const citation = `${resource.author} (${resource.publishedDate.getFullYear()}). ${resource.title}. Digital Library, Smart Campus.${resource.isbn ? ` ISBN: ${resource.isbn}` : ''}${resource.doi ? ` DOI: ${resource.doi}` : ''}`;
    
    navigator.clipboard.writeText(citation);
    toast.success('Citation copied to clipboard!');
    trackEvent('resource_cited', { resourceId: resource.id });
  };

  // Render functions
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
      <div className="relative h-48 bg-gradient-to-br from-gray-100 to-gray-200 overflow-hidden">
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
              <Sparkles className="h-3 w-3 mr-1" />
              PREMIUM
            </span>
          )}
        </div>

        {/* Type Icon */}
        <div className="absolute bottom-3 right-3 h-10 w-10 bg-white/90 backdrop-blur-sm rounded-xl flex items-center justify-center">
          {resourceTypeIcons[resource.type]}
        </div>

        {/* Quick Actions */}
        <div className="absolute top-3 right-3 flex flex-col space-y-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={(e) => {
              e.stopPropagation();
              toggleBookmark(resource.id);
            }}
            className={`h-8 w-8 rounded-lg backdrop-blur-sm flex items-center justify-center transition-colors ${
              bookmarkedResources.includes(resource.id)
                ? 'bg-purple-600 text-white'
                : 'bg-white/90 text-gray-700 hover:bg-white'
            }`}
          >
            <Bookmark className={`h-4 w-4 ${bookmarkedResources.includes(resource.id) ? 'fill-current' : ''}`} />
          </button>
          
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleShare(resource);
            }}
            className="h-8 w-8 bg-white/90 backdrop-blur-sm rounded-lg flex items-center justify-center text-gray-700 hover:bg-white transition-colors"
          >
            <Share2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-5">
        {/* Title & Author */}
        <h3 className="font-bold text-gray-900 mb-1 line-clamp-2 group-hover:text-purple-600 transition-colors">
          {resource.title}
        </h3>
        <p className="text-sm text-gray-600 mb-3">{resource.author}</p>

        {/* Description */}
        <p className="text-sm text-gray-500 line-clamp-2 mb-3">
          {resource.description}
        </p>

        {/* Metadata */}
        <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
          <span className="flex items-center">
            <Calendar className="h-3 w-3 mr-1" />
            {resource.publishedDate.getFullYear()}
          </span>
          <span>{resource.language}</span>
          <span>{resource.fileSize}</span>
        </div>

        {/* Stats */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3 text-sm">
            <span className="flex items-center text-yellow-500">
              <Star className="h-4 w-4 fill-current" />
              <span className="ml-1 text-gray-700 font-semibold">{resource.rating}</span>
            </span>
            <span className="flex items-center text-gray-600">
              <Eye className="h-4 w-4 mr-1" />
              {resource.views.toLocaleString()}
            </span>
            <span className="flex items-center text-gray-600">
              <Download className="h-4 w-4 mr-1" />
              {resource.downloads.toLocaleString()}
            </span>
          </div>
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

        {/* Action Buttons */}
        <div className="flex space-x-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleDownload(resource);
            }}
            className="flex-1 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg transition-all flex items-center justify-center"
          >
            <Download className="h-4 w-4 mr-2" />
            Download
          </button>
          
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleResourceClick(resource);
            }}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors"
          >
            <Eye className="h-4 w-4" />
          </button>
        </div>
      </div>
    </motion.div>
  );

  return (
    <>
      <Helmet>
        <title>Digital Library - Smart Campus</title>
        <meta name="description" content="Access millions of academic resources, books, journals, and multimedia content" />
      </Helmet>

      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
        {/* Header */}
        <header className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center"
            >
              <div className="flex items-center justify-center mb-6">
                <Library className="h-12 w-12 mr-4" />
                <h1 className="text-4xl font-bold">Digital Library</h1>
              </div>
              
              <p className="text-xl mb-8 text-white/90">
                Access millions of academic resources anytime, anywhere
              </p>

              {/* Search Bar */}
              <div className="max-w-3xl mx-auto">
                <div className="relative">
                  <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search books, journals, videos, and more..."
                    value={filters.query}
                    onChange={(e) => handleSearch(e.target.value)}
                    className="w-full pl-12 pr-32 py-4 bg-white text-gray-900 rounded-2xl focus:outline-none focus:ring-4 focus:ring-white/30 text-lg"
                  />
                  <button
                    onClick={() => setShowAdvancedSearch(!showAdvancedSearch)}
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 px-4 py-2 bg-purple-600 text-white rounded-xl font-medium hover:bg-purple-700 transition-colors"
                  >
                    Advanced Search
                  </button>
                </div>
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
                {[
                  { icon: <BookOpen />, value: stats.totalResources.toLocaleString(), label: 'Resources' },
                  { icon: <Download />, value: stats.totalDownloads.toLocaleString(), label: 'Downloads' },
                  { icon: <Users />, value: stats.activeUsers.toLocaleString(), label: 'Active Users' },
                  { icon: <Sparkles />, value: stats.newThisWeek, label: 'New This Week' }
                ].map((stat, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="bg-white/10 backdrop-blur-sm rounded-xl p-4"
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
        </header>

        {/* Navigation Tabs */}
        <div className="bg-white border-b sticky top-0 z-30">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between">
              <nav className="flex space-x-1">
                {[
                  { id: 'browse', label: 'Browse', icon: <Grid /> },
                  { id: 'collections', label: 'Collections', icon: <FolderOpen /> },
                  { id: 'reading-lists', label: 'Reading Lists', icon: <BookMarked /> },
                  { id: 'bookmarks', label: 'My Bookmarks', icon: <Bookmark /> },
                  { id: 'history', label: 'History', icon: <History /> }
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setCurrentTab(tab.id)}
                    className={`flex items-center space-x-2 px-4 py-3 font-medium transition-all border-b-2 ${
                      currentTab === tab.id
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
                  onClick={() => setFilters({ ...filters, viewMode: filters.viewMode === 'grid' ? 'list' : 'grid' })}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  {filters.viewMode === 'grid' ? <List className="h-5 w-5" /> : <Grid className="h-5 w-5" />}
                </button>
                
                <CTALink
                  to="/library/upload"
                  variant="primary"
                  size="sm"
                  icon={<Upload className="h-4 w-4" />}
                >
                  Upload Resource
                </CTALink>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex gap-8">
            {/* Sidebar Filters */}
            <aside className="w-64 flex-shrink-0 hidden lg:block">
              <div className="bg-white rounded-2xl p-6 shadow-lg sticky top-24">
                <h3 className="font-bold text-gray-900 mb-4">Filters</h3>
                
                {/* Resource Type */}
                <div className="mb-6">
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">Resource Type</h4>
                  <div className="space-y-2">
                    {filterOptions.types.map((type) => (
                      <label key={type} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={filters.type.includes(type)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              handleFilterChange('type', [...filters.type, type]);
                            } else {
                              handleFilterChange('type', filters.type.filter(t => t !== type));
                            }
                          }}
                          className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                        />
                        <span className="ml-2 text-sm text-gray-600 capitalize">{type}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Category */}
                <div className="mb-6">
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">Category</h4>
                  <select
                    multiple
                    value={filters.category}
                    onChange={(e) => {
                      const selected = Array.from(e.target.selectedOptions, option => option.value);
                      handleFilterChange('category', selected);
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    size={4}
                  >
                    {filterOptions.categories.map((category) => (
                      <option key={category} value={category}>{category}</option>
                    ))}
                  </select>
                </div>

                {/* Language */}
                <div className="mb-6">
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">Language</h4>
                  <select
                    value={filters.language}
                    onChange={(e) => handleFilterChange('language', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="all">All Languages</option>
                    {filterOptions.languages.map((language) => (
                      <option key={language} value={language}>{language}</option>
                    ))}
                  </select>
                </div>

                {/* Rating */}
                <div className="mb-6">
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">Minimum Rating</h4>
                  <div className="flex items-center space-x-2">
                    {[1, 2, 3, 4, 5].map((rating) => (
                      <button
                        key={rating}
                        onClick={() => handleFilterChange('rating', rating === filters.rating ? 0 : rating)}
                        className={`p-1 ${filters.rating >= rating ? 'text-yellow-500' : 'text-gray-300'}`}
                      >
                        <Star className="h-5 w-5 fill-current" />
                      </button>
                    ))}
                  </div>
                </div>

                {/* Sort By */}
                <div className="mb-6">
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">Sort By</h4>
                  <select
                    value={filters.sortBy}
                    onChange={(e) => handleFilterChange('sortBy', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="relevance">Relevance</option>
                    <option value="date">Newest First</option>
                    <option value="rating">Highest Rated</option>
                    <option value="downloads">Most Downloaded</option>
                    <option value="trending">Trending</option>
                  </select>
                </div>

                {/* Clear Filters */}
                <button
                  onClick={() => {
                    setFilters({
                      query: '',
                      type: [],
                      category: [],
                      subject: [],
                      language: 'all',
                      rating: 0,
                      accessLevel: [],
                      sortBy: 'relevance',
                      viewMode: 'grid'
                    });
                    setSearchParams({});
                  }}
                  className="w-full py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
                >
                  Clear All Filters
                </button>
              </div>
            </aside>

            {/* Main Content Area */}
            <div className="flex-1">
              {currentTab === 'browse' && (
                <>
                  {/* Results Header */}
                  <div className="flex items-center justify-between mb-6">
                    <p className="text-gray-600">
                      Found <span className="font-semibold">{sortedResources.length}</span> resources
                    </p>
                  </div>

                  {/* Resources Grid/List */}
                  {filters.viewMode === 'grid' ? (
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
                            className="w-32 h-32 object-cover rounded-lg"
                          />
                          <div className="flex-1">
                            <div className="flex items-start justify-between mb-2">
                              <div>
                                <h3 className="text-xl font-bold text-gray-900 mb-1">{resource.title}</h3>
                                <p className="text-gray-600">{resource.author}</p>
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
                            <p className="text-gray-500 mb-3">{resource.description}</p>
                            <div className="flex items-center space-x-6 text-sm text-gray-600 mb-3">
                              <span className="flex items-center">
                                <Calendar className="h-4 w-4 mr-1" />
                                {resource.publishedDate.getFullYear()}
                              </span>
                              <span className="flex items-center">
                                <Star className="h-4 w-4 mr-1 text-yellow-500" />
                                {resource.rating}
                              </span>
                              <span className="flex items-center">
                                <Download className="h-4 w-4 mr-1" />
                                {resource.downloads.toLocaleString()}
                              </span>
                              <span>{resource.fileSize}</span>
                            </div>
                            <div className="flex items-center space-x-3">
                              <button
                                onClick={() => handleDownload(resource)}
                                className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-medium hover:shadow-lg transition-all"
                              >
                                Download
                              </button>
                              <button
                                onClick={() => handleResourceClick(resource)}
                                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
                              >
                                View Details
                              </button>
                              <button
                                onClick={() => toggleBookmark(resource.id)}
                                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                              >
                                <Bookmark className={`h-5 w-5 ${bookmarkedResources.includes(resource.id) ? 'text-purple-600 fill-current' : 'text-gray-500'}`} />
                              </button>
                              <button
                                onClick={() => handleShare(resource)}
                                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                              >
                                <Share2 className="h-5 w-5 text-gray-500" />
                              </button>
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
                      
                      {totalPages > 5 && <span className="px-2">...</span>}
                      
                      {totalPages > 5 && (
                        <button
                          onClick={() => setCurrentPage(totalPages)}
                          className={`px-4 py-2 rounded-lg font-medium ${
                            currentPage === totalPages
                              ? 'bg-purple-600 text-white'
                              : 'hover:bg-gray-100 text-gray-700'
                          }`}
                        >
                          {totalPages}
                        </button>
                      )}
                      
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

              {currentTab === 'collections' && (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {collections.map((collection) => (
                    <motion.div
                      key={collection.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      whileHover={{ y: -5 }}
                      className="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-xl transition-all cursor-pointer"
                    >
                      <div className={`h-32 bg-gradient-to-r ${collection.color} relative`}>
                        <img
                          src={collection.thumbnail}
                          alt={collection.name}
                          className="w-full h-full object-cover opacity-30"
                        />
                        <div className="absolute inset-0 flex items-center justify-center">
                          <FolderOpen className="h-12 w-12 text-white" />
                        </div>
                      </div>
                      <div className="p-5">
                        <h3 className="font-bold text-gray-900 mb-2">{collection.name}</h3>
                        <p className="text-sm text-gray-600 mb-3">{collection.description}</p>
                        <div className="flex items-center justify-between text-sm text-gray-500 mb-3">
                          <span>{collection.resourceCount} resources</span>
                          <span>{collection.followers} followers</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <p className="text-xs text-gray-500">by {collection.createdBy}</p>
                          <CTALink
                            to={`/library/collection/${collection.id}`}
                            variant="primary"
                            size="sm"
                          >
                            View Collection
                          </CTALink>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}

              {currentTab === 'reading-lists' && (
                <div className="space-y-6">
                  {readingLists.map((list) => (
                    <motion.div
                      key={list.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="bg-white rounded-2xl p-6 shadow-lg"
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <h3 className="text-xl font-bold text-gray-900 mb-1">{list.name}</h3>
                          {list.courseCode && (
                            <p className="text-gray-600">
                              {list.courseCode} • {list.professor}
                            </p>
                          )}
                        </div>
                        {list.deadline && (
                          <div className="text-right">
                            <p className="text-sm text-gray-500">Deadline</p>
                            <p className="font-semibold text-orange-600">
                              {list.deadline.toLocaleDateString()}
                            </p>
                          </div>
                        )}
                      </div>
                      
                      <div className="grid md:grid-cols-2 gap-4 mb-4">
                        <div>
                          <h4 className="font-semibold text-gray-700 mb-2 flex items-center">
                            <AlertCircle className="h-4 w-4 mr-2 text-red-500" />
                            Mandatory ({list.mandatory.length})
                          </h4>
                          <ul className="space-y-1">
                            {list.mandatory.map((resourceId) => {
                              const resource = resources.find(r => r.id === resourceId);
                              return resource ? (
                                <li key={resourceId} className="text-sm text-gray-600">
                                  • {resource.title}
                                </li>
                              ) : null;
                            })}
                          </ul>
                        </div>
                        
                        <div>
                          <h4 className="font-semibold text-gray-700 mb-2 flex items-center">
                            <Info className="h-4 w-4 mr-2 text-blue-500" />
                            Supplementary ({list.supplementary.length})
                          </h4>
                          <ul className="space-y-1">
                            {list.supplementary.map((resourceId) => {
                              const resource = resources.find(r => r.id === resourceId);
                              return resource ? (
                                <li key={resourceId} className="text-sm text-gray-600">
                                  • {resource.title}
                                </li>
                              ) : null;
                            })}
                          </ul>
                        </div>
                      </div>
                      
                      <CTALink
                        to={`/library/reading-list/${list.id}`}
                        variant="primary"
                        size="sm"
                        showArrow
                      >
                        View Full List
                      </CTALink>
                    </motion.div>
                  ))}
                </div>
              )}

              {currentTab === 'bookmarks' && (
                <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-6">
                  {bookmarkedResources.map((resourceId) => {
                    const resource = resources.find(r => r.id === resourceId);
                    return resource ? renderResourceCard(resource) : null;
                  })}
                  
                  {bookmarkedResources.length === 0 && (
                    <div className="col-span-full text-center py-12">
                      <Bookmark className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                      <h3 className="text-xl font-semibold text-gray-700 mb-2">No bookmarks yet</h3>
                      <p className="text-gray-500">Start bookmarking resources to access them quickly</p>
                    </div>
                  )}
                </div>
              )}

              {currentTab === 'history' && (
                <div className="space-y-4">
                  {downloadHistory.map((resourceId) => {
                    const resource = resources.find(r => r.id === resourceId);
                    return resource ? (
                      <motion.div
                        key={resourceId}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="bg-white rounded-xl p-4 shadow-lg flex items-center justify-between"
                      >
                        <div className="flex items-center space-x-4">
                          {resourceTypeIcons[resource.type]}
                          <div>
                            <h4 className="font-semibold text-gray-900">{resource.title}</h4>
                            <p className="text-sm text-gray-600">{resource.author}</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-3">
                          <span className="text-sm text-gray-500">
                            Downloaded on {new Date().toLocaleDateString()}
                          </span>
                          <button
                            onClick={() => handleDownload(resource)}
                            className="px-3 py-1 bg-purple-100 text-purple-700 rounded-lg font-medium hover:bg-purple-200 transition-colors"
                          >
                            Re-download
                          </button>
                        </div>
                      </motion.div>
                    ) : null;
                  })}
                  
                  {downloadHistory.length === 0 && (
                    <div className="text-center py-12">
                      <History className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                      <h3 className="text-xl font-semibold text-gray-700 mb-2">No download history</h3>
                      <p className="text-gray-500">Your downloaded resources will appear here</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Resource Detail Modal */}
        <AnimatePresence>
          {showResourceModal && selectedResource && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
              onClick={() => setShowResourceModal(false)}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                className="bg-white rounded-3xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="p-8">
                  <div className="flex items-start justify-between mb-6">
                    <div>
                      <h2 className="text-3xl font-bold text-gray-900 mb-2">{selectedResource.title}</h2>
                      <p className="text-lg text-gray-600">{selectedResource.author}</p>
                    </div>
                    <button
                      onClick={() => setShowResourceModal(false)}
                      className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      <X className="h-6 w-6 text-gray-500" />
                    </button>
                  </div>

                  <div className="grid md:grid-cols-3 gap-8">
                    <div className="md:col-span-2">
                      <img
                        src={selectedResource.thumbnail}
                        alt={selectedResource.title}
                        className="w-full h-64 object-cover rounded-xl mb-6"
                      />
                      
                      <h3 className="font-semibold text-gray-900 mb-3">Description</h3>
                      <p className="text-gray-600 mb-6">{selectedResource.description}</p>
                      
                      <h3 className="font-semibold text-gray-900 mb-3">Tags</h3>
                      <div className="flex flex-wrap gap-2 mb-6">
                        {selectedResource.tags.map((tag, index) => (
                          <span
                            key={index}
                            className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>

                      <div className="flex space-x-3">
                        <button
                          onClick={() => handleDownload(selectedResource)}
                          className="flex-1 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all flex items-center justify-center"
                        >
                          <Download className="h-5 w-5 mr-2" />
                          Download {selectedResource.format}
                        </button>
                        
                        <button
                          onClick={() => toggleBookmark(selectedResource.id)}
                          className={`px-6 py-3 rounded-xl font-semibold transition-all ${
                            bookmarkedResources.includes(selectedResource.id)
                              ? 'bg-purple-100 text-purple-700'
                              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                          }`}
                        >
                          <Bookmark className={`h-5 w-5 ${bookmarkedResources.includes(selectedResource.id) ? 'fill-current' : ''}`} />
                        </button>
                        
                        <button
                          onClick={() => handleShare(selectedResource)}
                          className="px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-semibold hover:bg-gray-200 transition-colors"
                        >
                          <Share2 className="h-5 w-5" />
                        </button>
                      </div>
                    </div>

                    <div>
                      <div className="bg-gray-50 rounded-xl p-6 space-y-4">
                        <h3 className="font-semibold text-gray-900">Resource Details</h3>
                        
                        <div className="space-y-3 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Type</span>
                            <span className="font-medium capitalize">{selectedResource.type}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Format</span>
                            <span className="font-medium">{selectedResource.format}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">File Size</span>
                            <span className="font-medium">{selectedResource.fileSize}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Language</span>
                            <span className="font-medium">{selectedResource.language}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Published</span>
                            <span className="font-medium">{selectedResource.publishedDate.toLocaleDateString()}</span>
                          </div>
                          {selectedResource.pages && (
                            <div className="flex justify-between">
                              <span className="text-gray-600">Pages</span>
                              <span className="font-medium">{selectedResource.pages}</span>
                            </div>
                          )}
                          {selectedResource.duration && (
                            <div className="flex justify-between">
                              <span className="text-gray-600">Duration</span>
                              <span className="font-medium">{selectedResource.duration}</span>
                            </div>
                          )}
                          {selectedResource.isbn && (
                            <div className="flex justify-between">
                              <span className="text-gray-600">ISBN</span>
                              <span className="font-medium">{selectedResource.isbn}</span>
                            </div>
                          )}
                          {selectedResource.doi && (
                            <div className="flex justify-between">
                              <span className="text-gray-600">DOI</span>
                              <span className="font-medium">{selectedResource.doi}</span>
                            </div>
                          )}
                        </div>

                        <div className="pt-4 border-t">
                          <h4 className="font-semibold text-gray-900 mb-3">Statistics</h4>
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <span className="flex items-center text-gray-600">
                                <Star className="h-4 w-4 mr-1 text-yellow-500" />
                                Rating
                              </span>
                              <span className="font-medium">{selectedResource.rating}/5.0</span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="flex items-center text-gray-600">
                                <Eye className="h-4 w-4 mr-1" />
                                Views
                              </span>
                              <span className="font-medium">{selectedResource.views.toLocaleString()}</span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="flex items-center text-gray-600">
                                <Download className="h-4 w-4 mr-1" />
                                Downloads
                              </span>
                              <span className="font-medium">{selectedResource.downloads.toLocaleString()}</span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="flex items-center text-gray-600">
                                <Quote className="h-4 w-4 mr-1" />
                                Citations
                              </span>
                              <span className="font-medium">{selectedResource.citations.toLocaleString()}</span>
                            </div>
                          </div>
                        </div>

                        <div className="pt-4 border-t">
                          <button
                            onClick={() => handleCiteResource(selectedResource)}
                            className="w-full py-2 bg-purple-100 text-purple-700 rounded-lg font-medium hover:bg-purple-200 transition-colors"
                          >
                            Copy Citation
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </>
  );
};

export default DigitalLibrary;