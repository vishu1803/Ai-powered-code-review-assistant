"use client"

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { formatRelativeTime, getInitials } from "@/lib/utils"
import { 
  CheckCircle2, 
  AlertTriangle, 
  GitBranch, 
  FileText,
  ExternalLink,
  Clock
} from "lucide-react"
import Link from "next/link"

interface Activity {
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
}

interface RecentActivityProps {
  activities: Activity[]
  loading?: boolean
}

export default function RecentActivity({ activities, loading = false }: RecentActivityProps) {
  const getActivityIcon = (type: Activity['type']) => {
    switch (type) {
      case 'review_completed':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />
      case 'repository_added':
        return <GitBranch className="h-4 w-4 text-blue-500" />
      case 'issue_resolved':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      case 'analysis_started':
        return <FileText className="h-4 w-4 text-purple-500" />
      default:
        return <Clock className="h-4 w-4 text-muted-foreground" />
    }
  }

  const getActivityBadge = (type: Activity['type'], metadata?: Activity['metadata']) => {
    switch (type) {
      case 'review_completed':
        return <Badge variant="outline" className="text-green-600">Completed</Badge>
      case 'repository_added':
        return <Badge variant="outline" className="text-blue-600">New Repo</Badge>
      case 'issue_resolved':
        return (
          <Badge 
            variant="outline" 
            className={
              metadata?.severity === 'critical' ? 'text-red-600' :
              metadata?.severity === 'high' ? 'text-orange-600' :
              'text-yellow-600'
            }
          >
            {metadata?.severity || 'Issue'} Fixed
          </Badge>
        )
      case 'analysis_started':
        return <Badge variant="outline" className="text-purple-600">Analyzing</Badge>
      default:
        return null
    }
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Clock className="h-5 w-5" />
            <span>Recent Activity</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-start space-x-4">
              <div className="h-10 w-10 bg-muted animate-pulse rounded-full" />
              <div className="flex-1 space-y-2">
                <div className="h-4 w-3/4 bg-muted animate-pulse rounded" />
                <div className="h-3 w-1/2 bg-muted animate-pulse rounded" />
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Clock className="h-5 w-5" />
            <span>Recent Activity</span>
          </div>
          <Button variant="ghost" size="sm" asChild>
            <Link href="/activity">View All</Link>
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {activities.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No recent activity</p>
            <p className="text-sm">Start by connecting a repository or running a code review</p>
          </div>
        ) : (
          <div className="space-y-4">
            {activities.map((activity) => (
              <div key={activity.id} className="flex items-start space-x-4 p-3 rounded-lg hover:bg-muted/50 transition-colors">
                <div className="flex-shrink-0 mt-1">
                  {getActivityIcon(activity.type)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="text-sm font-medium">{activity.title}</p>
                      <p className="text-sm text-muted-foreground mt-1">{activity.description}</p>
                      
                      {activity.metadata?.repository && (
                        <p className="text-xs text-muted-foreground mt-1">
                          in <span className="font-medium">{activity.metadata.repository}</span>
                        </p>
                      )}
                    </div>
                    
                    <div className="flex items-center space-x-2 ml-4">
                      {getActivityBadge(activity.type, activity.metadata)}
                      {activity.url && (
                        <Button variant="ghost" size="sm" asChild>
                          <Link href={activity.url}>
                            <ExternalLink className="h-3 w-3" />
                          </Link>
                        </Button>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between mt-2">
                    <div className="flex items-center space-x-2">
                      {activity.user && (
                        <>
                          <Avatar className="h-5 w-5">
                            <AvatarImage src={activity.user.avatar} />
                            <AvatarFallback className="text-xs">
                              {getInitials(activity.user.name)}
                            </AvatarFallback>
                          </Avatar>
                          <span className="text-xs text-muted-foreground">
                            {activity.user.name}
                          </span>
                        </>
                      )}
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {formatRelativeTime(activity.timestamp)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
