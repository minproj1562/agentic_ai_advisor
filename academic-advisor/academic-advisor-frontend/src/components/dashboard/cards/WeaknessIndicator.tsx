import React from 'react';
import { Chip } from '@mui/material';

interface WeaknessIndicatorProps {
  weaknesses: any[];
}

export const WeaknessIndicator: React.FC<WeaknessIndicatorProps> = ({ weaknesses }) => {
  return (
    <Chip 
      label={`${weaknesses.length} weaknesses`}
      color={weaknesses.length > 0 ? 'error' : 'default'}
      size="small"
    />
  );
};

export default WeaknessIndicator;