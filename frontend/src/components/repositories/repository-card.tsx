"use client"

import { useState } from "react"
import Link from "next/link"
import { MoreHorizontal, GitBranch, Clock, AlertTriangle, Settings, Play, Trash2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { formatRelativeTime, formatDate } from "@/lib/utils"
import { Repository } from "@/lib/types/api"
import { repositoriesApi } from "@/lib/api/repositories"
import { toast } from "sonner"

interface RepositoryCardProps {
  repository: Repository & {
    stats?: {
      total_reviews: number
      completed_reviews: number
      average_quality_score?: number
      last_review_date?: string
    }
  }
  onUpdate?: (repository: Repository) => void
  onDelete?: (repositoryId: number) => void
}

export default function RepositoryCard({ repository, onUpdate, onDelete }: RepositoryCardProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  const getProviderIcon = (provider: string) => {
    switch (provider) {
      case 'github':
        return '🐙'
      case 'gitlab':
        return '🦊'
      case 'bitbucket':
        return '🪣'
      default:
        return '📁'
    }
  }

  const getLanguageColor = (language: string) => {
    const colors: Record<string, string> = {
      'TypeScript': 'bg-blue-500',
      'JavaScript': 'bg-yellow-500',
      'Python': 'bg-green-500',
      'Java': 'bg-orange-500',
      'Go': 'bg-cyan-500',
      'Rust': 'bg-orange-600',
      'C++': 'bg-pink-500',
      'C#': 'bg-purple-500',
    }
    return colors[language] || 'bg-gray-500'
  }

  const getQualityScoreColor = (score?: number) => {
    if (!score) return 'text-muted-foreground'
    if (score >= 8) return 'text-green-600'
    if (score >= 6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const completionRate = repository.stats ? 
    (repository.stats.completed_reviews / Math.max(repository.stats.total_reviews, 1)) * 100 : 0

  const handleTriggerAnalysis = async () => {
    setIsAnalyzing(true)
    try {
      await repositoriesApi.triggerAnalysis(repository.id)
      toast.success("Analysis started for " + repository.name)
    } catch (error) {
      toast.error("Failed to start analysis")
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleDelete = async () => {
    if (window.confirm(`Are you sure you want to disconnect ${repository.name}?`)) {
      try {
        await repositoriesApi.deleteRepository(repository.id)
        toast.success("Repository disconnected")
        onDelete?.(repository.id)
      } catch (error) {
        toast.error("Failed to disconnect repository")
      }
    }
  }

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">{getProviderIcon(repository.provider)}</span>
            <div>
              <CardTitle className="text-lg">
                <Link 
                  href={`/repositories/${repository.id}`}
                  className="hover:text-primary transition-colors"
                >
                  {repository.name}
                </Link>
              </CardTitle>
              <p className="text-sm text-muted-foreground">{repository.full_name}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {!repository.is_active && (
              <Badge variant="secondary">Inactive</Badge>
            )}
            {repository.is_private && (
              <Badge variant="outline">Private</Badge>
            )}
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={handleTriggerAnalysis} disabled={isAnalyzing}>
                  <Play className="h-4 w-4 mr-2" />
                  {isAnalyzing ? "Analyzing..." : "Run Analysis"}
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link href={`/repositories/${repository.id}/settings`}>
                    <Settings className="h-4 w-4 mr-2" />
                    Settings
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleDelete} className="text-destructive">
                  <Trash2 className="h-4 w-4 mr-2" />
                  Disconnect
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {repository.description && (
          <p className="text-sm text-muted-foreground mt-2">
            {repository.description}
          </p>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Repository Info */}
        <div className="flex items-center space-x-4 text-sm">
          {repository.language && (
            <div className="flex items-center space-x-1">
              <div className={`w-3 h-3 rounded-full ${getLanguageColor(repository.language)}`} />
              <span>{repository.language}</span>
            </div>
          )}
          
          <div className="flex items-center space-x-1 text-muted-foreground">
            <GitBranch className="h-3 w-3" />
            <span>{repository.default_branch}</span>
          </div>
          
          {repository.last_analysis && (
            <div className="flex items-center space-x-1 text-muted-foreground">
              <Clock className="h-3 w-3" />
              <span>{formatRelativeTime(repository.last_analysis)}</span>
            </div>
          )}
        </div>

        {/* Stats */}
        {repository.stats && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Review Progress</span>
              <span className="font-medium">{repository.stats.completed_reviews}/{repository.stats.total_reviews}</span>
            </div>
            <Progress value={completionRate} className="h-2" />
            
            <div className="flex items-center justify-between">
              <div className="text-sm">
                <span className="text-muted-foreground">Quality Score: </span>
                <span className={`font-medium ${getQualityScoreColor(repository.stats.average_quality_score)}`}>
                  {repository.stats.average_quality_score ? 
                    `${repository.stats.average_quality_score.toFixed(1)}/10` : 
                    'N/A'
                  }
                </span>
              </div>
              
              {repository.stats.last_review_date && (
                <div className="text-sm text-muted-foreground">
                  Last review: {formatDate(repository.stats.last_review_date)}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-2">
          <Button variant="outline" size="sm" asChild>
            <Link href={`/repositories/${repository.id}`}>
              View Details
            </Link>
          </Button>
          
          <Button size="sm" asChild>
            <Link href={`/reviews/new?repository=${repository.id}`}>
              New Review
            </Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
