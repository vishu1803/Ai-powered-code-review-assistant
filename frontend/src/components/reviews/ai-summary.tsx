"use client"

import { useState } from "react"
import { Sparkles, TrendingUp, AlertTriangle, CheckCircle, Lightbulb, Download, Share, RefreshCw } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Review } from "@/lib/types/api"
import { formatDateTime } from "@/lib/utils"

interface AISummaryProps {
  review: Review
  onGenerate: () => Promise<void>
}

interface Recommendation {
  id: string
  category: 'security' | 'performance' | 'maintainability' | 'quality' | 'testing'
  priority: 'high' | 'medium' | 'low'
  title: string
  description: string
  impact: string
  effort: 'low' | 'medium' | 'high'
  actionItems: string[]
}

interface QualityInsight {
  metric: string
  current: number
  target: number
  trend: 'up' | 'down' | 'stable'
  description: string
}

export default function AISummary({ review, onGenerate }: AISummaryProps) {
  const [isGenerating, setIsGenerating] = useState(false)
  const [activeTab, setActiveTab] = useState('summary')

  // Mock AI-generated recommendations (in real app, this would come from the API)
  const mockRecommendations: Recommendation[] = [
    {
      id: '1',
      category: 'security',
      priority: 'high',
      title: 'Address SQL Injection Vulnerabilities',
      description: 'Found 3 potential SQL injection points in database query functions',
      impact: 'High security risk - could lead to data breaches',
      effort: 'medium',
      actionItems: [
        'Use parameterized queries in user authentication module',
        'Implement input sanitization for search functionality', 
        'Add SQL injection protection middleware',
        'Conduct security review of all database interactions'
      ]
    },
    {
      id: '2', 
      category: 'performance',
      priority: 'medium',
      title: 'Optimize Database Queries',
      description: 'Several N+1 query patterns detected that could impact performance',
      impact: 'Medium performance impact under high load',
      effort: 'low',
      actionItems: [
        'Add database query optimization in user listing',
        'Implement proper eager loading for relationships',
        'Consider adding database indexes for frequently queried fields',
        'Use query batching for bulk operations'
      ]
    },
    {
      id: '3',
      category: 'maintainability', 
      priority: 'medium',
      title: 'Reduce Code Complexity',
      description: 'High cyclomatic complexity detected in 5 functions',
      impact: 'Affects code maintainability and testing',
      effort: 'high',
      actionItems: [
        'Refactor large functions into smaller, focused units',
        'Extract common patterns into reusable utilities',
        'Add comprehensive unit tests for complex logic',
        'Consider using design patterns to reduce complexity'
      ]
    }
  ]

  const mockInsights: QualityInsight[] = [
    {
      metric: 'Code Quality',
      current: review.code_quality_score || 7.8,
      target: 8.5,
      trend: 'up',
      description: 'Overall code quality has improved by 12% since last review'
    },
    {
      metric: 'Security Score',
      current: review.security_score || 8.2,
      target: 9.0,
      trend: 'stable',
      description: 'Security posture is strong with minor vulnerabilities addressed'
    },
    {
      metric: 'Test Coverage',
      current: review.test_coverage || 68,
      target: 80,
      trend: 'up',
      description: 'Test coverage increased by 8% with new unit tests added'
    }
  ]

  const handleGenerate = async () => {
    setIsGenerating(true)
    try {
      await onGenerate()
    } finally {
      setIsGenerating(false)  
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'security':
        return <AlertTriangle className="h-4 w-4 text-red-500" />
      case 'performance':
        return <TrendingUp className="h-4 w-4 text-green-500" />
      case 'maintainability':
        return <CheckCircle className="h-4 w-4 text-blue-500" />
      case 'quality':
        return <Sparkles className="h-4 w-4 text-purple-500" />
      case 'testing':
        return <CheckCircle className="h-4 w-4 text-orange-500" />
      default:
        return <Lightbulb className="h-4 w-4 text-gray-500" />
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'security':
        return 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
      case 'performance':
        return 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
      case 'maintainability':
        return 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
      case 'quality':
        return 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300'
      case 'testing':
        return 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300'
      default:
        return 'bg-gray-100 text-gray-700 dark:bg-gray-900 dark:text-gray-300'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
      case 'medium':
        return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
      case 'low':
        return 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
      default:
        return 'bg-gray-100 text-gray-700 dark:bg-gray-900 dark:text-gray-300'
    }
  }

  const getEffortBadge = (effort: string) => {
    const colors = {
      low: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
      medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300', 
      high: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
    }
    return colors[effort as keyof typeof colors] || colors.medium
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-green-500" />
      case 'down':
        return <TrendingUp className="h-4 w-4 text-red-500 rotate-180" />
      default:
        return <div className="h-4 w-4 bg-gray-400 rounded-full" />
    }
  }

  if (!review.ai_summary && !isGenerating) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <div className="space-y-4">
            <div className="w-16 h-16 mx-auto bg-gradient-to-br from-purple-400 to-blue-600 rounded-full flex items-center justify-center">
              <Sparkles className="h-8 w-8 text-white" />
            </div>
            <div>
              <h3 className="text-xl font-semibold mb-2">AI Summary Not Generated</h3>
              <p className="text-muted-foreground max-w-md mx-auto">
                Generate an AI-powered summary to get insights, recommendations, and quality analysis for this review.
              </p>
            </div>
            <Button onClick={handleGenerate} className="mt-4">
              <Sparkles className="h-4 w-4 mr-2" />
              Generate AI Summary
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (isGenerating) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <div className="space-y-4">
            <div className="w-16 h-16 mx-auto bg-gradient-to-br from-purple-400 to-blue-600 rounded-full flex items-center justify-center">
              <Sparkles className="h-8 w-8 text-white animate-pulse" />
            </div>
            <div>
              <h3 className="text-xl font-semibold mb-2">Generating AI Summary...</h3>
              <p className="text-muted-foreground">
                Analyzing code quality, security, and providing recommendations
              </p>
            </div>
            <div className="max-w-sm mx-auto">
              <Progress value={75} className="h-2" />
              <p className="text-xs text-muted-foreground mt-2">
                Processing insights and recommendations...
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <Sparkles className="h-5 w-5 text-purple-600" />
              <span>AI-Generated Summary</span>
            </CardTitle>
            <div className="flex items-center space-x-2">
              <Button size="sm" variant="outline">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
              <Button size="sm" variant="outline">
                <Share className="h-4 w-4 mr-2" />
                Share
              </Button>
              <Button size="sm" variant="outline" onClick={handleGenerate}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Regenerate
              </Button>
            </div>
          </div>
          <p className="text-sm text-muted-foreground">
            Generated on {formatDateTime(review.updated_at || review.created_at)}
          </p>
        </CardHeader>
      </Card>

      {/* AI Summary Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="summary">Summary</TabsTrigger>
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
          <TabsTrigger value="insights">Insights</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
        </TabsList>

        <TabsContent value="summary" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Executive Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="prose prose-sm max-w-none">
                <p>
                  {review.ai_summary || `This code review analyzed ${review.total_files} files and identified ${review.total_issues} issues across multiple categories. The overall code quality score is ${review.code_quality_score?.toFixed(1) || 'N/A'}/10, indicating ${review.code_quality_score && review.code_quality_score > 7 ? 'good' : 'room for improvement'} code health.`}
                </p>
                <p>
                  Key areas of focus include security improvements, performance optimizations, and maintainability enhancements. The analysis found {review.critical_issues} critical issues that should be addressed immediately, and {review.high_issues} high-priority items for the next development cycle.
                </p>
              </div>

              <Separator />

              <div className="grid gap-4 md:grid-cols-3">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{review.code_quality_score?.toFixed(1) || 'N/A'}</div>
                  <div className="text-sm text-muted-foreground">Quality Score</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{review.security_score?.toFixed(1) || 'N/A'}</div>
                  <div className="text-sm text-muted-foreground">Security Score</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">{review.maintainability_score?.toFixed(1) || 'N/A'}</div>
                  <div className="text-sm text-muted-foreground">Maintainability</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Key Findings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                  <div>
                    <p className="font-medium">Strengths</p>
                    <p className="text-sm text-muted-foreground">
                      Good separation of concerns, consistent naming conventions, and proper error handling in most modules.
                    </p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <AlertTriangle className="h-5 w-5 text-yellow-500 mt-0.5" />
                  <div>
                    <p className="font-medium">Areas for Improvement</p>
                    <p className="text-sm text-muted-foreground">
                      Security vulnerabilities in authentication, performance bottlenecks in data processing, and complex functions that need refactoring.
                    </p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <TrendingUp className="h-5 w-5 text-blue-500 mt-0.5" />
                  <div>
                    <p className="font-medium">Recommendations</p>
                    <p className="text-sm text-muted-foreground">
                      Focus on security hardening, add comprehensive testing, and improve documentation coverage.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="recommendations" className="space-y-4">
          {mockRecommendations.map((rec) => (
            <Card key={rec.id}>
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    {getCategoryIcon(rec.category)}
                    <div>
                      <CardTitle className="text-lg">{rec.title}</CardTitle>
                      <p className="text-sm text-muted-foreground">{rec.description}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge className={getPriorityColor(rec.priority)}>
                      {rec.priority} priority
                    </Badge>
                    <Badge className={getCategoryColor(rec.category)}>
                      {rec.category}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <h4 className="font-medium mb-2">Impact</h4>
                    <p className="text-sm text-muted-foreground">{rec.impact}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium">Effort:</span>
                    <Badge className={getEffortBadge(rec.effort)}>
                      {rec.effort}
                    </Badge>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium mb-2">Action Items</h4>
                  <ul className="space-y-1">
                    {rec.actionItems.map((item, index) => (
                      <li key={index} className="flex items-start space-x-2 text-sm">
                        <span className="text-muted-foreground mt-1">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="insights" className="space-y-4">
          {mockInsights.map((insight, index) => (
            <Card key={index}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    {getTrendIcon(insight.trend)}
                    <h3 className="font-medium">{insight.metric}</h3>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold">{insight.current}</div>
                    <div className="text-sm text-muted-foreground">/ {insight.target} target</div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Progress to target</span>
                    <span>{Math.round((insight.current / insight.target) * 100)}%</span>
                  </div>
                  <Progress value={(insight.current / insight.target) * 100} />
                </div>

                <p className="text-sm text-muted-foreground mt-3">{insight.description}</p>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="metrics">
          <Card>
            <CardHeader>
              <CardTitle>Detailed Metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-6 md:grid-cols-2">
                <div className="space-y-4">
                  <h4 className="font-medium">Code Quality Metrics</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm">Lines of Code</span>
                      <span className="font-medium">2,847</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Cyclomatic Complexity</span>
                      <span className="font-medium">4.2 avg</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Technical Debt</span>
                      <span className="font-medium">12h estimated</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Duplication</span>
                      <span className="font-medium">3.2%</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h4 className="font-medium">Issue Breakdown</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm">Critical Issues</span>
                      <Badge variant="destructive">{review.critical_issues}</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">High Priority</span>
                      <Badge className="bg-orange-100 text-orange-700">{review.high_issues}</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Medium Priority</span>
                      <Badge className="bg-yellow-100 text-yellow-700">{review.medium_issues}</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Low Priority</span>
                      <Badge className="bg-blue-100 text-blue-700">{review.low_issues}</Badge>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
