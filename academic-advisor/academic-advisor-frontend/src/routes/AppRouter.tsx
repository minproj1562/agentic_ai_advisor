// src/routes/AppRouter.tsx
import React, { lazy, Suspense } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ProtectedRoute from './ProtectedRoute';

// Lazy load all pages for optimal performance
const HomePage = lazy(() => import('../pages/HomePage'));
const ProgramsList = lazy(() => import('../pages/ProgramsList'));
const ProgramDetail = lazy(() => import('../pages/ProgramDetail'));
const CampusTour = lazy(() => import('../pages/CampusTour'));
const Demo = lazy(() => import('../pages/Demo'));
const Features = lazy(() => import('../pages/Features'));
const Departments = lazy(() => import('../pages/Departments'));
const Resources = lazy(() => import('../pages/Resources'));
const Register = lazy(() => import('../pages/Register'));
const Login = lazy(() => import('../pages/Login'));
const StudentPortal = lazy(() => import('../pages/StudentPortal'));
const FacultyPortal = lazy(() => import('../pages/FacultyPortal'));
const DigitalLibrary = lazy(() => import('../pages/DigitalLibrary'));
const CareerServices = lazy(() => import('../pages/CareerServices'));
const About = lazy(() => import('../pages/About'));
const Admissions = lazy(() => import('../pages/Admissions'));
const Academics = lazy(() => import('../pages/Academics'));
const Research = lazy(() => import('../pages/Research'));
const CampusLife = lazy(() => import('../pages/CampusLife'));
const Alumni = lazy(() => import('../pages/Alumni'));
const Help = lazy(() => import('../pages/Help'));
const NotFound = lazy(() => import('../pages/NotFound'));

// Route configuration with metadata
export const routeConfig = {
  // Public routes
  home: { path: '/', title: 'Smart Campus - AI-Powered Education Platform', component: HomePage, public: true },
  programs: { path: '/programs', title: 'Academic Programs', component: ProgramsList, public: true },
  programDetail: { path: '/programs/:id', title: 'Program Details', component: ProgramDetail, public: true },
  campusTour: { path: '/campus-tour', title: '360° Campus Tour', component: CampusTour, public: true },
  demo: { path: '/demo', title: 'Platform Demo', component: Demo, public: true },
  features: { path: '/features', title: 'Platform Features', component: Features, public: true },
  featureDetail: { path: '/features/:id', title: 'Feature Details', component: Features, public: true },
  departments: { path: '/departments', title: 'Academic Departments', component: Departments, public: true },
  departmentDetail: { path: '/departments/:id', title: 'Department Details', component: Departments, public: true },
  resources: { path: '/resources', title: 'Academic Resources', component: Resources, public: true },
  resourceDetail: { path: '/resources/:type', title: 'Resource Details', component: Resources, public: true },
  about: { path: '/about', title: 'About Us', component: About, public: true },
  admissions: { path: '/admissions', title: 'Admissions', component: Admissions, public: true },
  academics: { path: '/academics', title: 'Academics', component: Academics, public: true },
  research: { path: '/research', title: 'Research', component: Research, public: true },
  campusLife: { path: '/campus-life', title: 'Campus Life', component: CampusLife, public: true },
  careers: { path: '/careers', title: 'Career Services', component: CareerServices, public: true },
  library: { path: '/library', title: 'Digital Library', component: DigitalLibrary, public: true },
  alumni: { path: '/alumni', title: 'Alumni Network', component: Alumni, public: true },
  help: { path: '/help', title: 'Help & Support', component: Help, public: true },
  register: { path: '/register', title: 'Register', component: Register, public: true },
  login: { path: '/login', title: 'Login', component: Login, public: true },
  
  // Protected routes
  studentPortal: { path: '/student-portal', title: 'Student Portal', component: StudentPortal, public: false, role: 'student' },
  facultyPortal: { path: '/faculty-portal', title: 'Faculty Portal', component: FacultyPortal, public: false, role: 'faculty' },
  
  // Error routes
  notFound: { path: '/404', title: 'Page Not Found', component: NotFound, public: true },
};

const AppRouter: React.FC = () => {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Suspense fallback={<LoadingSpinner fullScreen />}>
        <Routes location={location} key={location.pathname}>
          {/* Public Routes */}
          <Route path="/" element={<HomePage />} />
          <Route path="/programs" element={<ProgramsList />} />
          <Route path="/programs/:id" element={<ProgramDetail />} />
          <Route path="/campus-tour" element={<CampusTour />} />
          <Route path="/demo" element={<Demo />} />
          <Route path="/features" element={<Features />} />
          <Route path="/features/:id" element={<Features />} />
          <Route path="/departments" element={<Departments />} />
          <Route path="/departments/:id" element={<Departments />} />
          <Route path="/resources" element={<Resources />} />
          <Route path="/resources/:type" element={<Resources />} />
          <Route path="/about" element={<About />} />
          <Route path="/admissions" element={<Admissions />} />
          <Route path="/academics" element={<Academics />} />
          <Route path="/research" element={<Research />} />
          <Route path="/campus-life" element={<CampusLife />} />
          <Route path="/careers" element={<CareerServices />} />
          <Route path="/library" element={<DigitalLibrary />} />
          <Route path="/alumni" element={<Alumni />} />
          <Route path="/help" element={<Help />} />
          <Route path="/register" element={<Register />} />
          <Route path="/login" element={<Login />} />
          
          {/* Protected Routes */}
          <Route
            path="/student-portal/*"
            element={
              <ProtectedRoute role="student">
                <StudentPortal />
              </ProtectedRoute>
            }
          />
          <Route
            path="/faculty-portal/*"
            element={
              <ProtectedRoute role="faculty">
                <FacultyPortal />
              </ProtectedRoute>
            }
          />
          
          {/* 404 Route */}
          <Route path="/404" element={<NotFound />} />
          <Route path="*" element={<Navigate to="/404" replace />} />
        </Routes>
      </Suspense>
    </AnimatePresence>
  );
};

export default AppRouter;