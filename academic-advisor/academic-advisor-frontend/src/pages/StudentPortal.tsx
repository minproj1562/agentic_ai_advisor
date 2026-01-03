// src/pages/StudentPortal.tsx
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import {
  User,
  Calendar,
  BookOpen,
  TrendingUp,
  Award,
  MessageSquare,
  Bell,
  Settings,
  LogOut,
  Clock,
  Target,
  Activity,
  BarChart3,
  FileText,
  Download,
  ChevronRight,
  ChevronLeft,
  Star,
  AlertCircle,
  CheckCircle,
  XCircle,
  Coffee,
  Sun,
  Moon,
  Cloud,
  Zap,
  Trophy,
  Users,
  Video,
  Mic,
  MicOff,
  Camera,
  CameraOff,
  Share2,
  Grid,
  List,
  Filter,
  Search,
  PlusCircle,
  MinusCircle,
  RefreshCw,
  ArrowUp,
  ArrowDown,
  Brain,
  Cpu,
  Database,
  GitBranch,
  Code,
  Terminal,
  Layers,
  Package,
  Server,
  Shield,
  Lock,
  Unlock,
  Key,
  Eye,
  EyeOff,
  Edit,
  Trash2,
  Copy,
  Clipboard,
  Link,
  ExternalLink,
  Upload,
  FolderOpen,
  Save,
  Printer,
  Mail,
  Phone,
  MapPin,
  Navigation,
  Compass,
  Map,
  Flag,
  Bookmark,
  Heart,
  ThumbsUp,
  ThumbsDown,
  MessageCircle,
  Send,
  Inbox,
  Archive,
  Trash,
  Tag,
  Hash,
  AtSign,
  DollarSign,
  Percent,
  Calculator,
  CreditCard,
  Wallet,
  Receipt,
  ShoppingCart,
  Package2,
  Gift,
  Briefcase,
  Paperclip,
  Image,
  Film,
  Music,
  Headphones,
  Volume2,
  VolumeX,
  Wifi,
  WifiOff,
  Bluetooth,
  Cast,
  Airplay,
  Monitor,
  Smartphone,
  Tablet,
  Watch,
  Tv,
  Radio,
  Speaker,
  Printer as PrinterIcon,
  HardDrive,
  CircuitBoard,
  Microscope,
  Telescope,
  Lightbulb,
  Flashlight,
  Battery,
  BatteryCharging,
  Power,
  Plug,
  Sunset,
  Sunrise,
  Wind,
  Droplet,
  Flame,
  Snowflake,
  Thermometer,
  Umbrella,
  CloudRain,
  CloudSnow,
  CloudLightning,
  Rainbow,
  Waves,
  Mountain,
  Flower,
  Leaf,
  Feather,
  Fish,
  Bird,
  Bug,
  Cat,
  Dog,
  Rabbit,
  Turtle,
  Squirrel,
  Trees,
  TreePine,
  Pizza,
  Apple,
  Cherry,
  Grape,
  //Lemon,
  Carrot,
  //Corn,
  Egg,
  Milk,
  Wheat,
  Utensils,
  GraduationCap,
  BookMarked,
  Library,
  School,
  Backpack,
  PenTool,
  Pencil,
  Brush,
  Palette,
  Scissors,
  Ruler,
  Eraser,
  Paperclip as PaperclipIcon,
  Link2,
  Unlink,
  Anchor,
  Globe,
  Crosshair,
  Move,
  Maximize2,
  Minimize2,
  Maximize,
  Minimize,
  Square,
  Circle,
  Triangle,
  Hexagon,
  Octagon,
  Star as StarIcon,
  Heart as HeartIcon,
  Club,
  Diamond,
  Spade
} from 'lucide-react';
import CTALink from '../components/common/CTALink';
import { useAuth } from '../hooks/useAuth';
import { useAnalytics } from '../hooks/useAnalytics';
import toast from 'react-hot-toast';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { X } from 'lucide-react';

