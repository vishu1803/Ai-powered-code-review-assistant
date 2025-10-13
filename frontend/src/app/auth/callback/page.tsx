"use client"

import { useEffect, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { useAuthStore } from "@/lib/store/auth-store"
import { setAuthTokens, getCurrentUserProfile } from "@/lib/auth"
import { toast } from "sonner"

export default function OAuthCallbackPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { setUser, setLoading } = useAuthStore()
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing')

  useEffect(() => {
    const handleOAuthCallback = async () => {
      try {
        setLoading(true)
        
        // Get tokens from URL parameters
        const accessToken = searchParams.get('access_token')
        const refreshToken = searchParams.get('refresh_token')
        const provider = searchParams.get('provider')
        const success = searchParams.get('success')
        const error = searchParams.get('error')

        // Check for error
        if (error) {
          const errorMessage = searchParams.get('message') || 'OAuth authentication failed'
          toast.error(`${provider} login failed: ${errorMessage}`)
          setStatus('error')
          setTimeout(() => router.push('/auth/login'), 3000)
          return
        }

        // Check for missing tokens
        if (!accessToken || !refreshToken) {
          toast.error('Missing authentication tokens')
          setStatus('error')
          setTimeout(() => router.push('/auth/login'), 3000)
          return
        }

        // Store tokens
        setAuthTokens({
          access_token: accessToken,
          refresh_token: refreshToken,
          token_type: 'bearer'
        })

        // Get user profile
        const user = await getCurrentUserProfile()
        if (!user) {
          throw new Error('Failed to get user profile')
        }

        // Update auth store
        setUser(user)
        setStatus('success')

        // Success message and redirect
        toast.success(`Successfully logged in with ${provider}!`)
        
        // Redirect to dashboard after short delay
        setTimeout(() => {
          router.push('/dashboard')
        }, 1500)

      } catch (error) {
        console.error('OAuth callback error:', error)
        toast.error('Authentication failed. Please try again.')
        setStatus('error')
        setTimeout(() => router.push('/auth/login'), 3000)
      } finally {
        setLoading(false)
      }
    }

    handleOAuthCallback()
  }, [searchParams, router, setUser, setLoading])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="max-w-md w-full mx-4">
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-8 text-center">
          <div className="mx-auto h-12 w-12 bg-primary rounded-lg flex items-center justify-center mb-4">
            <span className="text-2xl font-bold text-primary-foreground">AI</span>
          </div>
          
          {status === 'processing' && (
            <>
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
              <h2 className="text-xl font-semibold mb-2">Completing Sign In...</h2>
              <p className="text-muted-foreground">
                Please wait while we set up your account.
              </p>
            </>
          )}
          
          {status === 'success' && (
            <>
              <div className="h-8 w-8 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center mx-auto mb-4">
                <svg className="h-5 w-5 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold mb-2 text-green-600 dark:text-green-400">
                Sign In Successful!
              </h2>
              <p className="text-muted-foreground">
                Redirecting to your dashboard...
              </p>
            </>
          )}
          
          {status === 'error' && (
            <>
              <div className="h-8 w-8 rounded-full bg-red-100 dark:bg-red-900 flex items-center justify-center mx-auto mb-4">
                <svg className="h-5 w-5 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold mb-2 text-red-600 dark:text-red-400">
                Sign In Failed
              </h2>
              <p className="text-muted-foreground">
                Redirecting back to login...
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
