"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { 
  TrendingUp, 
  TrendingDown, 
  GitBranch, 
  FileText, 
  AlertTriangle, 
  Shield,
  BarChart3,
  Clock
} from "lucide-react"
import { cn } from "@/lib/utils"

interface StatsOverviewProps {
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
  loading?: boolean
}

export default function StatsOverview({ stats, loading = false }: StatsOverviewProps) {
  const completionRate = stats.total_reviews > 0 ? (stats.completed_reviews / stats.total_reviews) * 100 : 0
  const criticalIssueRate = stats.total_issues > 0 ? (stats.critical_issues / stats.total_issues) * 100 : 0
  
  const statCards = [
    {
      title: "Total Repositories",
      value: stats.total_repositories,
      subValue: `${stats.active_repositories} active`,
      icon: GitBranch,
      trend: stats.active_repositories > stats.total_repositories * 0.8 ? "up" : "down",
      color: "blue",
    },
    {
      title: "Code Reviews",
      value: stats.total_reviews,
      subValue: `${completionRate.toFixed(1)}% completed`,
      icon: FileText,
      trend: completionRate > 80 ? "up" : "down",
      color: "green",
    },
    {
      title: "Issues Found",
      value: stats.total_issues,
      subValue: `${stats.critical_issues} critical`,
      icon: AlertTriangle,
      trend: criticalIssueRate > 20 ? "down" : "up",
      color: stats.critical_issues > 0 ? "red" : "yellow",
    },
    {
      title: "Quality Score",
      value: `${stats.average_quality_score.toFixed(1)}/10`,
      subValue: stats.average_quality_score > 8 ? "Excellent" : stats.average_quality_score > 6 ? "Good" : "Needs work",
      icon: Shield,
      trend: stats.average_quality_score > 7 ? "up" : "down",
      color: stats.average_quality_score > 7 ? "green" : "yellow",
    },
  ]

  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="h-4 w-20 bg-muted animate-pulse rounded" />
              <div className="h-4 w-4 bg-muted animate-pulse rounded" />
            </CardHeader>
            <CardContent>
              <div className="h-8 w-16 bg-muted animate-pulse rounded mb-2" />
              <div className="h-3 w-24 bg-muted animate-pulse rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {statCards.map((stat, index) => {
        const IconComponent = stat.icon
        const isPositiveTrend = stat.trend === "up"
        
        return (
          <Card key={index}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.title}
              </CardTitle>
              <div className={cn(
                "h-8 w-8 rounded-lg flex items-center justify-center",
                {
                  "bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-300": stat.color === "blue",
                  "bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-300": stat.color === "green",
                  "bg-yellow-100 text-yellow-600 dark:bg-yellow-900 dark:text-yellow-300": stat.color === "yellow",
                  "bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-300": stat.color === "red",
                }
              )}>
                <IconComponent className="h-4 w-4" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                <span>{stat.subValue}</span>
                {isPositiveTrend ? (
                  <TrendingUp className="h-3 w-3 text-green-500" />
                ) : (
                  <TrendingDown className="h-3 w-3 text-red-500" />
                )}
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
