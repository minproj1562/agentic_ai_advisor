// src/pages/Departments.tsx
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, useParams } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import {
  Building,
  Users,
  GraduationCap,
  Award,
  BookOpen,
  Microscope,
  Code,
  Cpu,
  Atom,
  Palette,
  Heart,
  Briefcase,
  Calculator,
  Beaker, // Instead of Flask
  Globe,
  Languages,
  Music,
  Camera,
  Film,
  PenTool,
  Ruler,
  Wrench,
  Stethoscope,
  Scale,
  TreePine,
  Brain,
  CircuitBoard,
  Database,
  Network,
  Shield,
  Coins,
  TrendingUp,
  BarChart3,
  Search,
  Filter,
  Grid,
  List,
  MapPin,
  Phone,
  Mail,
  Calendar,
  Clock,
  Star,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ArrowRight,
  ExternalLink,
  Download,
  Share2,
  Bookmark,
  MessageSquare,
  Video,
  FileText,
  Trophy,
  Target,
  Eye,
  CheckCircle,
  X,
  Plus,
  User,
  Linkedin,
  Twitter,
  Github,
  Send
} from 'lucide-react';
import CTALink from '../components/common/CTALink';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

// Types
interface Faculty {
  id: string;
  name: string;
  designation: string;
  qualification: string;
  specialization: string[];
  experience: number;
  image: string;
  email: string;
  phone: string;
  office: string;
  consultationHours: string;
  publications: number;
  citations: number;
  hIndex: number;
  courses: string[];
  research: string[];
  awards: string[];
  social?: {
    linkedin?: string;
    twitter?: string;
    github?: string;
    scholar?: string;
  };
}

interface Course {
  id: string;
  code: string;
  name: string;
  credits: number;
  duration: string;
  level: 'undergraduate' | 'postgraduate' | 'doctoral';
  semester: number;
  instructor: string;
  schedule: string;
  enrolled: number;
  capacity: number;
  description: string;
  prerequisites: string[];
  outcomes: string[];
  syllabus: string;
}

interface ResearchArea {
  id: string;
  title: string;
  description: string;
  lead: string;
  members: number;
  projects: number;
  funding: string;
  publications: number;
  collaborations: string[];
  image: string;
}

interface Achievement {
  id: string;
  title: string;
  description: string;
  date: Date;
  category: 'award' | 'ranking' | 'research' | 'student';
  icon: React.ReactNode;
}

interface Department {
  id: string;
  name: string;
  code: string;
  description: string;
  established: number;
  vision: string;
  mission: string;
  icon: React.ReactNode;
  color: string;
  image: string;
  head: {
    name: string;
    image: string;
    qualification: string;
    message: string;
  };
  stats: {
    faculty: number;
    students: number;
    courses: number;
    research: number;
    publications: number;
    placements: number;
  };
  programs: {
    undergraduate: string[];
    postgraduate: string[];
    doctoral: string[];
    certificate: string[];
  };
  facilities: string[];
  achievements: Achievement[];
  faculty: Faculty[];
  courses: Course[];
  researchAreas: ResearchArea[];
  industryPartners: string[];
  alumniCompanies: string[];
  contact: {
    email: string;
    phone: string;
    location: string;
    hours: string;
  };
}

