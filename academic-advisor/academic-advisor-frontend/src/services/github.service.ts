// src/services/github.service.ts
interface FeatureRequest {
  title: string;
  description: string;
  userId?: string;
  userEmail?: string;
}

export const submitFeatureRequest = async (request: FeatureRequest): Promise<void> => {
  // Store in localStorage as fallback
  const savedRequests = JSON.parse(localStorage.getItem('feature_requests') || '[]');
  savedRequests.push({ ...request, timestamp: new Date().toISOString() });
  localStorage.setItem('feature_requests', JSON.stringify(savedRequests));

  // Simulate API call
  return new Promise((resolve) => {
    setTimeout(resolve, 1000);
  });
};