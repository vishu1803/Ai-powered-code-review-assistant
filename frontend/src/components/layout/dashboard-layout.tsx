"use client"

import { useState, useEffect } from "react"
import { useRouter, usePathname } from "next/navigation"
import Link from "next/link"
import { 
  BarChart3, 
  Code2, 
  FileText, 
  GitBranch, 
  Home, 
  Menu, 
  Settings, 
  Shield, 
  User,
  X,
  Bell,
  Search,
  Plus
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { useAuthStore } from "@/lib/store/auth-store"
import { getCurrentUserProfile, logout } from "@/lib/auth"
import { cn, getInitials } from "@/lib/utils"
import { toast } from "sonner"

interface SidebarItem {
  title: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  badge?: string
}

const sidebarItems: SidebarItem[] = [
  {
    title: "Dashboard",
    href: "/dashboard",
    icon: Home,
  },
  {
    title: "Repositories",
    href: "/repositories",
    icon: GitBranch,
  },
  {
    title: "Reviews",
    href: "/reviews",
    icon: FileText,
  },
  {
    title: "Code Analysis",
    href: "/analysis",
    icon: Code2,
  },
  {
    title: "Security",
    href: "/security",
    icon: Shield,
  },
  {
    title: "Analytics",
    href: "/analytics",
    icon: BarChart3,
  },
  {
    title: "Settings",
    href: "/settings",
    icon: Settings,
  },
]

interface DashboardLayoutProps {
  children: React.ReactNode
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const router = useRouter()
  const pathname = usePathname()
  const { user, setUser, isAuthenticated } = useAuthStore()
  
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const initializeAuth = async () => {
      if (!isAuthenticated) {
        router.push("/auth/login")
        return
      }

      if (!user) {
        try {
          const currentUser = await getCurrentUserProfile()
          if (currentUser) {
            setUser(currentUser)
          } else {
            router.push("/auth/login")
            return
          }
        } catch (error) {
          router.push("/auth/login")
          return
        }
      }

      setIsLoading(false)
    }

    initializeAuth()
  }, [isAuthenticated, user, setUser, router])

  const handleLogout = async () => {
    try {
      await logout()
    } catch (error) {
      // Logout function handles errors
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (!isAuthenticated || !user) {
    return null
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 bg-card border-r transform transition-transform duration-200 ease-in-out lg:translate-x-0 lg:static lg:inset-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between h-16 px-6 border-b">
            <div className="flex items-center space-x-2">
              <div className="h-8 w-8 bg-primary rounded-lg flex items-center justify-center">
                <span className="text-sm font-bold text-primary-foreground">AI</span>
              </div>
              <span className="font-semibold text-lg">Code Review</span>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            {sidebarItems.map((item) => {
              const isActive = pathname === item.href || pathname.startsWith(item.href + "/")
              
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground hover:bg-accent"
                  )}
                  onClick={() => setSidebarOpen(false)}
                >
                  <item.icon className="h-5 w-5" />
                  <span>{item.title}</span>
                  {item.badge && (
                    <span className="ml-auto bg-primary text-primary-foreground text-xs px-2 py-1 rounded-full">
                      {item.badge}
                    </span>
                  )}
                </Link>
              )
            })}
          </nav>

          {/* User Profile */}
          <div className="p-4 border-t">
            <div className="flex items-center space-x-3">
              <Avatar className="h-10 w-10">
                <AvatarImage src={user.avatar_url} alt={user.full_name || user.username} />
                <AvatarFallback>
                  {getInitials(user.full_name || user.username)}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">
                  {user.full_name || user.username}
                </p>
                <p className="text-xs text-muted-foreground truncate">
                  {user.email}
                </p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleLogout}
                className="h-8 w-8"
              >
                <User className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 bg-background border-b flex items-center justify-between px-6">
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu className="h-5 w-5" />
            </Button>
            
            {/* Search */}
            <div className="relative w-96 max-w-sm">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search repositories, reviews..."
                className="pl-10"
              />
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* Quick Actions */}
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              New Review
            </Button>

            {/* Notifications */}
            <Button variant="ghost" size="icon" className="relative">
              <Bell className="h-5 w-5" />
              <span className="absolute -top-1 -right-1 h-4 w-4 bg-destructive text-destructive-foreground text-xs rounded-full flex items-center justify-center">
                3
              </span>
            </Button>

            {/* User Menu */}
            <Avatar className="h-8 w-8 cursor-pointer">
              <AvatarImage src={user.avatar_url} alt={user.full_name || user.username} />
              <AvatarFallback>
                {getInitials(user.full_name || user.username)}
              </AvatarFallback>
            </Avatar>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 overflow-auto">
          <div className="container mx-auto px-6 py-8">
            {children}
          </div>
        </main>
      </div>

      {/* Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  )
}
