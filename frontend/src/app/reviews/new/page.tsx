"use client"

import { useState, useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { ArrowLeft, Play, FileText, GitBranch, Settings } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import DashboardLayout from "@/components/layout/dashboard-layout"
import { useRepositoryStore } from "@/lib/store/repository-store"
import { reviewsApi } from "@/lib/api/reviews"
import { repositoriesApi } from "@/lib/api/repositories"
import { Repository } from "@/lib/types/api"
import { toast } from "sonner"
import Link from "next/link"

interface ReviewFormData {
  title: string
  description: string
  repository_id: number | null
  branch: string
  commit_sha?: string
  analysis_type: 'full' | 'incremental' | 'custom'
  include_security: boolean
  include_performance: boolean
  include_style: boolean
  custom_rules: string[]
}

export default function NewReviewPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { repositories } = useRepositoryStore()
  
  const [formData, setFormData] = useState<ReviewFormData>({
    title: '',
    description: '',
    repository_id: null,
    branch: 'main',
    analysis_type: 'full',
    include_security: true,
    include_performance: true,
    include_style: false,
    custom_rules: [],
  })
  
  const [selectedRepository, setSelectedRepository] = useState<Repository | null>(null)
  const [availableBranches, setAvailableBranches] = useState<string[]>([])
  const [isLoadingBranches, setIsLoadingBranches] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Pre-select repository from URL params
  useEffect(() => {
    const repoId = searchParams.get('repository')
    if (repoId && repositories.length > 0) {
      const repo = repositories.find(r => r.id === parseInt(repoId))
      if (repo) {
        setSelectedRepository(repo)
        setFormData(prev => ({
          ...prev,
          repository_id: repo.id,
          title: `Code Review - ${repo.name}`,
          branch: repo.default_branch,
        }))
      }
    }
  }, [searchParams, repositories])

  // Load branches when repository is selected
  useEffect(() => {
    if (selectedRepository) {
      loadBranches(selectedRepository.id)
    }
  }, [selectedRepository])

  const loadBranches = async (repositoryId: number) => {
    setIsLoadingBranches(true)
    try {
      const response = await repositoriesApi.getRepositoryBranches(repositoryId)
      setAvailableBranches(response.branches || [])
    } catch (error) {
      toast.error("Failed to load branches")
      // Fallback to default branch
      setAvailableBranches([selectedRepository?.default_branch || 'main'])
    } finally {
      setIsLoadingBranches(false)
    }
  }

  const handleRepositoryChange = (repositoryId: string) => {
    const repo = repositories.find(r => r.id === parseInt(repositoryId))
    if (repo) {
      setSelectedRepository(repo)
      setFormData(prev => ({
        ...prev,
        repository_id: repo.id,
        branch: repo.default_branch,
        title: prev.title || `Code Review - ${repo.name}`,
      }))
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.repository_id || !formData.title.trim()) {
      toast.error("Please select a repository and enter a title")
      return
    }

    setIsSubmitting(true)
    
    try {
      // Create the review
      const review = await reviewsApi.createReview({
        title: formData.title,
        description: formData.description,
        repository_id: formData.repository_id,
        source_branch: formData.branch,
      })

      // Start analysis
      const analysisRequest = {
        repository_id: formData.repository_id,
        branch: formData.branch,
        commit_sha: formData.commit_sha,
        rules: [
          ...(formData.include_security ? ['security'] : []),
          ...(formData.include_performance ? ['performance'] : []),
          ...(formData.include_style ? ['style'] : []),
          ...formData.custom_rules,
        ],
      }

      await reviewsApi.startAnalysis(analysisRequest)
      
      toast.success("Review created and analysis started")
      router.push(`/reviews/${review.id}`)
      
    } catch (error) {
      toast.error("Failed to create review")
    } finally {
      setIsSubmitting(false)
    }
  }

  const analysisTypes = [
    {
      value: 'full',
      label: 'Full Analysis',
      description: 'Complete analysis of all files in the repository',
    },
    {
      value: 'incremental',
      label: 'Incremental Analysis',
      description: 'Only analyze files changed since last review',
    },
    {
      value: 'custom',
      label: 'Custom Analysis',
      description: 'Select specific files or patterns to analyze',
    },
  ]

  const availableRules = [
    { id: 'complexity', label: 'Cyclomatic Complexity', description: 'Check for overly complex functions' },
    { id: 'documentation', label: 'Documentation', description: 'Ensure proper code documentation' },
    { id: 'naming', label: 'Naming Conventions', description: 'Validate variable and function naming' },
    { id: 'testing', label: 'Test Coverage', description: 'Analyze test coverage and quality' },
    { id: 'dependencies', label: 'Dependencies', description: 'Check for outdated or vulnerable dependencies' },
  ]

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center space-x-4">
          <Button variant="ghost" size="icon" asChild>
            <Link href="/reviews">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">New Code Review</h1>
            <p className="text-muted-foreground">
              Start an AI-powered analysis of your code repository
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <FileText className="h-5 w-5" />
                <span>Review Details</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Repository Selection */}
              <div className="space-y-2">
                <Label htmlFor="repository">Repository</Label>
                <Select
                  value={formData.repository_id?.toString() || ''}
                  onValueChange={handleRepositoryChange}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a repository" />
                  </SelectTrigger>
                  <SelectContent>
                    {repositories.map((repo) => (
                      <SelectItem key={repo.id} value={repo.id.toString()}>
                        <div className="flex items-center space-x-2">
                          <span>{repo.provider === 'github' ? '🐙' : repo.provider === 'gitlab' ? '🦊' : '📁'}</span>
                          <span>{repo.full_name}</span>
                          {!repo.is_active && (
                            <Badge variant="secondary" className="text-xs">Inactive</Badge>
                          )}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Branch Selection */}
              {selectedRepository && (
                <div className="space-y-2">
                  <Label htmlFor="branch">Branch</Label>
                  <Select
                    value={formData.branch}
                    onValueChange={(value) => setFormData(prev => ({ ...prev, branch: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {isLoadingBranches ? (
                        <SelectItem value="" disabled>Loading branches...</SelectItem>
                      ) : (
                        availableBranches.map((branch) => (
                          <SelectItem key={branch} value={branch}>
                            <div className="flex items-center space-x-2">
                              <GitBranch className="h-3 w-3" />
                              <span>{branch}</span>
                              {branch === selectedRepository.default_branch && (
                                <Badge variant="outline" className="text-xs">default</Badge>
                              )}
                            </div>
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                </div>
              )}

              {/* Title */}
              <div className="space-y-2">
                <Label htmlFor="title">Title</Label>
                <Input
                  id="title"
                  placeholder="Enter review title"
                  value={formData.title}
                  onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                  required
                />
              </div>

              {/* Description */}
              <div className="space-y-2">
                <Label htmlFor="description">Description (Optional)</Label>
                <Textarea
                  id="description"
                  placeholder="Describe the purpose of this review"
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  rows={3}
                />
              </div>
            </CardContent>
          </Card>

          {/* Analysis Configuration */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Settings className="h-5 w-5" />
                <span>Analysis Configuration</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Analysis Type */}
              <div className="space-y-4">
                <Label>Analysis Type</Label>
                <div className="grid gap-4">
                  {analysisTypes.map((type) => (
                    <Card
                      key={type.value}
                      className={`cursor-pointer transition-all ${
                        formData.analysis_type === type.value ? 'ring-2 ring-primary' : ''
                      }`}
                      onClick={() => setFormData(prev => ({ ...prev, analysis_type: type.value as any }))}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start space-x-3">
                          <div className="mt-0.5">
                            <div className={`w-4 h-4 rounded-full border-2 ${
                              formData.analysis_type === type.value
                                ? 'bg-primary border-primary'
                                : 'border-muted-foreground'
                            }`} />
                          </div>
                          <div className="flex-1">
                            <h4 className="font-medium">{type.label}</h4>
                            <p className="text-sm text-muted-foreground">{type.description}</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>

              <Separator />

              {/* Analysis Options */}
              <div className="space-y-4">
                <Label>Analysis Options</Label>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="security"
                      checked={formData.include_security}
                      onCheckedChange={(checked) => 
                        setFormData(prev => ({ ...prev, include_security: checked }))
                      }
                    />
                    <Label htmlFor="security" className="flex-1">
                      <div className="font-medium">Security Analysis</div>
                      <div className="text-sm text-muted-foreground">
                        Scan for security vulnerabilities and issues
                      </div>
                    </Label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="performance"
                      checked={formData.include_performance}
                      onCheckedChange={(checked) => 
                        setFormData(prev => ({ ...prev, include_performance: checked }))
                      }
                    />
                    <Label htmlFor="performance" className="flex-1">
                      <div className="font-medium">Performance Analysis</div>
                      <div className="text-sm text-muted-foreground">
                        Check for performance bottlenecks and optimizations
                      </div>
                    </Label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="style"
                      checked={formData.include_style}
                      onCheckedChange={(checked) => 
                        setFormData(prev => ({ ...prev, include_style: checked }))
                      }
                    />
                    <Label htmlFor="style" className="flex-1">
                      <div className="font-medium">Code Style</div>
                      <div className="text-sm text-muted-foreground">
                        Enforce coding standards and style guidelines
                      </div>
                    </Label>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Custom Rules */}
              <div className="space-y-4">
                <Label>Additional Rules</Label>
                <div className="grid gap-3">
                  {availableRules.map((rule) => (
                    <div key={rule.id} className="flex items-center space-x-2">
                      <Checkbox
                        id={rule.id}
                        checked={formData.custom_rules.includes(rule.id)}
                        onCheckedChange={(checked) => {
                          if (checked) {
                            setFormData(prev => ({
                              ...prev,
                              custom_rules: [...prev.custom_rules, rule.id]
                            }))
                          } else {
                            setFormData(prev => ({
                              ...prev,
                              custom_rules: prev.custom_rules.filter(r => r !== rule.id)
                            }))
                          }
                        }}
                      />
                      <Label htmlFor={rule.id} className="flex-1 cursor-pointer">
                        <div className="font-medium">{rule.label}</div>
                        <div className="text-sm text-muted-foreground">{rule.description}</div>
                      </Label>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Actions */}
          <div className="flex items-center justify-between">
            <Button variant="outline" asChild>
              <Link href="/reviews">Cancel</Link>
            </Button>
            <Button type="submit" disabled={!formData.repository_id || isSubmitting}>
              <Play className="h-4 w-4 mr-2" />
              {isSubmitting ? 'Starting Analysis...' : 'Start Review'}
            </Button>
          </div>
        </form>
      </div>
    </DashboardLayout>
  )
}