// Types
interface Course {
  id: string;
  code: string;
  name: string;
  instructor: string;
  schedule: string;
  room: string;
  credits: number;
  attendance: number;
  grade: string;
  progress: number;
  nextClass: Date;
  assignments: Assignment[];
  color: string;
}

interface Assignment {
  id: string;
  title: string;
  dueDate: Date;
  status: 'pending' | 'submitted' | 'graded';
  grade?: number;
  maxGrade: number;
}

interface Event {
  id: string;
  title: string;
  type: 'class' | 'exam' | 'assignment' | 'event';
  time: string;
  location: string;
  color: string;
}

interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  time: Date;
  read: boolean;
}

interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  unlocked: boolean;
  progress: number;
  maxProgress: number;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
}

// Mock Data
const currentCourses: Course[] = [
  {
    id: '1',
    code: 'CS301',
    name: 'Data Structures & Algorithms',
    instructor: 'Dr. Sarah Johnson',
    schedule: 'Mon, Wed, Fri - 10:00 AM',
    room: 'Room 301, CS Building',
    credits: 4,
    attendance: 92,
    grade: 'A',
    progress: 75,
    nextClass: new Date(Date.now() + 86400000),
    color: 'from-blue-500 to-indigo-600',
    assignments: [
      { id: '1', title: 'Binary Trees Assignment', dueDate: new Date(Date.now() + 172800000), status: 'pending', maxGrade: 100 },
      { id: '2', title: 'Graph Algorithms Lab', dueDate: new Date(Date.now() + 432000000), status: 'pending', maxGrade: 50 }
    ]
  },
  {
    id: '2',
    code: 'CS302',
    name: 'Machine Learning',
    instructor: 'Prof. Michael Chen',
    schedule: 'Tue, Thu - 2:00 PM',
    room: 'Room 205, AI Lab',
    credits: 3,
    attendance: 88,
    grade: 'A-',
    progress: 68,
    nextClass: new Date(Date.now() + 172800000),
    color: 'from-purple-500 to-pink-600',
    assignments: [
      { id: '3', title: 'Neural Network Project', dueDate: new Date(Date.now() + 604800000), status: 'pending', maxGrade: 100 },
      { id: '4', title: 'ML Quiz 3', dueDate: new Date(Date.now() + 259200000), status: 'submitted', grade: 85, maxGrade: 100 }
    ]
  },
  {
    id: '3',
    code: 'CS303',
    name: 'Cloud Computing',
    instructor: 'Dr. Emily Roberts',
    schedule: 'Mon, Thu - 4:00 PM',
    room: 'Virtual Lab',
    credits: 3,
    attendance: 95,
    grade: 'A+',
    progress: 82,
    nextClass: new Date(Date.now() + 86400000),
    color: 'from-green-500 to-emerald-600',
    assignments: [
      { id: '5', title: 'AWS Deployment Project', dueDate: new Date(Date.now() + 864000000), status: 'pending', maxGrade: 150 }
    ]
  },
  {
    id: '4',
    code: 'MATH201',
    name: 'Discrete Mathematics',
    instructor: 'Prof. David Wilson',
    schedule: 'Tue, Fri - 11:00 AM',
    room: 'Room 105, Math Building',
    credits: 3,
    attendance: 90,
    grade: 'B+',
    progress: 70,
    nextClass: new Date(Date.now() + 259200000),
    color: 'from-orange-500 to-red-600',
    assignments: [
      { id: '6', title: 'Proof Techniques Assignment', dueDate: new Date(Date.now() + 345600000), status: 'graded', grade: 78, maxGrade: 100 }
    ]
  }
];

const todayEvents: Event[] = [
  { id: '1', title: 'Data Structures Lecture', type: 'class', time: '10:00 AM', location: 'Room 301', color: 'bg-blue-500' },
  { id: '2', title: 'ML Lab Session', type: 'class', time: '2:00 PM', location: 'AI Lab', color: 'bg-purple-500' },
  { id: '3', title: 'Project Submission', type: 'assignment', time: '11:59 PM', location: 'Online', color: 'bg-orange-500' },
  { id: '4', title: 'Tech Talk: Future of AI', type: 'event', time: '5:00 PM', location: 'Auditorium', color: 'bg-green-500' }
];

