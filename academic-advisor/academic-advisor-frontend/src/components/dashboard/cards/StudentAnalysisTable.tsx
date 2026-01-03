/**
 * Student Analysis Table Component
 * Enterprise-level React component with advanced features
 * Vite-compatible version
 */

import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TableSortLabel,
  Paper,
  TextField,
  IconButton,
  Tooltip,
  Chip,
  Box,
  Typography,
  Button,
  Menu,
  MenuItem,
  Checkbox,
  FormControlLabel,
  LinearProgress,
  Avatar,
  Skeleton,
  Alert,
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Collapse,
  Switch,
  Select,
  FormControl,
  InputLabel,
  Card,
  CardContent,
  CircularProgress,
} from '@mui/material';
import {
  Search as SearchIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Print as PrintIcon,
  Close as CloseIcon,
  Remove as RemoveIcon,
} from '@mui/icons-material';
import { useTheme, styled } from '@mui/material/styles';
import { useDebounce } from 'use-debounce';
import { format, parseISO } from 'date-fns';
import { CSVLink } from 'react-csv';
import { useReactToPrint } from 'react-to-print';

// Types (moved to top for better organization)
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

interface FilterOptions {
  department: string;
  cgpaMin: number;
  cgpaMax: number;
  riskLevel: string;
  semester: number | null;
  hasWeaknesses: boolean;
}

interface SortConfig {
  field: keyof StudentAnalysis;
  direction: 'asc' | 'desc';
}

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

// Mock services and hooks (replace with actual implementations)
const StudentAnalysisService = {
  getStudentsList: async (params: any) => {
    // Mock data - replace with actual API call
    return [
      {
        student_id: 'STU001',
        name: 'John Doe',
        department: 'CS',
        batch: 2023,
        current_semester: 4,
        cgpa: 8.5,
        sgpa_trend: [8.2, 8.4, 8.3, 8.6],
        latest_sgpa: 8.6,
        attendance: 85,
        weaknesses: [
          { subject: 'Mathematics', severity: 'medium', gap: 15, priority: 2 }
        ],
        weakness_count: 1,
        risk_score: 25,
        risk_level: 'low',
        improvement_trend: 'improving',
        recommendations_pending: 2,
        profile_completeness: 90,
        last_updated: new Date().toISOString(),
        metadata: {
          total_credits: 120,
          has_warnings: false,
          analysis_version: '1.0'
        }
      }
    ] as StudentAnalysis[];
  },
  exportToExcel: (data: StudentAnalysis[]) => {
    console.log('Exporting to Excel:', data);
    // Implement actual export logic
  },
  bulkAnalyze: async (studentIds: string[]) => {
    console.log('Bulk analyze:', studentIds);
  },
  sendBulkEmail: async (studentIds: string[]) => {
    console.log('Send bulk email:', studentIds);
  },
  generateBulkReport: async (studentIds: string[]) => {
    console.log('Generate bulk report:', studentIds);
  }
};

const useAuth = () => {
  return { user: { id: '1', name: 'Admin' } };
};

const useWebSocket = (channel: string) => {
  // Mock WebSocket implementation
  return {
    on: (event: string, callback: (data: any) => void) => {
      console.log(`WebSocket listening to ${event} on ${channel}`);
    },
    off: (event: string, callback: (data: any) => void) => {
      console.log(`WebSocket unsubscribed from ${event} on ${channel}`);
    }
  };
};

