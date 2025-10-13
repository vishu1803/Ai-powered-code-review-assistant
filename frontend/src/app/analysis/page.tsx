"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/lib/store/auth-store"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import DashboardLayout from "@/components/layout/dashboard-layout"
import { toast } from "sonner"
import { 
  FileText, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Code, 
  Bug,
  Shield,
  Zap,
  GitBranch,
  Github,
  Gitlab,
  Play,
  RefreshCw,
  Download,
  Eye,
  Filter,
  Search,
  ArrowLeft,
  Plus,
  Home
} from "lucide-react"
import apiClient from "@/lib/api/client"
import Link from "next/link"

interface Repository {
  id: number
  name: string
  full_name: string
  provider: string
  language: string | null
  is_active: boolean
  total_reviews: number
  created_at: string
}

interface Review {
  id: number
  title: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  code_quality_score: number | null
  security_score: number | null
  performance_score: number | null
  total_issues: number
  created_at: string
  updated_at: string
  repository_id: number
  repository?: {  // Made optional with ?
    name: string
    provider: string
  }
}

interface AnalyticsData {
  total_reviews: number
  completed_reviews: number
  total_issues_found: number
  average_quality_score: number
  average_security_score: number
  average_performance_score: number
  reviews_this_month: number
  critical_issues: number
}

