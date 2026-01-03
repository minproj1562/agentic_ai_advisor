import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { IconType } from 'react-icons';

interface StatCardProps {
  title: string;
  icon?: React.ReactNode; // Optional custom icon (from new version)
  Icon?: IconType; // Specific react-icons type (from existing version)
  value: string | number;
  change?: number; // Optional change percentage (from new version)
  subtext?: string; // Optional subtext (from existing version)
  actions?: { label: string; icon: IconType; onClick: () => void }[]; // Actions (from existing version)
  children?: React.ReactNode; // Optional children (from existing version)
  color?: string; // Optional color for icon background (from new version, defaults to accent)
  onClick?: () => void; // Optional click handler (from new version)
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  icon,
  Icon,
  value,
  change,
  subtext,
  actions,
  children,
  color = 'accent', // Default to accent to match existing design, fallback to blue if needed
  onClick
}) => {
  return (
    <motion.div
      className={`bg-white rounded-2xl shadow-lg p-6 hover:shadow-xl transition-shadow duration-300 ${onClick ? 'cursor-pointer' : ''}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-semibold text-primary">{title}</h3>
        {Icon && <Icon className="text-accent text-2xl" />}
        {icon && !Icon && (
          <div className={`h-12 w-12 bg-${color}-100 rounded-lg flex items-center justify-center`}>
            {icon}
          </div>
        )}
        {change !== undefined && (
          <span className={`text-sm font-medium flex items-center ${
            change > 0 ? 'text-green-600' : change < 0 ? 'text-red-600' : 'text-gray-600'
          }`}>
            {change > 0 ? '+' : ''}{change}%
            {change > 0 ? (
              <TrendingUp className="h-4 w-4 ml-1" />
            ) : change < 0 ? (
              <TrendingDown className="h-4 w-4 ml-1" />
            ) : null}
          </span>
        )}
      </div>
      <div className="text-3xl font-bold text-accent mb-2">{value}</div>
      {subtext && <p className="text-sm text-muted">{subtext}</p>}
      {actions && (
        <div className="mt-4 space-x-2">
          {actions.map((action, index) => (
            <motion.button
              key={index}
              onClick={action.onClick}
              className="flex items-center text-sm text-accent hover:text-warm transition-colors"
              whileHover={{ scale: 1.1 }}
            >
              <action.icon className="mr-1" /> {action.label}
            </motion.button>
          ))}
        </div>
      )}
      {children && <div className="mt-6">{children}</div>}
    </motion.div>
  );
};

export default StatCard;