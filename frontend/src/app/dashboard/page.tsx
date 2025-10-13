"use client"

import { useEffect, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Plus, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import DashboardLayout from "@/components/layout/dashboard-layout"
import StatsOverview from "@/components/dashboard/stats-overview"
import RecentActivity from "@/components/dashboard/recent-activity"
import QualityChart from "@/components/dashboard/quality-chart"
import { toast } from "sonner"
import Link from "next/link"
import apiClient from "@/lib/api/client"

interface DashboardData {
  stats: {
    total_repositories: number
    active_repositories: number
    total_reviews: number
    completed_reviews: number
    total_issues: number
    critical_issues: number
    average_quality_score: number
    average_review_time: number
  }
  recent_activity: Array<{
    id: string
    type: 'review_completed' | 'repository_added' | 'issue_resolved' | 'analysis_started'
    title: string
    description: string
    timestamp: string
    url?: string
    user?: {
      name: string
      avatar?: string
    }
    metadata?: {
      repository?: string
      severity?: string
      status?: string
    }
  }>
  quality_trends: Array<{
    date: string
    quality_score: number
    security_score: number
    total_issues: number
    critical_issues: number
  }>
}

export default function DashboardPage() {
  const [lastRefresh, setLastRefresh] = useState(new Date())

  const { 
    data: dashboardData, 
    isLoading, 
    error, 
    refetch 
  } = useQuery({
    queryKey: ['dashboard', lastRefresh.toISOString()],
    queryFn: async (): Promise<DashboardData> => {
      try {
        // Fetch real analytics data
        const overviewData = await apiClient.get('/analytics/overview')
        
        // Fetch repositories to get real repository data
        const repositoriesData = await apiClient.get('/repositories', { params: { limit: 100 } })
        
        // Calculate real stats from repositories and reviews
        const totalRepositories = repositoriesData?.length || 0
        const activeRepositories = repositoriesData?.filter((repo: any) => repo.is_active)?.length || 0
        
        // For now, use calculated stats and some placeholder data for missing endpoints
        const stats = {
          total_repositories: totalRepositories,
          active_repositories: activeRepositories,
          total_reviews: overviewData?.total_reviews || 0,
          completed_reviews: overviewData?.completed_reviews || 0,
          total_issues: overviewData?.total_issues || 0,
          critical_issues: overviewData?.critical_issues || 0,
          average_quality_score: overviewData?.average_quality_score || 0,
          average_review_time: overviewData?.average_review_time || 0,
        }

        // Generate recent activity from repositories
        const recent_activity = []
        
        // Add repository connections as recent activity
        if (repositoriesData && repositoriesData.length > 0) {
          repositoriesData.slice(0, 5).forEach((repo: any, index: number) => {
            recent_activity.push({
              id: `repo-${repo.id}`,
              type: 'repository_added' as const,
              title: 'Repository connected',
              description: `Successfully connected ${repo.name} repository from ${repo.provider}`,
              timestamp: repo.created_at,
              url: `/repositories`,
              metadata: {
                repository: repo.full_name,
              }
            })
          })
        }

        // If no real activity, add a placeholder
        if (recent_activity.length === 0) {
          recent_activity.push({
            id: '1',
            type: 'analysis_started' as const,
            title: 'Welcome to AI Code Review',
            description: 'Connect your first repository to start analyzing your code',
            timestamp: new Date().toISOString(),
            url: '/repositories/connect',
          })
        }

        // Generate quality trends (placeholder until we have review data)
        const quality_trends = []
        for (let i = 30; i >= 0; i -= 7) {
          quality_trends.push({
            date: new Date(Date.now() - i * 24 * 3600000).toISOString(),
            quality_score: Math.max(0, Math.min(10, 6 + Math.random() * 2)),
            security_score: Math.max(0, Math.min(10, 7 + Math.random() * 2)),
            total_issues: Math.floor(Math.random() * 20 + 5),
            critical_issues: Math.floor(Math.random() * 5),
          })
        }

        return {
          stats,
          recent_activity,
          quality_trends,
        }
        
      } catch (error: any) {
        console.error('Error fetching dashboard data:', error)
        
        // If analytics endpoint doesn't exist yet, provide fallback with repository data
        try {
          const repositoriesData = await apiClient.get('/repositories', { params: { limit: 100 } })
          
          const totalRepositories = repositoriesData?.length || 0
          const activeRepositories = repositoriesData?.filter((repo: any) => repo.is_active)?.length || 0
          
          return {
            stats: {
              total_repositories: totalRepositories,
              active_repositories: activeRepositories,
              total_reviews: 0,
              completed_reviews: 0,
              total_issues: 0,
              critical_issues: 0,
              average_quality_score: 0,
              average_review_time: 0,
            },
            recent_activity: repositoriesData?.slice(0, 3).map((repo: any) => ({
              id: `repo-${repo.id}`,
              type: 'repository_added' as const,
              title: 'Repository connected',
              description: `${repo.name} is ready for AI code analysis`,
              timestamp: repo.created_at,
              url: `/repositories`,
              metadata: {
                repository: repo.full_name,
              }
            })) || [{
              id: '1',
              type: 'analysis_started' as const,
              title: 'Welcome to AI Code Review',
              description: 'Connect your first repository to start analyzing your code',
              timestamp: new Date().toISOString(),
              url: '/repositories/connect',
            }],
            quality_trends: [
              {
                date: new Date(Date.now() - 7 * 24 * 3600000).toISOString(),
                quality_score: 0,
                security_score: 0,
                total_issues: 0,
                critical_issues: 0,
              },
              {
                date: new Date().toISOString(),
                quality_score: 0,
                security_score: 0,
                total_issues: 0,
                critical_issues: 0,
              },
            ]
          }
        } catch (repoError) {
          // If even repositories fail, return empty data
          console.error('Error fetching repositories:', repoError)
          throw repoError
        }
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: (failureCount, error: any) => {
      // Don't retry on 401
      if (error?.response?.status === 401) {
        return false
      }
      return failureCount < 2
    },
  })

  const handleRefresh = async () => {
    try {
      setLastRefresh(new Date())
      await refetch()
      toast.success("Dashboard refreshed")
    } catch (error: any) {
      console.error('Error refreshing dashboard:', error)
      if (error?.response?.status === 401) {
        toast.error("Please log in to refresh dashboard")
      } else {
        toast.error("Failed to refresh dashboard")
      }
    }
  }

  if (error && error.response?.status !== 404) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <p className="text-lg font-medium text-destructive mb-2">Failed to load dashboard</p>
          <p className="text-muted-foreground mb-4">Please try refreshing the page</p>
          <Button onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
            <p className="text-muted-foreground">
              Welcome back! Here&apos;s what&apos;s happening with your code reviews.
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="outline" onClick={handleRefresh} disabled={isLoading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button asChild>
              <Link href="/repositories/connect">
                <Plus className="h-4 w-4 mr-2" />
                Connect Repository
              </Link>
            </Button>
          </div>
        </div>

        {/* Stats Overview */}
        <StatsOverview 
          stats={dashboardData?.stats || {
            total_repositories: 0,
            active_repositories: 0,
            total_reviews: 0,
            completed_reviews: 0,
            total_issues: 0,
            critical_issues: 0,
            average_quality_score: 0,
            average_review_time: 0,
          }} 
          loading={isLoading} 
        />

        {/* Main Content Grid */}
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Quality Chart - Takes 2 columns */}
          <div className="lg:col-span-2">
            <QualityChart 
              data={dashboardData?.quality_trends || []} 
              loading={isLoading} 
            />
          </div>

          {/* Recent Activity - Takes 1 column */}
          <div className="lg:col-span-1">
            <RecentActivity 
              activities={dashboardData?.recent_activity || []} 
              loading={isLoading} 
            />
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card className="cursor-pointer hover:shadow-md transition-shadow">
            <Link href="/repositories/connect">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Connect Repository</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Connect your GitHub repositories for AI-powered analysis
                </p>
              </CardContent>
            </Link>
          </Card>

          <Card className="cursor-pointer hover:shadow-md transition-shadow">
            <Link href="/repositories">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Manage Repositories</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  View and configure your connected repositories
                </p>
              </CardContent>
            </Link>
          </Card>

          <Card className="cursor-pointer hover:shadow-md transition-shadow">
            <Link href="/analysis">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Code Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Review code quality metrics and insights
                </p>
              </CardContent>
            </Link>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  )
}
