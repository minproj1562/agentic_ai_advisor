// src/pages/ProgramDetail.tsx
import React from 'react';
import { useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import CTALink from '../components/common/CTALink';

const ProgramDetail: React.FC = () => {
  const { id } = useParams();
  
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white py-20">
      <div className="max-w-7xl mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <h1 className="text-4xl font-bold mb-4">Program Details</h1>
          <p className="text-xl text-gray-600">Program ID: {id}</p>
          <div className="mt-8">
            <CTALink to="/programs" variant="primary">
              Back to Programs
            </CTALink>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default ProgramDetail;