// src/hooks/useFacultyEmails.ts
/**
 * useFacultyEmails — React Query hook
 *
 * Fetches all faculty emails from the backend (MongoDB → Faculty collection).
 * No auth token required because the Login page calls this before login.
 *
 * Why a hook instead of a constant?
 * ----------------------------------
 * Previously the email list was hardcoded in 3 places:
 *   - Login.tsx
 *   - FacultyManagement.tsx
 *   - auth.service.ts
 *
 * Now it is stored in ONE place: MongoDB Faculty collection.
 * Any new faculty added by admin automatically appears everywhere.
 *
 * Caching strategy
 * ----------------
 * staleTime = 5 minutes → won't re-fetch within 5 minutes
 * gcTime    = 10 minutes → stays in React Query cache 10 minutes
 *
 * Fallback
 * --------
 * If the API call fails, the hook returns { emails: [], total: 0 }.
 * The login still works — we just can't show the green "approved" tick.
 */

import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface FacultyEmailEntry {
  email:      string;
  name:       string;
  department: string;
  status:     string;
}

export interface FacultyEmailsResponse {
  emails: FacultyEmailEntry[];
  total:  number;
  domain: string;
}

// ─── Base URL — reads from Vite env var, falls back to localhost ───────────────

const BASE_URL =
  (import.meta as any).env?.VITE_API_URL ?? 'http://localhost:8000/api/v1';

// ─── Main hook ────────────────────────────────────────────────────────────────

export const useFacultyEmails = () => {
  return useQuery<FacultyEmailsResponse>({
    queryKey: ['faculty-emails-public'],

    queryFn: async (): Promise<FacultyEmailsResponse> => {
      const response = await axios.get<FacultyEmailsResponse>(
        `${BASE_URL}/faculty/approved-emails`
      );
      return response.data;
    },

    staleTime: 5 * 60 * 1000,  // 5 minutes
    gcTime:    10 * 60 * 1000, // 10 minutes

    retry: 2, // retry twice on failure

    // Return empty response on error so the UI doesn't break
    placeholderData: {
      emails: [],
      total:  0,
      domain: '@fcrit.ac.in',
    },
  });
};

// ─── Convenience: returns just the Set of emails for O(1) lookup ──────────────

export const useFacultyEmailSet = (): Set<string> => {
  const { data } = useFacultyEmails();
  if (!data?.emails?.length) return new Set<string>();
  return new Set(data.emails.map((e) => e.email.toLowerCase().trim()));
};