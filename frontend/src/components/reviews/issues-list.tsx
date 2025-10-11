"use client"

import { useState, useMemo } from "react"
import { Search, Filter, CheckCircle, AlertTriangle, Bug, Shield, Zap, Eye, MessageSquare } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
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
import { Issue, IssueSeverity } from "@/lib/types/api"
import { cn } from "@/lib/utils"

interface IssuesListProps {
  issues: Issue[]
  loading?: boolean
  onIssueUpdate?: (issueId: number, updates: { is_resolved?: boolean; is_false_positive?: boolean }) => void
  onIssueSelect?: (issue: Issue | null) => void
  selectedIssue?: Issue | null
}

type FilterState = {
  search: string
  severity: IssueSeverity | 'all'
  category: string
  status: 'all' | 'open' | 'resolved' | 'false_positive'
  sortBy: 'severity' | 'file' | 'line' | 'category'
  sortOrder: 'asc' | 'desc'
}

export default function IssuesList({ 
  issues, 
  loading = false, 
  onIssueUpdate,
  onIssueSelect,
  selectedIssue 
}: IssuesListProps) {
  const [filters, setFilters] = useState<FilterState>({
    search: '',
    severity: 'all',
    category: 'all',
    status: 'all',
    sortBy: 'severity',
    sortOrder: 'desc',
  })

  const [selectedIssues, setSelectedIssues] = useState<Set<number>>(new Set())

  // Get unique categories from issues
  const categories = useMemo(() => {
    const cats = new Set(issues.map(issue => issue.category))
    return Array.from(cats).sort()
  }, [issues])

  // Filter and sort issues
  const filteredIssues = useMemo(() => {
    let filtered = [...issues]

    // Apply search filter
    if (filters.search) {
      const searchTerm = filters.search.toLowerCase()
      filtered = filtered.filter(issue =>
        issue.title.toLowerCase().includes(searchTerm) ||
        issue.description.toLowerCase().includes(searchTerm) ||
        issue.file_path.toLowerCase().includes(searchTerm)
      )
    }

    // Apply severity filter
    if (filters.severity !== 'all') {
      filtered = filtered.filter(issue => issue.severity === filters.severity)
    }

    // Apply category filter
    if (filters.category !== 'all') {
      filtered = filtered.filter(issue => issue.category === filters.category)
    }

    // Apply status filter
    if (filters.status !== 'all') {
      filtered = filtered.filter(issue => {
        switch (filters.status) {
          case 'open':
            return !issue.is_resolved && !issue.is_false_positive
          case 'resolved':
            return issue.is_resolved
          case 'false_positive':
            return issue.is_false_positive
          default:
            return true
        }
      })
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let comparison = 0
      
      switch (filters.sortBy) {
        case 'severity':
          const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 }
          comparison = severityOrder[a.severity] - severityOrder[b.severity]
          break
        case 'file':
          comparison = a.file_path.localeCompare(b.file_path)
          break
        case 'line':
          comparison = a.line_start - b.line_start
          break
        case 'category':
          comparison = a.category.localeCompare(b.category)
          break
      }

      return filters.sortOrder === 'asc' ? comparison : -comparison
    })

    return filtered
  }, [issues, filters])

  const getSeverityIcon = (severity: IssueSeverity) => {
    switch (severity) {
      case 'critical':
        return <AlertTriangle className="h-4 w-4 text-red-500" />
      case 'high':
        return <AlertTriangle className="h-4 w-4 text-orange-500" />
      case 'medium':
        return <Bug className="h-4 w-4 text-yellow-500" />
      case 'low':
        return <Bug className="h-4 w-4 text-blue-500" />
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'security':
        return <Shield className="h-4 w-4 text-red-500" />
      case 'performance':
        return <Zap className="h-4 w-4 text-green-500" />
      default:
        return <Bug className="h-4 w-4 text-muted-foreground" />
    }
  }

  const getSeverityColor = (severity: IssueSeverity) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
      case 'high':
        return 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300'
      case 'medium':
        return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
      case 'low':
        return 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
    }
  }

  const handleIssueToggle = (issueId: number) => {
    const newSelected = new Set(selectedIssues)
    if (newSelected.has(issueId)) {
      newSelected.delete(issueId)
    } else {
      newSelected.add(issueId)
    }
    setSelectedIssues(newSelected)
  }

  const handleSelectAll = () => {
    if (selectedIssues.size === filteredIssues.length) {
      setSelectedIssues(new Set())
    } else {
      setSelectedIssues(new Set(filteredIssues.map(issue => issue.id)))
    }
  }

  const handleBulkAction = async (action: 'resolve' | 'unresolve' | 'false_positive') => {
    if (!onIssueUpdate || selectedIssues.size === 0) return

    const updates = {
      resolve: { is_resolved: true, is_false_positive: false },
      unresolve: { is_resolved: false, is_false_positive: false },
      false_positive: { is_resolved: false, is_false_positive: true },
    }

    // Apply updates to all selected issues
    for (const issueId of selectedIssues) {
      await onIssueUpdate(issueId, updates[action])
    }

    setSelectedIssues(new Set())
  }

  const stats = useMemo(() => {
    const total = issues.length
    const resolved = issues.filter(i => i.is_resolved).length
    const falsePositive = issues.filter(i => i.is_false_positive).length
    const open = total - resolved - falsePositive
    const critical = issues.filter(i => i.severity === 'critical' && !i.is_resolved && !i.is_false_positive).length

    return { total, open, resolved, falsePositive, critical }
  }, [issues])

  if (loading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="p-4">
              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <div className="h-4 w-4 bg-muted animate-pulse rounded" />
                  <div className="h-4 w-1/3 bg-muted animate-pulse rounded" />
                  <div className="h-5 w-16 bg-muted animate-pulse rounded" />
                </div>
                <div className="h-3 w-2/3 bg-muted animate-pulse rounded" />
                <div className="h-3 w-1/2 bg-muted animate-pulse rounded" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold">{stats.total}</div>
            <div className="text-sm text-muted-foreground">Total</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-orange-600">{stats.open}</div>
            <div className="text-sm text-muted-foreground">Open</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-red-600">{stats.critical}</div>
            <div className="text-sm text-muted-foreground">Critical</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-green-600">{stats.resolved}</div>
            <div className="text-sm text-muted-foreground">Resolved</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">{stats.falsePositive}</div>
            <div className="text-sm text-muted-foreground">False Positive</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="flex flex-1 items-center space-x-4">
              {/* Search */}
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search issues..."
                  value={filters.search}
                  onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                  className="pl-10"
                />
              </div>

              {/* Severity Filter */}
              <Select
                value={filters.severity}
                onValueChange={(value: IssueSeverity | 'all') => 
                  setFilters(prev => ({ ...prev, severity: value }))
                }
              >
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Severity</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                </SelectContent>
              </Select>

              {/* Category Filter */}
              <Select
                value={filters.category}
                onValueChange={(value) => setFilters(prev => ({ ...prev, category: value }))}
              >
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {categories.map(category => (
                    <SelectItem key={category} value={category}>
                      {category.charAt(0).toUpperCase() + category.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* Status Filter */}
              <Select
                value={filters.status}
                onValueChange={(value: FilterState['status']) => 
                  setFilters(prev => ({ ...prev, status: value }))
                }
              >
                <SelectTrigger className="w-36">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="open">Open</SelectItem>
                  <SelectItem value="resolved">Resolved</SelectItem>
                  <SelectItem value="false_positive">False Positive</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Sort and Bulk Actions */}
            <div className="flex items-center space-x-2">
              <Select
                value={`${filters.sortBy}-${filters.sortOrder}`}
                onValueChange={(value) => {
                  const [sortBy, sortOrder] = value.split('-') as [FilterState['sortBy'], FilterState['sortOrder']]
                  setFilters(prev => ({ ...prev, sortBy, sortOrder }))
                }}
              >
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="severity-desc">Severity (High to Low)</SelectItem>
                  <SelectItem value="severity-asc">Severity (Low to High)</SelectItem>
                  <SelectItem value="file-asc">File (A to Z)</SelectItem>
                  <SelectItem value="file-desc">File (Z to A)</SelectItem>
                  <SelectItem value="line-asc">Line Number</SelectItem>
                  <SelectItem value="category-asc">Category</SelectItem>
                </SelectContent>
              </Select>

              {selectedIssues.size > 0 && (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline">
                      Actions ({selectedIssues.size})
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent>
                    <DropdownMenuLabel>Bulk Actions</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={() => handleBulkAction('resolve')}>
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Mark as Resolved
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleBulkAction('unresolve')}>
                      <AlertTriangle className="h-4 w-4 mr-2" />
                      Mark as Open
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleBulkAction('false_positive')}>
                      <Eye className="h-4 w-4 mr-2" />
                      Mark as False Positive
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Issues List */}
      {filteredIssues.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-500" />
            <h3 className="text-lg font-medium mb-2">No issues found</h3>
            <p className="text-muted-foreground">
              {filters.search || filters.severity !== 'all' || filters.category !== 'all' || filters.status !== 'all'
                ? "No issues match your current filters"
                : "Great job! No issues detected in this review."
              }
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {/* Select All */}
          <div className="flex items-center space-x-2 px-2">
            <Checkbox
              checked={selectedIssues.size === filteredIssues.length}
              onCheckedChange={handleSelectAll}
            />
            <span className="text-sm text-muted-foreground">
              Select all {filteredIssues.length} issues
            </span>
          </div>

          {/* Issues */}
          {filteredIssues.map((issue) => (
            <Card
              key={issue.id}
              className={cn(
                "cursor-pointer transition-all hover:shadow-md",
                selectedIssue?.id === issue.id && "ring-2 ring-primary",
                issue.is_resolved && "opacity-60",
                issue.is_false_positive && "opacity-40"
              )}
              onClick={() => onIssueSelect?.(issue)}
            >
              <CardContent className="p-4">
                <div className="flex items-start space-x-3">
                  <Checkbox
                    checked={selectedIssues.has(issue.id)}
                    onCheckedChange={() => handleIssueToggle(issue.id)}
                    onClick={(e) => e.stopPropagation()}
                  />

                  <div className="flex-1 space-y-2">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-3">
                        {getSeverityIcon(issue.severity)}
                        <div>
                          <h4 className="font-medium">{issue.title}</h4>
                          <p className="text-sm text-muted-foreground">
                            {issue.file_path}:{issue.line_start}
                            {issue.line_end && issue.line_end !== issue.line_start && 
                              `-${issue.line_end}`
                            }
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        <Badge className={getSeverityColor(issue.severity)}>
                          {issue.severity}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          <div className="flex items-center space-x-1">
                            {getCategoryIcon(issue.category)}
                            <span>{issue.category}</span>
                          </div>
                        </Badge>
                        {issue.is_resolved && (
                          <Badge className="bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300">
                            Resolved
                          </Badge>
                        )}
                        {issue.is_false_positive && (
                          <Badge className="bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300">
                            False Positive
                          </Badge>
                        )}
                      </div>
                    </div>

                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {issue.description}
                    </p>

                    {issue.code_snippet && (
                      <div className="bg-muted rounded-lg p-3 font-mono text-sm overflow-x-auto">
                        <pre className="whitespace-pre-wrap">{issue.code_snippet}</pre>
                      </div>
                    )}

                    {issue.suggested_fix && (
                      <div className="bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 rounded-lg p-3">
                        <div className="flex items-center space-x-2 mb-2">
                          <CheckCircle className="h-4 w-4 text-green-600" />
                          <span className="text-sm font-medium text-green-700 dark:text-green-300">
                            Suggested Fix
                          </span>
                        </div>
                        <p className="text-sm text-green-600 dark:text-green-400">
                          {issue.suggested_fix}
                        </p>
                      </div>
                    )}

                    {issue.ai_explanation && (
                      <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                        <div className="flex items-center space-x-2 mb-2">
                          <MessageSquare className="h-4 w-4 text-blue-600" />
                          <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
                            AI Explanation
                          </span>
                        </div>
                        <p className="text-sm text-blue-600 dark:text-blue-400">
                          {issue.ai_explanation}
                        </p>
                      </div>
                    )}

                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                        {issue.rule_id && (
                          <span>Rule: {issue.rule_id}</span>
                        )}
                        {issue.confidence_score && (
                          <span>Confidence: {Math.round(issue.confidence_score * 100)}%</span>
                        )}
                      </div>

                      <div className="flex items-center space-x-2">
                        {onIssueUpdate && !issue.is_resolved && !issue.is_false_positive && (
                          <>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={(e) => {
                                e.stopPropagation()
                                onIssueUpdate(issue.id, { is_resolved: true })
                              }}
                            >
                              <CheckCircle className="h-3 w-3 mr-1" />
                              Resolve
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={(e) => {
                                e.stopPropagation()
                                onIssueUpdate(issue.id, { is_false_positive: true })
                              }}
                            >
                              <Eye className="h-3 w-3 mr-1" />
                              False Positive
                            </Button>
                          </>
                        )}
                        {onIssueUpdate && (issue.is_resolved || issue.is_false_positive) && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={(e) => {
                              e.stopPropagation()
                              onIssueUpdate(issue.id, { is_resolved: false, is_false_positive: false })
                            }}
                          >
                            <AlertTriangle className="h-3 w-3 mr-1" />
                            Reopen
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
