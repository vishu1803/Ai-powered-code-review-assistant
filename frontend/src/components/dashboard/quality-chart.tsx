"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { TrendingUp, TrendingDown, BarChart3, Play, Plus } from "lucide-react"
import { formatDate } from "@/lib/utils"
import Link from "next/link"

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

  // Calculate trend safely
  const validData = data.filter(d => d.quality_score > 0)
  const firstScore = validData[0]?.quality_score || 0
  const lastScore = validData[validData.length - 1]?.quality_score || 0
  const trend = lastScore >= firstScore
  const trendPercentage = firstScore > 0 ? ((lastScore - firstScore) / firstScore * 100) : 0

  // Format data for chart
  const chartData = data.map(point => ({
    ...point,
    date: formatDate(point.date),
    formattedDate: point.date, // Keep original for sorting
  })).sort((a, b) => new Date(a.formattedDate).getTime() - new Date(b.formattedDate).getTime())

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5" />
            <span>Code Quality Trends</span>
          </div>
          {validData.length >= 2 && (
            <div className="flex items-center space-x-2">
              {trend ? (
                <TrendingUp className="h-4 w-4 text-green-500" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-500" />
              )}
              <Badge variant={trend ? "default" : "destructive"}>
                {trend ? '+' : ''}{Math.abs(trendPercentage).toFixed(1)}%
              </Badge>
            </div>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <div className="h-80 flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="font-medium">No quality data available yet</p>
              <p className="text-sm mt-1 mb-4">
                Run code analyses to see quality trends and improvements over time
              </p>
              <div className="flex justify-center space-x-2">
                <Button size="sm" variant="outline" asChild>
                  <Link href="/repositories/connect">
                    <Plus className="h-3 w-3 mr-2" />
                    Connect Repository
                  </Link>
                </Button>
                <Button size="sm" asChild>
                  <Link href="/analysis">
                    <Play className="h-3 w-3 mr-2" />
                    Start Analysis
                  </Link>
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Legend */}
            <div className="flex items-center justify-center space-x-6 text-sm">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                <span>Quality Score</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                <span>Security Score</span>
              </div>
            </div>
            
            <ResponsiveContainer width="100%" height={320}>
              <AreaChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
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
                  tick={{ fill: 'currentColor' }}
                />
                <YAxis 
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  domain={[0, 10]}
                  tick={{ fill: 'currentColor' }}
                  label={{ value: 'Score', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip 
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0]?.payload
                      return (
                        <div className="bg-background border rounded-lg p-3 shadow-lg">
                          <p className="font-medium mb-2">{label}</p>
                          <div className="space-y-1">
                            {payload.map((entry, index) => (
                              <div key={index} className="flex items-center justify-between space-x-4 text-sm">
                                <div className="flex items-center space-x-2">
                                  <div 
                                    className="w-3 h-3 rounded-full"
                                    style={{ backgroundColor: entry.color }}
                                  />
                                  <span>{entry.name}:</span>
                                </div>
                                <span className="font-medium">{entry.value?.toFixed(1)}</span>
                              </div>
                            ))}
                            {data && (
                              <>
                                <div className="border-t pt-2 mt-2 space-y-1">
                                  <div className="flex justify-between text-sm">
                                    <span>Total Issues:</span>
                                    <span className="font-medium">{data.total_issues}</span>
                                  </div>
                                  <div className="flex justify-between text-sm">
                                    <span>Critical Issues:</span>
                                    <span className="font-medium text-red-600">{data.critical_issues}</span>
                                  </div>
                                </div>
                              </>
                            )}
                          </div>
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
            
            {/* Summary Stats */}
            <div className="grid grid-cols-2 gap-4 pt-4 border-t text-sm">
              <div className="text-center">
                <div className="font-medium text-blue-600">
                  {lastScore > 0 ? lastScore.toFixed(1) : 'N/A'}
                </div>
                <div className="text-muted-foreground">Current Quality</div>
              </div>
              <div className="text-center">
                <div className="font-medium text-green-600">
                  {data[data.length - 1]?.security_score?.toFixed(1) || 'N/A'}
                </div>
                <div className="text-muted-foreground">Current Security</div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
