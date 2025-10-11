"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { ArrowLeft, Github, GitlabIcon as Gitlab, ExternalLink, CheckCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import DashboardLayout from "@/components/layout/dashboard-layout"
import { repositoriesApi } from "@/lib/api/repositories"
import { toast } from "sonner"

interface Repository {
  id: string
  name: string
  full_name: string
  description: string | null
  private: boolean
  language: string | null
  default_branch: string
  html_url: string
  clone_url: string
  updated_at: string
}

type Provider = 'github' | 'gitlab' | 'bitbucket'
type Step = 'provider' | 'auth' | 'select' | 'success'

export default function ConnectRepositoryPage() {
  const router = useRouter()
  
  const [currentStep, setCurrentStep] = useState<Step>('provider')
  const [selectedProvider, setSelectedProvider] = useState<Provider | null>(null)
  const [accessToken, setAccessToken] = useState('')
  const [repositories, setRepositories] = useState<Repository[]>([])
  const [selectedRepos, setSelectedRepos] = useState<Set<string>>(new Set())
  const [isLoading, setIsLoading] = useState(false)
  const [connectedRepos, setConnectedRepos] = useState<Repository[]>([])

  const providers = [
    {
      id: 'github' as Provider,
      name: 'GitHub',
      icon: Github,
      description: 'Connect repositories from GitHub.com',
      color: 'bg-gray-900 text-white',
      available: true,
    },
    {
      id: 'gitlab' as Provider,
      name: 'GitLab',
      icon: Gitlab,
      description: 'Connect repositories from GitLab.com',
      color: 'bg-orange-600 text-white',
      available: true,
    },
    {
      id: 'bitbucket' as Provider,
      name: 'Bitbucket',
      icon: ExternalLink,
      description: 'Connect repositories from Bitbucket.org',
      color: 'bg-blue-600 text-white',
      available: false,
    },
  ]

  const handleProviderSelect = (provider: Provider) => {
    setSelectedProvider(provider)
    setCurrentStep('auth')
  }

  const handleBack = () => {
    switch (currentStep) {
      case 'auth':
        setCurrentStep('provider')
        setSelectedProvider(null)
        break
      case 'select':
        setCurrentStep('auth')
        setRepositories([])
        break
      case 'success':
        setCurrentStep('select')
        setConnectedRepos([])
        break
    }
  }

  const fetchRepositories = async () => {
    if (!selectedProvider || !accessToken) return

    setIsLoading(true)
    try {
      // Simulate API call to fetch repositories
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      const mockRepos: Repository[] = [
        {
          id: '1',
          name: 'awesome-project',
          full_name: 'user/awesome-project',
          description: 'An awesome project built with React and TypeScript',
          private: false,
          language: 'TypeScript',
          default_branch: 'main',
          html_url: 'https://github.com/user/awesome-project',
          clone_url: 'https://github.com/user/awesome-project.git',
          updated_at: '2024-10-10T12:00:00Z',
        },
        {
          id: '2',
          name: 'api-backend',
          full_name: 'user/api-backend',
          description: 'FastAPI backend with PostgreSQL',
          private: true,
          language: 'Python',
          default_branch: 'develop',
          html_url: 'https://github.com/user/api-backend',
          clone_url: 'https://github.com/user/api-backend.git',
          updated_at: '2024-10-09T15:30:00Z',
        },
        {
          id: '3',
          name: 'mobile-app',
          full_name: 'user/mobile-app',
          description: null,
          private: false,
          language: 'Dart',
          default_branch: 'main',
          html_url: 'https://github.com/user/mobile-app',
          clone_url: 'https://github.com/user/mobile-app.git',
          updated_at: '2024-10-08T09:15:00Z',
        },
      ]

      setRepositories(mockRepos)
      setCurrentStep('select')
    } catch (error) {
      toast.error('Failed to fetch repositories. Please check your access token.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleRepositoryToggle = (repoId: string) => {
    const newSelected = new Set(selectedRepos)
    if (newSelected.has(repoId)) {
      newSelected.delete(repoId)
    } else {
      newSelected.add(repoId)
    }
    setSelectedRepos(newSelected)
  }

  const handleConnect = async () => {
    if (selectedRepos.size === 0) {
      toast.error('Please select at least one repository')
      return
    }

    setIsLoading(true)
    try {
      const reposToConnect = repositories.filter(repo => selectedRepos.has(repo.id))
      
      // Simulate connecting repositories
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      setConnectedRepos(reposToConnect)
      setCurrentStep('success')
      toast.success(`Successfully connected ${reposToConnect.length} repositories`)
    } catch (error) {
      toast.error('Failed to connect repositories')
    } finally {
      setIsLoading(false)
    }
  }

  const getLanguageColor = (language: string | null) => {
    if (!language) return 'bg-gray-500'
    
    const colors: Record<string, string> = {
      'TypeScript': 'bg-blue-500',
      'JavaScript': 'bg-yellow-500',
      'Python': 'bg-green-500',
      'Java': 'bg-orange-500',
      'Dart': 'bg-blue-400',
      'Go': 'bg-cyan-500',
      'Rust': 'bg-orange-600',
    }
    return colors[language] || 'bg-gray-500'
  }

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center space-x-4">
          {currentStep !== 'provider' && (
            <Button variant="ghost" size="icon" onClick={handleBack}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
          )}
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Connect Repository</h1>
            <p className="text-muted-foreground">
              Connect your code repositories to enable AI-powered code reviews
            </p>
          </div>
        </div>

        {/* Steps */}
        <div className="flex items-center space-x-4">
          {['provider', 'auth', 'select', 'success'].map((step, index) => (
            <div key={step} className="flex items-center space-x-2">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                currentStep === step
                  ? 'bg-primary text-primary-foreground'
                  : index < ['provider', 'auth', 'select', 'success'].indexOf(currentStep)
                    ? 'bg-green-500 text-white'
                    : 'bg-muted text-muted-foreground'
              }`}>
                {index < ['provider', 'auth', 'select', 'success'].indexOf(currentStep) ? (
                  <CheckCircle className="h-4 w-4" />
                ) : (
                  index + 1
                )}
              </div>
              {index < 3 && <div className="w-8 h-px bg-border" />}
            </div>
          ))}
        </div>

        {/* Content */}
        <Card>
          <CardContent className="p-8">
            {currentStep === 'provider' && (
              <div className="space-y-6">
                <div className="text-center">
                  <h2 className="text-2xl font-semibold mb-2">Choose a Provider</h2>
                  <p className="text-muted-foreground">
                    Select where your repositories are hosted
                  </p>
                </div>

                <div className="grid gap-4 md:grid-cols-3">
                  {providers.map((provider) => {
                    const IconComponent = provider.icon
                    
                    return (
                      <Card
                        key={provider.id}
                        className={`cursor-pointer transition-all hover:shadow-md ${
                          !provider.available ? 'opacity-50 cursor-not-allowed' : ''
                        }`}
                        onClick={() => provider.available && handleProviderSelect(provider.id)}
                      >
                        <CardContent className="p-6 text-center space-y-4">
                          <div className={`w-16 h-16 mx-auto rounded-lg flex items-center justify-center ${provider.color}`}>
                            <IconComponent className="h-8 w-8" />
                          </div>
                          <div>
                            <h3 className="font-semibold">{provider.name}</h3>
                            <p className="text-sm text-muted-foreground">
                              {provider.description}
                            </p>
                          </div>
                          {!provider.available && (
                            <Badge variant="secondary">Coming Soon</Badge>
                          )}
                        </CardContent>
                      </Card>
                    )
                  })}
                </div>
              </div>
            )}

            {currentStep === 'auth' && selectedProvider && (
              <div className="space-y-6">
                <div className="text-center">
                  <h2 className="text-2xl font-semibold mb-2">
                    Authenticate with {providers.find(p => p.id === selectedProvider)?.name}
                  </h2>
                  <p className="text-muted-foreground">
                    Provide your access token to fetch repositories
                  </p>
                </div>

                <div className="max-w-md mx-auto space-y-4">
                  <div className="space-y-2">
                    <label htmlFor="token" className="text-sm font-medium">
                      Personal Access Token
                    </label>
                    <Input
                      id="token"
                      type="password"
                      placeholder="Enter your access token"
                      value={accessToken}
                      onChange={(e) => setAccessToken(e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground">
                      Need help? 
                      <Link 
                        href={`https://docs.${selectedProvider}.com/authentication/tokens`}
                        target="_blank"
                        className="text-primary hover:underline ml-1"
                      >
                        Learn how to create a token
                      </Link>
                    </p>
                  </div>

                  <Button 
                    className="w-full" 
                    onClick={fetchRepositories}
                    disabled={!accessToken.trim() || isLoading}
                  >
                    {isLoading ? 'Fetching repositories...' : 'Fetch Repositories'}
                  </Button>
                </div>
              </div>
            )}

            {currentStep === 'select' && (
              <div className="space-y-6">
                <div className="text-center">
                  <h2 className="text-2xl font-semibold mb-2">Select Repositories</h2>
                  <p className="text-muted-foreground">
                    Choose which repositories to connect for code review
                  </p>
                </div>

                <div className="space-y-4">
                  {repositories.map((repo) => (
                    <Card 
                      key={repo.id}
                      className={`cursor-pointer transition-all ${
                        selectedRepos.has(repo.id) ? 'ring-2 ring-primary' : ''
                      }`}
                      onClick={() => handleRepositoryToggle(repo.id)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1 space-y-2">
                            <div className="flex items-center space-x-2">
                              <h3 className="font-semibold">{repo.name}</h3>
                              {repo.private && (
                                <Badge variant="secondary">Private</Badge>
                              )}
                            </div>
                            
                            <p className="text-sm text-muted-foreground">
                              {repo.full_name}
                            </p>
                            
                            {repo.description && (
                              <p className="text-sm text-muted-foreground">
                                {repo.description}
                              </p>
                            )}
                            
                            <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                              {repo.language && (
                                <div className="flex items-center space-x-1">
                                  <div className={`w-2 h-2 rounded-full ${getLanguageColor(repo.language)}`} />
                                  <span>{repo.language}</span>
                                </div>
                              )}
                              <span>Updated {new Date(repo.updated_at).toLocaleDateString()}</span>
                            </div>
                          </div>
                          
                          <div className="ml-4">
                            <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                              selectedRepos.has(repo.id)
                                ? 'bg-primary border-primary text-primary-foreground'
                                : 'border-muted-foreground'
                            }`}>
                              {selectedRepos.has(repo.id) && (
                                <CheckCircle className="h-3 w-3" />
                              )}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                <div className="flex items-center justify-between pt-4">
                  <p className="text-sm text-muted-foreground">
                    {selectedRepos.size} of {repositories.length} repositories selected
                  </p>
                  <Button 
                    onClick={handleConnect}
                    disabled={selectedRepos.size === 0 || isLoading}
                  >
                    {isLoading ? 'Connecting...' : `Connect ${selectedRepos.size} Repositories`}
                  </Button>
                </div>
              </div>
            )}

            {currentStep === 'success' && (
              <div className="space-y-6 text-center">
                <div className="w-16 h-16 mx-auto bg-green-100 rounded-full flex items-center justify-center">
                  <CheckCircle className="h-8 w-8 text-green-600" />
                </div>
                
                <div>
                  <h2 className="text-2xl font-semibold mb-2">Successfully Connected!</h2>
                  <p className="text-muted-foreground">
                    {connectedRepos.length} repositories have been connected and are ready for code review
                  </p>
                </div>

                <div className="space-y-2">
                  {connectedRepos.map((repo) => (
                    <div key={repo.id} className="flex items-center justify-center space-x-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span>{repo.full_name}</span>
                    </div>
                  ))}
                </div>

                <div className="flex items-center justify-center space-x-4 pt-4">
                  <Button variant="outline" asChild>
                    <Link href="/repositories">View Repositories</Link>
                  </Button>
                  <Button asChild>
                    <Link href="/reviews/new">Start First Review</Link>
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
