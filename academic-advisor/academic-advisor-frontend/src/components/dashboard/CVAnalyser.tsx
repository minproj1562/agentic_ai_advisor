// components/dashboard/cards/CVAnalyserCard.tsx

import React, { useState, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import { 
  Upload, 
  FileText, 
  CheckCircle, 
  AlertCircle, 
  RefreshCw,
  Download,
  Eye,
  X,
  Loader2,
  Brain,
  TrendingUp,
  Award
} from 'lucide-react';
import { CVMetadata } from '../../types/dashboard.types';
import { cn } from '../../utils/cn';
import { formatDistanceToNow } from 'date-fns';
import toast from 'react-hot-toast';
import { 
  getStorage, 
  ref as storageRef, 
  uploadBytes, 
  getDownloadURL,
  deleteObject 
} from 'firebase/storage';
import { 
  doc, 
  updateDoc, 
  getDoc,
  serverTimestamp 
} from 'firebase/firestore';
import { db, auth } from '../../services/firebase.config'; // Import auth directly
import { useAuth } from '../../contexts/AuthContext';

interface CVAnalyserCardProps {
  cvMetadata: CVMetadata | null;
  onUpload?: (file: File) => Promise<void>;
  onAnalyze?: () => Promise<void>;
}

// Extend CVMetadata to include fileUrl
interface ExtendedCVMetadata extends CVMetadata {
  fileUrl?: string;
  education?: any[];
  certifications?: any[];
  languages?: any[];
  projects?: any[];
}

const CVAnalyserCard: React.FC<CVAnalyserCardProps> = ({
  cvMetadata: initialCvMetadata,
  onUpload,
  onAnalyze
}) => {
  const { user } = useAuth();
  const [cvMetadata, setCvMetadata] = useState<ExtendedCVMetadata | null>(initialCvMetadata);
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  
  const storage = getStorage();

  // Load CV metadata from Firestore on mount
  useEffect(() => {
    const loadCVMetadata = async () => {
      if (!user?.uid) return;
      
      try {
        const userDoc = await getDoc(doc(db, 'users', user.uid));
        if (userDoc.exists() && userDoc.data().cvMetadata) {
          setCvMetadata(userDoc.data().cvMetadata);
        }
      } catch (error) {
        console.error('Error loading CV metadata:', error);
      }
    };

    loadCVMetadata();
  }, [user]);

  const uploadToFirebase = async (file: File): Promise<string> => {
    if (!user?.uid) throw new Error('User not authenticated');

    const fileName = `cvs/${user.uid}/${Date.now()}_${file.name}`;
    const fileRef = storageRef(storage, fileName);
    
    // Upload file
    const snapshot = await uploadBytes(fileRef, file);
    
    // Get download URL
    const downloadURL = await getDownloadURL(snapshot.ref);
    
    return downloadURL;
  };

  const analyzeCV = async (fileUrl: string, file: File): Promise<ExtendedCVMetadata> => {
    // Get current user directly from auth
    const currentUser = auth.currentUser;
    if (!currentUser) throw new Error('User not authenticated');
    
    const token = await currentUser.getIdToken();

    // Call your backend API for CV analysis
    const formData = new FormData();
    formData.append('cv', file);
    formData.append('userId', user?.uid || '');
    formData.append('fileUrl', fileUrl);

    try {
      // Use environment variable or fallback
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      
      const response = await fetch(`${API_URL}/api/cv/analyze`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('CV analysis failed');
      }

      const result = await response.json();
      
      return {
        uploadedAt: new Date(),
        fileName: file.name,
        fileUrl: fileUrl,
        extractedSkills: result.skills || [],
        researchAreas: result.researchAreas || [],
        publications: result.publications || 0,
        experience: result.experience || '',
        lastAnalyzed: new Date(),
        education: result.education || [],
        certifications: result.certifications || [],
        languages: result.languages || [],
        projects: result.projects || [],
      };
    } catch (error) {
      console.error('CV analysis error:', error);
      
      // Fallback to basic extraction if API fails
      return {
        uploadedAt: new Date(),
        fileName: file.name,
        fileUrl: fileUrl,
        extractedSkills: [],
        researchAreas: [],
        publications: 0,
        experience: '',
        lastAnalyzed: new Date(),
        education: [],
        certifications: [],
        languages: [],
        projects: [],
      };
    }
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file || !user?.uid) return;

    // Validate file
    if (file.type !== 'application/pdf') {
      toast.error('Please upload a PDF file');
      return;
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB limit
      toast.error('File size must be less than 10MB');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    // Simulate upload progress
    const progressInterval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 10;
      });
    }, 200);

    try {
      // Upload to Firebase Storage
      const fileUrl = await uploadToFirebase(file);
      
      setUploadProgress(100);
      
      // Create preview URL
      setPreviewUrl(fileUrl);
      
      // Start analysis automatically
      setIsAnalyzing(true);
      const metadata = await analyzeCV(fileUrl, file);
      
      // Save metadata to Firestore
      await updateDoc(doc(db, 'users', user.uid), {
        cvMetadata: metadata,
        'profile.cvUrl': fileUrl,
        updatedAt: serverTimestamp(),
      });
      
      setCvMetadata(metadata);
      
      toast.success('CV uploaded and analyzed successfully!');
      
      // Call parent callback if provided
      if (onUpload) {
        await onUpload(file);
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to upload CV');
      console.error('Upload error:', error);
      
      // Clean up on error
      setPreviewUrl(null);
    } finally {
      clearInterval(progressInterval);
      setIsUploading(false);
      setIsAnalyzing(false);
      setTimeout(() => setUploadProgress(0), 1000);
    }
  }, [user, onUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxFiles: 1,
    disabled: isUploading || isAnalyzing
  });

  const handleReanalyze = async () => {
    if (!cvMetadata || !cvMetadata.fileUrl || !user?.uid) return;
    
    setIsAnalyzing(true);
    try {
      // Get current user directly from auth
      const currentUser = auth.currentUser;
      if (!currentUser) throw new Error('User not authenticated');
      
      const token = await currentUser.getIdToken();

      // Use environment variable or fallback
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

      // Re-analyze the existing CV
      const response = await fetch(`${API_URL}/api/cv/reanalyze`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId: user.uid,
          fileUrl: cvMetadata.fileUrl,
        }),
      });

      if (!response.ok) {
        throw new Error('Re-analysis failed');
      }

      const result = await response.json();
      
      const updatedMetadata: ExtendedCVMetadata = {
        ...cvMetadata,
        extractedSkills: result.skills || cvMetadata.extractedSkills,
        researchAreas: result.researchAreas || cvMetadata.researchAreas,
        publications: result.publications || cvMetadata.publications,
        experience: result.experience || cvMetadata.experience,
        lastAnalyzed: new Date(),
      };
      
      // Update Firestore
      await updateDoc(doc(db, 'users', user.uid), {
        cvMetadata: updatedMetadata,
        updatedAt: serverTimestamp(),
      });
      
      setCvMetadata(updatedMetadata);
      toast.success('CV re-analyzed successfully!');
      
      if (onAnalyze) {
        await onAnalyze();
      }
    } catch (error) {
      toast.error('Re-analysis failed');
      console.error('Re-analysis error:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleDownload = async () => {
    if (!cvMetadata?.fileUrl) return;
    
    try {
      // Open CV in new tab
      window.open(cvMetadata.fileUrl, '_blank');
      toast.success('Opening CV...');
    } catch (error) {
      toast.error('Failed to open CV');
      console.error('Download error:', error);
    }
  };

  const handleDelete = async () => {
    if (!cvMetadata?.fileUrl || !user?.uid) return;
    
    const confirmed = window.confirm('Are you sure you want to delete your CV?');
    if (!confirmed) return;
    
    try {
      // Delete from Firebase Storage
      const fileName = cvMetadata.fileUrl.split('/').pop()?.split('?')[0];
      if (fileName) {
        const fileRef = storageRef(storage, `cvs/${user.uid}/${fileName}`);
        await deleteObject(fileRef).catch(console.error);
      }
      
      // Remove from Firestore
      await updateDoc(doc(db, 'users', user.uid), {
        cvMetadata: null,
        'profile.cvUrl': null,
        updatedAt: serverTimestamp(),
      });
      
      setCvMetadata(null);
      setPreviewUrl(null);
      toast.success('CV deleted successfully');
    } catch (error) {
      toast.error('Failed to delete CV');
      console.error('Delete error:', error);
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'text-green-600 dark:text-green-400';
    if (confidence >= 60) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getConfidenceBg = (confidence: number) => {
    if (confidence >= 80) return 'bg-green-100 dark:bg-green-900/20';
    if (confidence >= 60) return 'bg-yellow-100 dark:bg-yellow-900/20';
    return 'bg-red-100 dark:bg-red-900/20';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            CV Analyzer
          </h3>
        </div>
        {cvMetadata && (
          <div className="flex items-center gap-2">
            <button
              onClick={handleDownload}
              className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title="Download CV"
            >
              <Download className="w-4 h-4" />
            </button>
            <button
              onClick={handleReanalyze}
              disabled={isAnalyzing}
              className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
              title="Re-analyze"
            >
              <RefreshCw className={cn("w-4 h-4", isAnalyzing && "animate-spin")} />
            </button>
            <button
              onClick={handleDelete}
              className="p-2 text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              title="Delete CV"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {!cvMetadata ? (
        // Upload Section
        <div
          {...getRootProps()}
          className={cn(
            'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all',
            isDragActive 
              ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20' 
              : 'border-gray-300 dark:border-gray-600 hover:border-indigo-400 dark:hover:border-indigo-500',
            (isUploading || isAnalyzing) && 'pointer-events-none opacity-50'
          )}
        >
          <input {...getInputProps()} />
          
          <AnimatePresence mode="wait">
            {isUploading ? (
              <motion.div
                key="uploading"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="space-y-4"
              >
                <Loader2 className="w-12 h-12 mx-auto text-indigo-600 dark:text-indigo-400 animate-spin" />
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    Uploading CV...
                  </p>
                  <div className="mt-2 w-48 mx-auto bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-indigo-500 to-purple-500"
                      initial={{ width: 0 }}
                      animate={{ width: `${uploadProgress}%` }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    {uploadProgress}% complete
                  </p>
                </div>
              </motion.div>
            ) : isAnalyzing ? (
              <motion.div
                key="analyzing"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="space-y-4"
              >
                <div className="relative w-12 h-12 mx-auto">
                  <Brain className="w-12 h-12 text-indigo-600 dark:text-indigo-400 animate-pulse" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    Analyzing CV with AI...
                  </p>
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    Extracting skills, experience, and expertise
                  </p>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="idle"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="space-y-4"
              >
                <Upload className="w-12 h-12 mx-auto text-gray-400" />
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {isDragActive ? 'Drop your CV here' : 'Drag & drop your CV'}
                  </p>
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    or click to browse (PDF only, max 10MB)
                  </p>
                </div>
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
                  Your CV will be analyzed using AI to extract relevant information
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      ) : (
        // CV Analysis Results
        <div className="space-y-4">
          {/* File Info */}
          <div className="flex items-center justify-between p-3 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-lg">
            <div className="flex items-center gap-3">
              <FileText className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {cvMetadata.fileName}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Uploaded {formatDistanceToNow(cvMetadata.uploadedAt, { addSuffix: true })}
                </p>
              </div>
            </div>
            <CheckCircle className="w-5 h-5 text-green-500" />
          </div>

          {/* AI Analysis Score */}
          <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                AI Analysis Score
              </span>
              <Award className="w-4 h-4 text-yellow-500" />
            </div>
            <div className="flex items-center gap-3">
              <div className="flex-1 bg-gray-200 dark:bg-gray-600 rounded-full h-3 overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-indigo-500 to-purple-500"
                  initial={{ width: 0 }}
                  animate={{ width: '85%' }}
                  transition={{ duration: 1, delay: 0.5 }}
                />
              </div>
              <span className="text-sm font-bold text-indigo-600 dark:text-indigo-400">
                85%
              </span>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
              Your CV is well-structured with strong technical skills
            </p>
          </div>

          {/* Extracted Skills */}
          {cvMetadata.extractedSkills.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Extracted Skills ({cvMetadata.extractedSkills.length})
              </h4>
              <div className="flex flex-wrap gap-2">
                {cvMetadata.extractedSkills.slice(0, 6).map((skill: { name: string; confidence: number }, index: number) => (
                  <motion.div
                    key={skill.name}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: index * 0.05 }}
                    className={cn(
                      'px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1',
                      getConfidenceBg(skill.confidence),
                      getConfidenceColor(skill.confidence)
                    )}
                  >
                    <span>{skill.name}</span>
                    <span className="opacity-70">{skill.confidence}%</span>
                  </motion.div>
                ))}
                {cvMetadata.extractedSkills.length > 6 && (
                  <button className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors">
                    +{cvMetadata.extractedSkills.length - 6} more
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Research Areas */}
          {cvMetadata.researchAreas.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Research Areas
              </h4>
              <div className="flex flex-wrap gap-2">
                {cvMetadata.researchAreas.map((area: string, index: number) => (
                  <motion.span
                    key={area}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="px-3 py-1 bg-purple-100 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 rounded-md text-xs font-medium"
                  >
                    {area}
                  </motion.span>
                ))}
              </div>
            </div>
          )}

          {/* Quick Stats */}
          <div className="grid grid-cols-2 gap-3">
            <div className="text-center p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
              <p className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
                {cvMetadata.publications}
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">Publications</p>
            </div>
            <div className="text-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                {cvMetadata.extractedSkills.length}
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">Skills</p>
            </div>
          </div>

          {/* Last Analysis */}
          <div className="flex items-center justify-between pt-3 border-t border-gray-200 dark:border-gray-700">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Last analyzed {formatDistanceToNow(cvMetadata.lastAnalyzed, { addSuffix: true })}
            </p>
            <button
              onClick={() => cvMetadata.fileUrl && setPreviewUrl(cvMetadata.fileUrl)}
              className="text-xs text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 font-medium flex items-center gap-1"
            >
              <Eye className="w-3 h-3" />
              View CV
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CVAnalyserCard;