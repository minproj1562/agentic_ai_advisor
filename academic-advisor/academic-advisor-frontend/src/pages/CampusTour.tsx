// src/pages/CampusTour.tsx
import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Helmet } from 'react-helmet-async';
import { 
  Play, 
  Pause, 
  Volume2, 
  VolumeX,
  Maximize,
  RotateCw,
  Info,
  MapPin,
  Navigation,
  Camera,
  ChevronLeft,
  ChevronRight,
  Grid,
  Eye,
  Download,
  Share2,
  Heart,
  MessageCircle,
  Bookmark,
  Clock,
  Users,
  Building,
  TreePine,
  Wifi,
  Coffee,
  BookOpen,
  Activity,
  Award
} from 'lucide-react';
import CTALink from '../components/common/CTALink';
import { useAnalytics } from '../hooks/useAnalytics';
import toast from 'react-hot-toast';

// 360° Tour locations with metadata
const tourLocations = [
  {
    id: 'main-entrance',
    name: 'Main Entrance',
    description: 'Welcome to our state-of-the-art campus',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    image360: '/images/360/entrance.jpg',
    coordinates: { lat: 28.6139, lng: 77.2090 },
    hotspots: [
      { x: 30, y: 40, label: 'Reception', link: '#reception' },
      { x: 60, y: 50, label: 'Security Office', link: '#security' },
    ],
    stats: {
      visitors: '5000+ daily',
      security: '24/7 monitoring',
      accessibility: 'Fully accessible',
    },
    features: ['Biometric Entry', 'Visitor Management', 'Emergency Response'],
  },
  {
    id: 'library',
    name: 'Digital Library',
    description: '24/7 access to millions of resources',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    image360: '/images/360/library.jpg',
    coordinates: { lat: 28.6140, lng: 77.2091 },
    hotspots: [
      { x: 40, y: 30, label: 'Study Pods', link: '#study-pods' },
      { x: 70, y: 60, label: 'Digital Archives', link: '#archives' },
    ],
    stats: {
      books: '1M+ e-books',
      studySpaces: '500+ seats',
      computers: '200+ workstations',
    },
    features: ['AI Book Finder', 'Silent Zones', 'Group Study Rooms'],
  },
  {
    id: 'labs',
    name: 'Research Labs',
    description: 'Cutting-edge research facilities',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    image360: '/images/360/labs.jpg',
    coordinates: { lat: 28.6141, lng: 77.2092 },
    hotspots: [
      { x: 25, y: 45, label: 'AI Lab', link: '#ai-lab' },
      { x: 55, y: 35, label: 'Robotics Center', link: '#robotics' },
      { x: 80, y: 55, label: 'Biotech Lab', link: '#biotech' },
    ],
    stats: {
      equipment: '$10M+ worth',
      projects: '200+ ongoing',
      publications: '500+ annually',
    },
    features: ['3D Printing', 'Clean Rooms', 'Supercomputer Access'],
  },
  {
    id: 'auditorium',
    name: 'Grand Auditorium',
    description: 'World-class event space',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    image360: '/images/360/auditorium.jpg',
    coordinates: { lat: 28.6142, lng: 77.2093 },
    hotspots: [
      { x: 50, y: 40, label: 'Main Stage', link: '#stage' },
      { x: 30, y: 60, label: 'Control Room', link: '#control' },
    ],
    stats: {
      capacity: '2000 seats',
      events: '100+ annually',
      technology: '4K projection',
    },
    features: ['Live Streaming', 'Dolby Audio', 'Green Room'],
  },
  {
    id: 'sports',
    name: 'Sports Complex',
    description: 'Olympic-standard sports facilities',
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    image360: '/images/360/sports.jpg',
    coordinates: { lat: 28.6143, lng: 77.2094 },
    hotspots: [
      { x: 35, y: 50, label: 'Swimming Pool', link: '#pool' },
      { x: 65, y: 40, label: 'Gym', link: '#gym' },
      { x: 50, y: 70, label: 'Courts', link: '#courts' },
    ],
    stats: {
      facilities: '20+ sports',
      coaches: '50+ certified',
      achievements: '100+ medals',
    },
    features: ['Olympic Pool', 'Indoor Stadium', 'Fitness Center'],
  },
];

