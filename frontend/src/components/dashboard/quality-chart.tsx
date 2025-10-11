"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { TrendingUp, TrendingDown, BarChart3 } from "lucide-react"
import { formatDate } from "@/lib/utils"

interface QualityDataPoint {
  date: string
  quality_score: number
  security_score: number
  total_issues: number
  critical_issues: number
}

interface QualityChartProps {
  data: QualityDataPoint[]
  loading?: boolean
}

export default function QualityChart({ data, loading = false }: QualityChartProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5" />
            <span>Code Quality Trends</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80 w-full bg-muted animate-pulse rounded" />
        </CardContent>
      </Card>
    )
  }

  // Calculate trend
  const firstScore = data[0]?.quality_score || 0
  const lastScore = data[data.length - 1]?.quality_score || 0
  const trend = lastScore > firstScore
  const trendPercentage = firstScore > 0 ? ((lastScore - firstScore) / firstScore * 100) : 0

  // Format data for chart
  const chartData = data.map(point => ({
    ...point,
    date: formatDate(point.date),
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5" />
            <span>Code Quality Trends</span>
          </div>
          <div className="flex items-center space-x-2">
            {trend ? (
              <TrendingUp className="h-4 w-4 text-green-500" />
            ) : (
              <TrendingDown className="h-4 w-4 text-red-500" />
            )}
            <Badge variant={trend ? "default" : "destructive"}>
              {trend ? '+' : ''}{trendPercentage.toFixed(1)}%
            </Badge>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <div className="h-80 flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No quality data available</p>
              <p className="text-sm">Complete some code reviews to see quality trends</p>
            </div>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="qualityGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="securityGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis 
                dataKey="date" 
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <YAxis 
                fontSize={12}
                tickLine={false}
                axisLine={false}
                domain={[0, 10]}
              />
              <Tooltip 
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="bg-background border rounded-lg p-3 shadow-lg">
                        <p className="font-medium mb-2">{label}</p>
                        {payload.map((entry, index) => (
                          <div key={index} className="flex items-center space-x-2 text-sm">
                            <div 
                              className="w-3 h-3 rounded-full"
                              style={{ backgroundColor: entry.color }}
                            />
                            <span>{entry.name}: {entry.value}</span>
                          </div>
                        ))}
                      </div>
                    )
                  }
                  return null
                }}
              />
              <Area
                type="monotone"
                dataKey="quality_score"
                stroke="#3b82f6"
                strokeWidth={2}
                fill="url(#qualityGradient)"
                name="Quality Score"
              />
              <Area
                type="monotone"
                dataKey="security_score"
                stroke="#10b981"
                strokeWidth={2}
                fill="url(#securityGradient)"
                name="Security Score"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}
