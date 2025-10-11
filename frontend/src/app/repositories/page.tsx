"use client"

import { useState, useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import { Plus, Search, Filter, Grid3X3, List, RefreshCw } from "lucide-react"
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import DashboardLayout from "@/components/layout/dashboard-layout"
import RepositoryCard from "@/components/repositories/repository-card"
import RepositoryTable from "@/components/repositories/repository-table"
import { useRepositoryStore } from "@/lib/store/repository-store"
import { repositoriesApi } from "@/lib/api/repositories"
import { Repository } from "@/lib/types/api"
import { toast } from "sonner"
import Link from "next/link"
import { useDebounce } from "@/lib/hooks/use-debounce"

type ViewMode = 'grid' | 'list'
type SortOption = 'name' | 'created_at' | 'last_analysis' | 'quality_score'

export default function RepositoriesPage() {
  const { repositories, setRepositories, removeRepository, setLoading } = useRepositoryStore()
  
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedProvider, setSelectedProvider] = useState<string>('all')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')
  const [sortBy, setSortBy] = useState<SortOption>('name')
  
  const debouncedSearch = useDebounce(searchQuery, 300)

  const { 
    data: repositoriesData, 
    isLoading, 
    error, 
    refetch 
  } = useQuery({
    queryKey: ['repositories', debouncedSearch, selectedProvider, selectedStatus, sortBy],
    queryFn: async () => {
      const params: any = {
        search: debouncedSearch || undefined,
        provider: selectedProvider !== 'all' ? selectedProvider : undefined,
        is_active: selectedStatus === 'active' ? true : selectedStatus === 'inactive' ? false : undefined,
        limit: 100,
      }

      // Simulate repository data since we don't have real API yet
      const mockRepositories: Repository[] = [
        {
          id: 1,
          name: 'frontend-app',
          full_name: 'my-org/frontend-app',
          description: 'React-based frontend application with TypeScript',
          url: 'https://github.com/my-org/frontend-app',
          clone_url: 'https://github.com/my-org/frontend-app.git',
          default_branch: 'main',
          language: 'TypeScript',
          size: 1024,
          is_private: false,
          is_active: true,
          is_archived: false,
          provider: 'github',
          external_id: '12345',
          webhook_id: 'wh_123',
          analysis_enabled: true,
          auto_review: true,
          review_rules: {},
          notification_settings: {},
          total_reviews: 15,
          total_issues: 42,
          avg_review_time: 25,
          created_at: '2024-01-15T10:00:00Z',
          updated_at: '2024-10-10T15:30:00Z',
          last_analysis: '2024-10-10T14:20:00Z',
          owner_id: 1,
        },
        {
          id: 2,
          name: 'backend-api',
          full_name: 'my-org/backend-api',
          description: 'FastAPI backend with PostgreSQL database',
          url: 'https://github.com/my-org/backend-api',
          clone_url: 'https://github.com/my-org/backend-api.git',
          default_branch: 'develop',
          language: 'Python',
          size: 2048,
          is_private: true,
          is_active: true,
          is_archived: false,
          provider: 'github',
          external_id: '12346',
          webhook_id: 'wh_124',
          analysis_enabled: true,
          auto_review: false,
          review_rules: {},
          notification_settings: {},
          total_reviews: 28,
          total_issues: 18,
          avg_review_time: 32,
          created_at: '2024-02-01T09:15:00Z',
          updated_at: '2024-10-11T08:45:00Z',
          last_analysis: '2024-10-11T07:30:00Z',
          owner_id: 1,
        },
        {
          id: 3,
          name: 'mobile-client',
          full_name: 'my-org/mobile-client',
          description: 'React Native mobile application',
          url: 'https://gitlab.com/my-org/mobile-client',
          clone_url: 'https://gitlab.com/my-org/mobile-client.git',
          default_branch: 'main',
          language: 'JavaScript',
          size: 512,
          is_private: false,
          is_active: false,
          is_archived: true,
          provider: 'gitlab',
          external_id: '54321',
          analysis_enabled: false,
          auto_review: true,
          review_rules: {},
          notification_settings: {},
          total_reviews: 8,
          total_issues: 23,
          avg_review_time: 18,
          created_at: '2024-03-20T14:30:00Z',
          updated_at: '2024-09-15T11:20:00Z',
          last_analysis: '2024-09-10T16:45:00Z',
          owner_id: 1,
        }
      ]

      // Filter based on search and filters
      let filtered = mockRepositories

      if (debouncedSearch) {
        const query = debouncedSearch.toLowerCase()
        filtered = filtered.filter(repo => 
          repo.name.toLowerCase().includes(query) ||
          repo.description?.toLowerCase().includes(query) ||
          repo.language?.toLowerCase().includes(query)
        )
      }

      if (selectedProvider !== 'all') {
        filtered = filtered.filter(repo => repo.provider === selectedProvider)
      }

      if (selectedStatus === 'active') {
        filtered = filtered.filter(repo => repo.is_active)
      } else if (selectedStatus === 'inactive') {
        filtered = filtered.filter(repo => !repo.is_active)
      }

      // Sort
      filtered.sort((a, b) => {
        switch (sortBy) {
          case 'name':
            return a.name.localeCompare(b.name)
          case 'created_at':
            return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          case 'last_analysis':
            if (!a.last_analysis && !b.last_analysis) return 0
            if (!a.last_analysis) return 1
            if (!b.last_analysis) return -1
            return new Date(b.last_analysis).getTime() - new Date(a.last_analysis).getTime()
          default:
            return 0
        }
      })

      return filtered
    },
    staleTime: 5 * 60 * 1000,
  })

  useEffect(() => {
    if (repositoriesData) {
      setRepositories(repositoriesData)
    }
  }, [repositoriesData, setRepositories])

  useEffect(() => {
    setLoading(isLoading)
  }, [isLoading, setLoading])

  const handleRefresh = async () => {
    try {
      await refetch()
      toast.success("Repositories refreshed")
    } catch (error) {
      toast.error("Failed to refresh repositories")
    }
  }

  const handleRepositoryUpdate = (updatedRepo: Repository) => {
    const updatedRepos = repositories.map(repo => 
      repo.id === updatedRepo.id ? updatedRepo : repo
    )
    setRepositories(updatedRepos)
  }

  const handleRepositoryDelete = (repositoryId: number) => {
    removeRepository(repositoryId)
  }

  const activeCount = repositories.filter(r => r.is_active).length
  const totalCount = repositories.length

  if (error) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <p className="text-lg font-medium text-destructive mb-2">Failed to load repositories</p>
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
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Repositories</h1>
            <p className="text-muted-foreground">
              Manage and monitor your connected code repositories
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

        {/* Stats */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalCount}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Active</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{activeCount}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Inactive</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">{totalCount - activeCount}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Reviews Today</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">12</div>
            </CardContent>
          </Card>
        </div>

        {/* Filters and Search */}
        <Card>
          <CardContent className="p-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div className="flex flex-1 items-center space-x-4">
                {/* Search */}
                <div className="relative flex-1 max-w-sm">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search repositories..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>

                {/* Provider Filter */}
                <Select value={selectedProvider} onValueChange={setSelectedProvider}>
                  <SelectTrigger className="w-40">
                    <SelectValue placeholder="Provider" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Providers</SelectItem>
                    <SelectItem value="github">GitHub</SelectItem>
                    <SelectItem value="gitlab">GitLab</SelectItem>
                    <SelectItem value="bitbucket">Bitbucket</SelectItem>
                  </SelectContent>
                </Select>

                {/* Status Filter */}
                <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                  <SelectTrigger className="w-32">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
                  </SelectContent>
                </Select>

                {/* Sort */}
                <Select value={sortBy} onValueChange={(value: SortOption) => setSortBy(value)}>
                  <SelectTrigger className="w-40">
                    <SelectValue placeholder="Sort by" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="name">Name</SelectItem>
                    <SelectItem value="created_at">Created</SelectItem>
                    <SelectItem value="last_analysis">Last Analysis</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* View Mode Toggle */}
              <div className="flex items-center space-x-1">
                <Button
                  variant={viewMode === 'grid' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('grid')}
                >
                  <Grid3X3 className="h-4 w-4" />
                </Button>
                <Button
                  variant={viewMode === 'list' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('list')}
                >
                  <List className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        {isLoading ? (
          <div className="space-y-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <Card key={i}>
                <CardContent className="p-6">
                  <div className="space-y-3">
                    <div className="h-4 w-1/3 bg-muted animate-pulse rounded" />
                    <div className="h-3 w-2/3 bg-muted animate-pulse rounded" />
                    <div className="h-2 w-full bg-muted animate-pulse rounded" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : repositories.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <div className="space-y-4">
                <div className="mx-auto h-12 w-12 rounded-full bg-muted flex items-center justify-center">
                  <Plus className="h-6 w-6 text-muted-foreground" />
                </div>
                <div>
                  <h3 className="text-lg font-medium">No repositories found</h3>
                  <p className="text-muted-foreground">
                    {searchQuery || selectedProvider !== 'all' || selectedStatus !== 'all'
                      ? "No repositories match your current filters"
                      : "Get started by connecting your first repository"
                    }
                  </p>
                </div>
                <Button asChild>
                  <Link href="/repositories/connect">
                    Connect Repository
                  </Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div>
            {viewMode === 'grid' ? (
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {repositories.map((repository) => (
                  <RepositoryCard
                    key={repository.id}
                    repository={repository}
                    onUpdate={handleRepositoryUpdate}
                    onDelete={handleRepositoryDelete}
                  />
                ))}
              </div>
            ) : (
              <RepositoryTable
                repositories={repositories}
                onUpdate={handleRepositoryUpdate}
                onDelete={handleRepositoryDelete}
              />
            )}
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