const CampusTour: React.FC = () => {
  const [selectedLocation, setSelectedLocation] = useState(tourLocations[0]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [view360Active, setView360Active] = useState(false);
  const [viewAngle, setViewAngle] = useState({ x: 0, y: 0 });
  const [showInfo, setShowInfo] = useState(true);
  const [showMap, setShowMap] = useState(false);
  const [liked, setLiked] = useState(false);
  const [bookmarked, setBookmarked] = useState(false);
  const [showComments, setShowComments] = useState(false);
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const { trackEvent } = useAnalytics();

  // Handle 360 view mouse movement
  useEffect(() => {
    if (!view360Active) return;

    const handleMouseMove = (e: MouseEvent) => {
      const { clientX, clientY } = e;
      const { innerWidth, innerHeight } = window;
      
      setViewAngle({
        x: (clientX / innerWidth - 0.5) * 360,
        y: (clientY / innerHeight - 0.5) * 180,
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [view360Active]);

  // Handle fullscreen
  const toggleFullscreen = () => {
    if (!isFullscreen) {
      containerRef.current?.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
    setIsFullscreen(!isFullscreen);
  };

  // Handle location change
  const handleLocationChange = (location: typeof tourLocations[0]) => {
    setSelectedLocation(location);
    setIsPlaying(false);
    
    trackEvent('campus_tour_location_viewed', {
      locationId: location.id,
      locationName: location.name,
    });
  };

  // Handle sharing
  const handleShare = async () => {
    const shareData = {
      title: `${selectedLocation.name} - Campus Tour`,
      text: selectedLocation.description,
      url: `${window.location.origin}/campus-tour#${selectedLocation.id}`,
    };

    try {
      if (navigator.share) {
        await navigator.share(shareData);
        trackEvent('campus_tour_shared', { location: selectedLocation.id });
      } else {
        await navigator.clipboard.writeText(shareData.url);
        toast.success('Link copied to clipboard!');
      }
    } catch (error) {
      toast.error('Failed to share');
    }
  };

  return (
    <>
      <Helmet>
        <title>360° Campus Tour - Smart Campus</title>
        <meta name="description" content="Experience our campus through an immersive 360° virtual tour" />
      </Helmet>

      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white">
        {/* Header */}
        <motion.header
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-black/50 backdrop-blur-xl border-b border-white/10 sticky top-0 z-40"
        >
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <CTALink
                  to="/"
                  variant="ghost"
                  size="sm"
                  icon={<ChevronLeft className="h-4 w-4" />}
                  className="text-white hover:bg-white/10"
                >
                  Back
                </CTALink>
                
                <div className="flex items-center space-x-3">
                  <div className="h-10 w-10 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-xl flex items-center justify-center">
                    <Camera className="h-6 w-6" />
                  </div>
                  <div>
                    <h1 className="text-xl font-bold">360° Campus Tour</h1>
                    <p className="text-xs text-gray-400">Explore our world-class facilities</p>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <button
                  onClick={() => setShowMap(!showMap)}
                  className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                >
                  <MapPin className="h-5 w-5" />
                </button>
                
                <button
                  onClick={handleShare}
                  className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                >
                  <Share2 className="h-5 w-5" />
                </button>
                
                <CTALink
                  to="/admissions"
                  variant="gradient"
                  size="sm"
                  showArrow
                  analyticsEvent="campus_tour_apply_clicked"
                >
                  Apply Now
                </CTALink>
              </div>
            </div>
          </div>
        </motion.header>

        {/* Main Content */}
        <div className="flex flex-col lg:flex-row h-[calc(100vh-80px)]">
          {/* Sidebar - Location List */}
          <motion.aside
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="w-full lg:w-80 bg-gray-900/50 backdrop-blur-xl border-r border-white/10 overflow-y-auto"
          >
            <div className="p-4">
              <h2 className="text-lg font-bold mb-4 flex items-center">
                <Grid className="h-5 w-5 mr-2 text-purple-400" />
                Tour Locations
              </h2>
              
              <div className="space-y-2">
                {tourLocations.map((location) => (
                  <motion.button
                    key={location.id}
                    onClick={() => handleLocationChange(location)}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className={`w-full text-left p-4 rounded-xl transition-all ${
                      selectedLocation.id === location.id
                        ? 'bg-gradient-to-r from-indigo-600 to-purple-600'
                        : 'bg-white/5 hover:bg-white/10'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-semibold mb-1">{location.name}</h3>
                        <p className="text-xs text-gray-400">{location.description}</p>
                        
                        <div className="flex items-center space-x-3 mt-2 text-xs">
                          {location.features.slice(0, 2).map((feature, i) => (
                            <span key={i} className="text-purple-400">
                              • {feature}
                            </span>
                          ))}
                        </div>
                      </div>
                      
                      <ChevronRight className={`h-5 w-5 mt-1 transition-transform ${
                        selectedLocation.id === location.id ? 'rotate-90' : ''
                      }`} />
                    </div>
                  </motion.button>
                ))}
              </div>
            </div>
          </motion.aside>

          {/* Main Viewer Area */}
          <div className="flex-1 relative" ref={containerRef}>
            {/* 360 View / Video Player */}
            <div className="absolute inset-0 bg-black">
              {view360Active ? (
                // 360 Image Viewer
                <motion.div
                  className="relative w-full h-full overflow-hidden cursor-move"
                  style={{
                    backgroundImage: `url(${selectedLocation.image360})`,
                    backgroundSize: 'cover',
                    backgroundPosition: `${50 + viewAngle.x / 10}% ${50 + viewAngle.y / 10}%`,
                  }}
                >
                  {/* Hotspots */}
                  {selectedLocation.hotspots.map((hotspot, i) => (
                    <motion.div
                      key={i}
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ delay: i * 0.1 }}
                      className="absolute"
                      style={{ left: `${hotspot.x}%`, top: `${hotspot.y}%` }}
                    >
                      <button className="relative group">
                        <span className="absolute h-4 w-4 bg-purple-500 rounded-full animate-ping" />
                        <span className="relative flex h-4 w-4 bg-purple-600 rounded-full" />
                        
                        <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-black/90 text-white text-xs px-3 py-2 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                          {hotspot.label}
                        </div>
                      </button>
                    </motion.div>
                  ))}
                  
                  {/* Navigation Hint */}
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 1 }}
                    className="absolute top-4 left-4 bg-black/50 backdrop-blur-xl rounded-lg px-4 py-2 text-sm"
                  >
                    <Navigation className="h-4 w-4 inline mr-2" />
                    Move mouse to look around
                  </motion.div>
                </motion.div>
              ) : (
                // Video Player
                <div className="relative w-full h-full">
                  <iframe
                    src={`${selectedLocation.videoUrl}?autoplay=${isPlaying ? 1 : 0}&mute=${isMuted ? 1 : 0}`}
                    className="w-full h-full"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                </div>
              )}
            </div>

            {/* Control Bar */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black via-black/80 to-transparent p-6"
            >
              {/* Location Info */}
              {showInfo && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mb-4"
                >
                  <h2 className="text-2xl font-bold mb-2">{selectedLocation.name}</h2>
                  <p className="text-gray-300 mb-4">{selectedLocation.description}</p>
                  
                  {/* Stats */}
                  <div className="flex flex-wrap gap-4 mb-4">
                    {Object.entries(selectedLocation.stats).map(([key, value]) => (
                      <div key={key} className="bg-white/10 backdrop-blur-xl rounded-lg px-3 py-2">
                        <p className="text-xs text-gray-400 capitalize">{key.replace(/([A-Z])/g, ' $1')}</p>
                        <p className="text-sm font-semibold">{value}</p>
                      </div>
                    ))}
                  </div>
                  
                  {/* Features */}
                  <div className="flex flex-wrap gap-2">
                    {selectedLocation.features.map((feature, i) => (
                      <span
                        key={i}
                        className="px-3 py-1 bg-purple-600/20 border border-purple-500/30 rounded-full text-xs"
                      >
                        {feature}
                      </span>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Controls */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {/* Play/Pause */}
                  <button
                    onClick={() => setIsPlaying(!isPlaying)}
                    className="h-12 w-12 bg-white/20 backdrop-blur-xl rounded-full flex items-center justify-center hover:bg-white/30 transition-colors"
                  >
                    {isPlaying ? <Pause className="h-6 w-6" /> : <Play className="h-6 w-6 ml-1" />}
                  </button>
                  
                  {/* Volume */}
                  <button
                    onClick={() => setIsMuted(!isMuted)}
                    className="p-3 hover:bg-white/10 rounded-lg transition-colors"
                  >
                    {isMuted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
                  </button>
                  
                  {/* 360 Toggle */}
                  <button
                    onClick={() => setView360Active(!view360Active)}
                    className={`px-4 py-2 rounded-lg transition-colors flex items-center space-x-2 ${
                      view360Active ? 'bg-purple-600' : 'bg-white/20 hover:bg-white/30'
                    }`}
                  >
                    <Eye className="h-5 w-5" />
                    <span className="text-sm font-medium">360° View</span>
                  </button>
                  
                  {/* Info Toggle */}
                  <button
                    onClick={() => setShowInfo(!showInfo)}
                    className="p-3 hover:bg-white/10 rounded-lg transition-colors"
                  >
                    <Info className="h-5 w-5" />
                  </button>
                </div>

                <div className="flex items-center space-x-3">
                  {/* Like */}
                  <button
                    onClick={() => {
                      setLiked(!liked);
                      trackEvent('campus_tour_liked', { location: selectedLocation.id });
                    }}
                    className={`p-3 rounded-lg transition-colors ${
                      liked ? 'bg-red-600 text-white' : 'hover:bg-white/10'
                    }`}
                  >
                    <Heart className={`h-5 w-5 ${liked ? 'fill-current' : ''}`} />
                  </button>
                  
                  {/* Bookmark */}
                  <button
                    onClick={() => {
                      setBookmarked(!bookmarked);
                      toast.success(bookmarked ? 'Removed from bookmarks' : 'Added to bookmarks');
                    }}
                    className={`p-3 rounded-lg transition-colors ${
                      bookmarked ? 'bg-purple-600 text-white' : 'hover:bg-white/10'
                    }`}
                  >
                    <Bookmark className={`h-5 w-5 ${bookmarked ? 'fill-current' : ''}`} />
                  </button>
                  
                  {/* Comments */}
                  <button
                    onClick={() => setShowComments(!showComments)}
                    className="p-3 hover:bg-white/10 rounded-lg transition-colors relative"
                  >
                    <MessageCircle className="h-5 w-5" />
                    <span className="absolute -top-1 -right-1 h-4 w-4 bg-red-500 rounded-full text-xs flex items-center justify-center">
                      5
                    </span>
                  </button>
                  
                  {/* Download */}
                  <button
                    onClick={() => {
                      toast.success('Download started');
                      trackEvent('campus_tour_downloaded', { location: selectedLocation.id });
                    }}
                    className="p-3 hover:bg-white/10 rounded-lg transition-colors"
                  >
                    <Download className="h-5 w-5" />
                  </button>
                  
                  {/* Fullscreen */}
                  <button
                    onClick={toggleFullscreen}
                    className="p-3 hover:bg-white/10 rounded-lg transition-colors"
                  >
                    <Maximize className="h-5 w-5" />
                  </button>
                </div>
              </div>
            </motion.div>

            {/* Comments Panel */}
            <AnimatePresence>
              {showComments && (
                <motion.div
                  initial={{ opacity: 0, x: 100 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 100 }}
                  className="absolute top-0 right-0 bottom-0 w-96 bg-black/90 backdrop-blur-xl border-l border-white/10 p-6 overflow-y-auto"
                >
                  <h3 className="text-lg font-bold mb-4">Comments</h3>
                  {/* Add comments implementation */}
                  <p className="text-gray-400">Comments coming soon...</p>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Map Overlay */}
            <AnimatePresence>
              {showMap && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  className="absolute top-4 right-4 w-80 h-64 bg-black/90 backdrop-blur-xl rounded-xl border border-white/10 p-4"
                >
                  <h3 className="text-sm font-bold mb-2">Campus Map</h3>
                  {/* Add map implementation */}
                  <div className="w-full h-full bg-gray-800 rounded-lg flex items-center justify-center">
                    <MapPin className="h-8 w-8 text-gray-600" />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </>
  );
};

export default CampusTour;