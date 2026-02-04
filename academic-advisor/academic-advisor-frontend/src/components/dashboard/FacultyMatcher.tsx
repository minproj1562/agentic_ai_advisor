// academic-advisor/academic-advisor-frontend/src/components/dashboard/FacultyMatcher.tsx
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FaSearch, FaUserPlus, FaFilter, FaInfoCircle } from 'react-icons/fa';
import StatCard from '../common/StatCard';
import toast from 'react-hot-toast';

const FacultyMatcher: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({ sgpiThreshold: 6.0, topic: '' });
  const [matches, setMatches] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = async () => {
    setIsLoading(true);
    try {
      // Simulate API call to backend for matching
      const response = await fetch(`http://localhost:8000/match?topic=${filters.topic}&sgpi=${filters.sgpiThreshold}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
      });
      const data = await response.json();
      setMatches(data);
      toast.success('Matching complete!');
    } catch (error) {
      toast.error('Matching failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (searchTerm) handleSearch();
  }, [filters]);

  return (
    <StatCard
      title="Mentee Matcher"
      // FIXED: Render the icon as JSX element instead of passing the component
      icon={<FaSearch />}
      value="Find Matches"
    >
      <div className="mt-4 space-y-6">
        <div className="flex space-x-4">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by topic or student..."
            className="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
            aria-label="Search mentees"
          />
          <motion.button
            onClick={handleSearch}
            className="px-4 py-3 bg-accent text-white rounded-lg hover:bg-accent/90 flex items-center"
            whileHover={{ scale: 1.05 }}
            disabled={isLoading}
          >
            {isLoading ? <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <FaSearch />}
          </motion.button>
        </div>
        <div className="flex space-x-4">
          <input
            type="number"
            value={filters.sgpiThreshold}
            onChange={(e) => setFilters({ ...filters, sgpiThreshold: parseFloat(e.target.value) })}
            placeholder="SGPI Threshold"
            className="w-1/2 p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
            aria-label="SGPI threshold"
          />
          <input
            type="text"
            value={filters.topic}
            onChange={(e) => setFilters({ ...filters, topic: e.target.value })}
            placeholder="Topic Filter"
            className="w-1/2 p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
            aria-label="Topic filter"
          />
        </div>
        <ul className="space-y-4 max-h-60 overflow-y-auto">
          {matches.map((match: any, index) => (
            <motion.li
              key={index}
              className="p-4 bg-gray-50 rounded-lg flex justify-between items-center"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <div>
                <span className="font-medium">{match.student}</span>
                <span className="text-sm text-gray-500 ml-2">({(match.score * 100).toFixed(0)}%)</span>
              </div>
              <div className="text-sm text-gray-600">{match.reason}</div>
              <motion.button
                className="px-3 py-1 bg-warm text-white rounded-full hover:bg-warm/90"
                whileHover={{ scale: 1.1 }}
                onClick={() => toast.success(`Assigned ${match.student}`)}
              >
                <FaUserPlus />
              </motion.button>
              <motion.button
                className="ml-2 text-gray-500 hover:text-gray-700"
                whileHover={{ scale: 1.1 }}
              >
                <FaInfoCircle />
              </motion.button>
            </motion.li>
          ))}
        </ul>
      </div>
    </StatCard>
  );
};

export default FacultyMatcher;