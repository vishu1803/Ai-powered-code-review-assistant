"use client"

import { useState } from "react"
import Link from "next/link"
import { MoreHorizontal, ExternalLink, Settings, Play, Trash2, Eye } from "lucide-react"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { formatRelativeTime, formatDate } from "@/lib/utils"
import { Repository } from "@/lib/types/api"
import { repositoriesApi } from "@/lib/api/repositories"
import { toast } from "sonner"

interface RepositoryTableProps {
  repositories: Repository[]
  onUpdate?: (repository: Repository) => void
  onDelete?: (repositoryId: number) => void
}

export default function RepositoryTable({ repositories, onUpdate, onDelete }: RepositoryTableProps) {
  const [loadingStates, setLoadingStates] = useState<Record<number, boolean>>({})

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

  const getLanguageColor = (language?: string) => {
    if (!language) return 'bg-gray-500'
    
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

  const handleTriggerAnalysis = async (repository: Repository) => {
    setLoadingStates(prev => ({ ...prev, [repository.id]: true }))
    try {
      await repositoriesApi.triggerAnalysis(repository.id)
      toast.success(`Analysis started for ${repository.name}`)
    } catch (error) {
      toast.error("Failed to start analysis")
    } finally {
      setLoadingStates(prev => ({ ...prev, [repository.id]: false }))
    }
  }

  const handleDelete = async (repository: Repository) => {
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
    <div className="border rounded-lg">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12"></TableHead>
            <TableHead>Repository</TableHead>
            <TableHead>Language</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Last Analysis</TableHead>
            <TableHead>Reviews</TableHead>
            <TableHead>Issues</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {repositories.map((repository) => (
            <TableRow key={repository.id}>
              <TableCell>
                <Avatar className="h-8 w-8">
                  <AvatarFallback className="text-xs">
                    {getProviderIcon(repository.provider)}
                  </AvatarFallback>
                </Avatar>
              </TableCell>
              
              <TableCell>
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <Link
                      href={`/repositories/${repository.id}`}
                      className="font-medium hover:text-primary transition-colors"
                    >
                      {repository.name}
                    </Link>
                    {repository.is_private && (
                      <Badge variant="secondary" className="text-xs">Private</Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">{repository.full_name}</p>
                  {repository.description && (
                    <p className="text-xs text-muted-foreground line-clamp-1">
                      {repository.description}
                    </p>
                  )}
                </div>
              </TableCell>

              <TableCell>
                {repository.language && (
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${getLanguageColor(repository.language)}`} />
                    <span className="text-sm">{repository.language}</span>
                  </div>
                )}
              </TableCell>

              <TableCell>
                <div className="space-y-1">
                  <Badge 
                    variant={repository.is_active ? "default" : "secondary"}
                    className="text-xs"
                  >
                    {repository.is_active ? "Active" : "Inactive"}
                  </Badge>
                  {repository.is_archived && (
                    <Badge variant="outline" className="text-xs">Archived</Badge>
                  )}
                </div>
              </TableCell>

              <TableCell>
                <div className="text-sm">
                  {repository.last_analysis ? (
                    <>
                      <div>{formatRelativeTime(repository.last_analysis)}</div>
                      <div className="text-xs text-muted-foreground">
                        {formatDate(repository.last_analysis)}
                      </div>
                    </>
                  ) : (
                    <span className="text-muted-foreground">Never</span>
                  )}
                </div>
              </TableCell>

              <TableCell>
                <div className="text-sm">
                  <div className="font-medium">{repository.total_reviews}</div>
                  <div className="text-xs text-muted-foreground">
                    {repository.avg_review_time}m avg
                  </div>
                </div>
              </TableCell>

              <TableCell>
                <div className="text-sm">
                  <div className="font-medium">{repository.total_issues}</div>
                  <div className="text-xs text-muted-foreground">total found</div>
                </div>
              </TableCell>

              <TableCell className="text-right">
                <div className="flex items-center justify-end space-x-2">
                  <Button variant="ghost" size="sm" asChild>
                    <Link href={`/repositories/${repository.id}`}>
                      <Eye className="h-4 w-4" />
                    </Link>
                  </Button>
                  
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem asChild>
                        <Link href={repository.url} target="_blank">
                          <ExternalLink className="h-4 w-4 mr-2" />
                          View on {repository.provider}
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => handleTriggerAnalysis(repository)}
                        disabled={loadingStates[repository.id]}
                      >
                        <Play className="h-4 w-4 mr-2" />
                        {loadingStates[repository.id] ? "Starting..." : "Run Analysis"}
                      </DropdownMenuItem>
                      <DropdownMenuItem asChild>
                        <Link href={`/repositories/${repository.id}/settings`}>
                          <Settings className="h-4 w-4 mr-2" />
                          Settings
                        </Link>
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem 
                        onClick={() => handleDelete(repository)}
                        className="text-destructive"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Disconnect
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
