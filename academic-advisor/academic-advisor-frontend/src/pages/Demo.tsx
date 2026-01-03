// src/pages/Demo.tsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Play, X, ChevronRight, Check } from 'lucide-react';
import CTALink from '../components/common/CTALink';

const Demo: React.FC = () => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);

  const demoSteps = [
    { title: 'Dashboard Overview', duration: '2:30' },
    { title: 'Course Management', duration: '3:15' },
    { title: 'Performance Analytics', duration: '2:45' },
    { title: 'AI Recommendations', duration: '4:00' },
    { title: 'Communication Tools', duration: '2:00' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white py-20">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Platform Demo</h1>
          <p className="text-xl text-gray-600">See Smart Campus in action</p>
        </motion.div>

        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <div className="bg-black rounded-2xl aspect-video flex items-center justify-center relative">
              {!isPlaying ? (
                <button
                  onClick={() => setIsPlaying(true)}
                  className="h-20 w-20 bg-white/20 backdrop-blur-xl rounded-full flex items-center justify-center hover:bg-white/30 transition-colors"
                >
                  <Play className="h-10 w-10 text-white ml-2" />
                </button>
              ) : (
                <iframe
                  src="https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1"
                  className="w-full h-full rounded-2xl"
                  allow="autoplay; fullscreen"
                />
              )}
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-lg font-bold mb-4">Demo Chapters</h3>
            {demoSteps.map((step, index) => (
              <button
                key={index}
                onClick={() => setCurrentStep(index)}
                className={`w-full text-left p-4 rounded-xl transition-all ${
                  currentStep === index
                    ? 'bg-purple-600 text-white'
                    : 'bg-white hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {currentStep > index ? (
                      <Check className="h-5 w-5 text-green-500" />
                    ) : (
                      <span className={`h-5 w-5 rounded-full border-2 ${
                        currentStep === index ? 'border-white' : 'border-gray-300'
                      }`} />
                    )}
                    <span className="font-medium">{step.title}</span>
                  </div>
                  <span className="text-sm opacity-70">{step.duration}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="mt-12 text-center">
          <CTALink
            to="/register"
            variant="primary"
            size="lg"
            showArrow
          >
            Start Free Trial
          </CTALink>
        </div>
      </div>
    </div>
  );
};

export default Demo;