const StudentDetailModal: React.FC<{
  open: boolean;
  onClose: () => void;
  student: StudentAnalysis;
  onUpdate: (student: StudentAnalysis) => void;
}> = ({ open, onClose, student, onUpdate }) => {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Student Details - {student.name}</DialogTitle>
      <DialogContent>
        <Typography>Detailed view for {student.student_id}</Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

const PerformanceChart: React.FC<{ data: ChartPerformanceData }> = ({ data }) => {
  return (
    <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Typography variant="body2" color="text.secondary">
        Performance Chart - Trend: {data.trend}, Change: {data.percentageChange.toFixed(1)}%
      </Typography>
    </Box>
  );
};

// Styled Components
const StyledTableContainer = styled(TableContainer)(({ theme }: { theme: any }) => ({
  maxHeight: 'calc(100vh - 300px)',
  '&::-webkit-scrollbar': {
    width: 8,
    height: 8,
  },
  '&::-webkit-scrollbar-track': {
    backgroundColor: theme.palette.background.default,
  },
  '&::-webkit-scrollbar-thumb': {
    backgroundColor: theme.palette.primary.light,
    borderRadius: 4,
  },
}));

const StyledTableRow = styled(TableRow)(({ theme }: { theme: any }) => ({
  cursor: 'pointer',
  transition: 'all 0.3s ease',
  '&:hover': {
    backgroundColor: theme.palette.action.hover,
    transform: 'translateX(2px)',
  },
  '&.selected': {
    backgroundColor: theme.palette.action.selected,
  },
}));

const RiskChip = styled(Chip)<{ risklevel: 'low' | 'medium' | 'high' }>(({ theme, risklevel }: { theme: any; risklevel: 'low' | 'medium' | 'high' }) => ({
  fontWeight: 'bold',
  ...(risklevel === 'high' && {
    backgroundColor: theme.palette.error.light,
    color: theme.palette.error.contrastText,
  }),
  ...(risklevel === 'medium' && {
    backgroundColor: theme.palette.warning.light,
    color: theme.palette.warning.contrastText,
  }),
  ...(risklevel === 'low' && {
    backgroundColor: theme.palette.success.light,
    color: theme.palette.success.contrastText,
  }),
}));

const TrendIcon = styled(Box)<{ trend: string }>(({ theme, trend }: { theme: any; trend: string }) => ({
  display: 'inline-flex',
  alignItems: 'center',
  ...(trend === 'improving' && {
    color: theme.palette.success.main,
  }),
  ...(trend === 'declining' && {
    color: theme.palette.error.main,
  }),
  ...(trend === 'stable' && {
    color: theme.palette.info.main,
  }),
}));

// Helper function to calculate percentage change
const calculatePercentageChange = (trend: number[]): number => {
  if (trend.length < 2) return 0;
  const current = trend[trend.length - 1];
  const previous = trend[trend.length - 2];
  return ((current - previous) / previous) * 100;
};

// RiskBadge Component
const RiskBadge: React.FC<{ risk: string }> = ({ risk }) => {
  const getColor = () => {
    switch (risk?.toLowerCase()) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  return (
    <Chip 
      label={risk || 'Unknown'}
      color={getColor() as 'error' | 'warning' | 'success' | 'default'}
      size="small"
    />
  );
};

// WeaknessIndicator Component
const WeaknessIndicator: React.FC<{ weaknesses: any[] }> = ({ weaknesses }) => {
  return (
    <Chip 
      label={`${weaknesses.length} weaknesses`}
      color={weaknesses.length > 0 ? 'error' : 'default'}
      size="small"
    />
  );
};

// Main Component
export const StudentAnalysisTable: React.FC = () => {
  const theme = useTheme();
  const { user } = useAuth();
  const service = StudentAnalysisService;
  const tableRef = useRef<HTMLDivElement>(null);
  const ws = useWebSocket('student-analysis');

  // State Management
  const [students, setStudents] = useState<StudentAnalysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStudent, setSelectedStudent] = useState<StudentAnalysis | null>(null);
  const [selectedRows, setSelectedRows] = useState<Set<string>>(new Set());
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  
  // Pagination & Sorting
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    field: 'cgpa',
    direction: 'desc',
  });
  
  // Filtering
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm] = useDebounce(searchTerm, 300);
  const [filters, setFilters] = useState<FilterOptions>({
    department: '',
    cgpaMin: 0,
    cgpaMax: 10,
    riskLevel: '',
    semester: null,
    hasWeaknesses: false,
  });
  const [filterMenuAnchor, setFilterMenuAnchor] = useState<null | HTMLElement>(null);
  
  // UI State
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'warning' | 'info';
  }>({
    open: false,
    message: '',
    severity: 'info',
  });
  const [columnVisibility] = useState({
    student_id: true,
    name: true,
    department: true,
    batch: true,
    semester: true,
    cgpa: true,
    latest_sgpa: true,
    attendance: true,
    weaknesses: true,
    risk: true,
    trend: true,
    recommendations: true,
    actions: true,
  });
  const [autoRefresh, setAutoRefresh] = useState(false);

  // Data Fetching
  const fetchStudents = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await service.getStudentsList({
        skip: page * rowsPerPage,
        limit: rowsPerPage,
        department: filters.department,
        cgpaMin: filters.cgpaMin,
        cgpaMax: filters.cgpaMax,
        sortBy: sortConfig.field,
        sortOrder: sortConfig.direction,
      });
      
      setStudents(response);
    } catch (err) {
      setError('Failed to fetch student data. Please try again.');
      console.error('Error fetching students:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [page, rowsPerPage, filters, sortConfig]);

  // Initial Load & Updates
  useEffect(() => {
    fetchStudents();
  }, [fetchStudents]);

  // WebSocket Updates
  useEffect(() => {
    if (ws) {
      const handleStudentUpdate = (data: any) => {
        setStudents(prev => {
          const index = prev.findIndex(s => s.student_id === data.student_id);
          if (index !== -1) {
            const updated = [...prev];
            updated[index] = { ...updated[index], ...data };
            return updated;
          }
          return prev;
        });
      };

      ws.on('student-update', handleStudentUpdate);
      
      return () => {
        ws.off('student-update', handleStudentUpdate);
      };
    }
  }, [ws]);

  // Auto-refresh
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        handleRefresh();
      }, 30000); // Refresh every 30 seconds
      
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  // Filtered & Sorted Data
  const filteredStudents = useMemo(() => {
    let filtered = [...students];
    
    // Search filter
    if (debouncedSearchTerm) {
      filtered = filtered.filter(student =>
        student.name.toLowerCase().includes(debouncedSearchTerm.toLowerCase()) ||
        student.student_id.toLowerCase().includes(debouncedSearchTerm.toLowerCase())
      );
    }
    
    // Risk level filter
    if (filters.riskLevel) {
      filtered = filtered.filter(student => student.risk_level === filters.riskLevel);
    }
    
    // Semester filter
    if (filters.semester) {
      filtered = filtered.filter(student => student.current_semester === filters.semester);
    }
    
    // Has weaknesses filter
    if (filters.hasWeaknesses) {
      filtered = filtered.filter(student => student.weakness_count > 0);
    }
    
    return filtered;
  }, [students, debouncedSearchTerm, filters]);

  // Handlers
  const handleSort = (field: keyof StudentAnalysis) => {
    setSortConfig(prev => ({
      field,
      direction: prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  const handleRowClick = (student: StudentAnalysis) => {
    setSelectedStudent(student);
    setDetailModalOpen(true);
  };

  const handleRowExpand = (event: React.MouseEvent<HTMLButtonElement>, studentId: string) => {
    event.stopPropagation();
    setExpandedRows(prev => {
      const newSet = new Set(prev);
      if (newSet.has(studentId)) {
        newSet.delete(studentId);
      } else {
        newSet.add(studentId);
      }
      return newSet;
    });
  };

  const handleRowSelect = (studentId: string) => {
    setSelectedRows(prev => {
      const newSet = new Set(prev);
      if (newSet.has(studentId)) {
        newSet.delete(studentId);
      } else {
        newSet.add(studentId);
      }
      return newSet;
    });
  };

  const handleSelectAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      setSelectedRows(new Set(filteredStudents.map(s => s.student_id)));
    } else {
      setSelectedRows(new Set());
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchStudents();
    setSnackbar({
      open: true,
      message: 'Data refreshed successfully',
      severity: 'success',
    });
  };

  const handleExport = (format: 'csv' | 'excel' | 'pdf') => {
    if (format === 'excel') {
      service.exportToExcel(filteredStudents);
    } else if (format === 'pdf') {
      handlePrint();
    }
  };

  const handlePrint = useReactToPrint({
    contentRef: tableRef,
    documentTitle: `Student Analysis Report - ${format(new Date(), 'yyyy-MM-dd')}`,
  });

  const handleBulkAction = async (action: string) => {
    if (selectedRows.size === 0) {
      setSnackbar({
        open: true,
        message: 'Please select students first',
        severity: 'warning',
      });
      return;
    }
    
    try {
      switch (action) {
        case 'analyze':
          await service.bulkAnalyze(Array.from(selectedRows));
          break;
        case 'email':
          await service.sendBulkEmail(Array.from(selectedRows));
          break;
        case 'report':
          await service.generateBulkReport(Array.from(selectedRows));
          break;
      }
      
      setSnackbar({
        open: true,
        message: `${action} completed for ${selectedRows.size} students`,
        severity: 'success',
      });
      setSelectedRows(new Set());
    } catch (error) {
      setSnackbar({
        open: true,
        message: `Failed to perform ${action}`,
        severity: 'error',
      });
    }
  };

  const handleAutoRefreshChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setAutoRefresh(event.target.checked);
  };

  // Render helpers
  const renderTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving':
        return <TrendingUpIcon fontSize="small" />;
      case 'declining':
        return <TrendingDownIcon fontSize="small" />;
      default:
        return <RemoveIcon fontSize="small" />;
    }
  };

  const renderWeaknesses = (weaknesses: Weakness[]) => {
    if (!weaknesses || weaknesses.length === 0) {
      return <Chip label="None" size="small" color="success" />;
    }
    
    const topWeaknesses = weaknesses.slice(0, 2);
    const remaining = weaknesses.length - 2;
    
    return (
      <Box display="flex" gap={0.5} flexWrap="wrap">
        {topWeaknesses.map((w, index) => (
          <Tooltip key={index} title={`${w.subject} - Gap: ${w.gap}%`}>
            <Chip
              label={w.subject}
              size="small"
              color={
                w.severity === 'critical' ? 'error' :
                w.severity === 'high' ? 'warning' :
                'default'
              }
            />
          </Tooltip>
        ))}
        {remaining > 0 && (
          <Chip label={`+${remaining} more`} size="small" variant="outlined" />
        )}
      </Box>
    );
  };

  const renderExpandedRow = (student: StudentAnalysis) => {
    // Create data that matches the PerformanceChart's expected format
    const performanceData: ChartPerformanceData = {
      currentSGPI: student.latest_sgpa,
      previousSGPI: student.sgpa_trend[student.sgpa_trend.length - 2] || student.latest_sgpa,
      trend: student.improvement_trend === 'improving' ? 'up' : 
             student.improvement_trend === 'declining' ? 'down' : 'stable',
      percentageChange: calculatePercentageChange(student.sgpa_trend),
      semesterWiseData: student.sgpa_trend.map((sgpa, index) => ({
        semester: index + 1, // Use number instead of string
        sgpi: sgpa, // Use sgpi instead of sgpa to match expected interface
        credits: 20, // Default value
        courses: 6, // Default value
      }))
    };

    return (
      <TableRow>
        <TableCell colSpan={Object.values(columnVisibility).filter(v => v).length + 1}>
          <Collapse in={expandedRows.has(student.student_id)} timeout="auto" unmountOnExit>
            <Box margin={2}>
              <Box display="flex" gap={2} flexWrap="wrap">
                <Box flex={1} minWidth={300}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Performance Trend
                      </Typography>
                      <Box sx={{ height: 200 }}>
                        <PerformanceChart data={performanceData} />
                      </Box>
                    </CardContent>
                  </Card>
                </Box>
                <Box flex={1} minWidth={300}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Detailed Metrics
                      </Typography>
                      <Box display="flex" flexDirection="column" gap={1}>
                        <Typography variant="body2">
                          <strong>Total Credits:</strong> {student.metadata.total_credits}
                        </Typography>
                        <Typography variant="body2">
                          <strong>Profile Completeness:</strong> {student.profile_completeness}%
                        </Typography>
                        <Typography variant="body2">
                          <strong>Pending Recommendations:</strong> {student.recommendations_pending}
                        </Typography>
                        <Typography variant="body2">
                          <strong>Last Updated:</strong> {format(parseISO(student.last_updated), 'PPP')}
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Box>
              </Box>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    );
  };

  // Loading state
  if (loading && students.length === 0) {
    return (
      <Box p={3}>
        {[...Array(5)].map((_, index) => (
          <Skeleton key={index} variant="rectangular" height={60} sx={{ mb: 1 }} />
        ))}
      </Box>
    );
  }

  // Error state
  if (error) {
    return (
      <Alert severity="error" action={
        <Button color="inherit" size="small" onClick={handleRefresh}>
          Retry
        </Button>
      }>
        {error}
      </Alert>
    );
  }

  return (
    <Box>
      {/* Header Controls */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5" component="h2">
          Student Analysis Dashboard
        </Typography>
        
        <Box display="flex" gap={1} alignItems="center">
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={handleAutoRefreshChange}
                size="small"
              />
            }
            label="Auto-refresh"
          />
          
          <Tooltip title="Refresh data">
            <IconButton onClick={handleRefresh} disabled={refreshing}>
              {refreshing ? <CircularProgress size={20} /> : <RefreshIcon />}
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Export data">
            <IconButton onClick={(e: React.MouseEvent<HTMLElement>) => setFilterMenuAnchor(e.currentTarget)}>
              <DownloadIcon />
            </IconButton>
          </Tooltip>
          
          <Menu
            anchorEl={filterMenuAnchor}
            open={Boolean(filterMenuAnchor)}
            onClose={() => setFilterMenuAnchor(null)}
          >
            <MenuItem onClick={() => handleExport('csv')}>
              <CSVLink
                data={filteredStudents}
                filename={`student-analysis-${format(new Date(), 'yyyy-MM-dd')}.csv`}
                style={{ textDecoration: 'none', color: 'inherit' }}
              >
                Export as CSV
              </CSVLink>
            </MenuItem>
            <MenuItem onClick={() => handleExport('excel')}>Export as Excel</MenuItem>
            <MenuItem onClick={() => handleExport('pdf')}>Export as PDF</MenuItem>
          </Menu>
          
          <Tooltip title="Print">
            <IconButton onClick={handlePrint}>
              <PrintIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>
      
      {/* Filters and Search */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box display="flex" gap={2} alignItems="center" flexWrap="wrap">
          <Box flex={1} minWidth={200}>
            <TextField
              fullWidth
              variant="outlined"
              size="small"
              placeholder="Search by name or ID..."
              value={searchTerm}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
            />
          </Box>
          
          <Box minWidth={150}>
            <FormControl fullWidth size="small">
              <InputLabel>Department</InputLabel>
              <Select
                value={filters.department}
                onChange={(e) => setFilters(prev => ({ ...prev, department: e.target.value }))}
                label="Department"
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="CS">Computer Science</MenuItem>
                <MenuItem value="ECE">Electronics</MenuItem>
                <MenuItem value="MECH">Mechanical</MenuItem>
                <MenuItem value="CIVIL">Civil</MenuItem>
                <MenuItem value="EEE">Electrical</MenuItem>
              </Select>
            </FormControl>
          </Box>
          
          <Box minWidth={150}>
            <FormControl fullWidth size="small">
              <InputLabel>Risk Level</InputLabel>
              <Select
                value={filters.riskLevel}
                onChange={(e) => setFilters(prev => ({ ...prev, riskLevel: e.target.value }))}
                label="Risk Level"
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="low">Low</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="high">High</MenuItem>
              </Select>
            </FormControl>
          </Box>
          
          <FormControlLabel
            control={
              <Checkbox
                checked={filters.hasWeaknesses}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFilters(prev => ({ ...prev, hasWeaknesses: e.target.checked }))}
              />
            }
            label="Has Weaknesses"
          />
          
          {selectedRows.size > 0 && (
            <Box display="flex" gap={1} alignItems="center">
              <Button
                size="small"
                variant="contained"
                onClick={() => handleBulkAction('analyze')}
              >
                Analyze ({selectedRows.size})
              </Button>
              <IconButton size="small" onClick={() => setSelectedRows(new Set())}>
                <CloseIcon />
              </IconButton>
            </Box>
          )}
        </Box>
      </Paper>
      
      {/* Main Table */}
      <Paper ref={tableRef}>
        <StyledTableContainer>
          <Table stickyHeader size="medium">
            <TableHead>
              <TableRow>
                <TableCell padding="checkbox">
                  <Checkbox
                    indeterminate={selectedRows.size > 0 && selectedRows.size < filteredStudents.length}
                    checked={selectedRows.size === filteredStudents.length && filteredStudents.length > 0}
                    onChange={handleSelectAll}
                  />
                </TableCell>
                
                {columnVisibility.student_id && (
                  <TableCell>
                    <TableSortLabel
                      active={sortConfig.field === 'student_id'}
                      direction={sortConfig.direction}
                      onClick={() => handleSort('student_id')}
                    >
                      Student ID
                    </TableSortLabel>
                  </TableCell>
                )}
                
                {columnVisibility.name && (
                  <TableCell>
                    <TableSortLabel
                      active={sortConfig.field === 'name'}
                      direction={sortConfig.direction}
                      onClick={() => handleSort('name')}
                    >
                      Name
                    </TableSortLabel>
                  </TableCell>
                )}
                
                {columnVisibility.department && (
                  <TableCell>Department</TableCell>
                )}
                
                {columnVisibility.semester && (
                  <TableCell align="center">Semester</TableCell>
                )}
                
                {columnVisibility.cgpa && (
                  <TableCell align="center">
                    <TableSortLabel
                      active={sortConfig.field === 'cgpa'}
                      direction={sortConfig.direction}
                      onClick={() => handleSort('cgpa')}
                    >
                      CGPA
                    </TableSortLabel>
                  </TableCell>
                )}
                
                {columnVisibility.latest_sgpa && (
                  <TableCell align="center">Latest SGPA</TableCell>
                )}
                
                {columnVisibility.attendance && (
                  <TableCell align="center">
                    <TableSortLabel
                      active={sortConfig.field === 'attendance'}
                      direction={sortConfig.direction}
                      onClick={() => handleSort('attendance')}
                    >
                      Attendance
                    </TableSortLabel>
                  </TableCell>
                )}
                
                {columnVisibility.weaknesses && (
                  <TableCell>Weaknesses</TableCell>
                )}
                
                {columnVisibility.risk && (
                  <TableCell align="center">
                    <TableSortLabel
                      active={sortConfig.field === 'risk_score'}
                      direction={sortConfig.direction}
                      onClick={() => handleSort('risk_score')}
                    >
                      Risk
                    </TableSortLabel>
                  </TableCell>
                )}
                
                {columnVisibility.trend && (
                  <TableCell align="center">Trend</TableCell>
                )}
                
                {columnVisibility.actions && (
                  <TableCell align="center">Actions</TableCell>
                )}
              </TableRow>
            </TableHead>
            
            <TableBody>
              {filteredStudents
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((student) => (
                  <React.Fragment key={student.student_id}>
                    <StyledTableRow
                      hover
                      className={selectedRows.has(student.student_id) ? 'selected' : ''}
                      onClick={() => handleRowClick(student)}
                    >
                      <TableCell padding="checkbox" onClick={(e: React.MouseEvent) => e.stopPropagation()}>
                        <Checkbox
                          checked={selectedRows.has(student.student_id)}
                          onChange={() => handleRowSelect(student.student_id)}
                        />
                      </TableCell>
                      
                      {columnVisibility.student_id && (
                        <TableCell>{student.student_id}</TableCell>
                      )}
                      
                      {columnVisibility.name && (
                        <TableCell>
                          <Box display="flex" alignItems="center" gap={1}>
                            <Avatar sx={{ width: 32, height: 32 }}>
                              {student.name.charAt(0)}
                            </Avatar>
                            <Typography variant="body2">{student.name}</Typography>
                          </Box>
                        </TableCell>
                      )}
                      
                      {columnVisibility.department && (
                        <TableCell>{student.department}</TableCell>
                      )}
                      
                      {columnVisibility.semester && (
                        <TableCell align="center">{student.current_semester}</TableCell>
                      )}
                      
                      {columnVisibility.cgpa && (
                        <TableCell align="center">
                          <Typography
                            variant="body2"
                            color={
                              student.cgpa >= 8.5 ? 'success.main' :
                              student.cgpa >= 7.0 ? 'primary.main' :
                              student.cgpa >= 5.5 ? 'warning.main' :
                              'error.main'
                            }
                            fontWeight="bold"
                          >
                            {student.cgpa.toFixed(2)}
                          </Typography>
                        </TableCell>
                      )}
                      
                      {columnVisibility.latest_sgpa && (
                        <TableCell align="center">
                          {student.latest_sgpa.toFixed(2)}
                        </TableCell>
                      )}
                      
                      {columnVisibility.attendance && (
                        <TableCell align="center">
                          <Box display="flex" alignItems="center" gap={0.5}>
                            <LinearProgress
                              variant="determinate"
                              value={student.attendance}
                              sx={{ width: 60, height: 6 }}
                              color={student.attendance >= 75 ? 'success' : 'error'}
                            />
                            <Typography variant="caption">
                              {student.attendance.toFixed(0)}%
                            </Typography>
                          </Box>
                        </TableCell>
                      )}
                      
                      {columnVisibility.weaknesses && (
                        <TableCell>{renderWeaknesses(student.weaknesses)}</TableCell>
                      )}
                      
                      {columnVisibility.risk && (
                        <TableCell align="center">
                          <RiskChip
                            label={student.risk_level.toUpperCase()}
                            size="small"
                            risklevel={student.risk_level}
                          />
                        </TableCell>
                      )}
                      
                      {columnVisibility.trend && (
                        <TableCell align="center">
                          <TrendIcon trend={student.improvement_trend}>
                            {renderTrendIcon(student.improvement_trend)}
                          </TrendIcon>
                        </TableCell>
                      )}
                      
                      {columnVisibility.actions && (
                        <TableCell align="center" onClick={(e: React.MouseEvent) => e.stopPropagation()}>
                          <IconButton
                            size="small"
                            onClick={(e) => handleRowExpand(e, student.student_id)}
                          >
                            {expandedRows.has(student.student_id) ? 
                              <ExpandLessIcon /> : <ExpandMoreIcon />}
                          </IconButton>
                        </TableCell>
                      )}
                    </StyledTableRow>
                    
                    {expandedRows.has(student.student_id) && renderExpandedRow(student)}
                  </React.Fragment>
                ))}
              
              {filteredStudents.length === 0 && (
                <TableRow>
                  <TableCell colSpan={Object.values(columnVisibility).filter(v => v).length + 1} align="center">
                    <Box py={4}>
                      <Typography variant="body1" color="text.secondary">
                        No students found matching the criteria
                      </Typography>
                    </Box>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </StyledTableContainer>
        
        <TablePagination
          component="div"
          count={filteredStudents.length}
          page={page}
          onPageChange={(_: unknown, newPage: number) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e: React.ChangeEvent<HTMLInputElement>) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
          rowsPerPageOptions={[10, 25, 50, 100]}
        />
      </Paper>
      
      {/* Student Detail Modal */}
      {selectedStudent && (
        <StudentDetailModal
          open={detailModalOpen}
          onClose={() => setDetailModalOpen(false)}
          student={selectedStudent}
          onUpdate={(updated: StudentAnalysis) => {
            setStudents(prev => prev.map(s => 
              s.student_id === updated.student_id ? updated : s
            ));
          }}
        />
      )}
      
      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
          severity={snackbar.severity}
          variant="filled"
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default StudentAnalysisTable;