// Departments data
const departmentsData: Department[] = [
  {
    id: 'computer-science',
    name: 'Computer Science & Engineering',
    code: 'CSE',
    description: 'Leading the digital transformation with cutting-edge research in AI, ML, and emerging technologies',
    established: 1985,
    vision: 'To be a globally recognized center of excellence in computer science education and research',
    mission: 'To produce innovative technologists and researchers who can solve complex real-world problems',
    icon: <Code className="h-6 w-6" />,
    color: 'from-blue-500 to-indigo-600',
    image: 'https://images.unsplash.com/photo-1517077304055-6e89abbf09b0?w=800',
    head: {
      name: 'Dr. Sarah Johnson',
      image: 'https://ui-avatars.com/api/?name=Sarah+Johnson&background=6366f1&color=fff',
      qualification: 'Ph.D. (MIT), M.Tech (IIT Delhi)',
      message: 'Welcome to the Department of Computer Science, where innovation meets excellence.'
    },
    stats: {
      faculty: 45,
      students: 1200,
      courses: 68,
      research: 25,
      publications: 342,
      placements: 95
    },
    programs: {
      undergraduate: ['B.Tech Computer Science', 'B.Tech AI & ML', 'B.Tech Data Science'],
      postgraduate: ['M.Tech Computer Science', 'M.Tech AI', 'M.Tech Cybersecurity'],
      doctoral: ['Ph.D. Computer Science', 'Ph.D. Artificial Intelligence'],
      certificate: ['Full Stack Development', 'Machine Learning', 'Cloud Computing']
    },
    facilities: [
      'AI Research Lab',
      'High-Performance Computing Center',
      'Cybersecurity Lab',
      'IoT Lab',
      'Blockchain Lab',
      'Virtual Reality Lab',
      'Robotics Lab',
      '24/7 Computing Facility'
    ],
    achievements: [
      {
        id: '1',
        title: 'Best CS Department Award',
        description: 'Ranked #1 in the state for CS education',
        date: new Date('2024-01-15'),
        category: 'award',
        icon: <Trophy className="h-6 w-6" />
      },
      {
        id: '2',
        title: '₹10 Crore Research Grant',
        description: 'Received major funding for AI research',
        date: new Date('2023-12-01'),
        category: 'research',
        icon: <Award className="h-6 w-6" />
      }
    ],
    faculty: [
      {
        id: '1',
        name: 'Dr. Sarah Johnson',
        designation: 'Professor & Head',
        qualification: 'Ph.D. (MIT)',
        specialization: ['Artificial Intelligence', 'Machine Learning', 'Deep Learning'],
        experience: 20,
        image: 'https://ui-avatars.com/api/?name=Sarah+Johnson&background=6366f1&color=fff',
        email: 'sarah.johnson@university.edu',
        phone: '+91 98765 43210',
        office: 'Room 301, CS Building',
        consultationHours: 'Mon & Wed, 3-5 PM',
        publications: 156,
        citations: 4532,
        hIndex: 42,
        courses: ['CS301', 'CS401', 'CS501'],
        research: ['Deep Learning', 'Computer Vision', 'NLP'],
        awards: ['Best Teacher Award 2023', 'Research Excellence Award 2022'],
        social: {
          linkedin: 'https://linkedin.com',
          scholar: 'https://scholar.google.com'
        }
      },
      {
        id: '2',
        name: 'Prof. Michael Chen',
        designation: 'Associate Professor',
        qualification: 'Ph.D. (Stanford)',
        specialization: ['Cybersecurity', 'Blockchain', 'Cryptography'],
        experience: 15,
        image: 'https://ui-avatars.com/api/?name=Michael+Chen&background=6366f1&color=fff',
        email: 'michael.chen@university.edu',
        phone: '+91 98765 43211',
        office: 'Room 302, CS Building',
        consultationHours: 'Tue & Thu, 2-4 PM',
        publications: 98,
        citations: 2341,
        hIndex: 28,
        courses: ['CS302', 'CS402'],
        research: ['Blockchain Security', 'Quantum Cryptography'],
        awards: ['Innovation Award 2023'],
        social: {
          linkedin: 'https://linkedin.com',
          github: 'https://github.com',
          twitter: 'https://twitter.com'
        }
      }
    ],
    courses: [
      {
        id: '1',
        code: 'CS301',
        name: 'Data Structures & Algorithms',
        credits: 4,
        duration: '1 Semester',
        level: 'undergraduate',
        semester: 3,
        instructor: 'Dr. Sarah Johnson',
        schedule: 'Mon, Wed, Fri - 10:00 AM',
        enrolled: 120,
        capacity: 150,
        description: 'Comprehensive study of data structures and algorithm design',
        prerequisites: ['CS101', 'CS201'],
        outcomes: [
          'Master fundamental data structures',
          'Design efficient algorithms',
          'Analyze time and space complexity'
        ],
        syllabus: '/syllabus/CS301.pdf'
      }
    ],
    researchAreas: [
      {
        id: '1',
        title: 'Artificial Intelligence & Machine Learning',
        description: 'Cutting-edge research in deep learning, computer vision, and NLP',
        lead: 'Dr. Sarah Johnson',
        members: 25,
        projects: 12,
        funding: '₹5 Crore',
        publications: 89,
        collaborations: ['MIT', 'Stanford', 'IIT Delhi'],
        image: 'https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=400'
      }
    ],
    industryPartners: ['Google', 'Microsoft', 'Amazon', 'Adobe', 'IBM'],
    alumniCompanies: ['Google', 'Facebook', 'Apple', 'Netflix', 'Uber'],
    contact: {
      email: 'cse@university.edu',
      phone: '+91 98765 43200',
      location: 'CS Building, Main Campus',
      hours: 'Mon-Fri, 9 AM - 5 PM'
    }
  },
  {
    id: 'engineering',
    name: 'Mechanical Engineering',
    code: 'ME',
    description: 'Pioneering innovations in robotics, automation, and sustainable engineering',
    established: 1980,
    vision: 'To lead in mechanical engineering education and research for sustainable development',
    mission: 'To develop engineers who can design and build the future',
    icon: <Wrench className="h-6 w-6" />,
    color: 'from-orange-500 to-red-600',
    image: 'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=800',
    head: {
      name: 'Dr. Robert Williams',
      image: 'https://ui-avatars.com/api/?name=Robert+Williams&background=f97316&color=fff',
      qualification: 'Ph.D. (Cambridge), M.Tech (IIT Bombay)',
      message: 'Engineering the future with innovation and sustainability.'
    },
    stats: {
      faculty: 38,
      students: 950,
      courses: 52,
      research: 18,
      publications: 276,
      placements: 92
    },
    programs: {
      undergraduate: ['B.Tech Mechanical Engineering', 'B.Tech Robotics', 'B.Tech Aerospace'],
      postgraduate: ['M.Tech Mechanical', 'M.Tech Thermal', 'M.Tech Design'],
      doctoral: ['Ph.D. Mechanical Engineering'],
      certificate: ['CAD/CAM', 'Robotics', 'Industry 4.0']
    },
    facilities: [
      'Advanced Manufacturing Lab',
      'Robotics Lab',
      'Wind Tunnel',
      'Material Testing Lab',
      'CAD/CAM Center',
      'Thermal Lab',
      '3D Printing Facility',
      'Automation Lab'
    ],
    achievements: [],
    faculty: [],
    courses: [],
    researchAreas: [],
    industryPartners: ['Tesla', 'Boeing', 'General Electric', 'Siemens'],
    alumniCompanies: ['Tesla', 'SpaceX', 'Boeing', 'Airbus'],
    contact: {
      email: 'mech@university.edu',
      phone: '+91 98765 43201',
      location: 'Mechanical Building, Main Campus',
      hours: 'Mon-Fri, 9 AM - 5 PM'
    }
  },
  {
    id: 'business',
    name: 'School of Business',
    code: 'SOB',
    description: 'Developing future business leaders with global perspective and entrepreneurial mindset',
    established: 1990,
    vision: 'To be a premier business school creating ethical and innovative leaders',
    mission: 'To provide transformative business education that creates value for society',
    icon: <Briefcase className="h-6 w-6" />,
    color: 'from-green-500 to-emerald-600',
    image: 'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800',
    head: {
      name: 'Dr. Emily Roberts',
      image: 'https://ui-avatars.com/api/?name=Emily+Roberts&background=10b981&color=fff',
      qualification: 'Ph.D. (Harvard), MBA (Wharton)',
      message: 'Building tomorrow\'s business leaders today.'
    },
    stats: {
      faculty: 32,
      students: 800,
      courses: 45,
      research: 15,
      publications: 198,
      placements: 98
    },
    programs: {
      undergraduate: ['BBA', 'B.Com (Hons)', 'BBA Analytics'],
      postgraduate: ['MBA', 'MBA Finance', 'MBA Marketing', 'MBA Analytics'],
      doctoral: ['Ph.D. Management', 'Ph.D. Finance'],
      certificate: ['Digital Marketing', 'Financial Analysis', 'Entrepreneurship']
    },
    facilities: [
      'Bloomberg Terminal',
      'Business Analytics Lab',
      'Entrepreneurship Cell',
      'Case Study Rooms',
      'Trading Floor Simulation',
      'Executive Learning Center',
      'Innovation Hub',
      'Conference Center'
    ],
    achievements: [],
    faculty: [],
    courses: [],
    researchAreas: [],
    industryPartners: ['McKinsey', 'BCG', 'Deloitte', 'Goldman Sachs'],
    alumniCompanies: ['McKinsey', 'Google', 'Amazon', 'JP Morgan'],
    contact: {
      email: 'business@university.edu',
      phone: '+91 98765 43202',
      location: 'Business School Building, Main Campus',
      hours: 'Mon-Fri, 9 AM - 5 PM'
    }
  }
];

