"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Plus, Search, Filter, Calendar, MoreHorizontal, Eye, Play, ArrowLeft, Home, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import DashboardLayout from "@/components/layout/dashboard-layout"
import { ReviewSummary } from "@/lib/types/api"
import { formatDateTime, formatRelativeTime } from "@/lib/utils"
import { cn } from "@/lib/utils"
import apiClient from "@/lib/api/client"
import { toast } from "sonner"
import { useDebounce } from "@/lib/hooks/use-debounce"

export default function ReviewsPage() {
  const router = useRouter()
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [sortBy, setSortBy] = useState<string>('created_at')
  
  const debouncedSearch = useDebounce(searchQuery, 300)

  const { 
    data: reviews = [], 
    isLoading, 
    error, 
    refetch 
  } = useQuery({
    queryKey: ['reviews', debouncedSearch, statusFilter, sortBy],
    queryFn: async (): Promise<ReviewSummary[]> => {
      try {
        const params: any = {
          search: debouncedSearch || undefined,
          status: statusFilter !== 'all' ? statusFilter : undefined,
          sort_by: sortBy,
          limit: 100,
        }

        // Remove undefined values
        Object.keys(params).forEach(key => {
          if (params[key] === undefined) {
            delete params[key]
          }
        })

        const data = await apiClient.get<ReviewSummary[]>('/reviews', { params })
        return data || []
      } catch (error: any) {
        console.error('Error fetching reviews:', error)
        
        if (error.response?.status === 404) {
          // No reviews found - return empty array
          return []
        } else if (error.response?.status === 401) {
          toast.error('Please log in to view reviews')
          return []
        }
        
        throw error
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: (failureCount, error: any) => {
      // Don't retry on 401 or 404
      if (error?.response?.status === 401 || error?.response?.status === 404) {
        return false
      }
      return failureCount < 2
    },
  })

  const handleRefresh = async () => {
    try {
      await refetch()
      toast.success("Reviews refreshed")
    } catch (error: any) {
      console.error('Error refreshing reviews:', error)
      if (error?.response?.status === 401) {
        toast.error("Please log in to refresh reviews")
      } else {
        toast.error("Failed to refresh reviews")
      }
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
        return 'bg-gray-100 text-gray-700 dark:bg-gray-900 dark:text-gray-300'
    }
  }

  const getQualityScoreColor = (score?: number) => {
    if (!score) return 'text-muted-foreground'
    if (score >= 8) return 'text-green-600'
    if (score >= 6) return 'text-yellow-600'
    return 'text-red-600'
  }

  // Filter and sort reviews locally if needed
  const filteredReviews = reviews.filter(review => {
    if (statusFilter !== 'all' && review.status !== statusFilter) return false
    if (searchQuery && !review.title.toLowerCase().includes(searchQuery.toLowerCase())) return false
    return true
  })

  if (error && error.response?.status !== 404) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <p className="text-lg font-medium text-destructive mb-2">Failed to load reviews</p>
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
      <div className="space-y-6">
        {/* Header with Back Button */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button variant="ghost" onClick={() => router.push('/dashboard')}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Code Reviews</h1>
              <p className="text-muted-foreground">
                Track and manage your AI-powered code reviews
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="outline" onClick={() => router.push('/dashboard')}>
              <Home className="mr-2 h-4 w-4" />
              Dashboard
            </Button>
            <Button variant="outline" onClick={handleRefresh} disabled={isLoading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button asChild>
              <Link href="/analysis">
                <Plus className="h-4 w-4 mr-2" />
                Start Analysis
              </Link>
            </Button>
          </div>
        </div>

        {/* Filters */}
        <Card>
          <CardContent className="p-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div className="flex flex-1 items-center space-x-4">
                <div className="relative flex-1 max-w-sm">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search reviews..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>

                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-40">
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

                <Select value={sortBy} onValueChange={setSortBy}>
                  <SelectTrigger className="w-40">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="created_at">Date Created</SelectItem>
                    <SelectItem value="completed_at">Date Completed</SelectItem>
                    <SelectItem value="quality_score">Quality Score</SelectItem>
                    <SelectItem value="issues">Issues Found</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Reviews Table */}
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Review</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Issues</TableHead>
                <TableHead>Quality Score</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell>
                      <div className="space-y-2">
                        <div className="h-4 w-48 bg-muted animate-pulse rounded" />
                        <div className="h-3 w-32 bg-muted animate-pulse rounded" />
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="h-5 w-20 bg-muted animate-pulse rounded" />
                    </TableCell>
                    <TableCell>
                      <div className="h-4 w-16 bg-muted animate-pulse rounded" />
                    </TableCell>
                    <TableCell>
                      <div className="h-4 w-12 bg-muted animate-pulse rounded" />
                    </TableCell>
                    <TableCell>
                      <div className="h-4 w-24 bg-muted animate-pulse rounded" />
                    </TableCell>
                    <TableCell>
                      <div className="h-8 w-8 bg-muted animate-pulse rounded" />
                    </TableCell>
                  </TableRow>
                ))
              ) : filteredReviews.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-12">
                    <div className="space-y-2">
                      <p className="text-lg font-medium">No reviews found</p>
                      <p className="text-muted-foreground">
                        {reviews.length === 0 
                          ? "Start analyzing your repositories to see reviews here" 
                          : searchQuery || statusFilter !== 'all' 
                            ? "No reviews match your current filters"
                            : "Create your first code review to get started"
                        }
                      </p>
                      <div className="flex justify-center space-x-2 mt-4">
                        {searchQuery || statusFilter !== 'all' ? (
                          <Button 
                            variant="outline" 
                            onClick={() => {
                              setSearchQuery('')
                              setStatusFilter('all')
                            }}
                          >
                            Clear Filters
                          </Button>
                        ) : null}
                        <Button asChild>
                          <Link href="/analysis">
                            <Plus className="h-4 w-4 mr-2" />
                            Start Analysis
                          </Link>
                        </Button>
                      </div>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                filteredReviews.map((review) => (
                  <TableRow key={review.id}>
                    <TableCell>
                      <div className="space-y-1">
                        <Link
                          href={`/reviews/${review.id}`}
                          className="font-medium hover:text-primary transition-colors"
                        >
                          {review.title}
                        </Link>
                        <div className="text-sm text-muted-foreground">
                          Repository ID: {review.repository_id}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={getStatusColor(review.status)}>
                        {review.status.replace('_', ' ')}
                      </Badge>
                      {review.status === 'in_progress' && (
                        <div className="mt-1 text-xs text-muted-foreground">
                          {Math.round(review.progress * 100)}% complete
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <span className="font-medium">{review.total_issues}</span>
                        {review.critical_issues > 0 && (
                          <Badge variant="destructive" className="text-xs">
                            {review.critical_issues} critical
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className={cn("font-medium", getQualityScoreColor(review.code_quality_score))}>
                        {review.code_quality_score ? `${review.code_quality_score.toFixed(1)}/10` : 'N/A'}
                      </span>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="text-sm">{formatRelativeTime(review.created_at)}</div>
                        <div className="text-xs text-muted-foreground">
                          {formatDateTime(review.created_at).split(',')[0]}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <Button size="sm" variant="ghost" asChild>
                          <Link href={`/reviews/${review.id}`}>
                            <Eye className="h-4 w-4" />
                          </Link>
                        </Button>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button size="sm" variant="ghost">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem asChild>
                              <Link href={`/reviews/${review.id}`}>
                                <Eye className="h-4 w-4 mr-2" />
                                View Details  
                              </Link>
                            </DropdownMenuItem>
                            {review.status === 'pending' && (
                              <DropdownMenuItem>
                                <Play className="h-4 w-4 mr-2" />
                                Start Analysis
                              </DropdownMenuItem>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </Card>
      </div>
    </DashboardLayout>
  )
}
