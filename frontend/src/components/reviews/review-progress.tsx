"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Clock, FileText, Zap } from "lucide-react"
import { Review } from "@/lib/types/api"

interface ReviewProgressProps {
  review: Review
}

export default function ReviewProgress({ review }: ReviewProgressProps) {
  const progressPercentage = Math.round(review.progress * 100)
  const estimatedTimeRemaining = review.analysis_metadata?.estimated_time_remaining
  const currentFile = review.analysis_metadata?.current_file

  return (
    <Card className="border-blue-200 bg-blue-50/50 dark:border-blue-800 dark:bg-blue-950/20">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center space-x-2">
            <Zap className="h-5 w-5 text-blue-600" />
            <span>Analysis in Progress</span>
          </CardTitle>
          <Badge variant="outline" className="text-blue-600 border-blue-600">
            {progressPercentage}% Complete
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="font-medium">Overall Progress</span>
            <span className="text-muted-foreground">
              {review.analyzed_files} of {review.total_files} files
            </span>
          </div>
          <Progress value={progressPercentage} className="h-2" />
        </div>

        {/* Current Status */}
        <div className="grid gap-4 md:grid-cols-3">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <FileText className="h-4 w-4 text-blue-600" />
            </div>
            <div>
              <p className="text-sm font-medium">Files Processed</p>
              <p className="text-xs text-muted-foreground">
                {review.analyzed_files} / {review.total_files}
              </p>
            </div>
          </div>

          {estimatedTimeRemaining && (
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg">
                <Clock className="h-4 w-4 text-orange-600" />
              </div>
              <div>
                <p className="text-sm font-medium">Time Remaining</p>
                <p className="text-xs text-muted-foreground">
                  ~{Math.ceil(estimatedTimeRemaining / 60)} minutes
                </p>
              </div>
            </div>
          )}

          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
              <Zap className="h-4 w-4 text-green-600" />
            </div>
            <div>
              <p className="text-sm font-medium">Issues Found</p>
              <p className="text-xs text-muted-foreground">
                {review.total_issues} total
              </p>
            </div>
          </div>
        </div>

        {/* Current File */}
        {currentFile && (
          <div className="bg-background rounded-lg p-3 border">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
              <span className="text-sm font-medium">Currently analyzing:</span>
            </div>
            <p className="text-sm text-muted-foreground font-mono mt-1">
              {currentFile}
            </p>
          </div>
        )}

        {/* Real-time Updates Indicator */}
        <div className="flex items-center justify-center space-x-2 text-xs text-muted-foreground">
          <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
          <span>Real-time updates enabled</span>
        </div>
      </CardContent>
    </Card>
  )
}