export default function AnalysisPage() {
  const router = useRouter()
  const { user } = useAuthStore()
  const [activeTab, setActiveTab] = useState("overview")
  const [repositories, setRepositories] = useState<Repository[]>([])
  const [reviews, setReviews] = useState<Review[]>([])
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(false)
  const [selectedRepo, setSelectedRepo] = useState<string>("")
  const [analysisType, setAnalysisType] = useState("full")
  const [filterStatus, setFilterStatus] = useState("all")

  // Fetch data on component mount
  useEffect(() => {
    fetchRepositories()
    fetchReviews()
    fetchAnalytics()
  }, [])

  const fetchRepositories = async () => {
    try {
      const data = await apiClient.get<Repository[]>('/repositories')
      setRepositories(data)
    } catch (error) {
      console.error('Error fetching repositories:', error)
      // Don't show error for empty repositories
      if (error?.response?.status !== 404) {
        toast.error('Failed to fetch repositories')
      }
    }
  }

  const fetchReviews = async () => {
    try {
      const data = await apiClient.get<Review[]>('/reviews')
      setReviews(data)
    } catch (error) {
      console.error('Error fetching reviews:', error)
      // Don't show error for empty reviews
      if (error?.response?.status !== 404) {
        toast.error('Failed to fetch reviews')
      }
    }
  }

  const fetchAnalytics = async () => {
    try {
      const data = await apiClient.get<AnalyticsData>('/analytics/overview')
      setAnalytics(data)
    } catch (error) {
      console.error('Error fetching analytics:', error)
      // Don't show error for analytics as it's supplementary
    }
  }

  const startAnalysis = async () => {
    if (!selectedRepo) {
      toast.error('Please select a repository')
      return
    }

    setLoading(true)
    try {
      const response = await apiClient.post('/reviews', {
        repository_id: parseInt(selectedRepo),
        analysis_type: analysisType,
        title: `${analysisType} analysis - ${new Date().toLocaleDateString()}`
      })
      
      toast.success('Analysis started successfully!')
      fetchReviews() // Refresh reviews list
      setSelectedRepo("")
    } catch (error: any) {
      console.error('Error starting analysis:', error)
      const message = error.response?.data?.detail || 'Failed to start analysis'
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
      case 'in_progress': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300'
      case 'pending': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
      case 'failed': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300'
    }
  }

  const getProviderIcon = (provider?: string) => {
    switch (provider) {
      case 'github': return <Github className="h-4 w-4" />
      case 'gitlab': return <Gitlab className="h-4 w-4" />
      default: return <GitBranch className="h-4 w-4" />
    }
  }

  // Helper function to get repository name safely
  const getRepositoryName = (review: Review) => {
    if (review.repository?.name) {
      return review.repository.name
    }
    // Find repository by ID
    const repo = repositories.find(r => r.id === review.repository_id)
    return repo?.name || `Repository ${review.repository_id}`
  }

  // Helper function to get repository provider safely
  const getRepositoryProvider = (review: Review) => {
    if (review.repository?.provider) {
      return review.repository.provider
    }
    // Find repository by ID
    const repo = repositories.find(r => r.id === review.repository_id)
    return repo?.provider || 'github'
  }

  const filteredReviews = reviews.filter(review => 
    filterStatus === 'all' || review.status === filterStatus
  )

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header with Back Button */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button variant="ghost" onClick={() => router.push('/dashboard')}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Code Analysis</h1>
              <p className="text-muted-foreground">
                AI-powered code quality analysis and security reviews
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="outline" onClick={() => router.push('/dashboard')}>
              <Home className="mr-2 h-4 w-4" />
              Dashboard
            </Button>
            {repositories.length > 0 ? (
              <Button onClick={startAnalysis} disabled={loading}>
                {loading ? (
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Play className="mr-2 h-4 w-4" />
                )}
                {loading ? 'Starting...' : 'Start Analysis'}
              </Button>
            ) : (
              <Button asChild>
                <Link href="/repositories/connect">
                  <Plus className="mr-2 h-4 w-4" />
                  Connect Repository
                </Link>
              </Button>
            )}
          </div>
        </div>

        {/* No Repositories State */}
        {repositories.length === 0 && (
          <Card>
            <CardContent className="flex flex-col items-center justify-center h-64 text-center">
              <GitBranch className="h-16 w-16 text-muted-foreground/50 mb-4" />
              <h3 className="text-lg font-medium mb-2">No Repositories Connected</h3>
              <p className="text-muted-foreground mb-6 max-w-md">
                Connect your GitHub repositories to start analyzing your code with AI-powered insights.
              </p>
              <Button asChild size="lg">
                <Link href="/repositories/connect">
                  <Github className="mr-2 h-5 w-5" />
                  Connect GitHub Repository
                </Link>
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Content when repositories exist */}
        {repositories.length > 0 && (
          <>
            {/* Stats Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Reviews</CardTitle>
                  <FileText className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{analytics?.total_reviews || reviews.length}</div>
                  <p className="text-xs text-muted-foreground">
                    {analytics?.reviews_this_month || 0} this month
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Issues Found</CardTitle>
                  <Bug className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {analytics?.total_issues_found || reviews.reduce((sum, review) => sum + review.total_issues, 0)}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {analytics?.critical_issues || 0} critical
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Quality Score</CardTitle>
                  <Shield className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {analytics?.average_quality_score ? `${Math.round(analytics.average_quality_score)}%` : '--'}
                  </div>
                  <Progress value={analytics?.average_quality_score || 0} className="mt-2" />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Security Score</CardTitle>
                  <Zap className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {analytics?.average_security_score ? `${Math.round(analytics.average_security_score)}%` : '--'}
                  </div>
                  <Progress value={analytics?.average_security_score || 0} className="mt-2" />
                </CardContent>
              </Card>
            </div>

            {/* Main Content Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
              <TabsList>
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="new-analysis">New Analysis</TabsTrigger>
                <TabsTrigger value="reviews">Review History</TabsTrigger>
                <TabsTrigger value="repositories">Repositories</TabsTrigger>
              </TabsList>

              {/* Overview Tab */}
              <TabsContent value="overview" className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <Card>
                    <CardHeader>
                      <CardTitle>Recent Reviews</CardTitle>
                      <CardDescription>Your latest code analysis results</CardDescription>
                    </CardHeader>
                    <CardContent>
                      {reviews.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-32 text-center">
                          <FileText className="h-8 w-8 text-muted-foreground/50 mb-2" />
                          <p className="text-muted-foreground">No reviews yet</p>
                          <p className="text-sm text-muted-foreground mt-1">Start your first analysis</p>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          {reviews.slice(0, 3).map((review) => (
                            <div key={review.id} className="flex items-center justify-between p-3 border rounded-lg">
                              <div className="flex items-center space-x-3">
                                {getProviderIcon(getRepositoryProvider(review))}
                                <div>
                                  <p className="font-medium">{review.title}</p>
                                  <p className="text-sm text-muted-foreground">{getRepositoryName(review)}</p>
                                </div>
                              </div>
                              <Badge className={getStatusColor(review.status)}>
                                {review.status}
                              </Badge>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Connected Repositories</CardTitle>
                      <CardDescription>Ready for AI code analysis</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {repositories.slice(0, 3).map((repo) => (
                          <div key={repo.id} className="flex items-center justify-between p-3 border rounded-lg">
                            <div className="flex items-center space-x-3">
                              {getProviderIcon(repo.provider)}
                              <div>
                                <p className="font-medium">{repo.name}</p>
                                <p className="text-sm text-muted-foreground">{repo.language || 'Unknown'}</p>
                              </div>
                            </div>
                            <Badge variant="outline">
                              {repo.total_reviews} reviews
                            </Badge>
                          </div>
                        ))}
                      </div>
                      {repositories.length > 3 && (
                        <div className="mt-4 pt-4 border-t">
                          <Button variant="outline" size="sm" asChild className="w-full">
                            <Link href="/repositories">
                              View All {repositories.length} Repositories
                            </Link>
                          </Button>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              {/* New Analysis Tab */}
              <TabsContent value="new-analysis" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Start New Analysis</CardTitle>
                    <CardDescription>
                      Run AI-powered code analysis on your repositories
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="repository">Select Repository</Label>
                        <Select value={selectedRepo} onValueChange={setSelectedRepo}>
                          <SelectTrigger>
                            <SelectValue placeholder="Choose a repository..." />
                          </SelectTrigger>
                          <SelectContent>
                            {repositories.map((repo) => (
                              <SelectItem key={repo.id} value={repo.id.toString()}>
                                <div className="flex items-center space-x-2">
                                  {getProviderIcon(repo.provider)}
                                  <span>{repo.name}</span>
                                </div>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="analysis-type">Analysis Type</Label>
                        <Select value={analysisType} onValueChange={setAnalysisType}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="full">Full Analysis</SelectItem>
                            <SelectItem value="security">Security Only</SelectItem>
                            <SelectItem value="performance">Performance Only</SelectItem>
                            <SelectItem value="quality">Code Quality Only</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="flex justify-end">
                      <Button onClick={startAnalysis} disabled={loading || !selectedRepo}>
                        {loading ? (
                          <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                          <Play className="mr-2 h-4 w-4" />
                        )}
                        {loading ? 'Starting Analysis...' : 'Start Analysis'}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Reviews Tab */}
              <TabsContent value="reviews" className="space-y-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between">
                    <div>
                      <CardTitle>Analysis History</CardTitle>
                      <CardDescription>All your code analysis results</CardDescription>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Select value={filterStatus} onValueChange={setFilterStatus}>
                        <SelectTrigger className="w-32">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All Status</SelectItem>
                          <SelectItem value="completed">Completed</SelectItem>
                          <SelectItem value="in_progress">In Progress</SelectItem>
                          <SelectItem value="pending">Pending</SelectItem>
                          <SelectItem value="failed">Failed</SelectItem>
                        </SelectContent>
                      </Select>
                      <Button variant="outline" size="sm" onClick={fetchReviews}>
                        <RefreshCw className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {filteredReviews.length === 0 ? (
                      <div className="flex flex-col items-center justify-center h-32 text-center">
                        <Clock className="h-8 w-8 text-muted-foreground/50 mb-2" />
                        <p className="text-muted-foreground">No reviews found</p>
                        <p className="text-sm text-muted-foreground mt-1">
                          {reviews.length === 0 ? 'Start your first analysis' : 'Try adjusting the filter'}
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {filteredReviews.map((review) => (
                          <div key={review.id} className="border rounded-lg p-4">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center space-x-3">
                                {getProviderIcon(getRepositoryProvider(review))}
                                <div>
                                  <h3 className="font-medium">{review.title}</h3>
                                  <p className="text-sm text-muted-foreground">{getRepositoryName(review)}</p>
                                </div>
                              </div>
                              <Badge className={getStatusColor(review.status)}>
                                {review.status}
                              </Badge>
                            </div>
                            
                            <div className="grid gap-4 md:grid-cols-4 mt-4">
                              <div>
                                <p className="text-sm font-medium">Quality Score</p>
                                <p className="text-2xl font-bold">
                                  {review.code_quality_score ? `${Math.round(review.code_quality_score)}%` : '--'}
                                </p>
                              </div>
                              <div>
                                <p className="text-sm font-medium">Security Score</p>
                                <p className="text-2xl font-bold">
                                  {review.security_score ? `${Math.round(review.security_score)}%` : '--'}
                                </p>
                              </div>
                              <div>
                                <p className="text-sm font-medium">Performance Score</p>
                                <p className="text-2xl font-bold">
                                  {review.performance_score ? `${Math.round(review.performance_score)}%` : '--'}
                                </p>
                              </div>
                              <div>
                                <p className="text-sm font-medium">Issues Found</p>
                                <p className="text-2xl font-bold">{review.total_issues}</p>
                              </div>
                            </div>

                            <div className="flex items-center justify-between mt-4 pt-4 border-t">
                              <p className="text-sm text-muted-foreground">
                                Created {new Date(review.created_at).toLocaleDateString()}
                              </p>
                              <div className="flex space-x-2">
                                <Button variant="outline" size="sm" asChild>
                                  <Link href={`/reviews/${review.id}`}>
                                    <Eye className="mr-2 h-4 w-4" />
                                    View Details
                                  </Link>
                                </Button>
                                {review.status === 'completed' && (
                                  <Button variant="outline" size="sm">
                                    <Download className="mr-2 h-4 w-4" />
                                    Export Report
                                  </Button>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Repositories Tab */}
              <TabsContent value="repositories" className="space-y-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between">
                    <div>
                      <CardTitle>Connected Repositories</CardTitle>
                      <CardDescription>Manage your connected repositories</CardDescription>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button onClick={fetchRepositories} variant="outline" size="sm">
                        <RefreshCw className="h-4 w-4" />
                      </Button>
                      <Button asChild size="sm">
                        <Link href="/repositories/connect">
                          <Plus className="mr-2 h-4 w-4" />
                          Connect More
                        </Link>
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {repositories.map((repo) => (
                        <div key={repo.id} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              {getProviderIcon(repo.provider)}
                              <div>
                                <h3 className="font-medium">{repo.name}</h3>
                                <p className="text-sm text-muted-foreground">
                                  {repo.full_name} • {repo.language || 'Unknown'}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center space-x-4">
                              <div className="text-right">
                                <p className="text-sm font-medium">{repo.total_reviews}</p>
                                <p className="text-xs text-muted-foreground">reviews</p>
                              </div>
                              <Badge variant={repo.is_active ? 'default' : 'secondary'}>
                                {repo.is_active ? 'Active' : 'Inactive'}
                              </Badge>
                              <Button 
                                variant="outline" 
                                size="sm"
                                onClick={() => {
                                  setSelectedRepo(repo.id.toString())
                                  setActiveTab('new-analysis')
                                }}
                              >
                                <Play className="mr-2 h-4 w-4" />
                                Analyze
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </>
        )}
      </div>
    </DashboardLayout>
  )
}