const notifications: Notification[] = [
  {
    id: '1',
    title: 'Assignment Graded',
    message: 'Your ML Quiz 3 has been graded. Score: 85/100',
    type: 'success',
    time: new Date(Date.now() - 3600000),
    read: false
  },
  {
    id: '2',
    title: 'Class Rescheduled',
    message: 'Cloud Computing class moved to 5:00 PM today',
    type: 'warning',
    time: new Date(Date.now() - 7200000),
    read: false
  },
  {
    id: '3',
    title: 'New Study Material',
    message: 'Prof. Johnson uploaded new notes for DSA',
    type: 'info',
    time: new Date(Date.now() - 10800000),
    read: true
  }
];

const achievements: Achievement[] = [
  {
    id: '1',
    title: 'Perfect Attendance',
    description: 'Attend all classes for a month',
    icon: <Trophy className="h-8 w-8" />,
    unlocked: true,
    progress: 30,
    maxProgress: 30,
    rarity: 'rare'
  },
  {
    id: '2',
    title: 'Dean\'s List',
    description: 'Maintain GPA above 3.5',
    icon: <Award className="h-8 w-8" />,
    unlocked: true,
    progress: 1,
    maxProgress: 1,
    rarity: 'epic'
  },
  {
    id: '3',
    title: 'Code Master',
    description: 'Submit 50 programming assignments',
    icon: <Code className="h-8 w-8" />,
    unlocked: false,
    progress: 35,
    maxProgress: 50,
    rarity: 'common'
  },
  {
    id: '4',
    title: 'Research Pioneer',
    description: 'Publish a research paper',
    icon: <Microscope className="h-8 w-8" />,
    unlocked: false,
    progress: 0,
    maxProgress: 1,
    rarity: 'legendary'
  }
];

// Performance data for charts
const performanceData = [
  { month: 'Jan', gpa: 3.2, attendance: 85, assignments: 92 },
  { month: 'Feb', gpa: 3.4, attendance: 88, assignments: 88 },
  { month: 'Mar', gpa: 3.5, attendance: 92, assignments: 95 },
  { month: 'Apr', gpa: 3.6, attendance: 90, assignments: 87 },
  { month: 'May', gpa: 3.7, attendance: 93, assignments: 91 },
  { month: 'Jun', gpa: 3.8, attendance: 95, assignments: 94 }
];

const skillsData = [
  { skill: 'Programming', value: 85, fullMark: 100 },
  { skill: 'Mathematics', value: 78, fullMark: 100 },
  { skill: 'Problem Solving', value: 92, fullMark: 100 },
  { skill: 'Communication', value: 75, fullMark: 100 },
  { skill: 'Leadership', value: 70, fullMark: 100 },
  { skill: 'Research', value: 65, fullMark: 100 }
];

const gradeDistribution = [
  { name: 'A+', value: 2, color: '#10b981' },
  { name: 'A', value: 3, color: '#22c55e' },
  { name: 'A-', value: 2, color: '#84cc16' },
  { name: 'B+', value: 1, color: '#facc15' },
  { name: 'B', value: 1, color: '#fb923c' }
];

