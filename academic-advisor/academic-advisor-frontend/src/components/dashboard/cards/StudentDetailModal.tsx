// academic-advisor/academic-advisor-frontend/src/components/dashboard/cards/StudentDetailModal.tsx
/**
 * Student Detail Modal Component
 * Shows comprehensive student analysis details
 * Vite-compatible version
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Tabs,
  Tab,
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Avatar,
  Divider,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Close as CloseIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  Assignment as AssignmentIcon,
  Analytics as AnalyticsIcon,
  Download as DownloadIcon,
  Share as ShareIcon,
  Print as PrintIcon,
} from '@mui/icons-material';

// Types
interface Weakness {
  subject: string;
  topic?: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  gap: number;
  priority: number;
}

interface StudentAnalysis {
  student_id: string;
  name: string;
  department: string;
  batch: number;
  current_semester: number;
  cgpa: number;
  sgpa_trend: number[];
  latest_sgpa: number;
  attendance: number;
  weaknesses: Weakness[];
  weakness_count: number;
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high';
  improvement_trend: 'improving' | 'stable' | 'declining';
  recommendations_pending: number;
  profile_completeness: number;
  last_updated: string;
  metadata: {
    total_credits: number;
    has_warnings: boolean;
    analysis_version: string;
  };
}

interface Props {
  open: boolean;
  onClose: () => void;
  student: StudentAnalysis | null;
  onUpdate?: (student: StudentAnalysis) => void;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

// Performance Data Interface that matches PerformanceChart expectations
interface ChartPerformanceData {
  currentSGPI: number;
  previousSGPI: number;
  trend: 'stable' | 'up' | 'down';
  percentageChange: number;
  semesterWiseData: Array<{
    semester: number;
    sgpi: number;
    credits?: number;
    courses?: number;
  }>;
}

// Mock services (replace with actual implementations)
const StudentAnalysisService = {
  getStudentDetails: async (studentId: string) => {
    // Mock implementation
    return {
      predictions: {
        nextSemesterPrediction: 8.7,
        confidence: 85
      },
      recommendations: [
        {
          title: "Focus on Mathematics",
          description: "Improve understanding of calculus concepts",
          priority: "high"
        },
        {
          title: "Increase Study Hours",
          description: "Add 2 more hours per week for Physics",
          priority: "medium"
        }
      ]
    };
  },
  
  triggerWeaknessAnalysis: async (studentId: string, deepAnalysis: boolean) => {
    // Mock implementation
    return { job_id: 'mock-job-id', status: 'started' };
  },
  
  getAnalysisStatus: async (studentId: string) => {
    // Mock implementation
    return { status: 'completed', result: { weaknesses: [] } };
  }
};

// Mock PerformanceChart component
const PerformanceChart: React.FC<{ data: ChartPerformanceData | null }> = ({ data }) => {
  if (!data) {
    return (
      <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          No performance data available
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Box>
        <Typography variant="h6" gutterBottom>
          Performance Trend
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Current SGPI: {data.currentSGPI.toFixed(2)} | Trend: {data.trend} | Change: {data.percentageChange.toFixed(1)}%
        </Typography>
        <Box sx={{ mt: 2 }}>
          {data.semesterWiseData.map((semester, index) => (
            <Box key={index} display="flex" alignItems="center" gap={1} mb={1}>
              <Typography variant="body2" minWidth={80}>
                Semester {semester.semester}:
              </Typography>
              <LinearProgress
                variant="determinate"
                value={(semester.sgpi / 10) * 100}
                sx={{ flex: 1, height: 8 }}
                color={
                  semester.sgpi >= 8.5 ? 'success' :
                  semester.sgpi >= 7.0 ? 'primary' :
                  semester.sgpi >= 5.5 ? 'warning' : 'error'
                }
              />
              <Typography variant="body2" minWidth={40}>
                {semester.sgpi.toFixed(2)}
              </Typography>
            </Box>
          ))}
        </Box>
      </Box>
    </Box>
  );
};

// Create placeholder components for missing ones
const WeaknessAnalysisChart: React.FC<{ 
  weaknesses: any[]; 
  onRunAnalysis: () => void;
  analysisRunning: boolean;
}> = ({ weaknesses, onRunAnalysis, analysisRunning }) => (
  <Card>
    <CardContent>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">Weakness Analysis</Typography>
        <Button 
          variant="outlined" 
          onClick={onRunAnalysis}
          disabled={analysisRunning}
          startIcon={analysisRunning ? <CircularProgress size={16} /> : <AnalyticsIcon />}
        >
          {analysisRunning ? 'Analyzing...' : 'Analyze Weaknesses'}
        </Button>
      </Box>
      {weaknesses && weaknesses.length > 0 ? (
        <Box>
          <Typography variant="body2" color="text.secondary" mb={2}>
            {weaknesses.length} weaknesses identified
          </Typography>
          <List>
            {weaknesses.slice(0, 5).map((weakness, index) => (
              <ListItem key={index}>
                <ListItemText
                  primary={weakness.subject}
                  secondary={`Severity: ${weakness.severity} - Gap: ${weakness.gap}%`}
                />
                <Chip 
                  label={weakness.severity} 
                  color={
                    weakness.severity === 'critical' ? 'error' :
                    weakness.severity === 'high' ? 'warning' :
                    'default'
                  }
                  size="small"
                />
              </ListItem>
            ))}
          </List>
        </Box>
      ) : (
        <Typography variant="body2" color="text.secondary">
          No weaknesses identified. Run analysis to detect weaknesses.
        </Typography>
      )}
    </CardContent>
  </Card>
);

const PredictiveAnalysis: React.FC<{ 
  predictions: any;
  historicalData: any;
}> = ({ predictions, historicalData }) => (
  <Card>
    <CardContent>
      <Typography variant="h6" gutterBottom>
        Predictive Analysis
      </Typography>
      <Typography variant="body2" color="text.secondary" mb={2}>
        Based on historical performance data
      </Typography>
      {predictions ? (
        <Box>
          <Box display="flex" alignItems="center" gap={2} mb={2}>
            <Box flex={1}>
              <Typography variant="body2" color="text.secondary">
                Predicted Next Semester Performance
              </Typography>
              <Typography variant="h4" color="primary.main">
                {predictions?.nextSemesterPrediction?.toFixed(2) || 'N/A'}
              </Typography>
            </Box>
            <Box flex={1}>
              <Typography variant="body2" color="text.secondary">
                Confidence Level
              </Typography>
              <LinearProgress
                variant="determinate"
                value={predictions?.confidence || 0}
                sx={{ height: 8, mb: 1 }}
              />
              <Typography variant="body2">
                {predictions?.confidence || 'N/A'}%
              </Typography>
            </Box>
          </Box>
          <Alert severity="info" sx={{ mt: 2 }}>
            Based on {historicalData?.semesterWiseData?.length || 0} semesters of historical data
          </Alert>
        </Box>
      ) : (
        <Typography variant="body2" color="text.secondary">
          No prediction data available. Run analysis to generate predictions.
        </Typography>
      )}
    </CardContent>
  </Card>
);

const RecommendationsList: React.FC<{ 
  recommendations: any[];
  studentId: string;
}> = ({ recommendations, studentId }) => (
  <Card>
    <CardContent>
      <Typography variant="h6" gutterBottom>
        Recommendations
      </Typography>
      {recommendations && recommendations.length > 0 ? (
        <List>
          {recommendations.map((rec, index) => (
            <ListItem key={index}>
              <ListItemText
                primary={rec.title}
                secondary={rec.description}
              />
              <Chip 
                label={rec.priority} 
                color={
                  rec.priority === 'high' ? 'error' :
                  rec.priority === 'medium' ? 'warning' :
                  'success'
                }
                size="small"
              />
            </ListItem>
          ))}
        </List>
      ) : (
        <Box textAlign="center" py={4}>
          <AssignmentIcon color="disabled" sx={{ fontSize: 48, mb: 2 }} />
          <Typography variant="body2" color="text.secondary">
            No recommendations available yet.
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Run analysis to get personalized recommendations.
          </Typography>
        </Box>
      )}
    </CardContent>
  </Card>
);

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => (
  <div role="tabpanel" hidden={value !== index} {...other}>
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
);

export const StudentDetailModal: React.FC<Props> = ({
  open,
  onClose,
  student,
  onUpdate
}) => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [detailedData, setDetailedData] = useState<any>(null);
  const [analysisRunning, setAnalysisRunning] = useState(false);
  const service = StudentAnalysisService;

  useEffect(() => {
    if (open && student) {
      fetchDetailedData();
    }
  }, [open, student]);

  const fetchDetailedData = async () => {
    if (!student) return;
    
    setLoading(true);
    try {
      const data = await service.getStudentDetails(student.student_id);
      setDetailedData(data);
    } catch (error) {
      console.error('Failed to fetch detailed data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRunAnalysis = async () => {
    if (!student) return;
    
    setAnalysisRunning(true);
    try {
      const result = await service.triggerWeaknessAnalysis(student.student_id, true);
      
      // Poll for results
      if (result.job_id) {
        const checkStatus = setInterval(async () => {
          const status = await service.getAnalysisStatus(student.student_id);
          
          if (status.status === 'completed') {
            clearInterval(checkStatus);
            setAnalysisRunning(false);
            fetchDetailedData();
            
            if (onUpdate && status.result) {
              onUpdate({ ...student, ...status.result });
            }
          }
        }, 2000);
      }
    } catch (error) {
      console.error('Failed to run analysis:', error);
      setAnalysisRunning(false);
    }
  };

  const handleExport = async (format: 'pdf' | 'excel') => {
    // Export implementation
    console.log(`Exporting as ${format} for student:`, student?.student_id);
  };

  // Create performance data for the chart
  const getPerformanceData = (): ChartPerformanceData | null => {
    if (!student?.sgpa_trend) return null;
    
    // Convert improvement_trend string to the expected trend type
    const trend: 'stable' | 'up' | 'down' = 
      student.improvement_trend === 'improving' ? 'up' : 
      student.improvement_trend === 'declining' ? 'down' : 'stable';
    
    const percentageChange = student.sgpa_trend.length > 1 ? 
      ((student.sgpa_trend[student.sgpa_trend.length - 1] - student.sgpa_trend[student.sgpa_trend.length - 2]) / student.sgpa_trend[student.sgpa_trend.length - 2]) * 100 : 0;

    return {
      currentSGPI: student.latest_sgpa,
      previousSGPI: student.sgpa_trend[student.sgpa_trend.length - 2] || student.latest_sgpa,
      trend: trend,
      percentageChange: percentageChange,
      semesterWiseData: student.sgpa_trend.map((sgpa: number, index: number) => ({
        semester: index + 1,
        sgpi: sgpa,
        credits: 20,
        courses: 6,
      }))
    };
  };

  if (!student) {
    return null;
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      sx={{ '& .MuiDialog-paper': { height: '90vh' } }}
    >
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box display="flex" alignItems="center" gap={2}>
            <Avatar sx={{ bgcolor: 'primary.main' }}>
              {student?.name?.charAt(0)}
            </Avatar>
            <Box>
              <Typography variant="h6">{student?.name}</Typography>
              <Typography variant="caption" color="text.secondary">
                {student?.student_id} | {student?.department} | Semester {student?.current_semester}
              </Typography>
            </Box>
          </Box>
          <Box>
            <Tooltip title="Export">
              <IconButton onClick={() => handleExport('pdf')}>
                <DownloadIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Share">
              <IconButton>
                <ShareIcon />
              </IconButton>
            </Tooltip>
            <IconButton onClick={onClose}>
              <CloseIcon />
            </IconButton>
          </Box>
        </Box>
      </DialogTitle>
      
      <DialogContent dividers>
        {loading ? (
          <Box display="flex" justifyContent="center" alignItems="center" height={400}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
              <Tab label="Overview" />
              <Tab label="Performance Analysis" />
              <Tab label="Weaknesses" />
              <Tab label="Predictions" />
              <Tab label="Recommendations" />
            </Tabs>
            
            <TabPanel value={tabValue} index={0}>
              {/* Overview Tab */}
              <Box display="flex" gap={3} flexWrap="wrap">
                <Box flex={1} minWidth={300}>
                  <Card>
                    <CardContent>
                      <Typography variant="subtitle2" color="text.secondary">
                        Academic Performance
                      </Typography>
                      <Typography variant="h4" sx={{ mt: 1 }}>
                        {student?.cgpa?.toFixed(2)}
                      </Typography>
                      <Typography variant="caption">CGPA</Typography>
                      
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="body2">
                          Latest SGPA: {student?.latest_sgpa?.toFixed(2)}
                        </Typography>
                        <Typography variant="body2">
                          Attendance: {student?.attendance?.toFixed(0)}%
                        </Typography>
                        <Box display="flex" alignItems="center" gap={1} sx={{ mt: 1 }}>
                          <TrendingUpIcon 
                            color={
                              student?.improvement_trend === 'improving' ? 'success' :
                              student?.improvement_trend === 'declining' ? 'error' : 'disabled'
                            } 
                            fontSize="small" 
                          />
                          <Typography variant="caption" color="text.secondary">
                            Trend: {student?.improvement_trend}
                          </Typography>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                </Box>
                
                <Box flex={1} minWidth={300}>
                  <Card>
                    <CardContent>
                      <Typography variant="subtitle2" color="text.secondary">
                        Risk Assessment
                      </Typography>
                      <Box sx={{ mt: 2 }}>
                        <Chip
                          label={`Risk: ${student?.risk_level?.toUpperCase()}`}
                          color={
                            student?.risk_level === 'high' ? 'error' :
                            student?.risk_level === 'medium' ? 'warning' :
                            'success'
                          }
                          sx={{ mb: 2 }}
                        />
                        <LinearProgress
                          variant="determinate"
                          value={student?.risk_score || 0}
                          sx={{ mt: 1, mb: 1 }}
                          color={
                            student?.risk_score > 70 ? 'error' :
                            student?.risk_score > 40 ? 'warning' :
                            'success'
                          }
                        />
                        <Typography variant="caption">
                          Risk Score: {student?.risk_score?.toFixed(0)}%
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Box>
                
                <Box flex={1} minWidth={300}>
                  <Card>
                    <CardContent>
                      <Typography variant="subtitle2" color="text.secondary">
                        Quick Stats
                      </Typography>
                      <List dense>
                        <ListItem>
                          <ListItemText
                            primary="Weaknesses"
                            secondary={`${student?.weakness_count || 0} identified`}
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText
                            primary="Recommendations"
                            secondary={`${student?.recommendations_pending || 0} pending`}
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText
                            primary="Profile Complete"
                            secondary={`${student?.profile_completeness || 0}%`}
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText
                            primary="Total Credits"
                            secondary={`${student?.metadata?.total_credits || 0}`}
                          />
                        </ListItem>
                      </List>
                    </CardContent>
                  </Card>
                </Box>
              </Box>
            </TabPanel>
            
            <TabPanel value={tabValue} index={1}>
              {/* Performance Analysis Tab */}
              <Box sx={{ height: 400 }}>
                <PerformanceChart data={getPerformanceData()} />
              </Box>
            </TabPanel>
            
            <TabPanel value={tabValue} index={2}>
              {/* Weaknesses Tab */}
              <WeaknessAnalysisChart
                weaknesses={student?.weaknesses || []}
                onRunAnalysis={handleRunAnalysis}
                analysisRunning={analysisRunning}
              />
            </TabPanel>
            
            <TabPanel value={tabValue} index={3}>
              {/* Predictions Tab */}
              <PredictiveAnalysis
                predictions={detailedData?.predictions}
                historicalData={getPerformanceData()}
              />
            </TabPanel>
            
            <TabPanel value={tabValue} index={4}>
              {/* Recommendations Tab */}
              <RecommendationsList
                recommendations={detailedData?.recommendations || []}
                studentId={student.student_id}
              />
            </TabPanel>
          </>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
        <Button
          variant="contained"
          onClick={handleRunAnalysis}
          disabled={analysisRunning}
          startIcon={analysisRunning ? <CircularProgress size={20} /> : <AnalyticsIcon />}
        >
          {analysisRunning ? 'Analyzing...' : 'Run Deep Analysis'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default StudentDetailModal;