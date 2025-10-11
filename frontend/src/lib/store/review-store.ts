import { create } from 'zustand';
import { Review, Issue, Comment, AnalysisProgress } from '@/lib/types/api';

interface ReviewState {
  reviews: Review[];
  currentReview: Review | null;
  issues: Issue[];
  comments: Comment[];
  analysisProgress: AnalysisProgress | null;
  isLoading: boolean;
  
  // Actions
  setReviews: (reviews: Review[]) => void;
  addReview: (review: Review) => void;
  updateReview: (id: number, updates: Partial<Review>) => void;
  removeReview: (id: number) => void;
  setCurrentReview: (review: Review | null) => void;
  setIssues: (issues: Issue[]) => void;
  updateIssue: (id: number, updates: Partial<Issue>) => void;
  setComments: (comments: Comment[]) => void;
  addComment: (comment: Comment) => void;
  setAnalysisProgress: (progress: AnalysisProgress | null) => void;
  setLoading: (loading: boolean) => void;
}

export const useReviewStore = create<ReviewState>((set, get) => ({
  reviews: [],
  currentReview: null,
  issues: [],
  comments: [],
  analysisProgress: null,
  isLoading: false,

  setReviews: (reviews) =>
    set({ reviews }),

  addReview: (review) =>
    set((state) => ({
      reviews: [review, ...state.reviews],
    })),

  updateReview: (id, updates) =>
    set((state) => ({
      reviews: state.reviews.map((review) =>
        review.id === id ? { ...review, ...updates } : review
      ),
      currentReview:
        state.currentReview?.id === id
          ? { ...state.currentReview, ...updates }
          : state.currentReview,
    })),

  removeReview: (id) =>
    set((state) => ({
      reviews: state.reviews.filter((review) => review.id !== id),
      currentReview:
        state.currentReview?.id === id ? null : state.currentReview,
    })),

  setCurrentReview: (review) =>
    set({ currentReview: review }),

  setIssues: (issues) =>
    set({ issues }),

  updateIssue: (id, updates) =>
    set((state) => ({
      issues: state.issues.map((issue) =>
        issue.id === id ? { ...issue, ...updates } : issue
      ),
    })),

  setComments: (comments) =>
    set({ comments }),

  addComment: (comment) =>
    set((state) => ({
      comments: [...state.comments, comment],
    })),

  setAnalysisProgress: (analysisProgress) =>
    set({ analysisProgress }),

  setLoading: (isLoading) =>
    set({ isLoading }),
}));
