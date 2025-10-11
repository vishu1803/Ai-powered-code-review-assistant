"use client"

import { useState, useEffect, useMemo } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { 
  FileText, 
  Search, 
  ChevronRight, 
  ChevronDown, 
  AlertTriangle, 
  Eye,
  Copy,
  Download,
  ExternalLink
} from "lucide-react"
import { Review, Issue } from "@/lib/types/api"
import { cn } from "@/lib/utils"
import { toast } from "sonner"

interface CodeViewerProps {
  review: Review
  issues: Issue[]
  selectedIssue?: Issue | null
  onIssueSelect?: (issue: Issue) => void
}

interface FileTreeNode {
  name: string
  path: string
  type: 'file' | 'directory'
  children?: FileTreeNode[]
  issueCount?: number
  issues?: Issue[]
}

// Mock code content - in a real app, this would come from the API
const getFileContent = (filePath: string): string => {
  // This is mock data - replace with actual API call
  const mockFiles: Record<string, string> = {
    'src/app/dashboard/page.tsx': `import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const response = await fetch('/api/dashboard')
      return response.json()
    }
  })

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Dashboard</h1>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {data?.stats && (
          <Card>
            <CardHeader>
              <CardTitle>Total Users</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{data.stats.totalUsers}</div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}`,
    'src/lib/api/client.ts': `import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = \`Bearer \${token}\`
  }
  return config
})

export default apiClient`,
  }

  return mockFiles[filePath] || `// File content for ${filePath}
// This is mock content for demonstration
export default function Component() {
  return <div>Hello World</div>
}`
}

