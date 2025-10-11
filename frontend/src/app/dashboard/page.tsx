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
import { dashboardApi } from "@/lib/api/repositories"
import { toast } from "sonner"
import Link from "next/link"

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
      // In a real implementation, this would be a single API call
      // For now, we'll simulate the data structure
      return {
        stats: {
          total_repositories: 12,
          active_repositories: 10,
          total_reviews: 45,
          completed_reviews: 38,
          total_issues: 127,
          critical_issues: 8,
          average_quality_score: 7.8,
          average_review_time: 24,
        },
        recent_activity: [
          {
            id: '1',
            type: 'review_completed',
            title: 'Code review completed',
            description: 'Review for feature/user-authentication branch completed with 3 issues found',
            timestamp: new Date(Date.now() - 30 * 60000).toISOString(),
            url: '/reviews/123',
            user: {
              name: 'John Doe',
              avatar: undefined,
            },
            metadata: {
              repository: 'my-app/frontend',
              status: 'completed',
            }
          },
          {
            id: '2',
            type: 'repository_added',
            title: 'New repository connected',
            description: 'Successfully connected backend-api repository from GitHub',
            timestamp: new Date(Date.now() - 2 * 3600000).toISOString(),
            url: '/repositories/456',
            user: {
              name: 'John Doe',
              avatar: undefined,
            },
            metadata: {
              repository: 'my-app/backend-api',
            }
          },
          {
            id: '3',
            type: 'issue_resolved',
            title: 'Critical security issue resolved',
            description: 'SQL injection vulnerability in user login function has been fixed',
            timestamp: new Date(Date.now() - 4 * 3600000).toISOString(),
            url: '/reviews/124/issues/789',
            user: {
              name: 'John Doe',
              avatar: undefined,
            },
            metadata: {
              repository: 'my-app/backend-api',
              severity: 'critical',
            }
          },
        ],
        quality_trends: [
          {
            date: new Date(Date.now() - 30 * 24 * 3600000).toISOString(),
            quality_score: 6.5,
            security_score: 7.2,
            total_issues: 45,
            critical_issues: 12,
          },
          {
            date: new Date(Date.now() - 20 * 24 * 3600000).toISOString(),
            quality_score: 7.1,
            security_score: 7.8,
            total_issues: 38,
            critical_issues: 9,
          },
          {
            date: new Date(Date.now() - 10 * 24 * 3600000).toISOString(),
            quality_score: 7.6,
            security_score: 8.2,
            total_issues: 32,
            critical_issues: 6,
          },
          {
            date: new Date().toISOString(),
            quality_score: 7.8,
            security_score: 8.5,
            total_issues: 27,
            critical_issues: 3,
          },
        ]
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  const handleRefresh = async () => {
    try {
      setLastRefresh(new Date())
      await refetch()
      toast.success("Dashboard refreshed")
    } catch (error) {
      toast.error("Failed to refresh dashboard")
    }
  }

  if (error) {
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
            <Link href="/reviews/new">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Start New Review</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Analyze code changes with AI-powered review tools
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
                  Connect and configure your code repositories
                </p>
              </CardContent>
            </Link>
          </Card>

          <Card className="cursor-pointer hover:shadow-md transition-shadow">
            <Link href="/analytics">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">View Analytics</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Insights and trends from your code quality metrics
                </p>
              </CardContent>
            </Link>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  )
}
