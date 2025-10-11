import { create } from 'zustand';
import { Repository, ReviewSummary } from '@/lib/types/api';

interface RepositoryState {
  repositories: Repository[];
  currentRepository: Repository | null;
  recentReviews: ReviewSummary[];
  isLoading: boolean;
  
  // Actions
  setRepositories: (repositories: Repository[]) => void;
  addRepository: (repository: Repository) => void;
  updateRepository: (id: number, updates: Partial<Repository>) => void;
  removeRepository: (id: number) => void;
  setCurrentRepository: (repository: Repository | null) => void;
  setRecentReviews: (reviews: ReviewSummary[]) => void;
  setLoading: (loading: boolean) => void;
}

export const useRepositoryStore = create<RepositoryState>((set, get) => ({
  repositories: [],
  currentRepository: null,
  recentReviews: [],
  isLoading: false,

  setRepositories: (repositories) =>
    set({ repositories }),

  addRepository: (repository) =>
    set((state) => ({
      repositories: [...state.repositories, repository],
    })),

  updateRepository: (id, updates) =>
    set((state) => ({
      repositories: state.repositories.map((repo) =>
        repo.id === id ? { ...repo, ...updates } : repo
      ),
      currentRepository:
        state.currentRepository?.id === id
          ? { ...state.currentRepository, ...updates }
          : state.currentRepository,
    })),

  removeRepository: (id) =>
    set((state) => ({
      repositories: state.repositories.filter((repo) => repo.id !== id),
      currentRepository:
        state.currentRepository?.id === id ? null : state.currentRepository,
    })),

  setCurrentRepository: (repository) =>
    set({ currentRepository: repository }),

  setRecentReviews: (recentReviews) =>
    set({ recentReviews }),

  setLoading: (isLoading) =>
    set({ isLoading }),
}));
