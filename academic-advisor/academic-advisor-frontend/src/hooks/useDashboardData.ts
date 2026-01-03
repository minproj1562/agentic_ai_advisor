// src/hooks/useDashboardData.ts
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { useState, useEffect, useCallback } from 'react';
import { DashboardData, Student, MentorshipSlot, Notification, CVMetadata } from '../types/dashboard.types';
import { 
  collection, 
  doc, 
  getDoc, 
  getDocs, 
  query, 
  where, 
  orderBy, 
  limit,
  onSnapshot,
  Unsubscribe,
  setDoc,
  DocumentSnapshot,
  QueryDocumentSnapshot
} from 'firebase/firestore';
import { db } from '../services/firebase.config';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

interface UseDashboardDataReturn {
  data: DashboardData | undefined;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  refetch: () => void;
  updateData: (updates: Partial<DashboardData>) => void;
}

export const useDashboardData = (facultyId: string): UseDashboardDataReturn => {
  const queryClient = useQueryClient();
  const { user, loading: authLoading } = useAuth();
  const [realtimeData, setRealtimeData] = useState<Partial<DashboardData>>({});
  const [listeners, setListeners] = useState<Unsubscribe[]>([]);

  // Wait for auth loading and user role to be set
  const isReady = !authLoading && !!user && user.role === 'faculty' && user.uid === facultyId;

  useEffect(() => {
    if (facultyId && user && user.uid !== facultyId) {
      console.warn('Unauthorized access attempt or invalid facultyId:', facultyId, user?.uid);
      throw new Error('Unauthorized access or invalid faculty ID');
    }
  }, [facultyId, user]);

  const fetchFacultyData = async () => {
    if (!isReady) throw new Error('User data not ready');
    try {
      const facultyDoc = await getDoc(doc(db, 'users', facultyId));
      if (!facultyDoc.exists()) throw new Error('Faculty not found');
      const data = facultyDoc.data();
      return {
        id: facultyId,
        name: data.displayName || data.name,
        email: data.email,
        department: data.department || 'Computer Science',
        profilePhoto: data.profilePhoto,
        role: data.title || 'Professor',
        expertise: data.expertise || [],
        joinedDate: data.metadata?.createdAt ? new Date(data.metadata.createdAt) : new Date(),
        totalMentees: data.stats?.totalMentees || 0,
        badges: data.badges || [],
      };
    } catch (error) {
      if (error instanceof Error && error.message.includes('permission-denied')) {
        throw new Error('Insufficient permissions to access faculty data');
      }
      throw error;
    }
  };

  const fetchMentees = async (): Promise<Student[]> => {
    if (!facultyId) return [];
    try {
      const menteesQuery = query(
        collection(db, 'mentorships'),
        where('facultyId', '==', facultyId),
        where('status', '==', 'active')
      );
      const menteesSnapshot = await getDocs(menteesQuery);
      const menteeIds = menteesSnapshot.docs.map(doc => doc.data().studentId);
      if (menteeIds.length === 0) return [];

      const students: Student[] = [];
      for (const studentId of menteeIds) {
        try {
          const studentDoc = await getDoc(doc(db, 'users', studentId));
          if (studentDoc.exists()) {
            const studentData = studentDoc.data();
            const academicQuery = query(
              collection(db, 'academicRecords'),
              where('studentId', '==', studentId),
              orderBy('semester', 'desc'),
              limit(4)
            );
            const academicSnapshot = await getDocs(academicQuery);
            const sgpiTrend = academicSnapshot.docs.map(doc => doc.data().sgpi || 0);
            students.push({
              id: studentId,
              name: studentData.displayName || studentData.name,
              email: studentData.email,
              rollNumber: studentData.rollNumber || `CS${Date.now()}`,
              currentSGPI: sgpiTrend[0] || 0,
              sgpiTrend: sgpiTrend.reverse(),
              weakSubjects: studentData.weakSubjects || [],
              strongSubjects: studentData.strongSubjects || [],
              lastInteraction: studentData.lastInteraction ? new Date(studentData.lastInteraction) : new Date(),
              status: determineStudentStatus(sgpiTrend),
            });
          }
        } catch (error) {
          console.error(`Error fetching mentee ${studentId}:`, error);
          continue;
        }
      }
      return students;
    } catch (error) {
      if (error instanceof Error && error.message.includes('permission-denied')) {
        toast.error('Insufficient permissions to access mentee data');
      }
      return [];
    }
  };

  const fetchMentorshipSlots = async (): Promise<MentorshipSlot[]> => {
    if (!facultyId) return [];
    try {
      const slotsQuery = query(
        collection(db, 'mentorshipSlots'),
        where('facultyId', '==', facultyId),
        where('date', '>=', new Date()),
        orderBy('date', 'asc'),
        limit(20)
      );
      const slotsSnapshot = await getDocs(slotsQuery);
      return slotsSnapshot.docs.map(doc => {
        const data = doc.data();
        return {
          id: doc.id,
          date: data.date.toDate(),
          startTime: data.startTime,
          endTime: data.endTime,
          isBooked: data.isBooked || false,
          studentId: data.studentId,
          type: data.type || 'Regular',
        };
      });
    } catch (error) {
      if (error instanceof Error && error.message.includes('permission-denied')) {
        toast.error('Insufficient permissions to access slots data');
      }
      return [];
    }
  };

  const fetchNotifications = async (): Promise<Notification[]> => {
    if (!facultyId) return [];
    try {
      const notificationsQuery = query(
        collection(db, 'notifications'),
        where('userId', '==', facultyId),
        orderBy('timestamp', 'desc'),
        limit(10)
      );
      const notificationsSnapshot = await getDocs(notificationsQuery);
      return notificationsSnapshot.docs.map(doc => {
        const data = doc.data();
        return {
          id: doc.id,
          title: data.title,
          message: data.message,
          type: data.type || 'info',
          timestamp: data.timestamp.toDate(),
          isRead: data.isRead || false,
          actionUrl: data.actionUrl,
        };
      });
    } catch (error) {
      if (error instanceof Error && error.message.includes('permission-denied')) {
        toast.error('Insufficient permissions to access notifications');
      }
      return [];
    }
  };

  const fetchDashboardData = async (): Promise<DashboardData> => {
    if (!isReady) throw new Error('User data not ready');
    try {
      const [faculty, mentees, slots, notifications] = await Promise.all([
        fetchFacultyData(),
        fetchMentees(),
        fetchMentorshipSlots(),
        fetchNotifications(),
      ]);
      const cvMetadataDoc = await getDoc(doc(db, 'users', facultyId, 'cv_metadata', 'latest'));
      const cvMetadata = cvMetadataDoc.exists() ? (cvMetadataDoc.data() as CVMetadata) : null;
      const stats = {
        totalMentees: mentees.length,
        atRiskStudents: mentees.filter(m => m.status === 'At Risk').length,
        improvingStudents: mentees.filter(m => m.status === 'Improving').length,
        upcomingSlots: slots.filter(s => !s.isBooked).length,
        unreadNotifications: notifications.filter(n => !n.isRead).length,
      };
      return { faculty, mentees, cvMetadata, mentorshipSlots: slots, notifications, stats };
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      throw error;
    }
  };

  // Update useEffect for real-time listeners to respect isReady
  useEffect(() => {
    if (!isReady) return;
    const unsubscribers: Unsubscribe[] = [];
    
    const setupListener = (collectionPath: string, field: string, callback: (snapshot: any) => void) => {
      const unsubscribe = onSnapshot(
        query(collection(db, collectionPath), where(field, '==', facultyId), orderBy('timestamp', 'desc'), limit(10)),
        callback,
        (error: Error) => {
          console.error(`${collectionPath} listener error:`, error);
          if (error.message.includes('permission-denied')) {
            toast.error(`Permission denied for ${collectionPath}`);
          }
        }
      );
      unsubscribers.push(unsubscribe);
    };

    setupListener('notifications', 'userId', (snapshot) => {
      const notifications = snapshot.docs.map((doc: QueryDocumentSnapshot) => ({
        id: doc.id,
        ...doc.data(),
        timestamp: doc.data().timestamp.toDate(),
      })) as Notification[];
      setRealtimeData(prev => ({ ...prev, notifications }));
      snapshot.docChanges().forEach((change: any) => {
        if (change.type === 'added' && change.doc.data().timestamp.toDate() > new Date(Date.now() - 5000)) {
          toast(change.doc.data().title, { icon: '🔔', duration: 4000 });
        }
      });
    });

    setupListener('mentorshipSlots', 'facultyId', (snapshot) => {
      const slots = snapshot.docs.map((doc: QueryDocumentSnapshot) => ({
        id: doc.id,
        ...doc.data(),
        date: doc.data().date.toDate(),
      })) as MentorshipSlot[];
      setRealtimeData(prev => ({ ...prev, mentorshipSlots: slots }));
    });

    const cvMetadataUnsubscribe = onSnapshot(
      doc(db, 'users', facultyId, 'cv_metadata', 'latest'),
      (doc: DocumentSnapshot) => {
        if (doc.exists()) {
          const cvMetadata = doc.data() as CVMetadata;
          setRealtimeData(prev => ({ ...prev, cvMetadata }));
        }
      },
      (error: Error) => {
        console.error('CV metadata listener error:', error);
        if (error.message.includes('permission-denied')) {
          toast.error('Permission denied for CV metadata');
        }
      }
    );
    unsubscribers.push(cvMetadataUnsubscribe);

    setListeners(unsubscribers);
    return () => unsubscribers.forEach(unsubscribe => unsubscribe());
  }, [facultyId, user, isReady]);

  const { data, isLoading, isError, error, refetch } = useQuery<DashboardData, Error>({
    queryKey: ['dashboardData', facultyId],
    queryFn: fetchDashboardData,
    enabled: isReady,
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000, // Changed from cacheTime to gcTime
    refetchOnWindowFocus: true,
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });

  const mergedData = data ? {
    ...data,
    ...realtimeData,
    // Type-safe property access
    notifications: (realtimeData as any).notifications || data.notifications,
    mentorshipSlots: (realtimeData as any).mentorshipSlots || data.mentorshipSlots,
    cvMetadata: (realtimeData as any).cvMetadata || data.cvMetadata,
  } as DashboardData : undefined;

  const updateDataMutation = useMutation({
    mutationFn: async (updates: Partial<DashboardData>) => {
      if (!user || user.uid !== facultyId) throw new Error('Unauthorized update attempt');
      if (updates.cvMetadata) {
        await setDoc(doc(db, 'users', facultyId, 'cv_metadata', 'latest'), updates.cvMetadata, { merge: true });
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboardData', facultyId] });
      toast.success('Data updated successfully');
    },
    onError: (error: Error) => {
      toast.error('Failed to update data');
      console.error('Update error:', error);
    },
  });

  const updateData = useCallback((updates: Partial<DashboardData>) => {
    updateDataMutation.mutate(updates);
  }, [updateDataMutation]);

  return {
    data: mergedData,
    isLoading: !isReady || isLoading,
    isError,
    error: error as Error | null,
    refetch,
    updateData,
  };
};

function determineStudentStatus(sgpiTrend: number[]): Student['status'] {
  if (sgpiTrend.length < 2) return 'Active';
  const recent = sgpiTrend[sgpiTrend.length - 1];
  const previous = sgpiTrend[sgpiTrend.length - 2];
  if (recent < 7.0) return 'At Risk';
  if (recent > previous) return 'Improving';
  return 'Active';
}