export default function CodeViewer({ review, issues, selectedIssue, onIssueSelect }: CodeViewerProps) {
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set())
  const [searchQuery, setSearchQuery] = useState('')
  const [highlightedLines, setHighlightedLines] = useState<Set<number>>(new Set())

  // Build file tree from issues
  const fileTree = useMemo(() => {
    const tree: FileTreeNode[] = []
    const pathMap = new Map<string, FileTreeNode>()

    // Get unique file paths from issues
    const filePaths = [...new Set(issues.map(issue => issue.file_path))]

    filePaths.forEach(filePath => {
      const parts = filePath.split('/')
      let currentPath = ''

      parts.forEach((part, index) => {
        const isFile = index === parts.length - 1
        currentPath = currentPath ? `${currentPath}/${part}` : part

        if (!pathMap.has(currentPath)) {
          const node: FileTreeNode = {
            name: part,
            path: currentPath,
            type: isFile ? 'file' : 'directory',
            children: isFile ? undefined : [],
            issues: isFile ? issues.filter(issue => issue.file_path === filePath) : undefined,
            issueCount: isFile ? issues.filter(issue => issue.file_path === filePath).length : 0,
          }

          pathMap.set(currentPath, node)

          if (index === 0) {
            tree.push(node)
          } else {
            const parentPath = parts.slice(0, index).join('/')
            const parent = pathMap.get(parentPath)
            if (parent && parent.children) {
              parent.children.push(node)
            }
          }
        }

        // Update issue count for directories
        if (!isFile) {
          const dirNode = pathMap.get(currentPath)
          if (dirNode) {
            dirNode.issueCount = (dirNode.issueCount || 0) + issues.filter(issue => 
              issue.file_path.startsWith(currentPath + '/')
            ).length
          }
        }
      })
    })

    return tree
  }, [issues])

  // Auto-select file if issue is selected
  useEffect(() => {
    if (selectedIssue && selectedIssue.file_path !== selectedFile) {
      setSelectedFile(selectedIssue.file_path)
      setHighlightedLines(new Set([selectedIssue.line_start]))
    }
  }, [selectedIssue, selectedFile])

  const toggleDirectory = (path: string) => {
    const newExpanded = new Set(expandedDirs)
    if (newExpanded.has(path)) {
      newExpanded.delete(path)
    } else {
      newExpanded.add(path)
    }
    setExpandedDirs(newExpanded)
  }

  const renderFileTree = (nodes: FileTreeNode[], level = 0) => {
    return nodes.map(node => (
      <div key={node.path}>
        <div
          className={cn(
            "flex items-center space-x-2 px-2 py-1 hover:bg-muted/50 cursor-pointer rounded-sm",
            selectedFile === node.path && "bg-muted",
            level > 0 && "ml-4"
          )}
          onClick={() => {
            if (node.type === 'file') {
              setSelectedFile(node.path)
              setHighlightedLines(new Set())
            } else {
              toggleDirectory(node.path)
            }
          }}
        >
          {node.type === 'directory' && (
            <>
              {expandedDirs.has(node.path) ? (
                <ChevronDown className="h-3 w-3" />
              ) : (
                <ChevronRight className="h-3 w-3" />
              )}
            </>
          )}
          <FileText className="h-4 w-4" />
          <span className="text-sm flex-1">{node.name}</span>
          {node.issueCount! > 0 && (
            <Badge variant="destructive" className="text-xs">
              {node.issueCount}
            </Badge>
          )}
        </div>
        {node.type === 'directory' && expandedDirs.has(node.path) && node.children && (
          renderFileTree(node.children, level + 1)
        )}
      </div>
    ))
  }

  const getFileContent = (filePath: string) => {
    // Mock implementation - replace with actual API call
    return `// File: ${filePath}
import React from 'react'
import { useState, useEffect } from 'react'

export default function Component() {
  const [data, setData] = useState(null)
  
  useEffect(() => {
    fetchData()
  }, [])
  
  const fetchData = async () => {
    try {
      const response = await fetch('/api/data')
      const result = await response.json()
      setData(result)
    } catch (error) {
      console.error('Error fetching data:', error)
    }
  }
  
  return (
    <div>
      <h1>Component</h1>
      {data && <pre>{JSON.stringify(data, null, 2)}</pre>}
    </div>
  )
}`
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success("Copied to clipboard")
  }

  const fileContent = selectedFile ? getFileContent(selectedFile) : ''
  const fileLines = fileContent.split('\n')
  const fileIssues = selectedFile ? issues.filter(issue => issue.file_path === selectedFile) : []

  return (
    <div className="grid gap-6 lg:grid-cols-4">
      {/* File Tree */}
      <div className="lg:col-span-1">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center space-x-2">
              <FileText className="h-5 w-5" />
              <span>Files</span>
            </CardTitle>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search files..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </CardHeader>
          <CardContent className="space-y-1 max-h-96 overflow-y-auto">
            {fileTree.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                No files with issues
              </p>
            ) : (
              renderFileTree(fileTree)
            )}
          </CardContent>
        </Card>
      </div>

      {/* Code Display */}
      <div className="lg:col-span-3">
        {selectedFile ? (
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <FileText className="h-5 w-5" />
                  <span className="font-mono text-sm">{selectedFile}</span>
                  {fileIssues.length > 0 && (
                    <Badge variant="destructive">
                      {fileIssues.length} issues
                    </Badge>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => copyToClipboard(fileContent)}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                  <Button size="sm" variant="outline">
                    <ExternalLink className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="relative">
                {/* Issue indicators sidebar */}
                <div className="absolute left-0 top-0 w-4 h-full bg-muted/30 border-r">
                  {fileIssues.map(issue => (
                    <div
                      key={issue.id}
                      className={cn(
                        "absolute w-full h-1 cursor-pointer",
                        issue.severity === 'critical' && "bg-red-500",
                        issue.severity === 'high' && "bg-orange-500",
                        issue.severity === 'medium' && "bg-yellow-500",
                        issue.severity === 'low' && "bg-blue-500"
                      )}
                      style={{
                        top: `${(issue.line_start / fileLines.length) * 100}%`,
                      }}
                      onClick={() => {
                        onIssueSelect?.(issue)
                        setHighlightedLines(new Set([issue.line_start]))
                      }}
                      title={issue.title}
                    />
                  ))}
                </div>

                {/* Code content */}
                <div className="pl-6 overflow-x-auto">
                  <pre className="text-sm">
                    {fileLines.map((line, index) => {
                      const lineNumber = index + 1
                      const lineIssues = fileIssues.filter(issue => 
                        lineNumber >= issue.line_start && 
                        lineNumber <= (issue.line_end || issue.line_start)
                      )
                      const hasIssue = lineIssues.length > 0
                      const isHighlighted = highlightedLines.has(lineNumber)
                      const isSelected = selectedIssue && 
                        lineNumber >= selectedIssue.line_start && 
                        lineNumber <= (selectedIssue.line_end || selectedIssue.line_start)

                      return (
                        <div
                          key={lineNumber}
                          className={cn(
                            "flex hover:bg-muted/50",
                            hasIssue && "bg-red-50 dark:bg-red-950/20",
                            isHighlighted && "bg-yellow-100 dark:bg-yellow-900/20",
                            isSelected && "bg-blue-100 dark:bg-blue-900/20"
                          )}
                        >
                          <span className="select-none text-muted-foreground text-right w-12 pr-4 py-0.5">
                            {lineNumber}
                          </span>
                          <code className="flex-1 py-0.5 pr-4">
                            {line || ' '}
                          </code>
                          {hasIssue && (
                            <div className="flex items-center space-x-1 pr-2">
                              {lineIssues.map(issue => (
                                <button
                                  key={issue.id}
                                  className={cn(
                                    "w-3 h-3 rounded-full cursor-pointer hover:scale-110 transition-transform",
                                    issue.severity === 'critical' && "bg-red-500",
                                    issue.severity === 'high' && "bg-orange-500",
                                    issue.severity === 'medium' && "bg-yellow-500",
                                    issue.severity === 'low' && "bg-blue-500"
                                  )}
                                  onClick={() => onIssueSelect?.(issue)}
                                  title={issue.title}
                                />
                              ))}
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </pre>
                </div>
              </div>

              {/* Selected Issue Details */}
              {selectedIssue && selectedIssue.file_path === selectedFile && (
                <div className="mt-4 p-4 bg-muted/50 rounded-lg">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <AlertTriangle className={cn(
                        "h-4 w-4",
                        selectedIssue.severity === 'critical' && "text-red-500",
                        selectedIssue.severity === 'high' && "text-orange-500",
                        selectedIssue.severity === 'medium' && "text-yellow-500",
                        selectedIssue.severity === 'low' && "text-blue-500"
                      )} />
                      <h4 className="font-medium">{selectedIssue.title}</h4>
                      <Badge className={cn(
                        selectedIssue.severity === 'critical' && "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
                        selectedIssue.severity === 'high' && "bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300",
                        selectedIssue.severity === 'medium' && "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300",
                        selectedIssue.severity === 'low' && "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300"
                      )}>
                        {selectedIssue.severity}
                      </Badge>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => onIssueSelect?.(selectedIssue)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  </div>
                  
                  <p className="text-sm text-muted-foreground mb-3">
                    {selectedIssue.description}
                  </p>

                  {selectedIssue.suggested_fix && (
                    <div className="bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 rounded p-3">
                      <h5 className="font-medium text-green-700 dark:text-green-300 mb-2">
                        Suggested Fix:
                      </h5>
                      <p className="text-sm text-green-600 dark:text-green-400">
                        {selectedIssue.suggested_fix}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardContent className="p-12 text-center">
              <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
              <h3 className="text-lg font-medium mb-2">Select a file to view</h3>
              <p className="text-muted-foreground">
                Choose a file from the tree on the left to see its contents and issues
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
