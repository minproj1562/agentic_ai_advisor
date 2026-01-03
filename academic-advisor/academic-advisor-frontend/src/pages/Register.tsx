// src/pages/Register.tsx (Full corrected code with TypeScript fixes and form progression)
import React, { useState, useEffect, FC } from 'react';
import { useForm, Controller, SubmitHandler, Control, FieldErrors } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { auth, db } from '../services/firebase.config';
import { createUserWithEmailAndPassword, sendEmailVerification, GoogleAuthProvider, signInWithPopup } from 'firebase/auth';
import { doc, setDoc } from 'firebase/firestore';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { FaUserGraduate, FaChalkboardTeacher, FaUpload, FaCheckCircle, FaEye, FaEyeSlash, FaGoogle } from 'react-icons/fa';
import { User } from '../types/auth.types';
import { AuthLayout } from '../components/AuthLayout';

interface FormData {
  role: 'student' | 'faculty';
  email: string;
  password: string;
  confirmPassword: string;
  firstName: string;
  lastName: string;
  institution: string;
  program?: string;
  department?: string;
  semester?: number;
  careerInterests?: string[];
  title?: string;
  coursesTaught?: string[];
  researchAreas?: string[];
  cv?: File | null;
  consent: boolean;
}

type StringFieldNames = 'email' | 'password' | 'confirmPassword' | 'firstName' | 'lastName' | 'institution' | 'program' | 'department' | 'title';

