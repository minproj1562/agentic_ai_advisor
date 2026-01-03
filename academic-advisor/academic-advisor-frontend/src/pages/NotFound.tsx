// src/pages/NotFound.tsx
import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Home, Search, HelpCircle } from 'lucide-react';
import CTALink from '../components/common/CTALink';

const NotFound: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center max-w-2xl"
      >
        <motion.div
          animate={{ rotate: [0, 10, -10, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="text-9xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent mb-8"
        >
          404
        </motion.div>
        
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Page Not Found</h1>
        <p className="text-xl text-gray-600 mb-8">
          The page you're looking for doesn't exist or has been moved.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <CTALink
            to="/"
            variant="primary"
            size="lg"
            icon={<Home className="h-5 w-5" />}
          >
            Go Home
          </CTALink>
          <CTALink
            to="/help"
            variant="secondary"
            size="lg"
            icon={<HelpCircle className="h-5 w-5" />}
          >
            Get Help
          </CTALink>
        </div>
      </motion.div>
    </div>
  );
};

export default NotFound;