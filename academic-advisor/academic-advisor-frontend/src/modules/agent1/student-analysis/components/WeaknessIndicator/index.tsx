// src/modules/agent1/student-analysis/components/WeaknessIndicator/index.tsx
import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  CircularProgress,
  Alert,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Button,
  Tooltip,
  IconButton,
  Stack,
  Divider,
  Grid,
  Paper
} from '@mui/material';
import {
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as CheckIcon,
  ExpandMore as ExpandMoreIcon,
  Lightbulb as LightbulbIcon,
  School as SchoolIcon,
  TrendingDown as TrendingDownIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
  PlayArrow as PlayIcon,
  OpenInNew as OpenInNewIcon,
  BookmarkBorder as BookmarkIcon,
  AccessTime as TimeIcon,
  TrendingUp as TrendingUpIcon
} from '@mui/icons-material';
import { useWeaknessAnalysis } from '../../../performance-analytics/hooks/useWeaknessAnalysis';
import { WeaknessChart } from './WeaknessChart';
import { SeverityLevel, AnalysisBasis } from '../../../../../services/weakness.service';
import toast from 'react-hot-toast';

const GridItem = Grid as any;

interface WeaknessIndicatorProps {
  studentId: string;
  studentInterests?: string[];
  recommendedElectives?: string[];
  honoursMinors?: string[];
  autoAnalyze?: boolean;
  showControls?: boolean;
}

type AnalysisType = 'interest' | 'electives' | 'honours_minors' | 'performance' | 'combined';