const schema = yup.object().shape({
  role: yup.string().oneOf(['student', 'faculty'] as const, 'Role is required').required('Role is required'),
  email: yup.string().email('Invalid email format').required('Email is required'),
  password: yup
    .string()
    .min(8, 'Password must be at least 8 characters')
    .matches(/[0-9]/, 'Password must contain a number')
    .matches(/[!@#$%^&*]/, 'Password must contain a special symbol')
    .required('Password is required'),
  confirmPassword: yup
    .string()
    .oneOf([yup.ref('password')], 'Passwords must match')
    .required('Confirm password is required'),
  firstName: yup.string().required('First name is required'),
  lastName: yup.string().required('Last name is required'),
  institution: yup.string().required('Institution is required'),
  program: yup.string().when('role', {
    is: 'student',
    then: (schema) => schema.required('Program is required'),
    otherwise: (schema) => schema.optional(),
  }),
  department: yup.string().when('role', {
    is: 'student',
    then: (schema) => schema.required('Department is required'),
    otherwise: (schema) => schema.optional(),
  }),
  semester: yup.number().when('role', {
    is: 'student',
    then: (schema) => schema.min(1, 'Semester must be at least 1').required('Semester is required'),
    otherwise: (schema) => schema.optional(),
  }),
  careerInterests: yup.array().of(yup.string().defined()).when('role', {
    is: 'student',
    then: (schema) => schema.min(1, 'Select at least one career interest'),
    otherwise: (schema) => schema.optional(),
  }),
  title: yup.string().when('role', {
    is: 'faculty',
    then: (schema) => schema.required('Title is required'),
    otherwise: (schema) => schema.optional(),
  }),
  coursesTaught: yup.array().of(yup.string().defined()).when('role', {
    is: 'faculty',
    then: (schema) => schema.min(1, 'At least one course is required'),
    otherwise: (schema) => schema.optional(),
  }),
  researchAreas: yup.array().of(yup.string().defined()).when('role', {
    is: 'faculty',
    then: (schema) => schema.min(1, 'At least one research area is required'),
    otherwise: (schema) => schema.optional(),
  }),
  cv: yup.mixed<File>().when('role', {
    is: 'faculty',
    then: (schema) => schema
      .required('CV is required')
      .test('fileSize', 'File size must be less than 10MB', (value) => value && value.size <= 10 * 1024 * 1024)
      .test('fileType', 'Only PDF files are allowed', (value) => value && value.type === 'application/pdf'),
    otherwise: (schema) => schema.nullable().optional(),
  }),
  consent: yup.boolean().oneOf([true], 'You must agree to the terms').required(),
});

const InputField: React.FC<{
  id: string;
  label: string;
  control: Control<FormData>;
  name: StringFieldNames;
  type?: string;
  errors: FieldErrors<FormData>;
  className?: string;
}> = ({ id, label, control, name, type = 'text', errors, className = '' }) => (
  <div className="relative">
    <Controller
      name={name}
      control={control}
      render={({ field }) => (
        <input
          {...field}
          id={id}
          type={type}
          value={field.value ?? ''}
          onChange={(e) => field.onChange(e.target.value)}
          className={`form-input ${className} peer`}
          aria-invalid={!!errors[name]}
        />
      )}
    />
    <label htmlFor={id} className="form-label">
      {label}
    </label>
    {errors[name] && <p className="text-red-500 text-sm mt-1">{errors[name]?.message}</p>}
  </div>
);

const PasswordField: React.FC<{
  id: string;
  label: string;
  control: Control<FormData>;
  name: StringFieldNames;
  errors: FieldErrors<FormData>;
  showPassword: boolean;
  toggleShowPassword: () => void;
}> = ({ id, label, control, name, errors, showPassword, toggleShowPassword }) => (
  <div className="relative">
    <Controller
      name={name}
      control={control}
      render={({ field }) => (
        <input
          {...field}
          id={id}
          type={showPassword ? 'text' : 'password'}
          value={field.value ?? ''}
          onChange={(e) => field.onChange(e.target.value)}
          className="form-input peer"
          aria-invalid={!!errors[name]}
        />
      )}
    />
    <label htmlFor={id} className="form-label">
      {label}
    </label>
    <button
      type="button"
      onClick={toggleShowPassword}
      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500"
    >
      {showPassword ? <FaEyeSlash /> : <FaEye />}
    </button>
    {errors[name] && <p className="text-red-500 text-sm mt-1">{errors[name]?.message}</p>}
  </div>
);

const RoleSelector: React.FC<{
  role: 'student' | 'faculty' | null;
  setRole: (role: 'student' | 'faculty') => void;
  setValue: (name: 'role', value: 'student' | 'faculty') => void;
  nextStep: () => void;
}> = ({ role, setRole, setValue, nextStep }) => (
  <div className="space-y-6">
    <h3 className="text-lg font-medium text-gray-700">Select Your Role</h3>
    <div className="flex space-x-4">
      <button
        type="button"
        onClick={() => {
          setRole('student');
          setValue('role', 'student');
          nextStep();
        }}
        className={`flex-1 p-4 bg-white border border-gray-300 rounded-lg shadow hover:bg-gray-50 flex items-center justify-center ${role === 'student' ? 'bg-blue-100' : ''}`}
      >
        <FaUserGraduate className="mr-2" /> Student
      </button>
      <button
        type="button"
        onClick={() => {
          setRole('faculty');
          setValue('role', 'faculty');
          nextStep();
        }}
        className={`flex-1 p-4 bg-white border border-gray-300 rounded-lg shadow hover:bg-gray-50 flex items-center justify-center ${role === 'faculty' ? 'bg-blue-100' : ''}`}
      >
        <FaChalkboardTeacher className="mr-2" /> Faculty
      </button>
    </div>
  </div>
);

const OAuthButtons: React.FC<{
  handleGoogleSignUp: () => void;
  loading: boolean;
}> = ({ handleGoogleSignUp, loading }) => (
  <div className="mt-6">
    <button
      type="button"
      onClick={handleGoogleSignUp}
      disabled={loading}
      className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 shadow rounded-lg bg-white hover:bg-gray-50"
    >
      <FaGoogle className="mr-2" /> Sign up with Google
    </button>
  </div>
);

const FacultyCVUploader: React.FC<{
  control: Control<FormData>;
  watch: (name: 'cv') => File | null | undefined;
  errors: FieldErrors<FormData>;
}> = ({ control, watch, errors }) => (
  <div className="mb-6">
    <label className="block text-muted mb-2">Upload CV</label>
    <Controller
      name="cv"
      control={control}
      render={({ field: { onChange, value } }) => (
        <input
          type="file"
          accept="application/pdf"
          onChange={(e) => onChange(e.target.files?.[0] || null)}
          className="w-full p-3 border rounded-lg"
        />
      )}
    />
    {watch('cv') && <p className="text-sm text-gray-600 mt-1">Selected: {watch('cv')?.name}</p>}
    {errors.cv && <p className="text-red-500 text-sm mt-1">{errors.cv?.message}</p>}
  </div>
);

const TermsCheckbox: React.FC<{
  control: Control<FormData>;
  errors: FieldErrors<FormData>;
}> = ({ control, errors }) => (
  <div className="mb-6">
    <Controller
      name="consent"
      control={control}
      render={({ field }) => (
        <label className="flex items-center">
          <input 
            type="checkbox" 
            className="mr-2" 
            checked={field.value} 
            onChange={field.onChange}
            onBlur={field.onBlur}
            ref={field.ref}
          />
          I agree to the terms and conditions
        </label>
      )}
    />
    {errors.consent && <p className="text-red-500 text-sm mt-1">{errors.consent?.message}</p>}
  </div>
);

const ProgressStepper: React.FC<{ step: number }> = ({ step }) => (
  <div className="flex justify-between mb-8">
    {[1, 2, 3].map((s) => (
      <div key={s} className={`flex-1 h-1 ${step >= s ? 'bg-blue-600' : 'bg-gray-300'}`} />
    ))}
  </div>
);

const Register: FC = () => {
  const [role, setRole] = useState<'student' | 'faculty' | null>(null);
  const [step, setStep] = useState<number>(1);
  const [success, setSuccess] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState<boolean>(false);
  const { login } = useAuth();

  const { control, handleSubmit, formState: { errors, isValid }, watch, setValue, reset, trigger } = useForm<FormData>({
    resolver: yupResolver(schema as any),
    mode: 'onChange',
    defaultValues: {
      role: 'student',
      email: '',
      password: '',
      confirmPassword: '',
      firstName: '',
      lastName: '',
      institution: '',
      program: '',
      department: '',
      semester: undefined,
      careerInterests: [],
      title: '',
      coursesTaught: [],
      researchAreas: [],
      cv: null,
      consent: false,
    },
  });

  useEffect(() => {
    if (role) {
      trigger();
    }
  }, [role, trigger]);

  const nextStep = () => {
    if (role) {
      setStep((prev) => prev + 1);
    }
  };

  const prevStep = () => setStep((prev) => prev - 1);

  const onSubmit: SubmitHandler<FormData> = async (data) => {
    setLoading(true);
    setErrorMessage('');
    try {
      const userCredential = await createUserWithEmailAndPassword(auth, data.email, data.password);
      await sendEmailVerification(userCredential.user);

      const userData: Partial<User> = {
        uid: userCredential.user.uid,
        email: data.email,
        displayName: `${data.firstName} ${data.lastName}`,
        role: data.role,
        emailVerified: false,
        metadata: {
          createdAt: new Date().toISOString(),
          lastLoginAt: new Date().toISOString(),
          lastActiveAt: new Date().toISOString(),
        },
      };
      await setDoc(doc(db, 'users', userCredential.user.uid), userData);

      const fullUserData = {
        ...userData,
        ...(data.role === 'student' && { program: data.program, department: data.department, semester: data.semester, careerInterests: data.careerInterests }),
        ...(data.role === 'faculty' && { title: data.title, coursesTaught: data.coursesTaught, researchAreas: data.researchAreas }),
      };
      await setDoc(doc(db, 'users', userCredential.user.uid), fullUserData, { merge: true });

      if (data.role === 'faculty' && data.cv) {
        const formData = new FormData();
        formData.append('uid', userCredential.user.uid);
        formData.append('cv', data.cv);

        const response = await fetch('http://localhost:8000/api/v1/cv/parse-cv', {
          method: 'POST',
          body: formData,
        });
        if (!response.ok) {
          console.warn('CV upload failed:', await response.text());
        } else {
          const cvResult = await response.json();
          console.log('CV Analysis:', cvResult);
          await setDoc(doc(db, 'users', userCredential.user.uid), {
            cvAnalysis: cvResult,
          }, { merge: true });
        }
      }

      await new Promise((resolve) => setTimeout(resolve, 1000));
      await login({ email: data.email, password: data.password, rememberMe: false });
      setSuccess(true);
    } catch (error: any) {
      setErrorMessage(error.message || 'An error occurred during registration. Please try again.');
      if (error.code === 'auth/email-already-in-use') {
        setErrorMessage('This email is already registered. Please log in or use a different email.');
      } else if (error.code === 'auth/invalid-email') {
        setErrorMessage('Invalid email format. Please use a valid institutional email.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignUp = async () => {
    setLoading(true);
    setErrorMessage('');
    try {
      const provider = new GoogleAuthProvider();
      const userCredential = await signInWithPopup(auth, provider);
      await sendEmailVerification(userCredential.user);

      const userData: Partial<User> = {
        uid: userCredential.user.uid,
        email: userCredential.user.email || '',
        displayName: userCredential.user.displayName || '',
        role: role || 'student',
        emailVerified: false,
        metadata: {
          createdAt: new Date().toISOString(),
          lastLoginAt: new Date().toISOString(),
          lastActiveAt: new Date().toISOString(),
        },
      };

      await setDoc(doc(db, 'users', userCredential.user.uid), userData);

      await login({ email: userCredential.user.email || '', password: '', rememberMe: false });
      setSuccess(true);
    } catch (error: any) {
      setErrorMessage(error.message || 'Google sign-up failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <AuthLayout>
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="flex flex-col items-center justify-center max-w-md w-full bg-white/90 backdrop-blur-md rounded-2xl shadow-lg p-8"
        >
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ duration: 0.8, type: 'spring' }}
            className="w-24 h-24 bg-accent rounded-full flex items-center justify-center mb-6 shadow-lg"
          >
            <FaCheckCircle size={48} className="text-white" />
          </motion.div>
          <h2 className="text-3xl font-heading text-primary mb-2 text-center">Welcome Aboard! 🎓</h2>
          <p className="text-lg text-muted mb-4 text-center">Your academic journey just got smarter.</p>
          <p className="text-sm text-muted text-center">
            Please check your email ({watch('email') || 'your email'}) for a verification link to activate your account.
            If you don't receive it, check your spam/junk folder or contact support.
          </p>
        </motion.div>
      </AuthLayout>
    );
  }

  const basicFields = ['firstName', 'lastName', 'email', 'password', 'confirmPassword'] as const;

  return (
    <AuthLayout>
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="grid grid-cols-1 md:grid-cols-2 max-w-7xl w-full bg-white/90 backdrop-blur-md rounded-3xl shadow-2xl overflow-hidden border border-accent/20"
      >
        <div className="hidden md:flex flex-col justify-center p-12 bg-gradient-to-tr from-primary to-accent text-white relative overflow-hidden">
          <motion.div
            initial={{ y: -20 }}
            animate={{ y: 0 }}
            transition={{ duration: 0.8 }}
            className="absolute top-0 right-0 w-48 h-48 bg-white opacity-5 rounded-full blur-3xl"
          />
          <motion.h1
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            className="text-5xl font-heading mb-6 leading-tight"
          >
            Unlock Your Academic Potential
          </motion.h1>
          <motion.ul
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="space-y-4 text-lg"
          >
            <li className="flex items-center">
              <FaCheckCircle className="mr-3 text-warm" /> AI-Powered Study Plans
            </li>
            <li className="flex items-center">
              <FaCheckCircle className="mr-3 text-warm" /> Expert Mentor Matching
            </li>
            <li className="flex items-center">
              <FaCheckCircle className="mr-3 text-warm" /> Career-Aligned Recommendations
            </li>
          </motion.ul>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="mt-8 text-sm opacity-80"
          >
            Partnered with Leading Universities Worldwide
          </motion.div>
        </div>

        <div className="p-8 md:p-12 relative">
          {errorMessage && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 p-4 bg-red-100 text-red-700 rounded-lg shadow"
              role="alert"
              aria-live="assertive"
            >
              {errorMessage}
            </motion.div>
          )}
          <ProgressStepper step={step} />
          <h2 className="text-3xl font-heading text-primary mb-8 text-center md:text-left">Join the Future of Learning</h2>

          <form onSubmit={handleSubmit(onSubmit as any)} noValidate>
            <AnimatePresence mode="wait">
              {step === 1 && (
                <motion.div
                  key="step1"
                  initial={{ opacity: 0, x: 50 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -50 }}
                  transition={{ duration: 0.4 }}
                >
                  <RoleSelector role={role} setRole={setRole} setValue={setValue} nextStep={nextStep} />
                </motion.div>
              )}

              {step === 2 && (
                <motion.div
                  key="step2"
                  initial={{ opacity: 0, x: 50 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -50 }}
                  transition={{ duration: 0.4 }}
                  className="space-y-6"
                >
                  <InputField
                    id="firstName"
                    label="First Name"
                    control={control as Control<FormData>}
                    name="firstName"
                    errors={errors}
                  />
                  <InputField
                    id="lastName"
                    label="Last Name"
                    control={control as Control<FormData>}
                    name="lastName"
                    errors={errors}
                  />
                  <InputField
                    id="email"
                    label="Email (use college email)"
                    control={control as Control<FormData>}
                    name="email"
                    type="email"
                    errors={errors}
                  />
                  <PasswordField
                    id="password"
                    label="Password"
                    control={control as Control<FormData>}
                    name="password"
                    errors={errors}
                    showPassword={showPassword}
                    toggleShowPassword={() => setShowPassword(!showPassword)}
                  />
                  <PasswordField
                    id="confirmPassword"
                    label="Confirm Password"
                    control={control as Control<FormData>}
                    name="confirmPassword"
                    errors={errors}
                    showPassword={showConfirmPassword}
                    toggleShowPassword={() => setShowConfirmPassword(!showConfirmPassword)}
                  />
                  <div className="mb-6">
                    <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <motion.div
                        className="h-1.5 bg-gradient-to-r from-red-500 via-yellow-500 to-green-500"
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.min((watch('password')?.length || 0) / 12 * 100, 100)}%` }}
                        transition={{ duration: 0.3 }}
                      />
                    </div>
                    <ul className="text-sm text-muted mt-2 grid grid-cols-3 gap-1">
                      <li className={(watch('password')?.length || 0) >= 8 ? 'text-green-500' : 'text-red-500'}>
                        ≥8 chars
                      </li>
                      <li className={/[0-9]/.test(watch('password') || '') ? 'text-green-500' : 'text-red-500'}>
                        Number
                      </li>
                      <li className={/[!@#$%^&*]/.test(watch('password') || '') ? 'text-green-500' : 'text-red-500'}>
                        Symbol
                      </li>
                    </ul>
                  </div>
                  <div className="flex justify-between">
                    <motion.button
                      type="button"
                      onClick={prevStep}
                      whileHover={{ scale: 1.05 }}
                      className="btn-secondary"
                      aria-label="Go back"
                    >
                      Back
                    </motion.button>
                    <motion.button
                      type="button"
                      onClick={nextStep}
                      disabled={loading || !basicFields.every(
                        (field) => !errors[field] && !!watch(field)
                      )}
                      whileHover={{ scale: 1.05 }}
                      className="btn-gradient disabled:opacity-50"
                      aria-label="Proceed to next step"
                    >
                      Next
                    </motion.button>
                  </div>
                  <OAuthButtons handleGoogleSignUp={handleGoogleSignUp} loading={loading} />
                </motion.div>
              )}

              {step === 3 && (
                <motion.div
                  key="step3"
                  initial={{ opacity: 0, x: 50 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -50 }}
                  transition={{ duration: 0.4 }}
                  className="space-y-6"
                >
                  <InputField
                    id="institution"
                    label="University / Institution"
                    control={control as Control<FormData>}
                    name="institution"
                    errors={errors}
                  />
                  {role === 'student' && (
                    <>
                      <div className="relative">
                        <Controller
                          name="program"
                          control={control as Control<FormData>}
                          render={({ field }) => (
                            <select {...field} id="program" className="form-input peer appearance-none">
                              <option value=""> </option>
                              <option>B.Tech</option>
                              <option>BSc</option>
                              <option>MSc</option>
                              <option>Diploma</option>
                            </select>
                          )}
                        />
                        <label htmlFor="program" className="form-label">
                          Program / Degree
                        </label>
                        {errors.program && (
                          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-500 text-sm mt-1">
                            {errors.program?.message}
                          </motion.p>
                        )}
                      </div>
                      <InputField
                        id="department"
                        label="Department / Major"
                        control={control as Control<FormData>}
                        name="department"
                        errors={errors}
                      />
                      <div className="relative">
                        <Controller
                          name="semester"
                          control={control as Control<FormData>}
                          render={({ field }) => (
                            <select 
                              {...field} 
                              id="semester" 
                              className="form-input peer appearance-none"
                              value={field.value ?? ''}
                              onChange={(e) => field.onChange(e.target.value ? parseInt(e.target.value, 10) : undefined)}
                            >
                              <option value=""> </option>
                              {[...Array(8)].map((_, i) => (
                                <option key={i} value={i + 1}>
                                  {i + 1}
                                </option>
                              ))}
                            </select>
                          )}
                        />
                        <label htmlFor="semester" className="form-label">
                          Current Semester
                        </label>
                        {errors.semester && (
                          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-500 text-sm mt-1">
                            {errors.semester?.message}
                          </motion.p>
                        )}
                      </div>
                      <Controller
                        name="careerInterests"
                        control={control as Control<FormData>}
                        render={({ field }) => (
                          <div className="mb-6">
                            <label className="block text-muted mb-2">Career Interests (select multiple)</label>
                            <div className="flex flex-wrap gap-3">
                              {['Data Science', 'AI', 'Software Eng', 'Research', 'Machine Learning', 'Entrepreneurship'].map(
                                (interest) => (
                                  <motion.button
                                    key={interest}
                                    type="button"
                                    onClick={() => {
                                      const val = field.value || [];
                                      setValue(
                                        'careerInterests',
                                        val.includes(interest) ? val.filter((i) => i !== interest) : [...val, interest]
                                      );
                                    }}
                                    whileHover={{ scale: 1.05 }}
                                    className={`px-4 py-2 rounded-full shadow transition ${
                                      field.value?.includes(interest)
                                        ? 'bg-warm text-white'
                                        : 'bg-gray-200 text-textPrimary hover:bg-gray-300'
                                    }`}
                                    aria-pressed={field.value?.includes(interest)}
                                  >
                                    {interest}
                                  </motion.button>
                                )
                              )}
                            </div>
                            {errors.careerInterests && (
                              <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-500 text-sm mt-1">
                                {errors.careerInterests?.message}
                              </motion.p>
                            )}
                          </div>
                        )}
                      />
                    </>
                  )}
                  {role === 'faculty' && (
                    <>
                      <InputField
                        id="title"
                        label="Title (e.g., Professor)"
                        control={control as Control<FormData>}
                        name="title"
                        errors={errors}
                      />
                      <div className="mb-6">
                        <label className="block text-muted mb-2">Courses Taught (add tags)</label>
                        <Controller
                          name="coursesTaught"
                          control={control as Control<FormData>}
                          render={({ field }) => (
                            <div>
                              <input
                                placeholder="Add course and press Enter"
                                onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
                                  if (e.key === 'Enter' && e.currentTarget.value) {
                                    const val = field.value || [];
                                    setValue('coursesTaught', [...val, e.currentTarget.value]);
                                    e.currentTarget.value = '';
                                    e.preventDefault();
                                  }
                                }}
                                className="w-full p-3 border rounded-lg focus:outline-none focus:border-accent"
                                aria-label="Add course"
                              />
                              <div className="flex flex-wrap gap-2 mt-3">
                                {field.value?.map((course, i) => (
                                  <motion.span
                                    key={i}
                                    initial={{ scale: 0 }}
                                    animate={{ scale: 1 }}
                                    className="tag"
                                  >
                                    {course}
                                    <button
                                      type="button"
                                      onClick={() =>
                                        setValue(
                                          'coursesTaught',
                                          (field.value || []).filter((_, index) => index !== i)
                                        )
                                      }
                                      className="ml-2 text-sm"
                                      aria-label={`Remove ${course}`}
                                    >
                                      ×
                                    </button>
                                  </motion.span>
                                ))}
                              </div>
                              {errors.coursesTaught && (
                                <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-500 text-sm mt-1">
                                  {errors.coursesTaught?.message}
                                </motion.p>
                              )}
                            </div>
                          )}
                        />
                      </div>
                      <div className="mb-6">
                        <label className="block text-muted mb-2">Research Areas (add tags)</label>
                        <Controller
                          name="researchAreas"
                          control={control as Control<FormData>}
                          render={({ field }) => (
                            <div>
                              <input
                                placeholder="Add area and press Enter"
                                onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
                                  if (e.key === 'Enter' && e.currentTarget.value) {
                                    const val = field.value || [];
                                    setValue('researchAreas', [...val, e.currentTarget.value]);
                                    e.currentTarget.value = '';
                                    e.preventDefault();
                                  }
                                }}
                                className="w-full p-3 border rounded-lg focus:outline-none focus:border-accent"
                                aria-label="Add research area"
                              />
                              <div className="flex flex-wrap gap-2 mt-3">
                                {field.value?.map((area, i) => (
                                  <motion.span
                                    key={i}
                                    initial={{ scale: 0 }}
                                    animate={{ scale: 1 }}
                                    className="tag"
                                  >
                                    {area}
                                    <button
                                      type="button"
                                      onClick={() =>
                                        setValue(
                                          'researchAreas',
                                          (field.value || []).filter((_, index) => index !== i)
                                        )
                                      }
                                      className="ml-2 text-sm"
                                      aria-label={`Remove ${area}`}
                                    >
                                      ×
                                    </button>
                                  </motion.span>
                                ))}
                              </div>
                              {errors.researchAreas && (
                                <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-500 text-sm mt-1">
                                  {errors.researchAreas?.message}
                                </motion.p>
                              )}
                            </div>
                          )}
                        />
                      </div>
                      <FacultyCVUploader control={control as Control<FormData>} watch={watch} errors={errors} />
                    </>
                  )}
                  <TermsCheckbox control={control as Control<FormData>} errors={errors} />
                  <div className="flex justify-between">
                    <motion.button
                      type="button"
                      onClick={prevStep}
                      whileHover={{ scale: 1.05 }}
                      className="btn-secondary"
                      aria-label="Go back"
                    >
                      Back
                    </motion.button>
                    <motion.button
                      type="submit"
                      disabled={!isValid || loading}
                      whileHover={{ scale: 1.05 }}
                      className="btn-gradient flex items-center justify-center disabled:opacity-50"
                      aria-label="Create account"
                    >
                      {loading ? (
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{ duration: 1, repeat: Infinity }}
                          className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
                        />
                      ) : (
                        'Create Account'
                      )}
                    </motion.button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </form>
        </div>
      </motion.div>
    </AuthLayout>
  );
};

export default Register;