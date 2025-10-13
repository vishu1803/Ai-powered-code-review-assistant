"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/lib/store/auth-store"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"
import { toast } from "sonner"
import { 
  Search,
  Github,
  GitBranch,
  Star,
  Eye,
  Lock,
  Unlock,
  RefreshCw,
  Plus,
  Check,
  ArrowLeft,
  AlertCircle
} from "lucide-react"
import apiClient from "@/lib/api/client"

interface GitHubRepository {
  id: number
  name: string
  full_name: string
  description: string | null
  html_url: string
  clone_url: string
  default_branch: string
  language: string | null
  private: boolean
  stargazers_count: number
  watchers_count: number
  updated_at: string
  is_connected: boolean
}

export default function ConnectRepositoryPage() {
  const router = useRouter()
  const { user } = useAuthStore()
  const [repositories, setRepositories] = useState<GitHubRepository[]>([])
  const [filteredRepos, setFilteredRepos] = useState<GitHubRepository[]>([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [connectingRepos, setConnectingRepos] = useState<Set<number>>(new Set())
  const [githubConnectionStatus, setGithubConnectionStatus] = useState<'checking' | 'connected' | 'not_connected'>('checking')

  // Debug user info
  useEffect(() => {
    console.log('=== DEBUG USER INFO ===')
    console.log('User exists:', !!user)
    console.log('User github_id:', user?.github_id)
    console.log('User email:', user?.email)
    console.log('Full user object:', user)
    console.log('======================')
  }, [user])

  useEffect(() => {
    if (user) {
      checkGitHubConnection()
    }
  }, [user])

  useEffect(() => {
    if (searchQuery) {
      const filtered = repositories.filter(repo => 
        repo.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        repo.description?.toLowerCase().includes(searchQuery.toLowerCase())
      )
      setFilteredRepos(filtered)
    } else {
      setFilteredRepos(repositories)
    }
  }, [searchQuery, repositories])

  const checkGitHubConnection = async () => {
    if (!user) return

    // First check if user.github_id exists
    if (user.github_id) {
      setGithubConnectionStatus('connected')
      fetchGitHubRepositories()
      return
    }

    // If no github_id, try to fetch repositories anyway to see if token exists
    try {
      setLoading(true)
      const data = await apiClient.get<GitHubRepository[]>('/repositories/github/available')
      // If we got data, GitHub is connected
      setGithubConnectionStatus('connected')
      setRepositories(data)
      setFilteredRepos(data)
      toast.success(`Found ${data.length} repositories`)
    } catch (error: any) {
      console.error('GitHub connection check failed:', error)
      
      if (error.response?.status === 400) {
        // GitHub not connected
        setGithubConnectionStatus('not_connected')
      } else {
        // Other error - still show as not connected
        setGithubConnectionStatus('not_connected')
        toast.error('Failed to check GitHub connection')
      }
    } finally {
      setLoading(false)
    }
  }

  const fetchGitHubRepositories = async () => {
    setLoading(true)
    try {
      const data = await apiClient.get<GitHubRepository[]>('/repositories/github/available')
      setRepositories(data)
      setFilteredRepos(data)
      setGithubConnectionStatus('connected')
      toast.success(`Found ${data.length} repositories`)
    } catch (error: any) {
      console.error('Error fetching repositories:', error)
      
      if (error.response?.status === 400) {
        const message = error.response?.data?.detail || 'GitHub account not connected'
        toast.error(message)
        setGithubConnectionStatus('not_connected')
      } else {
        toast.error('Failed to fetch repositories. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const connectRepository = async (repo: GitHubRepository) => {
    setConnectingRepos(prev => new Set([...prev, repo.id]))
    
    try {
      await apiClient.post('/repositories/github/connect', null, {
        params: { external_id: repo.id.toString() }
      })
      
      // Update repository status locally
      setRepositories(prev => 
        prev.map(r => 
          r.id === repo.id ? { ...r, is_connected: true } : r
        )
      )
      
      toast.success(`${repo.name} connected successfully!`)
    } catch (error: any) {
      console.error('Error connecting repository:', error)
      const message = error.response?.data?.detail || 'Failed to connect repository'
      toast.error(message)
    } finally {
      setConnectingRepos(prev => {
        const newSet = new Set(prev)
        newSet.delete(repo.id)
        return newSet
      })
    }
  }

  const handleReauthenticate = () => {
    // Redirect to GitHub OAuth
    window.location.href = 'http://localhost:8000/api/v1/auth/oauth/github'
  }

  // If user is not logged in
  if (!user) {
    return (
      <div className="container mx-auto py-8">
        <div className="max-w-2xl mx-auto text-center">
          <Card>
            <CardHeader>
              <CardTitle>Authentication Required</CardTitle>
              <CardDescription>
                You need to be logged in to connect repositories
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={() => router.push('/auth/login')}>
                Sign In
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  // If still checking GitHub connection
  if (githubConnectionStatus === 'checking') {
    return (
      <div className="container mx-auto py-8">
        <div className="max-w-2xl mx-auto text-center">
          <Card>
            <CardContent className="p-12">
              <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
              <p>Checking GitHub connection...</p>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  // If GitHub is not connected
  if (githubConnectionStatus === 'not_connected') {
    return (
      <div className="container mx-auto py-8">
        <div className="max-w-2xl mx-auto text-center">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-center gap-2">
                <Github className="h-6 w-6" />
                GitHub Not Connected
              </CardTitle>
              <CardDescription>
                Connect your GitHub account to access your repositories
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start gap-3 text-left bg-blue-50 dark:bg-blue-950/20 p-4 rounded-lg">
                <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
                <div>
                  <p className="font-medium text-blue-900 dark:text-blue-100">
                    Why connect GitHub?
                  </p>
                  <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                    We need access to your GitHub repositories to perform AI code reviews. 
                    Your data is secure and we only access what you explicitly connect.
                  </p>
                </div>
              </div>
              
              <div className="space-y-2">
                <Button onClick={handleReauthenticate} size="lg">
                  <Github className="mr-2 h-5 w-5" />
                  Connect GitHub Account
                </Button>
                
                <div className="text-sm text-muted-foreground">
                  <p>Debug info:</p>
                  <p>User ID: {user?.id}</p>
                  <p>GitHub ID: {user?.github_id || 'Not set'}</p>
                  <p>Email: {user?.email}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  // Main page - GitHub is connected
  return (
    <div className="container mx-auto py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Connect Repository</h1>
            <p className="text-muted-foreground">
              Choose repositories to analyze with AI Code Review Assistant
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button onClick={fetchGitHubRepositories} disabled={loading} variant="outline" size="sm">
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={handleReauthenticate} variant="outline" size="sm">
            <Github className="mr-2 h-4 w-4" />
            Re-authenticate
          </Button>
        </div>
      </div>

      {/* Search and Filters */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Github className="h-5 w-5" />
              <span className="font-medium">GitHub Repositories</span>
              <Badge variant="secondary">{repositories.length} total</Badge>
              <Badge variant="outline">{repositories.filter(r => r.is_connected).length} connected</Badge>
            </div>
            <div className="flex items-center space-x-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                <Input
                  placeholder="Search repositories..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 w-64"
                />
              </div>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Repository List */}
      {loading ? (
        <div className="space-y-4">
          {[...Array(6)].map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <div className="animate-pulse">
                  <div className="h-4 bg-muted rounded w-1/3 mb-2"></div>
                  <div className="h-3 bg-muted rounded w-2/3 mb-4"></div>
                  <div className="flex space-x-4">
                    <div className="h-3 bg-muted rounded w-16"></div>
                    <div className="h-3 bg-muted rounded w-12"></div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : filteredRepos.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <GitBranch className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">
              {searchQuery ? 'No repositories found' : repositories.length === 0 ? 'No repositories available' : 'No matching repositories'}
            </h3>
            <p className="text-muted-foreground mb-4">
              {searchQuery 
                ? 'Try adjusting your search terms'
                : repositories.length === 0 
                  ? 'No repositories found in your GitHub account'
                  : 'No repositories match your search'
              }
            </p>
            {searchQuery && (
              <Button variant="outline" onClick={() => setSearchQuery('')}>
                Clear Search
              </Button>
            )}
            {repositories.length === 0 && (
              <Button variant="outline" onClick={handleReauthenticate}>
                <Github className="mr-2 h-4 w-4" />
                Re-authenticate GitHub
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredRepos.map((repo) => (
            <Card key={repo.id} className={repo.is_connected ? 'bg-green-50 dark:bg-green-950/20' : ''}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-semibold">{repo.name}</h3>
                      <Badge variant={repo.private ? 'secondary' : 'outline'}>
                        {repo.private ? (
                          <>
                            <Lock className="mr-1 h-3 w-3" />
                            Private
                          </>
                        ) : (
                          <>
                            <Unlock className="mr-1 h-3 w-3" />
                            Public
                          </>
                        )}
                      </Badge>
                      {repo.language && (
                        <Badge variant="outline">{repo.language}</Badge>
                      )}
                      {repo.is_connected && (
                        <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300">
                          <Check className="mr-1 h-3 w-3" />
                          Connected
                        </Badge>
                      )}
                    </div>
                    
                    <p className="text-muted-foreground mb-4">
                      {repo.description || 'No description available'}
                    </p>
                    
                    <div className="flex items-center space-x-6 text-sm text-muted-foreground">
                      <div className="flex items-center space-x-1">
                        <Star className="h-4 w-4" />
                        <span>{repo.stargazers_count}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Eye className="h-4 w-4" />
                        <span>{repo.watchers_count}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <GitBranch className="h-4 w-4" />
                        <span>{repo.default_branch}</span>
                      </div>
                      <span>Updated {new Date(repo.updated_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => window.open(repo.html_url, '_blank')}
                    >
                      <Github className="mr-2 h-4 w-4" />
                      View
                    </Button>
                    
                    {repo.is_connected ? (
                      <Button disabled size="sm" className="bg-green-100 text-green-800 hover:bg-green-100">
                        <Check className="mr-2 h-4 w-4" />
                        Connected
                      </Button>
                    ) : (
                      <Button
                        onClick={() => connectRepository(repo)}
                        disabled={connectingRepos.has(repo.id)}
                        size="sm"
                      >
                        {connectingRepos.has(repo.id) ? (
                          <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                          <Plus className="mr-2 h-4 w-4" />
                        )}
                        {connectingRepos.has(repo.id) ? 'Connecting...' : 'Connect'}
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="mt-8 text-center">
        <Button variant="outline" onClick={() => router.push('/dashboard')}>
          Back to Dashboard
        </Button>
      </div>
    </div>
  )
}