export const WeaknessIndicator: React.FC<WeaknessIndicatorProps> = ({
  studentId,
  studentInterests = [],
  recommendedElectives = [],
  honoursMinors = [],
  autoAnalyze = true,
  showControls = true
}) => {
  const [analysisType, setAnalysisType] = useState<AnalysisType>('combined');
  const [expandedWeakness, setExpandedWeakness] = useState<string | false>(false);

  const {
    weaknessData,
    summary,
    loading,
    error,
    analyzing,
    analyzeByInterest,
    analyzeByElectives,
    analyzeByHonours,
    analyzeByPerformance,
    analyzeCombined,
    refreshAnalysis,
    clearError
  } = useWeaknessAnalysis(studentId, {
    analysisBasis: analysisType,
    autoLoad: autoAnalyze,
    interests: studentInterests,
    electives: recommendedElectives,
    honours: honoursMinors
  });

  // Auto-analyze on mount if enabled
  useEffect(() => {
    if (autoAnalyze && !weaknessData && !loading) {
      handleAnalysis();
    }
  }, [autoAnalyze]);

  const handleAnalysis = async () => {
    try {
      switch (analysisType) {
        case 'interest':
          await analyzeByInterest(studentInterests);
          break;
        case 'electives':
          await analyzeByElectives(recommendedElectives);
          break;
        case 'honours_minors':
          await analyzeByHonours(honoursMinors);
          break;
        case 'performance':
          await analyzeByPerformance();
          break;
        case 'combined':
          await analyzeCombined(studentInterests, recommendedElectives, honoursMinors);
          break;
      }
    } catch (err) {
      console.error('Analysis error:', err);
    }
  };

  const getSeverityColor = (severity: SeverityLevel): 'error' | 'warning' | 'info' | 'success' => {
    switch (severity) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      default: return 'success';
    }
  };

  const getSeverityIcon = (severity: SeverityLevel) => {
    switch (severity) {
      case 'critical': return <ErrorIcon color="error" />;
      case 'high': return <WarningIcon color="warning" />;
      case 'medium': return <TrendingDownIcon color="info" />;
      default: return <CheckIcon color="success" />;
    }
  };

  const getRiskLevel = (score: number): { text: string; color: string } => {
    if (score >= 75) return { text: 'Critical Risk', color: '#d32f2f' };
    if (score >= 50) return { text: 'High Risk', color: '#f57c00' };
    if (score >= 25) return { text: 'Moderate Risk', color: '#fbc02d' };
    return { text: 'Low Risk', color: '#388e3c' };
  };

  const getAnalysisBasisLabel = (basis: string): string => {
    const labels: { [key: string]: string } = {
      'interest': 'Based on your interests',
      'electives': 'Based on recommended electives',
      'honours_minors': 'Based on honours/minors',
      'performance': 'Based on academic performance',
      'combined': 'Comprehensive analysis'
    };
    return labels[basis] || basis;
  };

  if (loading) {
    return (
      <Card sx={{ height: '100%' }}>
        <CardContent>
          <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" p={4}>
            <CircularProgress size={48} />
            <Typography variant="body2" color="text.secondary" mt={2}>
              Loading weakness analysis...
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" display="flex" alignItems="center" gap={1}>
            <TrendingDownIcon color="primary" />
            Weakness Analysis
          </Typography>
          
          {showControls && (
            <Stack direction="row" spacing={1}>
              <Tooltip title="Refresh Analysis">
                <IconButton 
                  onClick={refreshAnalysis} 
                  disabled={analyzing}
                  size="small"
                >
                  <RefreshIcon className={analyzing ? 'animate-spin' : ''} />
                </IconButton>
              </Tooltip>
            </Stack>
          )}
        </Box>

        {/* Analysis Type Selector */}
        {showControls && (
          <FormControl fullWidth size="small" sx={{ mb: 2 }}>
            <InputLabel>Analysis Based On</InputLabel>
            <Select
              value={analysisType}
              label="Analysis Based On"
              onChange={(e) => setAnalysisType(e.target.value as AnalysisType)}
            >
              <MenuItem value="combined">
                <Box display="flex" alignItems="center">
                  <span style={{ marginLeft: 8 }}>Comprehensive (All Factors)</span>
                </Box>
              </MenuItem>
              <MenuItem value="interest">
                <span style={{ marginLeft: 8 }}>My Interests</span>
              </MenuItem>
              <MenuItem value="electives">
                <span style={{ marginLeft: 8 }}>Recommended Electives</span>
              </MenuItem>
              <MenuItem value="honours_minors">
                <span style={{ marginLeft: 8 }}>Honours/Minors</span>
              </MenuItem>
              <MenuItem value="performance">
                <span style={{ marginLeft: 8 }}>Academic Performance</span>
              </MenuItem>
            </Select>
          </FormControl>
        )}

        {/* Run Analysis Button */}
        {showControls && !weaknessData && !analyzing && (
          <Button
            fullWidth
            variant="contained"
            startIcon={<PlayIcon />}
            onClick={handleAnalysis}
            sx={{ mb: 2 }}
          >
            Run {analysisType === 'combined' ? 'Comprehensive' : ''} Analysis
          </Button>
        )}

        {/* Error Display */}
        {error && (
          <Alert 
            severity="error" 
            sx={{ mb: 2 }}
            onClose={clearError}
          >
            {error}
          </Alert>
        )}

        {/* Analyzing State */}
        {analyzing && (
          <Box sx={{ mb: 2 }}>
            <LinearProgress />
            <Typography variant="caption" color="text.secondary" display="block" textAlign="center" mt={1}>
              Analyzing weaknesses...
            </Typography>
          </Box>
        )}

        {/* Analysis Results */}
        {weaknessData && !analyzing && (
          <>
            {/* Analysis Info */}
            <Paper variant="outlined" sx={{ p: 2, mb: 2, bgcolor: 'primary.50' }}>
              <Typography variant="caption" color="text.secondary" display="block">
                {getAnalysisBasisLabel(weaknessData.analysis_basis)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Last analyzed: {new Date(weaknessData.analysis_timestamp).toLocaleString()}
              </Typography>
            </Paper>

            {/* Overall Risk Score */}
            <Box sx={{ mb: 3, p: 2, bgcolor: 'background.default', borderRadius: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Overall Risk Score
              </Typography>
              <Box display="flex" alignItems="center" gap={2}>
                <LinearProgress
                  variant="determinate"
                  value={weaknessData.overall_risk_score}
                  color={
                    weaknessData.overall_risk_score >= 75 ? 'error' :
                    weaknessData.overall_risk_score >= 50 ? 'warning' : 'success'
                  }
                  sx={{ flexGrow: 1, height: 10, borderRadius: 5 }}
                />
                <Typography variant="h6" fontWeight="bold">
                  {weaknessData.overall_risk_score.toFixed(1)}%
                </Typography>
              </Box>
              <Typography 
                variant="caption" 
                sx={{ 
                  color: getRiskLevel(weaknessData.overall_risk_score).color,
                  fontWeight: 'bold'
                }}
              >
                {getRiskLevel(weaknessData.overall_risk_score).text}
              </Typography>
            </Box>

            {/* Summary Stats */}
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <GridItem item xs={6} sm={3}>
                <Paper variant="outlined" sx={{ p: 1.5, textAlign: 'center' }}>
                  <Typography variant="h6" color="error.main">{weaknessData.critical_count}</Typography>
                  <Typography variant="caption">Critical</Typography>
                </Paper>
              </GridItem>
              <GridItem item xs={6} sm={3}>
                <Paper variant="outlined" sx={{ p: 1.5, textAlign: 'center' }}>
                  <Typography variant="h6" color="warning.main">{weaknessData.high_count}</Typography>
                  <Typography variant="caption">High</Typography>
                </Paper>
              </GridItem>
              <GridItem item xs={6} sm={3}>
                <Paper variant="outlined" sx={{ p: 1.5, textAlign: 'center' }}>
                  <Typography variant="h6" color="info.main">{weaknessData.medium_count}</Typography>
                  <Typography variant="caption">Medium</Typography>
                </Paper>
              </GridItem>
              <GridItem item xs={6} sm={3}>
                <Paper variant="outlined" sx={{ p: 1.5, textAlign: 'center' }}>
                  <Typography variant="h6" color="success.main">{weaknessData.low_count}</Typography>
                  <Typography variant="caption">Low</Typography>
                </Paper>
              </GridItem>
            </Grid>

            {/* Priority Areas */}
            {weaknessData.priority_areas.length > 0 && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" gutterBottom display="flex" alignItems="center" gap={1}>
                  <WarningIcon fontSize="small" color="error" />
                  Priority Areas (Top {weaknessData.priority_areas.length})
                </Typography>
                <Box display="flex" gap={1} flexWrap="wrap">
                  {weaknessData.priority_areas.map((area, index) => (
                    <Chip
                      key={index}
                      label={area}
                      color="error"
                      variant="outlined"
                      size="small"
                      icon={<WarningIcon />}
                    />
                  ))}
                </Box>
              </Box>
            )}

            {/* Key Insights */}
            {weaknessData.key_insights && weaknessData.key_insights.length > 0 && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" gutterBottom display="flex" alignItems="center" gap={1}>
                  <InfoIcon fontSize="small" color="primary" />
                  Key Insights
                </Typography>
                <List dense>
                  {weaknessData.key_insights.map((insight, index) => (
                    <ListItem key={index}>
                      <ListItemIcon sx={{ minWidth: 30 }}>
                        <LightbulbIcon fontSize="small" color="primary" />
                      </ListItemIcon>
                      <ListItemText 
                        primary={insight}
                        primaryTypographyProps={{ variant: 'body2' }}
                      />
                    </ListItem>
                  ))}
                </List>
              </Box>
            )}

            {/* Weakness Chart */}
            {weaknessData.weaknesses.length > 0 && (
              <Box sx={{ mb: 3, height: 250 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Weakness Distribution
                </Typography>
                <WeaknessChart weaknesses={weaknessData.weaknesses} />
              </Box>
            )}

            {/* Detailed Weaknesses */}
            <Typography variant="subtitle2" gutterBottom>
              Detailed Analysis ({weaknessData.weaknesses.length} areas identified)
            </Typography>
            
            {weaknessData.weaknesses.length === 0 ? (
              <Alert severity="success" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  No significant weaknesses detected! Keep up the good work.
                </Typography>
              </Alert>
            ) : (
              <Box sx={{ mb: 2 }}>
                {weaknessData.weaknesses.map((weakness, index) => (
                  <Accordion 
                    key={weakness.id || index}
                    expanded={expandedWeakness === weakness.id}
                    onChange={(_, isExpanded) => setExpandedWeakness(isExpanded ? weakness.id : false)}
                  >
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Box display="flex" alignItems="center" gap={2} width="100%">
                        {getSeverityIcon(weakness.severity)}
                        <Box flexGrow={1}>
                          <Typography variant="subtitle2">{weakness.subject}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {weakness.related_to}
                          </Typography>
                        </Box>
                        <Chip
                          label={`${weakness.current_score.toFixed(0)}%`}
                          size="small"
                          color={getSeverityColor(weakness.severity)}
                        />
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails>
                      {/* Topic */}
                      {weakness.topic && (
                        <Typography variant="body2" gutterBottom>
                          <strong>Topic:</strong> {weakness.topic}
                        </Typography>
                      )}

                      {/* Gap & Target */}
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" gutterBottom>
                          <strong>Gap Analysis:</strong>
                        </Typography>
                        <Box display="flex" alignItems="center" gap={2}>
                          <Typography variant="caption">Current: {weakness.current_score.toFixed(0)}%</Typography>
                          <LinearProgress 
                            variant="determinate" 
                            value={(weakness.current_score / weakness.target_score) * 100}
                            sx={{ flexGrow: 1, height: 6 }}
                            color={getSeverityColor(weakness.severity)}
                          />
                          <Typography variant="caption">Target: {weakness.target_score.toFixed(0)}%</Typography>
                        </Box>
                        <Typography variant="caption" color="text.secondary">
                          Gap: {weakness.gap_percentage.toFixed(0)}% | Confidence: {(weakness.confidence * 100).toFixed(0)}%
                        </Typography>
                      </Box>

                      {/* Impact */}
                      {(weakness.impact_on_interest || weakness.impact_on_elective || weakness.impact_on_career) && (
                        <Alert severity="info" sx={{ mb: 2 }} icon={<InfoIcon />}>
                          <Typography variant="caption">
                            <strong>Impact:</strong> {weakness.impact_on_interest || weakness.impact_on_elective || weakness.impact_on_career}
                          </Typography>
                        </Alert>
                      )}

                      {/* Improvement Suggestions */}
                      <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
                        <LightbulbIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                        Improvement Suggestions
                      </Typography>
                      <List dense>
                        {weakness.improvement_suggestions.map((suggestion, idx) => (
                          <ListItem key={idx}>
                            <ListItemIcon sx={{ minWidth: 30 }}>
                              <CheckIcon fontSize="small" color="success" />
                            </ListItemIcon>
                            <ListItemText 
                              primary={suggestion}
                              primaryTypographyProps={{ variant: 'body2' }}
                            />
                          </ListItem>
                        ))}
                      </List>

                      {/* Estimated Time */}
                      <Box display="flex" alignItems="center" gap={1} sx={{ mt: 2, mb: 2 }}>
                        <TimeIcon fontSize="small" color="action" />
                        <Typography variant="caption" color="text.secondary">
                          <strong>Estimated improvement time:</strong> {weakness.estimated_improvement_time}
                        </Typography>
                      </Box>

                      {/* Recommended Resources */}
                      {weakness.recommended_resources.length > 0 && (
                        <>
                          <Divider sx={{ my: 2 }} />
                          <Typography variant="subtitle2" sx={{ mb: 1 }}>
                            <SchoolIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
                            Recommended Resources
                          </Typography>
                          <List dense>
                            {weakness.recommended_resources.map((resource, idx) => (
                              <ListItem key={idx}>
                                <ListItemIcon sx={{ minWidth: 30 }}>
                                  <BookmarkIcon fontSize="small" color="primary" />
                                </ListItemIcon>
                                <ListItemText
                                  primary={resource.title}
                                  secondary={`${resource.platform} • ${resource.type}`}
                                  primaryTypographyProps={{ variant: 'body2' }}
                                  secondaryTypographyProps={{ variant: 'caption' }}
                                />
                                {resource.url && (
                                  <IconButton 
                                    size="small" 
                                    href={resource.url} 
                                    target="_blank"
                                    rel="noopener noreferrer"
                                  >
                                    <OpenInNewIcon fontSize="small" />
                                  </IconButton>
                                )}
                              </ListItem>
                            ))}
                          </List>
                        </>
                      )}
                    </AccordionDetails>
                  </Accordion>
                ))}
              </Box>
            )}

            {/* Study Plan */}
            {weaknessData.study_plan && (
              <Box sx={{ mt: 3 }}>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle2" display="flex" alignItems="center" gap={1}>
                      <TrendingUpIcon fontSize="small" color="success" />
                      Personalized Study Plan
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body2" gutterBottom>
                      <strong>Duration:</strong> {weaknessData.study_plan.duration}
                    </Typography>
                    <Typography variant="body2" gutterBottom>
                      <strong>Weekly Commitment:</strong> {weaknessData.study_plan.weekly_commitment || `${weaknessData.study_plan.weekly_hours} hours`}
                    </Typography>

                    {/* Focus Areas */}
                    {weaknessData.study_plan.focus_areas && weaknessData.study_plan.focus_areas.length > 0 && (
                      <>
                        <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>Focus Areas:</Typography>
                        <List dense>
                          {weaknessData.study_plan.focus_areas.map((area: any, idx: number) => (
                            <ListItem key={idx}>
                              <ListItemText
                                primary={`${area.priority}. ${area.topic}`}
                                secondary={`Target: ${area.target_score}% | ${area.weekly_hours} hours/week`}
                                primaryTypographyProps={{ variant: 'body2' }}
                                secondaryTypographyProps={{ variant: 'caption' }}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </>
                    )}

                    {/* Phases */}
                    {weaknessData.study_plan.phases && (
                      <>
                        <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>Learning Phases:</Typography>
                        <List dense>
                          {weaknessData.study_plan.phases.map((phase: any, idx: number) => (
                            <ListItem key={idx}>
                              <ListItemText
                                primary={`${phase.name || `Phase ${idx + 1}`} (Week ${phase.week || phase.weeks})`}
                                secondary={Array.isArray(phase.focus) ? phase.focus.join(', ') : phase.focus}
                                primaryTypographyProps={{ variant: 'body2' }}
                                secondaryTypographyProps={{ variant: 'caption' }}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </>
                    )}

                    {/* Milestones */}
                    {weaknessData.study_plan.milestones && (
                      <>
                        <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>Milestones:</Typography>
                        <List dense>
                          {weaknessData.study_plan.milestones.map((milestone: any, idx: number) => (
                            <ListItem key={idx}>
                              <ListItemIcon sx={{ minWidth: 30 }}>
                                <CheckIcon fontSize="small" color="success" />
                              </ListItemIcon>
                              <ListItemText
                                primary={`Week ${milestone.week}: ${milestone.target}`}
                                primaryTypographyProps={{ variant: 'body2' }}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </>
                    )}
                  </AccordionDetails>
                </Accordion>
              </Box>
            )}

            {/* Improvement Potential */}
            {weaknessData.improvement_potential > 0 && (
              <Alert severity="success" sx={{ mt: 2 }} icon={<TrendingUpIcon />}>
                <Typography variant="body2">
                  <strong>Improvement Potential:</strong> {weaknessData.improvement_potential.toFixed(1)}% 
                  {' '}with focused effort on the identified areas.
                </Typography>
              </Alert>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default WeaknessIndicator;