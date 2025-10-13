"use client"

import { useState, useEffect, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { 
  ArrowLeft, 
  Play, 
  Pause, 
  RefreshCw, 
  Download, 
  Share, 
  MessageSquare,
  AlertTriangle,
  CheckCircle,
  Clock,
  FileText,
  Code,
  Shield,
  BarChart3,
  Home
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import DashboardLayout from "@/components/layout/dashboard-layout"
import ReviewProgress from "@/components/reviews/review-progress"
import IssuesList from "@/components/reviews/issues-list"
import CodeViewer from "@/components/reviews/code-viewer"
import CommentsPanel from "@/components/reviews/comments-panel"
import AISummary from "@/components/reviews/ai-summary"
import { Review, Issue, Comment } from "@/lib/types/api"
import { toast } from "sonner"
import Link from "next/link"
import { formatDateTime, formatRelativeTime } from "@/lib/utils"
import apiClient from "@/lib/api/client"

export default function ReviewDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const queryClient = useQueryClient()
  
  const reviewId = parseInt(params.id as string)
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null)
  const [isPolling, setIsPolling] = useState(false)

  // Fetch review details
  const { 
    data: review, 
    isLoading: isLoadingReview, 
    error: reviewError,
    refetch: refetchReview
  } = useQuery({
    queryKey: ['review', reviewId],
    queryFn: async (): Promise<Review> => {
      const data = await apiClient.get<Review>(`/reviews/${reviewId}`)
      return data
    },
    enabled: !!reviewId,
    refetchInterval: (data) => {
      // Poll every 3 seconds if review is in progress
      return data?.status === 'in_progress' ? 3000 : false
    },
  })

  // Fetch issues
  const { 
    data: issues = [], 
    isLoading: isLoadingIssues,
    refetch: refetchIssues
  } = useQuery({
    queryKey: ['review-issues', reviewId],
    queryFn: async (): Promise<Issue[]> => {
      try {
        const data = await apiClient.get<Issue[]>(`/reviews/${reviewId}/issues`)
        return data || []
      } catch (error: any) {
        if (error.response?.status === 404) {
          return []
        }
        throw error
      }
    },
    enabled: !!reviewId && review?.status !== 'pending',
  })

  // Fetch comments
  const { 
    data: comments = [],
    refetch: refetchComments
  } = useQuery({
    queryKey: ['review-comments', reviewId],
    queryFn: async (): Promise<Comment[]> => {
      try {
        const data = await apiClient.get<Comment[]>(`/reviews/${reviewId}/comments`)
        return data || []
      } catch (error: any) {
        if (error.response?.status === 404) {
          return []
        }
        throw error
      }
    },
    enabled: !!reviewId,
  })

  // Real-time progress updates
  const checkProgress = useCallback(async () => {
    if (review?.status === 'in_progress') {
      try {
        const progress = await apiClient.get(`/reviews/${reviewId}/progress`)
        // Update the review cache with new progress
        queryClient.setQueryData(['review', reviewId], (oldData: Review | undefined) => {
          if (!oldData) return oldData
          return {
            ...oldData,
            progress: progress.progress,
            analyzed_files: progress.analyzed_files,
            total_files: progress.total_files,
          }
        })
      } catch (error) {
        console.error('Failed to fetch progress:', error)
      }
    }
  }, [review?.status, reviewId, queryClient])

  useEffect(() => {
    if (review?.status === 'in_progress') {
      const interval = setInterval(checkProgress, 2000)
      setIsPolling(true)
      return () => {
        clearInterval(interval)
        setIsPolling(false)
      }
    }
  }, [review?.status, checkProgress])

  const handleGenerateSummary = async () => {
    try {
      await apiClient.post(`/reviews/${reviewId}/summary`)
      toast.success("AI summary generation started")
      setTimeout(() => refetchReview(), 2000)
    } catch (error: any) {
      console.error('Error generating summary:', error)
      toast.error("Failed to generate summary")
    }
  }

  const handleIssueUpdate = async (issueId: number, updates: any) => {
    try {
      await apiClient.patch(`/reviews/${reviewId}/issues/${issueId}`, updates)
      refetchIssues()
      toast.success("Issue updated")
    } catch (error: any) {
      console.error('Error updating issue:', error)
      toast.error("Failed to update issue")
    }
  }

  const handleAddComment = async (content: string, issueId?: number) => {
    try {
      await apiClient.post(`/reviews/${reviewId}/comments`, {
        content,
        issue_id: issueId,
      })
      refetchComments()
      toast.success("Comment added")
    } catch (error: any) {
      console.error('Error adding comment:', error)
      toast.error("Failed to add comment")
    }
  }

  if (reviewError) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <p className="text-lg font-medium text-destructive mb-2">Failed to load review</p>
          <p className="text-muted-foreground mb-4">
            {reviewError?.response?.status === 404 
              ? "Review not found or you don't have access" 
              : "Please try refreshing the page"}
          </p>
          <div className="flex space-x-2">
            <Button variant="outline" onClick={() => router.push('/reviews')}>
              Back to Reviews
            </Button>
            <Button onClick={() => refetchReview()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (isLoadingReview) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <div className="flex items-center space-x-4">
            <div className="h-8 w-8 bg-muted animate-pulse rounded" />
            <div className="space-y-2">
              <div className="h-8 w-64 bg-muted animate-pulse rounded" />
              <div className="h-4 w-96 bg-muted animate-pulse rounded" />
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Card key={i}>
                <CardContent className="p-6">
                  <div className="space-y-3">
                    <div className="h-4 w-20 bg-muted animate-pulse rounded" />
                    <div className="h-8 w-16 bg-muted animate-pulse rounded" />
                    <div className="h-3 w-24 bg-muted animate-pulse rounded" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (!review) return null

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'in_progress':
        return <Clock className="h-5 w-5 text-blue-500 animate-pulse" />
      case 'failed':
        return <AlertTriangle className="h-5 w-5 text-red-500" />
      default:
        return <Clock className="h-5 w-5 text-muted-foreground" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
      case 'in_progress':
        return 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
      case 'failed':
        return 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
      default:
        return 'bg-muted text-muted-foreground'
    }
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header with Navigation */}
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-4">
            <Button variant="ghost" size="icon" asChild>
              <Link href="/reviews">
                <ArrowLeft className="h-4 w-4" />
              </Link>
            </Button>
            <div className="space-y-1">
              <div className="flex items-center space-x-3">
                <h1 className="text-3xl font-bold tracking-tight">{review.title}</h1>
                <Badge className={getStatusColor(review.status)}>
                  <div className="flex items-center space-x-1">
                    {getStatusIcon(review.status)}
                    <span className="capitalize">{review.status.replace('_', ' ')}</span>
                  </div>
                </Badge>
                {isPolling && (
                  <Badge variant="outline" className="text-blue-600">
                    <div className="flex items-center space-x-1">
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
                      <span>Live Updates</span>
                    </div>
                  </Badge>
                )}
              </div>
              <p className="text-muted-foreground">
                {review.description || `Code review for ${review.source_branch || 'main'} branch`}
              </p>
              <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                <span>Created {formatRelativeTime(review.created_at)}</span>
                {review.completed_at && (
                  <span>Completed {formatRelativeTime(review.completed_at)}</span>
                )}
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button variant="outline" onClick={() => router.push('/reviews')}>
              <Home className="h-4 w-4 mr-2" />
              Reviews
            </Button>
            <Button variant="outline" onClick={() => refetchReview()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            {review.status === 'completed' && (
              <>
                <Button variant="outline">
                  <Download className="h-4 w-4 mr-2" />
                  Export
                </Button>
                <Button variant="outline">
                  <Share className="h-4 w-4 mr-2" />
                  Share
                </Button>
              </>
            )}
            {!review.ai_summary && review.status === 'completed' && (
              <Button onClick={handleGenerateSummary}>
                Generate AI Summary
              </Button>
            )}
          </div>
        </div>

        {/* Progress (if in progress) */}
        {review.status === 'in_progress' && review.progress !== undefined && (
          <Card>
            <CardContent className="p-6">
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Analysis Progress</span>
                  <span>{Math.round(review.progress * 100)}%</span>
                </div>
                <Progress value={review.progress * 100} />
                <p className="text-xs text-muted-foreground">
                  {review.analyzed_files || 0} of {review.total_files || 0} files analyzed
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Stats Overview */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center space-x-2">
                <FileText className="h-4 w-4" />
                <span>Files Analyzed</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{review.analyzed_files || 0}</div>
              <p className="text-xs text-muted-foreground">
                of {review.total_files || 0} total files
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center space-x-2">
                <AlertTriangle className="h-4 w-4" />
                <span>Issues Found</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{review.total_issues || 0}</div>
              <p className="text-xs text-muted-foreground">
                {review.critical_issues || 0} critical
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center space-x-2">
                <Shield className="h-4 w-4" />
                <span>Quality Score</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {review.code_quality_score ? `${review.code_quality_score.toFixed(1)}/10` : 'N/A'}
              </div>
              <p className="text-xs text-muted-foreground">
                {review.security_score ? `Security: ${review.security_score.toFixed(1)}/10` : 'Analyzing...'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center space-x-2">
                <MessageSquare className="h-4 w-4" />
                <span>Comments</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{comments.length}</div>
              <p className="text-xs text-muted-foreground">
                {issues.filter(i => !i.is_resolved).length} unresolved
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="issues">
              Issues ({issues.length})
            </TabsTrigger>
            <TabsTrigger value="code">Code</TabsTrigger>
            <TabsTrigger value="comments">
              Comments ({comments.length})
            </TabsTrigger>
            <TabsTrigger value="ai-summary">AI Summary</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-3">
              <div className="lg:col-span-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Recent Issues</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {isLoadingIssues ? (
                      <div className="space-y-3">
                        {Array.from({ length: 3 }).map((_, i) => (
                          <div key={i} className="space-y-2">
                            <div className="h-4 w-3/4 bg-muted animate-pulse rounded" />
                            <div className="h-3 w-1/2 bg-muted animate-pulse rounded" />
                          </div>
                        ))}
                      </div>
                    ) : issues && issues.length > 0 ? (
                      <div className="space-y-3">
                        {issues.slice(0, 5).map((issue) => (
                          <div
                            key={issue.id}
                            className="flex items-start space-x-3 p-3 rounded-lg hover:bg-muted/50 cursor-pointer"
                            onClick={() => {
                              setSelectedIssue(issue)
                              setActiveTab('issues')
                            }}
                          >
                            <div className={`mt-1 w-2 h-2 rounded-full ${
                              issue.severity === 'critical' ? 'bg-red-500' :
                              issue.severity === 'high' ? 'bg-orange-500' :
                              issue.severity === 'medium' ? 'bg-yellow-500' : 'bg-blue-500'
                            }`} />
                            <div className="flex-1">
                              <h4 className="font-medium">{issue.title}</h4>
                              <p className="text-sm text-muted-foreground">
                                {issue.file_path}:{issue.line_start}
                              </p>
                            </div>
                            <Badge variant="outline" className="text-xs">
                              {issue.severity}
                            </Badge>
                          </div>
                        ))}
                        {issues.length > 5 && (
                          <Button variant="ghost" onClick={() => setActiveTab('issues')}>
                            View all {issues.length} issues
                          </Button>
                        )}
                      </div>
                    ) : (
                      <p className="text-muted-foreground text-center py-8">
                        {review.status === 'completed' 
                          ? "No issues found. Great job! 🎉" 
                          : "Analysis in progress..."}
                      </p>
                    )}
                  </CardContent>
                </Card>
              </div>

              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Quality Metrics</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {review.code_quality_score && (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>Code Quality</span>
                          <span>{review.code_quality_score.toFixed(1)}/10</span>
                        </div>
                        <Progress value={review.code_quality_score * 10} />
                      </div>
                    )}
                    {review.security_score && (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>Security</span>
                          <span>{review.security_score.toFixed(1)}/10</span>
                        </div>
                        <Progress value={review.security_score * 10} />
                      </div>
                    )}
                    {review.maintainability_score && (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>Maintainability</span>
                          <span>{review.maintainability_score.toFixed(1)}/10</span>
                        </div>
                        <Progress value={review.maintainability_score * 10} />
                      </div>
                    )}
                    {!review.code_quality_score && !review.security_score && (
                      <p className="text-muted-foreground text-sm">
                        Quality metrics will appear after analysis completes
                      </p>
                    )}
                  </CardContent>
                </Card>

                {review.ai_recommendations && review.ai_recommendations.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">AI Recommendations</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {review.ai_recommendations.slice(0, 3).map((rec, index) => (
                          <div key={index} className="space-y-1">
                            <h4 className="font-medium text-sm">{rec.title}</h4>
                            <p className="text-xs text-muted-foreground">{rec.description}</p>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          </TabsContent>

          <TabsContent value="issues">
            {/* Issues List Component - Create a simple version if component doesn't exist */}
            <Card>
              <CardHeader>
                <CardTitle>Issues ({issues.length})</CardTitle>
              </CardHeader>
              <CardContent>
                {isLoadingIssues ? (
                  <div className="space-y-4">
                    {Array.from({ length: 3 }).map((_, i) => (
                      <div key={i} className="space-y-2 p-4 border rounded">
                        <div className="h-4 w-3/4 bg-muted animate-pulse rounded" />
                        <div className="h-3 w-1/2 bg-muted animate-pulse rounded" />
                      </div>
                    ))}
                  </div>
                ) : issues.length > 0 ? (
                  <div className="space-y-4">
                    {issues.map((issue) => (
                      <div key={issue.id} className="border rounded-lg p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h3 className="font-medium">{issue.title}</h3>
                            <p className="text-sm text-muted-foreground mt-1">
                              {issue.description}
                            </p>
                            <div className="flex items-center space-x-4 mt-2 text-xs text-muted-foreground">
                              <span>{issue.file_path}:{issue.line_start}</span>
                              <Badge variant="outline" className="text-xs">
                                {issue.category}
                              </Badge>
                            </div>
                          </div>
                          <Badge 
                            variant={issue.severity === 'critical' ? 'destructive' : 'outline'}
                            className="ml-4"
                          >
                            {issue.severity}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground text-center py-8">
                    No issues found
                  </p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="code">
            <Card>
              <CardHeader>
                <CardTitle>Code Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground text-center py-8">
                  Code viewer will be available soon
                </p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="comments">
            <Card>
              <CardHeader>
                <CardTitle>Comments ({comments.length})</CardTitle>
              </CardHeader>
              <CardContent>
                {comments.length > 0 ? (
                  <div className="space-y-4">
                    {comments.map((comment) => (
                      <div key={comment.id} className="border rounded-lg p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <p>{comment.content}</p>
                            <p className="text-xs text-muted-foreground mt-2">
                              {formatRelativeTime(comment.created_at)}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground text-center py-8">
                    No comments yet
                  </p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="ai-summary">
            <Card>
              <CardHeader>
                <CardTitle>AI Summary</CardTitle>
              </CardHeader>
              <CardContent>
                {review.ai_summary ? (
                  <div className="prose dark:prose-invert max-w-none">
                    <p>{review.ai_summary}</p>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-muted-foreground mb-4">
                      No AI summary available yet
                    </p>
                    {review.status === 'completed' && (
                      <Button onClick={handleGenerateSummary}>
                        Generate AI Summary
                      </Button>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  )
}