const Departments: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const { user } = useAuth();

  // State
  const [departments] = useState(departmentsData);
  const [selectedDepartment, setSelectedDepartment] = useState<Department | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [selectedFaculty, setSelectedFaculty] = useState<Faculty | null>(null);
  const [expandedSections, setExpandedSections] = useState<string[]>(['programs']);
  const [bookmarkedDepartments, setBookmarkedDepartments] = useState<string[]>([]);

  // Load department if ID is provided
  useEffect(() => {
    if (id) {
      const dept = departments.find(d => d.id === id);
      if (dept) {
        setSelectedDepartment(dept);
      }
    }
  }, [id, departments]);

  // Toggle section expansion
  const toggleSection = (section: string) => {
    setExpandedSections(prev =>
      prev.includes(section)
        ? prev.filter(s => s !== section)
        : [...prev, section]
    );
  };

  // Toggle bookmark
  const toggleBookmark = (deptId: string) => {
    setBookmarkedDepartments(prev =>
      prev.includes(deptId)
        ? prev.filter(id => id !== deptId)
        : [...prev, deptId]
    );
    toast.success(
      bookmarkedDepartments.includes(deptId)
        ? 'Removed from bookmarks'
        : 'Added to bookmarks'
    );
  };

  // Handle faculty contact
  const handleFacultyContact = (faculty: Faculty) => {
    setSelectedFaculty(faculty);
    toast.success('Contact information displayed');
  };

  // Handle course enrollment
  const handleCourseEnroll = (course: Course) => {
    navigate(`/courses/${course.code}`);
  };

  // Download syllabus
  const handleDownloadSyllabus = (course: Course) => {
    toast.success(`Downloading syllabus for ${course.name}`);
  };

  // Render department overview
  const renderDepartmentOverview = (dept: Department) => (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="relative h-64 md:h-96 rounded-3xl overflow-hidden">
        <img
          src={dept.image}
          alt={dept.name}
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent" />
        <div className="absolute bottom-0 left-0 right-0 p-8 text-white">
          <div className="flex items-center space-x-4 mb-4">
            <div className={`h-16 w-16 bg-gradient-to-r ${dept.color} rounded-2xl flex items-center justify-center`}>
              {dept.icon}
            </div>
            <div>
              <h1 className="text-4xl font-bold">{dept.name}</h1>
              <p className="text-lg opacity-90">Established {dept.established}</p>
            </div>
          </div>
          <p className="text-lg opacity-90 max-w-3xl">{dept.description}</p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {Object.entries(dept.stats).map(([key, value]) => (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-xl p-4 shadow-lg text-center"
          >
            <div className="text-3xl font-bold text-purple-600">
              {key === 'placements' ? `${value}%` : value}
            </div>
            <div className="text-sm text-gray-600 capitalize">
              {key.replace(/([A-Z])/g, ' $1').trim()}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Department Head Message */}
      <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-2xl p-8">
        <div className="flex items-start space-x-6">
          <img
            src={dept.head.image}
            alt={dept.head.name}
            className="h-24 w-24 rounded-full object-cover"
          />
          <div className="flex-1">
            <h3 className="text-xl font-bold text-gray-900 mb-1">Message from the Head</h3>
            <p className="text-gray-600 mb-2">
              {dept.head.name} • {dept.head.qualification}
            </p>
            <p className="text-gray-700 italic">"{dept.head.message}"</p>
          </div>
        </div>
      </div>

      {/* Vision & Mission */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl p-6 shadow-lg">
          <div className="flex items-center mb-4">
            <Eye className="h-6 w-6 text-purple-600 mr-3" />
            <h3 className="text-xl font-bold text-gray-900">Vision</h3>
          </div>
          <p className="text-gray-700">{dept.vision}</p>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-lg">
          <div className="flex items-center mb-4">
            <Target className="h-6 w-6 text-purple-600 mr-3" />
            <h3 className="text-xl font-bold text-gray-900">Mission</h3>
          </div>
          <p className="text-gray-700">{dept.mission}</p>
        </div>
      </div>

      {/* Programs Offered */}
      <div className="bg-white rounded-2xl p-6 shadow-lg">
        <button
          onClick={() => toggleSection('programs')}
          className="w-full flex items-center justify-between mb-4"
        >
          <h3 className="text-xl font-bold text-gray-900 flex items-center">
            <GraduationCap className="h-6 w-6 text-purple-600 mr-3" />
            Programs Offered
          </h3>
          {expandedSections.includes('programs') ? (
            <ChevronUp className="h-5 w-5 text-gray-500" />
          ) : (
            <ChevronDown className="h-5 w-5 text-gray-500" />
          )}
        </button>
        
        <AnimatePresence>
          {expandedSections.includes('programs') && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="grid md:grid-cols-2 lg:grid-cols-4 gap-6"
            >
              {Object.entries(dept.programs).map(([level, programs]) => (
                <div key={level}>
                  <h4 className="font-semibold text-gray-900 mb-3 capitalize">
                    {level.replace(/([A-Z])/g, ' $1').trim()}
                  </h4>
                  <ul className="space-y-2">
                    {programs.map((program, index) => (
                      <li key={index} className="flex items-start">
                        <CheckCircle className="h-4 w-4 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                        <span className="text-sm text-gray-600">{program}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Facilities */}
      <div className="bg-white rounded-2xl p-6 shadow-lg">
        <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
          <Building className="h-6 w-6 text-purple-600 mr-3" />
          Facilities & Infrastructure
        </h3>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-3">
          {dept.facilities.map((facility, index) => (
            <div
              key={index}
              className="flex items-center p-3 bg-purple-50 rounded-xl"
            >
              <CheckCircle className="h-5 w-5 text-purple-600 mr-2 flex-shrink-0" />
              <span className="text-sm text-gray-700">{facility}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Industry Partners */}
      <div className="bg-white rounded-2xl p-6 shadow-lg">
        <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
          <Briefcase className="h-6 w-6 text-purple-600 mr-3" />
          Industry Partners
        </h3>
        <div className="flex flex-wrap gap-4">
          {dept.industryPartners.map((partner, index) => (
            <div
              key={index}
              className="px-4 py-2 bg-gray-100 rounded-lg font-medium text-gray-700"
            >
              {partner}
            </div>
          ))}
        </div>
      </div>

      {/* Recent Achievements */}
      {dept.achievements.length > 0 && (
        <div className="bg-white rounded-2xl p-6 shadow-lg">
          <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
            <Trophy className="h-6 w-6 text-purple-600 mr-3" />
            Recent Achievements
          </h3>
          <div className="space-y-4">
            {dept.achievements.map((achievement) => (
              <div
                key={achievement.id}
                className="flex items-start space-x-4 p-4 bg-gradient-to-r from-yellow-50 to-orange-50 rounded-xl"
              >
                <div className="flex-shrink-0 h-10 w-10 bg-yellow-500 rounded-xl flex items-center justify-center text-white">
                  {achievement.icon}
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900">{achievement.title}</h4>
                  <p className="text-sm text-gray-600">{achievement.description}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {achievement.date.toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  // Render faculty tab
  const renderFacultyTab = (dept: Department) => (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Faculty Members</h2>
        <div className="flex items-center space-x-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search faculty..."
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
        </div>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {dept.faculty.map((faculty) => (
          <motion.div
            key={faculty.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ y: -5 }}
            className="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-xl transition-all"
          >
            <div className="p-6">
              <div className="flex items-start space-x-4 mb-4">
                <img
                  src={faculty.image}
                  alt={faculty.name}
                  className="h-16 w-16 rounded-full object-cover"
                />
                <div className="flex-1">
                  <h3 className="font-bold text-gray-900">{faculty.name}</h3>
                  <p className="text-sm text-gray-600">{faculty.designation}</p>
                  <p className="text-xs text-gray-500">{faculty.qualification}</p>
                </div>
              </div>

              <div className="space-y-3 mb-4">
                <div className="text-sm">
                  <span className="text-gray-600">Specialization:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {faculty.specialization.map((spec, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full"
                      >
                        {spec}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center">
                  <div>
                    <div className="text-lg font-bold text-purple-600">{faculty.publications}</div>
                    <div className="text-xs text-gray-500">Publications</div>
                  </div>
                  <div>
                    <div className="text-lg font-bold text-purple-600">{faculty.hIndex}</div>
                    <div className="text-xs text-gray-500">h-index</div>
                  </div>
                  <div>
                    <div className="text-lg font-bold text-purple-600">{faculty.experience}</div>
                    <div className="text-xs text-gray-500">Years</div>
                  </div>
                </div>

                <div className="text-sm space-y-1">
                  <div className="flex items-center text-gray-600">
                    <Mail className="h-4 w-4 mr-2" />
                    <span className="text-xs">{faculty.email}</span>
                  </div>
                  <div className="flex items-center text-gray-600">
                    <MapPin className="h-4 w-4 mr-2" />
                    <span className="text-xs">{faculty.office}</span>
                  </div>
                  <div className="flex items-center text-gray-600">
                    <Clock className="h-4 w-4 mr-2" />
                    <span className="text-xs">{faculty.consultationHours}</span>
                  </div>
                </div>
              </div>

              <div className="flex space-x-2">
                <button
                  onClick={() => handleFacultyContact(faculty)}
                  className="flex-1 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 transition-colors"
                >
                  Contact
                </button>
                <button
                  className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  <ExternalLink className="h-4 w-4" />
                </button>
              </div>

              {faculty.social && (
                <div className="flex items-center justify-center space-x-3 mt-3 pt-3 border-t">
                  {faculty.social.linkedin && (
                    <a href={faculty.social.linkedin} target="_blank" rel="noopener noreferrer">
                      <Linkedin className="h-4 w-4 text-gray-500 hover:text-blue-600" />
                    </a>
                  )}
                  {faculty.social.twitter && (
                    <a href={faculty.social.twitter} target="_blank" rel="noopener noreferrer">
                      <Twitter className="h-4 w-4 text-gray-500 hover:text-blue-400" />
                    </a>
                  )}
                  {faculty.social.github && (
                    <a href={faculty.social.github} target="_blank" rel="noopener noreferrer">
                      <Github className="h-4 w-4 text-gray-500 hover:text-gray-900" />
                    </a>
                  )}
                </div>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );

  // Render courses tab
  const renderCoursesTab = (dept: Department) => (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Courses Offered</h2>
        <div className="flex items-center space-x-3">
          <select className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500">
            <option>All Levels</option>
            <option>Undergraduate</option>
            <option>Postgraduate</option>
            <option>Doctoral</option>
          </select>
        </div>
      </div>

      <div className="space-y-4">
        {dept.courses.map((course) => (
          <motion.div
            key={course.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white rounded-2xl shadow-lg p-6 hover:shadow-xl transition-all"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <span className="px-3 py-1 bg-purple-100 text-purple-700 text-sm font-bold rounded-full">
                    {course.code}
                  </span>
                  <span className="px-3 py-1 bg-green-100 text-green-700 text-sm font-medium rounded-full">
                    {course.credits} Credits
                  </span>
                  <span className="px-3 py-1 bg-blue-100 text-blue-700 text-sm font-medium rounded-full capitalize">
                    {course.level}
                  </span>
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">{course.name}</h3>
                <p className="text-gray-600 mb-3">{course.description}</p>
                
                <div className="grid md:grid-cols-2 gap-4 mb-4">
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center text-gray-600">
                      <User className="h-4 w-4 mr-2" />
                      Instructor: {course.instructor}
                    </div>
                    <div className="flex items-center text-gray-600">
                      <Calendar className="h-4 w-4 mr-2" />
                      Schedule: {course.schedule}
                    </div>
                    <div className="flex items-center text-gray-600">
                      <Users className="h-4 w-4 mr-2" />
                      Enrolled: {course.enrolled}/{course.capacity}
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <h4 className="font-semibold text-gray-900">Prerequisites:</h4>
                    <div className="flex flex-wrap gap-2">
                      {course.prerequisites.map((prereq, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded"
                        >
                          {prereq}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="flex space-x-3">
                  <button
                    onClick={() => handleCourseEnroll(course)}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors"
                  >
                    Enroll Now
                  </button>
                  <button
                    onClick={() => handleDownloadSyllabus(course)}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors flex items-center"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Syllabus
                  </button>
                </div>
              </div>
              
              <div className="ml-6">
                <div className="text-center">
                  <div className="relative h-20 w-20">
                    <svg className="transform -rotate-90 h-20 w-20">
                      <circle
                        cx="40"
                        cy="40"
                        r="36"
                        stroke="currentColor"
                        strokeWidth="8"
                        fill="none"
                        className="text-gray-200"
                      />
                      <circle
                        cx="40"
                        cy="40"
                        r="36"
                        stroke="currentColor"
                        strokeWidth="8"
                        fill="none"
                        strokeDasharray={2 * Math.PI * 36}
                        strokeDashoffset={2 * Math.PI * 36 * (1 - course.enrolled / course.capacity)}
                        className="text-purple-600"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-sm font-bold">
                        {Math.round((course.enrolled / course.capacity) * 100)}%
                      </span>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">Filled</p>
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );

  // Render research tab
  const renderResearchTab = (dept: Department) => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Research Areas</h2>
      
      <div className="grid md:grid-cols-2 gap-6">
        {dept.researchAreas.map((research) => (
          <motion.div
            key={research.id}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            whileHover={{ scale: 1.02 }}
            className="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-xl transition-all"
          >
            <div className="h-48 overflow-hidden">
              <img
                src={research.image}
                alt={research.title}
                className="w-full h-full object-cover"
              />
            </div>
            <div className="p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-2">{research.title}</h3>
              <p className="text-gray-600 mb-4">{research.description}</p>
              
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="text-center p-2 bg-purple-50 rounded-lg">
                  <div className="text-lg font-bold text-purple-600">{research.projects}</div>
                  <div className="text-xs text-gray-600">Active Projects</div>
                </div>
                <div className="text-center p-2 bg-green-50 rounded-lg">
                  <div className="text-lg font-bold text-green-600">{research.funding}</div>
                  <div className="text-xs text-gray-600">Funding</div>
                </div>
                <div className="text-center p-2 bg-blue-50 rounded-lg">
                  <div className="text-lg font-bold text-blue-600">{research.publications}</div>
                  <div className="text-xs text-gray-600">Publications</div>
                </div>
                <div className="text-center p-2 bg-orange-50 rounded-lg">
                  <div className="text-lg font-bold text-orange-600">{research.members}</div>
                  <div className="text-xs text-gray-600">Researchers</div>
                </div>
              </div>
              
              <div className="mb-4">
                <p className="text-sm text-gray-600 mb-2">
                  <span className="font-semibold">Lead:</span> {research.lead}
                </p>
                <p className="text-sm text-gray-600">
                  <span className="font-semibold">Collaborations:</span> {research.collaborations.join(', ')}
                </p>
              </div>
              
              <CTALink
                to={`/research/${research.id}`}
                variant="primary"
                size="sm"
                className="w-full"
              >
                Explore Research
              </CTALink>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );

  return (
    <>
      <Helmet>
        <title>{selectedDepartment ? selectedDepartment.name + ' - ' : ''}Departments - Smart Campus</title>
        <meta name="description" content="Explore our academic departments and their offerings" />
      </Helmet>

      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
        {!selectedDepartment ? (
          // Departments List View
          <>
            <section className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white py-20">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-center"
                >
                  <h1 className="text-5xl font-bold mb-6">Academic Departments</h1>
                  <p className="text-xl text-white/90 max-w-3xl mx-auto">
                    Explore our world-class departments offering cutting-edge education and research opportunities
                  </p>
                </motion.div>
              </div>
            </section>

            <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center space-x-4">
                  <button
                    onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    {viewMode === 'grid' ? <List className="h-5 w-5" /> : <Grid className="h-5 w-5" />}
                  </button>
                </div>
                
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search departments..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>

              <div className={viewMode === 'grid' ? 'grid md:grid-cols-2 lg:grid-cols-3 gap-6' : 'space-y-6'}>
                {departments
                  .filter(dept => 
                    dept.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                    dept.description.toLowerCase().includes(searchQuery.toLowerCase())
                  )
                  .map((dept, index) => (
                    <motion.div
                      key={dept.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      whileHover={{ y: -5 }}
                      className="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-2xl transition-all"
                    >
                      <div className="h-48 relative overflow-hidden">
                        <img
                          src={dept.image}
                          alt={dept.name}
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                        <div className="absolute top-4 right-4">
                          <button
                            onClick={() => toggleBookmark(dept.id)}
                            className={`p-2 rounded-lg backdrop-blur-sm ${
                              bookmarkedDepartments.includes(dept.id)
                                ? 'bg-purple-600 text-white'
                                : 'bg-white/90 text-gray-700'
                            }`}
                          >
                            <Bookmark className={`h-5 w-5 ${
                              bookmarkedDepartments.includes(dept.id) ? 'fill-current' : ''
                            }`} />
                          </button>
                        </div>
                        <div className="absolute bottom-4 left-4">
                          <div className={`h-12 w-12 bg-gradient-to-r ${dept.color} rounded-xl flex items-center justify-center text-white`}>
                            {dept.icon}
                          </div>
                        </div>
                      </div>
                      
                      <div className="p-6">
                        <h3 className="text-xl font-bold text-gray-900 mb-2">{dept.name}</h3>
                        <p className="text-gray-600 mb-4 line-clamp-2">{dept.description}</p>
                        
                        <div className="grid grid-cols-3 gap-3 mb-4">
                          <div className="text-center">
                            <div className="text-lg font-bold text-purple-600">{dept.stats.faculty}</div>
                            <div className="text-xs text-gray-500">Faculty</div>
                          </div>
                          <div className="text-center">
                            <div className="text-lg font-bold text-purple-600">{dept.stats.students}</div>
                            <div className="text-xs text-gray-500">Students</div>
                          </div>
                          <div className="text-center">
                            <div className="text-lg font-bold text-purple-600">{dept.stats.courses}</div>
                            <div className="text-xs text-gray-500">Courses</div>
                          </div>
                        </div>
                        
                        <CTALink
                          to={`/departments/${dept.id}`}
                          variant="primary"
                          size="sm"
                          className="w-full"
                        >
                          Explore Department
                        </CTALink>
                      </div>
                    </motion.div>
                  ))}
              </div>
            </section>
          </>
        ) : (
          // Department Detail View
          <div>
            <div className="bg-white border-b sticky top-0 z-30">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between py-4">
                  <div className="flex items-center space-x-4">
                    <button
                      onClick={() => {
                        setSelectedDepartment(null);
                        navigate('/departments');
                      }}
                      className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      <ChevronLeft className="h-5 w-5" />
                    </button>
                    <nav className="flex space-x-1">
                      {['overview', 'faculty', 'courses', 'research', 'contact'].map((tab) => (
                        <button
                          key={tab}
                          onClick={() => setActiveTab(tab)}
                          className={`px-4 py-2 rounded-lg font-medium capitalize transition-all ${
                            activeTab === tab
                              ? 'bg-purple-100 text-purple-700'
                              : 'text-gray-600 hover:bg-gray-100'
                          }`}
                        >
                          {tab}
                        </button>
                      ))}
                    </nav>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <button
                      onClick={() => toggleBookmark(selectedDepartment.id)}
                      className={`p-2 rounded-lg transition-colors ${
                        bookmarkedDepartments.includes(selectedDepartment.id)
                          ? 'bg-purple-100 text-purple-600'
                          : 'hover:bg-gray-100 text-gray-600'
                      }`}
                    >
                      <Bookmark className={`h-5 w-5 ${
                        bookmarkedDepartments.includes(selectedDepartment.id) ? 'fill-current' : ''
                      }`} />
                    </button>
                    <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-600">
                      <Share2 className="h-5 w-5" />
                    </button>
                    <CTALink
                      to="/admissions"
                      variant="primary"
                      size="sm"
                    >
                      Apply Now
                    </CTALink>
                  </div>
                </div>
              </div>
            </div>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
              {activeTab === 'overview' && renderDepartmentOverview(selectedDepartment)}
              {activeTab === 'faculty' && renderFacultyTab(selectedDepartment)}
              {activeTab === 'courses' && renderCoursesTab(selectedDepartment)}
              {activeTab === 'research' && renderResearchTab(selectedDepartment)}
              {activeTab === 'contact' && (
                <div className="bg-white rounded-2xl shadow-lg p-8">
                  <h2 className="text-2xl font-bold text-gray-900 mb-6">Contact Information</h2>
                  <div className="grid md:grid-cols-2 gap-8">
                    <div className="space-y-4">
                      <div className="flex items-start space-x-3">
                        <Mail className="h-5 w-5 text-purple-600 mt-1" />
                        <div>
                          <p className="font-semibold text-gray-900">Email</p>
                          <a href={`mailto:${selectedDepartment.contact.email}`} className="text-purple-600 hover:underline">
                            {selectedDepartment.contact.email}
                          </a>
                        </div>
                      </div>
                      <div className="flex items-start space-x-3">
                        <Phone className="h-5 w-5 text-purple-600 mt-1" />
                        <div>
                          <p className="font-semibold text-gray-900">Phone</p>
                          <a href={`tel:${selectedDepartment.contact.phone}`} className="text-purple-600 hover:underline">
                            {selectedDepartment.contact.phone}
                          </a>
                        </div>
                      </div>
                      <div className="flex items-start space-x-3">
                        <MapPin className="h-5 w-5 text-purple-600 mt-1" />
                        <div>
                          <p className="font-semibold text-gray-900">Location</p>
                          <p className="text-gray-600">{selectedDepartment.contact.location}</p>
                        </div>
                      </div>
                      <div className="flex items-start space-x-3">
                        <Clock className="h-5 w-5 text-purple-600 mt-1" />
                        <div>
                          <p className="font-semibold text-gray-900">Office Hours</p>
                          <p className="text-gray-600">{selectedDepartment.contact.hours}</p>
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <form className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Your Name
                          </label>
                          <input
                            type="text"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Email
                          </label>
                          <input
                            type="email"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Message
                          </label>
                          <textarea
                            rows={4}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          />
                        </div>
                        <button
                          type="submit"
                          className="w-full py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors"
                        >
                          Send Message
                        </button>
                      </form>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default Departments;