const StudentPortal: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { trackEvent } = useAnalytics();
  
  // State
  const [selectedTab, setSelectedTab] = useState('dashboard');
  const [showNotifications, setShowNotifications] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null);
  const [upcomingDeadlines, setUpcomingDeadlines] = useState<Assignment[]>([]);
  const [greeting, setGreeting] = useState('');
  const [currentDateTime, setCurrentDateTime] = useState(new Date());
  const [studyStreak, setStudyStreak] = useState(15);
  const [weeklyGoalProgress, setWeeklyGoalProgress] = useState(65);
  const [showAchievementModal, setShowAchievementModal] = useState(false);
  const [selectedAchievement, setSelectedAchievement] = useState<Achievement | null>(null);

  // Get greeting based on time
  useEffect(() => {
    const hour = new Date().getHours();
    if (hour < 12) setGreeting('Good Morning');
    else if (hour < 17) setGreeting('Good Afternoon');
    else setGreeting('Good Evening');

    // Update time every second
    const timer = setInterval(() => {
      setCurrentDateTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Get upcoming deadlines
  useEffect(() => {
    const allAssignments = currentCourses.flatMap(course => 
      course.assignments.map(assignment => ({
        ...assignment,
        courseName: course.name,
        courseCode: course.code
      }))
    );
    
    const upcoming = allAssignments
      .filter(a => a.status === 'pending')
      .sort((a, b) => a.dueDate.getTime() - b.dueDate.getTime())
      .slice(0, 5);
    
    setUpcomingDeadlines(upcoming);
  }, []);

  // Calculate stats
  const calculateGPA = () => {
    const gradePoints: { [key: string]: number } = {
      'A+': 4.0, 'A': 3.7, 'A-': 3.3,
      'B+': 3.0, 'B': 2.7, 'B-': 2.3,
      'C+': 2.0, 'C': 1.7, 'C-': 1.3,
      'D': 1.0, 'F': 0
    };
    
    let totalPoints = 0;
    let totalCredits = 0;
    
    currentCourses.forEach(course => {
      totalPoints += (gradePoints[course.grade] || 0) * course.credits;
      totalCredits += course.credits;
    });
    
    return totalCredits > 0 ? (totalPoints / totalCredits).toFixed(2) : '0.00';
  };

  const calculateAttendance = () => {
    const total = currentCourses.reduce((sum, course) => sum + course.attendance, 0);
    return Math.round(total / currentCourses.length);
  };

  const handleLogout = () => {
    trackEvent('logout', { userId: user?.id });
    logout();
    navigate('/');
    toast.success('Logged out successfully');
  };

  const handleCourseClick = (course: Course) => {
    setSelectedCourse(course);
    trackEvent('course_viewed', { courseId: course.id, courseName: course.name });
  };

  const handleAssignmentSubmit = (assignment: Assignment) => {
    trackEvent('assignment_submitted', { assignmentId: assignment.id });
    toast.success(`Assignment "${assignment.title}" submitted successfully`);
  };

  const handleJoinClass = (course: Course) => {
    trackEvent('class_joined', { courseId: course.id });
    // Implement video call integration
    toast.success(`Joining ${course.name} class...`);
  };

  const markNotificationAsRead = (notificationId: string) => {
    // Update notification status
    trackEvent('notification_read', { notificationId });
  };

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Welcome Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 rounded-3xl p-8 text-white"
      >
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">
              {greeting}, {user?.name?.split(' ')[0]}! 👋
            </h1>
            <p className="text-white/80 mb-4">
              {currentDateTime.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
            </p>
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2">
                <Flame className="h-5 w-5 text-orange-300" />
                <span className="font-semibold">{studyStreak} day streak</span>
              </div>
              <div className="flex items-center space-x-2">
                <Target className="h-5 w-5 text-green-300" />
                <span className="font-semibold">{weeklyGoalProgress}% weekly goal</span>
              </div>
              <div className="flex items-center space-x-2">
                <Trophy className="h-5 w-5 text-yellow-300" />
                <span className="font-semibold">Rank #12 in class</span>
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-5xl font-bold mb-2">{currentDateTime.toLocaleTimeString()}</div>
            <div className="flex items-center justify-end space-x-2">
              <Cloud className="h-5 w-5" />
              <span>28°C, Partly Cloudy</span>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { label: 'Current GPA', value: calculateGPA(), icon: <TrendingUp />, color: 'from-blue-500 to-indigo-600', change: '+0.2' },
          { label: 'Attendance', value: `${calculateAttendance()}%`, icon: <Calendar />, color: 'from-green-500 to-emerald-600', change: '+5%' },
          { label: 'Assignments', value: `${upcomingDeadlines.length} Due`, icon: <FileText />, color: 'from-orange-500 to-red-600', change: '3 this week' },
          { label: 'Study Hours', value: '24.5h', icon: <Clock />, color: 'from-purple-500 to-pink-600', change: '+4.5h' }
        ].map((stat, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all"
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`h-12 w-12 bg-gradient-to-r ${stat.color} rounded-xl flex items-center justify-center text-white`}>
                {React.cloneElement(stat.icon, { className: 'h-6 w-6' })}
              </div>
              <span className="text-xs text-green-600 font-semibold">{stat.change}</span>
            </div>
            <div className="text-3xl font-bold text-gray-900 mb-1">{stat.value}</div>
            <div className="text-sm text-gray-600">{stat.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Left Column - Courses & Schedule */}
        <div className="lg:col-span-2 space-y-6">
          {/* Today's Schedule */}
          <div className="bg-white rounded-2xl p-6 shadow-lg">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-900">Today's Schedule</h2>
              <CTALink
                to="/student-portal/schedule"
                variant="ghost"
                size="sm"
                showArrow
              >
                View Full Schedule
              </CTALink>
            </div>
            
            <div className="space-y-3">
              {todayEvents.map((event, index) => (
                <motion.div
                  key={event.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-center space-x-4 p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors cursor-pointer"
                >
                  <div className={`h-2 w-2 rounded-full ${event.color}`} />
                  <div className="flex-1">
                    <div className="font-semibold text-gray-900">{event.title}</div>
                    <div className="text-sm text-gray-600">{event.location}</div>
                  </div>
                  <div className="text-sm text-gray-500">{event.time}</div>
                  {event.type === 'class' && (
                    <button
                      onClick={() => toast.success('Joining class...')}
                      className="px-3 py-1 bg-green-100 text-green-700 rounded-lg text-sm font-medium hover:bg-green-200 transition-colors"
                    >
                      Join
                    </button>
                  )}
                </motion.div>
              ))}
            </div>
          </div>

          {/* Current Courses */}
          <div className="bg-white rounded-2xl p-6 shadow-lg">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-900">My Courses</h2>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  {viewMode === 'grid' ? <List className="h-5 w-5" /> : <Grid className="h-5 w-5" />}
                </button>
                <CTALink
                  to="/programs"
                  variant="primary"
                  size="sm"
                  icon={<PlusCircle className="h-4 w-4" />}
                >
                  Add Course
                </CTALink>
              </div>
            </div>

            <div className={viewMode === 'grid' ? 'grid md:grid-cols-2 gap-4' : 'space-y-4'}>
              {currentCourses.map((course, index) => (
                <motion.div
                  key={course.id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.1 }}
                  onClick={() => handleCourseClick(course)}
                  className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl p-5 hover:shadow-lg transition-all cursor-pointer group"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="flex items-center space-x-2 mb-1">
                        <span className={`text-sm font-bold bg-gradient-to-r ${course.color} bg-clip-text text-transparent`}>
                          {course.code}
                        </span>
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                          {course.credits} Credits
                        </span>
                      </div>
                      <h3 className="font-semibold text-gray-900 group-hover:text-purple-600 transition-colors">
                        {course.name}
                      </h3>
                      <p className="text-sm text-gray-600">{course.instructor}</p>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-gray-900">{course.grade}</div>
                      <div className="text-xs text-gray-500">Current Grade</div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Course Progress</span>
                      <span className="font-semibold">{course.progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${course.progress}%` }}
                        transition={{ duration: 1, delay: index * 0.1 }}
                        className={`h-2 bg-gradient-to-r ${course.color} rounded-full`}
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-between mt-4 text-sm">
                    <div className="flex items-center space-x-3">
                      <div className="flex items-center text-gray-600">
                        <Calendar className="h-4 w-4 mr-1" />
                        {course.schedule}
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleJoinClass(course);
                      }}
                      className="px-3 py-1 bg-purple-100 text-purple-700 rounded-lg font-medium hover:bg-purple-200 transition-colors"
                    >
                      Join Class
                    </button>
                  </div>

                  {course.assignments.filter(a => a.status === 'pending').length > 0 && (
                    <div className="mt-3 pt-3 border-t">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-orange-600 font-medium">
                          {course.assignments.filter(a => a.status === 'pending').length} pending assignments
                        </span>
                        <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-purple-600 group-hover:translate-x-1 transition-all" />
                      </div>
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          </div>

          {/* Performance Analytics */}
          <div className="bg-white rounded-2xl p-6 shadow-lg">
            <h2 className="text-xl font-bold text-gray-900 mb-6">Performance Analytics</h2>
            
            <div className="grid md:grid-cols-2 gap-6">
              {/* GPA Trend */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-4">GPA Trend</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis domain={[0, 4]} />
                    <Tooltip />
                    <Area type="monotone" dataKey="gpa" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.3} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Grade Distribution */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-4">Grade Distribution</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={gradeDistribution}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {gradeDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex flex-wrap justify-center gap-2 mt-4">
                  {gradeDistribution.map((grade) => (
                    <div key={grade.name} className="flex items-center space-x-2">
                      <div className="h-3 w-3 rounded-full" style={{ backgroundColor: grade.color }} />
                      <span className="text-xs text-gray-600">{grade.name}: {grade.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - Sidebar */}
        <div className="space-y-6">
          {/* Upcoming Deadlines */}
          <div className="bg-white rounded-2xl p-6 shadow-lg">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-gray-900">Upcoming Deadlines</h2>
              <AlertCircle className="h-5 w-5 text-orange-500" />
            </div>
            
            <div className="space-y-3">
              {upcomingDeadlines.map((assignment: any, index) => {
                const daysLeft = Math.ceil((assignment.dueDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
                const urgency = daysLeft <= 2 ? 'text-red-600 bg-red-50' : daysLeft <= 5 ? 'text-orange-600 bg-orange-50' : 'text-green-600 bg-green-50';
                
                return (
                  <motion.div
                    key={assignment.id}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <p className="font-semibold text-gray-900 text-sm">{assignment.title}</p>
                        <p className="text-xs text-gray-600">{assignment.courseCode} - {assignment.courseName}</p>
                      </div>
                      <span className={`text-xs font-bold px-2 py-1 rounded-full ${urgency}`}>
                        {daysLeft}d left
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-500">
                        Due: {assignment.dueDate.toLocaleDateString()}
                      </span>
                      <button
                        onClick={() => handleAssignmentSubmit(assignment)}
                        className="text-xs text-purple-600 hover:text-purple-700 font-medium"
                      >
                        Submit →
                      </button>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>

          {/* Skills Radar */}
          <div className="bg-white rounded-2xl p-6 shadow-lg">
            <h2 className="text-lg font-bold text-gray-900 mb-6">Skills Assessment</h2>
            <ResponsiveContainer width="100%" height={250}>
              <RadarChart data={skillsData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="skill" />
                <PolarRadiusAxis angle={90} domain={[0, 100]} />
                <Radar name="Skills" dataKey="value" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.6} />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* Achievements */}
          <div className="bg-white rounded-2xl p-6 shadow-lg">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-gray-900">Achievements</h2>
              <Trophy className="h-5 w-5 text-yellow-500" />
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              {achievements.slice(0, 4).map((achievement) => (
                <motion.button
                  key={achievement.id}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => {
                    setSelectedAchievement(achievement);
                    setShowAchievementModal(true);
                  }}
                  className={`p-4 rounded-xl text-center transition-all ${
                    achievement.unlocked
                      ? 'bg-gradient-to-br from-yellow-50 to-orange-50 hover:from-yellow-100 hover:to-orange-100'
                      : 'bg-gray-100 opacity-50'
                  }`}
                >
                  <div className={`mb-2 ${achievement.unlocked ? 'text-yellow-600' : 'text-gray-400'}`}>
                    {achievement.icon}
                  </div>
                  <p className="text-xs font-semibold text-gray-900">{achievement.title}</p>
                  {!achievement.unlocked && (
                    <div className="mt-2">
                      <div className="w-full bg-gray-200 rounded-full h-1">
                        <div
                          className="h-1 bg-purple-600 rounded-full"
                          style={{ width: `${(achievement.progress / achievement.maxProgress) * 100}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {achievement.progress}/{achievement.maxProgress}
                      </p>
                    </div>
                  )}
                </motion.button>
              ))}
            </div>
            
            <CTALink
              to="/student-portal/achievements"
              variant="ghost"
              size="sm"
              className="w-full mt-4"
              showArrow
            >
              View All Achievements
            </CTALink>
          </div>

          {/* Study Groups */}
          <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl p-6 text-white">
            <h2 className="text-lg font-bold mb-4">Active Study Groups</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-white/20 backdrop-blur-xl rounded-xl">
                <div className="flex items-center space-x-3">
                  <Users className="h-5 w-5" />
                  <div>
                    <p className="font-semibold">DSA Problem Solving</p>
                    <p className="text-xs opacity-80">5 members online</p>
                  </div>
                </div>
                <button className="px-3 py-1 bg-white/30 rounded-lg text-sm hover:bg-white/40 transition-colors">
                  Join
                </button>
              </div>
              <div className="flex items-center justify-between p-3 bg-white/20 backdrop-blur-xl rounded-xl">
                <div className="flex items-center space-x-3">
                  <Users className="h-5 w-5" />
                  <div>
                    <p className="font-semibold">ML Study Group</p>
                    <p className="text-xs opacity-80">3 members online</p>
                  </div>
                </div>
                <button className="px-3 py-1 bg-white/30 rounded-lg text-sm hover:bg-white/40 transition-colors">
                  Join
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <>
      <Helmet>
        <title>Student Portal - Smart Campus</title>
        <meta name="description" content="Access your courses, grades, and academic resources" />
      </Helmet>

      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
        {/* Header */}
        <header className="bg-white border-b sticky top-0 z-40">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center space-x-8">
                <div className="flex items-center space-x-3">
                  <div className="h-10 w-10 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center">
                    <GraduationCap className="h-6 w-6 text-white" />
                  </div>
                  <span className="text-xl font-bold">Student Portal</span>
                </div>

                <nav className="hidden md:flex items-center space-x-1">
                  {[
                    { id: 'dashboard', label: 'Dashboard', icon: <Grid /> },
                    { id: 'courses', label: 'Courses', icon: <BookOpen /> },
                    { id: 'grades', label: 'Grades', icon: <TrendingUp /> },
                    { id: 'schedule', label: 'Schedule', icon: <Calendar /> },
                    { id: 'resources', label: 'Resources', icon: <Library /> }
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setSelectedTab(tab.id)}
                      className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all ${
                        selectedTab === tab.id
                          ? 'bg-purple-100 text-purple-700'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      {React.cloneElement(tab.icon, { className: 'h-4 w-4' })}
                      <span className="font-medium">{tab.label}</span>
                    </button>
                  ))}
                </nav>
              </div>

              <div className="flex items-center space-x-4">
                <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                  <Search className="h-5 w-5 text-gray-600" />
                </button>
                
                <button
                  onClick={() => setShowNotifications(!showNotifications)}
                  className="relative p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <Bell className="h-5 w-5 text-gray-600" />
                  {notifications.filter(n => !n.read).length > 0 && (
                    <span className="absolute top-0 right-0 h-2 w-2 bg-red-500 rounded-full" />
                  )}
                </button>

                <div className="flex items-center space-x-3">
                  <div className="text-right">
                    <p className="text-sm font-semibold text-gray-900">{user?.name}</p>
                    <p className="text-xs text-gray-500">ID: {user?.id || 'ST2024001'}</p>
                  </div>
                  <img
                    src={`https://ui-avatars.com/api/?name=${user?.name}&background=7c3aed&color=fff`}
                    alt={user?.name}
                    className="h-10 w-10 rounded-full"
                  />
                </div>

                <button
                  onClick={handleLogout}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  aria-label="Logout"
                >
                  <LogOut className="h-5 w-5 text-gray-600" />
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Notifications Dropdown */}
        <AnimatePresence>
          {showNotifications && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="absolute top-16 right-4 w-96 bg-white rounded-2xl shadow-2xl z-50 overflow-hidden"
            >
              <div className="p-4 border-b">
                <div className="flex items-center justify-between">
                  <h3 className="font-bold text-gray-900">Notifications</h3>
                  <button
                    onClick={() => setShowNotifications(false)}
                    className="p-1 hover:bg-gray-100 rounded-lg"
                  >
                    <X className="h-4 w-4 text-gray-500" />
                  </button>
                </div>
              </div>
              
              <div className="max-h-96 overflow-y-auto">
                {notifications.map((notification) => (
                  <div
                    key={notification.id}
                    onClick={() => markNotificationAsRead(notification.id)}
                    className={`p-4 border-b hover:bg-gray-50 cursor-pointer ${
                      !notification.read ? 'bg-blue-50' : ''
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      <div className={`h-2 w-2 rounded-full mt-2 ${
                        notification.type === 'success' ? 'bg-green-500' :
                        notification.type === 'warning' ? 'bg-yellow-500' :
                        notification.type === 'error' ? 'bg-red-500' :
                        'bg-blue-500'
                      }`} />
                      <div className="flex-1">
                        <p className="font-semibold text-gray-900 text-sm">{notification.title}</p>
                        <p className="text-xs text-gray-600 mt-1">{notification.message}</p>
                        <p className="text-xs text-gray-400 mt-2">
                          {new Date(notification.time).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="p-4 border-t">
                <CTALink
                  to="/student-portal/notifications"
                  variant="ghost"
                  size="sm"
                  className="w-full"
                >
                  View All Notifications
                </CTALink>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {selectedTab === 'dashboard' && renderDashboard()}
          
          {selectedTab === 'courses' && (
            <div>
              <h1 className="text-3xl font-bold mb-6">My Courses</h1>
              {/* Implement courses view */}
            </div>
          )}
          
          {selectedTab === 'grades' && (
            <div>
              <h1 className="text-3xl font-bold mb-6">Grades & Transcripts</h1>
              {/* Implement grades view */}
            </div>
          )}
          
          {selectedTab === 'schedule' && (
            <div>
              <h1 className="text-3xl font-bold mb-6">Class Schedule</h1>
              {/* Implement schedule view */}
            </div>
          )}
          
          {selectedTab === 'resources' && (
            <div>
              <h1 className="text-3xl font-bold mb-6">Learning Resources</h1>
              {/* Implement resources view */}
            </div>
          )}
        </main>

        {/* Achievement Modal */}
        <AnimatePresence>
          {showAchievementModal && selectedAchievement && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
              onClick={() => setShowAchievementModal(false)}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                className="bg-white rounded-3xl max-w-md w-full p-8"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="text-center">
                  <div className={`inline-flex items-center justify-center h-20 w-20 rounded-full mb-4 ${
                    selectedAchievement.unlocked
                      ? 'bg-gradient-to-r from-yellow-400 to-orange-400'
                      : 'bg-gray-200'
                  }`}>
                    <div className="text-white">
                      {selectedAchievement.icon}
                    </div>
                  </div>
                  
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    {selectedAchievement.title}
                  </h2>
                  
                  <p className="text-gray-600 mb-4">
                    {selectedAchievement.description}
                  </p>
                  
                  {!selectedAchievement.unlocked && (
                    <div className="mb-6">
                      <div className="flex items-center justify-between text-sm mb-2">
                        <span className="text-gray-600">Progress</span>
                        <span className="font-semibold">
                          {selectedAchievement.progress}/{selectedAchievement.maxProgress}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-3">
                        <div
                          className="h-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-full"
                          style={{ width: `${(selectedAchievement.progress / selectedAchievement.maxProgress) * 100}%` }}
                        />
                      </div>
                    </div>
                  )}
                  
                  <div className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-semibold ${
                    selectedAchievement.rarity === 'legendary' ? 'bg-purple-100 text-purple-700' :
                    selectedAchievement.rarity === 'epic' ? 'bg-blue-100 text-blue-700' :
                    selectedAchievement.rarity === 'rare' ? 'bg-green-100 text-green-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {selectedAchievement.rarity.toUpperCase()}
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

export default StudentPortal;