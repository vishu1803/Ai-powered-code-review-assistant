import { redirect } from 'next/navigation'

export default function HomePage() {
  // Redirect to dashboard for authenticated users
  // In a real app, check authentication state here
  redirect('/dashboard')
}
