"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Shield, AlertTriangle, CheckCircle, RefreshCw, ArrowLeft, Home } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import DashboardLayout from "@/components/layout/dashboard-layout"
import Link from "next/link"
import { useRouter } from "next/navigation"
import apiClient from "@/lib/api/client"

export default function SecurityPage() {
  const router = useRouter()

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button variant="ghost" onClick={() => router.push('/dashboard')}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Security Dashboard</h1>
              <p className="text-muted-foreground">
                Monitor security issues and vulnerabilities in your code
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="outline" onClick={() => router.push('/dashboard')}>
              <Home className="mr-2 h-4 w-4" />
              Dashboard
            </Button>
          </div>
        </div>

        {/* Coming Soon Card */}
        <Card>
          <CardContent className="flex flex-col items-center justify-center h-64 text-center">
            <Shield className="h-16 w-16 text-muted-foreground/50 mb-4" />
            <h3 className="text-lg font-medium mb-2">Security Dashboard</h3>
            <p className="text-muted-foreground mb-6 max-w-md">
              Security monitoring and vulnerability analysis features are coming soon.
            </p>
            <div className="flex space-x-2">
              <Button variant="outline" asChild>
                <Link href="/analysis">
                  Start Code Analysis
                </Link>
              </Button>
              <Button asChild>
                <Link href="/repositories/connect">
                  Connect Repository
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
