// src/modules/agent1/student-analysis/components/WeaknessIndicator/WeaknessChart.tsx
import React, { useMemo } from 'react';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Cell,
  PieChart,
  Pie
} from 'recharts';
import { Box, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material';
import { WeaknessArea, SeverityLevel } from '../../../../../services/weakness.service';

interface WeaknessChartProps {
  weaknesses: WeaknessArea[];
  chartType?: 'radar' | 'bar' | 'pie';
  height?: number;
}

export const WeaknessChart: React.FC<WeaknessChartProps> = ({
  weaknesses,
  chartType: initialChartType = 'radar',
  height = 300
}) => {
  const [chartType, setChartType] = React.useState<'radar' | 'bar' | 'pie'>(initialChartType);

  // Color mapping for severity levels
  const getSeverityColor = (severity: SeverityLevel): string => {
    const colorMap: { [key in SeverityLevel]: string } = {
      critical: '#d32f2f',
      high: '#f57c00',
      medium: '#fbc02d',
      low: '#388e3c'
    };
    return colorMap[severity];
  };

  // Prepare data for radar chart
  const radarData = useMemo(() => {
    return weaknesses.slice(0, 8).map(w => ({
      subject: w.subject.length > 15 ? w.subject.substring(0, 15) + '...' : w.subject,
      fullSubject: w.subject,
      score: w.current_score,
      target: w.target_score,
      gap: w.gap_percentage,
      severity: w.severity
    }));
  }, [weaknesses]);

  // Prepare data for bar chart
  const barData = useMemo(() => {
    return weaknesses.slice(0, 10).map(w => ({
      name: w.subject.length > 20 ? w.subject.substring(0, 20) + '...' : w.subject,
      fullName: w.subject,
      current: w.current_score,
      target: w.target_score,
      gap: w.gap_percentage,
      severity: w.severity
    }));
  }, [weaknesses]);

  // Prepare data for pie chart (severity distribution)
  const pieData = useMemo(() => {
    const severityCounts: { [key in SeverityLevel]: number } = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0
    };

    weaknesses.forEach(w => {
      severityCounts[w.severity]++;
    });

    return Object.entries(severityCounts)
      .filter(([_, count]) => count > 0)
      .map(([severity, count]) => ({
        name: severity.charAt(0).toUpperCase() + severity.slice(1),
        value: count,
        severity: severity as SeverityLevel
      }));
  }, [weaknesses]);

  // Custom tooltip for radar and bar charts
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <Box
          sx={{
            backgroundColor: 'white',
            padding: 2,
            border: '1px solid #ccc',
            borderRadius: 1,
            boxShadow: 2
          }}
        >
          <Typography variant="body2" fontWeight="bold">
            {data.fullSubject || data.fullName}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Current Score: {data.current || data.score}%
          </Typography>
          <br />
          <Typography variant="caption" color="text.secondary">
            Target: {data.target}%
          </Typography>
          <br />
          <Typography variant="caption" color="error">
            Gap: {data.gap}%
          </Typography>
        </Box>
      );
    }
    return null;
  };

  // Render radar chart
  const renderRadarChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <RadarChart data={radarData}>
        <PolarGrid stroke="#e0e0e0" />
        <PolarAngleAxis
          dataKey="subject"
          tick={{ fill: '#666', fontSize: 12 }}
        />
        <PolarRadiusAxis
          angle={90}
          domain={[0, 100]}
          tick={{ fill: '#666', fontSize: 10 }}
        />
        <Radar
          name="Current Score"
          dataKey="score"
          stroke="#2196f3"
          fill="#2196f3"
          fillOpacity={0.5}
        />
        <Radar
          name="Target Score"
          dataKey="target"
          stroke="#4caf50"
          fill="#4caf50"
          fillOpacity={0.3}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
      </RadarChart>
    </ResponsiveContainer>
  );

  // Render bar chart
  const renderBarChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={barData} layout="vertical" margin={{ left: 20, right: 20, top: 20, bottom: 20 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" domain={[0, 100]} />
        <YAxis dataKey="name" type="category" width={150} tick={{ fontSize: 11 }} />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        <Bar dataKey="current" name="Current Score" radius={[0, 4, 4, 0]}>
          {barData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={getSeverityColor(entry.severity)} />
          ))}
        </Bar>
        <Bar dataKey="target" name="Target Score" fill="#4caf50" fillOpacity={0.3} radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );

  // Render pie chart
  const renderPieChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={pieData}
          cx="50%"
          cy="50%"
          labelLine={true}
          label={(entry) => `${entry.name}: ${entry.value}`}
          outerRadius={100}
          dataKey="value"
        >
          {pieData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={getSeverityColor(entry.severity)} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );

  if (weaknesses.length === 0) {
    return (
      <Box
        display="flex"
        alignItems="center"
        justifyContent="center"
        height={height}
        bgcolor="grey.50"
        borderRadius={1}
      >
        <Typography variant="body2" color="text.secondary">
          No weakness data to display
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      {/* Chart Type Selector */}
      <Box display="flex" justifyContent="center" mb={2}>
        <ToggleButtonGroup
          value={chartType}
          exclusive
          onChange={(_, newType) => newType && setChartType(newType)}
          size="small"
        >
          <ToggleButton value="radar">Radar</ToggleButton>
          <ToggleButton value="bar">Bar</ToggleButton>
          <ToggleButton value="pie">Distribution</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {/* Chart Display */}
      {chartType === 'radar' && renderRadarChart()}
      {chartType === 'bar' && renderBarChart()}
      {chartType === 'pie' && renderPieChart()}
    </Box>
  );
};

export default WeaknessChart;