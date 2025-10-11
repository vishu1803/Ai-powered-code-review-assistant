// User types
export interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  avatar_url?: string;
  bio?: string;
  location?: string;
  company?: string;
  website?: string;
  is_active: boolean;
  is_verified: boolean;
  is_superuser: boolean;
  github_id?: string;
  gitlab_id?: string;
  bitbucket_id?: string;
  preferences: Record<string, any>;
  notification_settings: Record<string, any>;
  created_at: string;
  updated_at?: string;
  last_login?: string;
}

export interface UserCreate {
  email: string;
  username: string;
  password: string;
  full_name?: string;
  avatar_url?: string;
  bio?: string;
  location?: string;
  company?: string;
  website?: string;
}

export interface UserUpdate {
  email?: string;
  username?: string;
  full_name?: string;
  avatar_url?: string;
  bio?: string;
  location?: string;
  company?: string;
  website?: string;
  preferences?: Record<string, any>;
  notification_settings?: Record<string, any>;
}

// Authentication types
export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

// Repository types
export interface Repository {
  id: number;
  name: string;
  full_name: string;
  description?: string;
  url: string;
  clone_url: string;
  default_branch: string;
  language?: string;
  size: number;
  is_private: boolean;
  is_active: boolean;
  is_archived: boolean;
  provider: 'github' | 'gitlab' | 'bitbucket';
  external_id: string;
  webhook_id?: string;
  analysis_enabled: boolean;
  auto_review: boolean;
  review_rules: Record<string, any>;
  notification_settings: Record<string, any>;
  total_reviews: number;
  total_issues: number;
  avg_review_time: number;
  created_at: string;
  updated_at?: string;
  last_analysis?: string;
  owner_id: number;
}

export interface RepositoryCreate {
  name: string;
  full_name: string;
  description?: string;
  url: string;
  clone_url: string;
  default_branch?: string;
  language?: string;
  is_private?: boolean;
  provider: 'github' | 'gitlab' | 'bitbucket';
  external_id: string;
}

export interface ConnectRepositoryRequest {
  provider: 'github' | 'gitlab' | 'bitbucket';
  repository_url: string;
  access_token?: string;
}

// Review types
export type ReviewStatus = 'pending' | 'in_progress' | 'completed' | 'failed';
export type IssueSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface Review {
  id: number;
  title: string;
  description?: string;
  status: ReviewStatus;
  progress: number;
  pr_number?: number;
  pr_title?: string;
  pr_url?: string;
  source_branch?: string;
  target_branch?: string;
  total_files: number;
  analyzed_files: number;
  total_issues: number;
  critical_issues: number;
  high_issues: number;
  medium_issues: number;
  low_issues: number;
  code_quality_score?: number;
  security_score?: number;
  maintainability_score?: number;
  test_coverage?: number;
  ai_summary?: string;
  ai_recommendations: Array<Record<string, any>>;
  analysis_metadata: Record<string, any>;
  created_at: string;
  updated_at?: string;
  completed_at?: string;
  repository_id: number;
  author_id: number;
  issues?: Issue[];
  comments?: Comment[];
}

export interface ReviewCreate {
  title: string;
  description?: string;
  repository_id: number;
  pr_number?: number;
  pr_title?: string;
  pr_url?: string;
  source_branch?: string;
  target_branch?: string;
}

export interface ReviewSummary {
  id: number;
  title: string;
  status: ReviewStatus;
  progress: number;
  total_issues: number;
  critical_issues: number;
  code_quality_score?: number;
  created_at: string;
  completed_at?: string;
  repository_id: number;
}

// Issue types
export interface Issue {
  id: number;
  title: string;
  description: string;
  category: string;
  severity: IssueSeverity;
  rule_id?: string;
  file_path: string;
  line_start: number;
  line_end?: number;
  column_start?: number;
  column_end?: number;
  code_snippet?: string;
  suggested_fix?: string;
  ai_explanation?: string;
  confidence_score?: number;
  is_resolved: boolean;
  is_false_positive: boolean;
  created_at: string;
  updated_at?: string;
  resolved_at?: string;
  review_id: number;
  comments?: Comment[];
}

export interface IssueUpdate {
  is_resolved?: boolean;
  is_false_positive?: boolean;
}

// Comment types
export interface Comment {
  id: number;
  content: string;
  comment_type: string;
  file_path?: string;
  line_number?: number;
  is_resolved: boolean;
  created_at: string;
  updated_at?: string;
  author_id: number;
  review_id?: number;
  issue_id?: number;
  parent_id?: number;
  author?: User;
}

export interface CommentCreate {
  content: string;
  comment_type?: string;
  file_path?: string;
  line_number?: number;
  review_id?: number;
  issue_id?: number;
  parent_id?: number;
}

// Analysis types
export interface AnalysisRequest {
  repository_id: number;
  branch?: string;
  commit_sha?: string;
  files?: string[];
  rules?: string[];
}

export interface AnalysisProgress {
  review_id: number;
  status: ReviewStatus;
  progress: number;
  current_file?: string;
  total_files: number;
  analyzed_files: number;
  estimated_time_remaining?: number;
}

// Analytics types
export interface UserStatistics {
  total_users: number;
  active_users: number;
  verified_users: number;
  github_users: number;
  gitlab_users: number;
  recent_registrations: number;
  activation_rate: number;
  verification_rate: number;
}

export interface ReviewStatistics {
  total_reviews: number;
  completed_reviews: number;
  pending_reviews: number;
  in_progress_reviews: number;
  failed_reviews: number;
  average_quality_score: number;
  average_security_score: number;
  total_issues_found: number;
  critical_issues_found: number;
  high_issues_found: number;
  issues_resolved: number;
  average_review_time: number;
  review_frequency: number;
  top_issue_categories: Array<{ category: string; count: number }>;
  quality_trend: 'stable' | 'improving' | 'declining';
}

// Pagination types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface PaginationParams {
  skip?: number;
  limit?: number;
  search?: string;
  sort_by?: string;
  sort_desc?: boolean;
}

// API Error types
export interface ApiErrorResponse {
  error: {
    message: string;
    type: string;
    status_code: number;
    details?: any;
  };
}

// Notification types
export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  timestamp: string;
  read: boolean;
  action_url?: string;
}

// Theme types
export type Theme = 'light' | 'dark' | 'system';

// Dashboard types
export interface DashboardStats {
  total_repositories: number;
  active_repositories: number;
  total_reviews: number;
  completed_reviews: number;
  total_issues: number;
  critical_issues: number;
  average_quality_score: number;
  recent_activity: Array<{
    id: number;
    type: 'review_completed' | 'repository_added' | 'issue_resolved';
    title: string;
    description: string;
    timestamp: string;
    url?: string;
  }>;
}
