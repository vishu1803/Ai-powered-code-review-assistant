import apiClient from './client';
import { Review, ReviewCreate, ReviewSummary, Issue, Comment, CommentCreate, AnalysisRequest, AnalysisProgress, PaginationParams } from '@/lib/types/api';

export const reviewsApi = {
  // Get user's reviews
  async getReviews(params?: PaginationParams & {
    repository_id?: number;
    status?: string;
  }) {
    const searchParams = new URLSearchParams();
    
    if (params?.skip) searchParams.append('skip', params.skip.toString());
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.repository_id) searchParams.append('repository_id', params.repository_id.toString());
    if (params?.status) searchParams.append('status', params.status);

    return apiClient.get<ReviewSummary[]>(`/reviews?${searchParams.toString()}`);
  },

  // Get single review with details
  async getReview(id: number) {
    return apiClient.get<Review>(`/reviews/${id}`);
  },

  // Create new review
  async createReview(data: ReviewCreate) {
    return apiClient.post<Review>('/reviews', data);
  },

  // Update review
  async updateReview(id: number, data: Partial<Review>) {
    return apiClient.put<Review>(`/reviews/${id}`, data);
  },

  // Delete review
  async deleteReview(id: number) {
    return apiClient.delete(`/reviews/${id}`);
  },

  // Start code analysis
  async startAnalysis(data: AnalysisRequest) {
    return apiClient.post<{ review_id: number; task_id: string }>('/reviews/analyze', data);
  },

  // Get analysis progress
  async getAnalysisProgress(reviewId: number) {
    return apiClient.get<AnalysisProgress>(`/reviews/${reviewId}/progress`);
  },

  // Get review issues
  async getReviewIssues(reviewId: number, params?: {
    severity?: string;
    category?: string;
    resolved?: boolean;
  }) {
    const searchParams = new URLSearchParams();
    
    if (params?.severity) searchParams.append('severity', params.severity);
    if (params?.category) searchParams.append('category', params.category);
    if (params?.resolved !== undefined) searchParams.append('resolved', params.resolved.toString());

    return apiClient.get<Issue[]>(`/reviews/${reviewId}/issues?${searchParams.toString()}`);
  },

  // Update issue
  async updateIssue(issueId: number, data: { is_resolved?: boolean; is_false_positive?: boolean }) {
    return apiClient.put<Issue>(`/reviews/issues/${issueId}`, data);
  },

  // Get review comments
  async getReviewComments(reviewId: number) {
    return apiClient.get<Comment[]>(`/reviews/${reviewId}/comments`);
  },

  // Add comment
  async addComment(reviewId: number, data: CommentCreate) {
    return apiClient.post<Comment>(`/reviews/${reviewId}/comments`, data);
  },

  // Generate AI summary
  async generateSummary(reviewId: number) {
    return apiClient.post(`/reviews/${reviewId}/summary`);
  },
};
