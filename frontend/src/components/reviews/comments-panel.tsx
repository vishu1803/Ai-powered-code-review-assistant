"use client"

import { useState, useRef, useEffect } from "react"
import { MessageSquare, Reply, MoreHorizontal, Heart, ThumbsUp, Edit, Trash2, Send, Paperclip } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Comment } from "@/lib/types/api"
import { formatRelativeTime, getInitials } from "@/lib/utils"
import { cn } from "@/lib/utils"

interface CommentsPanelProps {
  comments: Comment[]
  onAddComment: (content: string, issueId?: number, parentId?: number) => Promise<void>
  onUpdateComment?: (commentId: number, content: string) => Promise<void>
  onDeleteComment?: (commentId: number) => Promise<void>
  currentUserId?: number
}

interface CommentThread {
  comment: Comment
  replies: Comment[]
}

export default function CommentsPanel({ 
  comments, 
  onAddComment, 
  onUpdateComment,
  onDeleteComment,
  currentUserId = 1 // Mock current user ID
}: CommentsPanelProps) {
  const [newComment, setNewComment] = useState('')
  const [replyingTo, setReplyingTo] = useState<number | null>(null)
  const [editingComment, setEditingComment] = useState<number | null>(null)
  const [editContent, setEditContent] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [commentType, setCommentType] = useState<'general' | 'suggestion' | 'question' | 'approval'>('general')
  const [filter, setFilter] = useState<'all' | 'general' | 'suggestion' | 'question' | 'approval'>('all')

  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Group comments into threads (parent comments with their replies)
  const commentThreads: CommentThread[] = comments
    .filter(comment => !comment.parent_id)
    .map(comment => ({
      comment,
      replies: comments
        .filter(reply => reply.parent_id === comment.id)
        .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
    }))
    .sort((a, b) => new Date(b.comment.created_at).getTime() - new Date(a.comment.created_at).getTime())

  // Filter threads based on selected filter
  const filteredThreads = commentThreads.filter(thread => {
    if (filter === 'all') return true
    return thread.comment.comment_type === filter || 
           thread.replies.some(reply => reply.comment_type === filter)
  })

  const handleSubmitComment = async () => {
    if (!newComment.trim()) return

    setIsSubmitting(true)
    try {
      await onAddComment(newComment, undefined, replyingTo || undefined)
      setNewComment('')
      setReplyingTo(null)
      setCommentType('general')
    } catch (error) {
      console.error('Failed to add comment:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleEditComment = async (commentId: number) => {
    if (!editContent.trim() || !onUpdateComment) return

    try {
      await onUpdateComment(commentId, editContent)
      setEditingComment(null)
      setEditContent('')
    } catch (error) {
      console.error('Failed to update comment:', error)
    }
  }

  const handleDeleteComment = async (commentId: number) => {
    if (!onDeleteComment) return

    if (window.confirm('Are you sure you want to delete this comment?')) {
      try {
        await onDeleteComment(commentId)
      } catch (error) {
        console.error('Failed to delete comment:', error)
      }
    }
  }

  const startReply = (commentId: number) => {
    setReplyingTo(commentId)
    textareaRef.current?.focus()
  }

  const startEdit = (comment: Comment) => {
    setEditingComment(comment.id)
    setEditContent(comment.content)
  }

  const getCommentTypeIcon = (type: string) => {
    switch (type) {
      case 'suggestion':
        return '💡'
      case 'question':
        return '❓'
      case 'approval':
        return '✅'
      default:
        return '💬'
    }
  }

  const getCommentTypeColor = (type: string) => {
    switch (type) {
      case 'suggestion':
        return 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
      case 'question':
        return 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300'
      case 'approval':
        return 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
      default:
        return 'bg-gray-100 text-gray-700 dark:bg-gray-900 dark:text-gray-300'
    }
  }

  const CommentItem = ({ comment, isReply = false }: { comment: Comment; isReply?: boolean }) => (
    <div className={cn("space-y-3", isReply && "ml-12 pl-4 border-l-2 border-muted")}>
      <div className="flex items-start space-x-3">
        <Avatar className="h-8 w-8">
          <AvatarImage src={comment.author?.avatar_url} />
          <AvatarFallback className="text-xs">
            {getInitials(comment.author?.full_name || comment.author?.username || 'Unknown')}
          </AvatarFallback>
        </Avatar>

        <div className="flex-1 space-y-2">
          <div className="flex items-center space-x-2">
            <span className="font-medium text-sm">
              {comment.author?.full_name || comment.author?.username || 'Unknown'}
            </span>
            <Badge className={getCommentTypeColor(comment.comment_type)} variant="outline">
              <span className="mr-1">{getCommentTypeIcon(comment.comment_type)}</span>
              {comment.comment_type}
            </Badge>
            <span className="text-xs text-muted-foreground">
              {formatRelativeTime(comment.created_at)}
            </span>
            {comment.updated_at && comment.updated_at !== comment.created_at && (
              <span className="text-xs text-muted-foreground">(edited)</span>
            )}
          </div>

          {comment.file_path && (
            <div className="text-xs text-muted-foreground font-mono bg-muted px-2 py-1 rounded">
              {comment.file_path}
              {comment.line_number && `:${comment.line_number}`}
            </div>
          )}

          {editingComment === comment.id ? (
            <div className="space-y-2">
              <Textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                placeholder="Edit your comment..."
                className="min-h-[80px]"
              />
              <div className="flex items-center space-x-2">
                <Button size="sm" onClick={() => handleEditComment(comment.id)}>
                  Save
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setEditingComment(null)
                    setEditContent('')
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <div className="prose prose-sm max-w-none">
              <p className="text-sm whitespace-pre-wrap">{comment.content}</p>
            </div>
          )}

          <div className="flex items-center space-x-4">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => startReply(comment.id)}
              className="h-6 px-2 text-xs"
            >
              <Reply className="h-3 w-3 mr-1" />
              Reply
            </Button>

            <Button size="sm" variant="ghost" className="h-6 px-2 text-xs">
              <ThumbsUp className="h-3 w-3 mr-1" />
              Like
            </Button>

            {comment.author?.id === currentUserId && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button size="sm" variant="ghost" className="h-6 w-6 p-0">
                    <MoreHorizontal className="h-3 w-3" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => startEdit(comment)}>
                    <Edit className="h-4 w-4 mr-2" />
                    Edit
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem 
                    onClick={() => handleDeleteComment(comment.id)}
                    className="text-destructive"
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
        </div>
      </div>
    </div>
  )

  const commentCounts = {
    total: comments.length,
    general: comments.filter(c => c.comment_type === 'general').length,
    suggestion: comments.filter(c => c.comment_type === 'suggestion').length,
    question: comments.filter(c => c.comment_type === 'question').length,
    approval: comments.filter(c => c.comment_type === 'approval').length,
  }

  return (
    <div className="space-y-6">
      {/* Header with filters */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <MessageSquare className="h-5 w-5" />
              <span>Discussion ({commentCounts.total})</span>
            </CardTitle>
            <Select value={filter} onValueChange={(value: any) => setFilter(value)}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Comments ({commentCounts.total})</SelectItem>
                <SelectItem value="general">💬 General ({commentCounts.general})</SelectItem>
                <SelectItem value="suggestion">💡 Suggestions ({commentCounts.suggestion})</SelectItem>
                <SelectItem value="question">❓ Questions ({commentCounts.question})</SelectItem>
                <SelectItem value="approval">✅ Approvals ({commentCounts.approval})</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>

        <CardContent>
          {/* New Comment Form */}
          <div className="space-y-4 p-4 bg-muted/30 rounded-lg">
            <div className="flex items-center space-x-4">
              <Avatar className="h-8 w-8">
                <AvatarFallback>You</AvatarFallback>
              </Avatar>
              <Select value={commentType} onValueChange={(value: any) => setCommentType(value)}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="general">💬 General</SelectItem>
                  <SelectItem value="suggestion">💡 Suggestion</SelectItem>
                  <SelectItem value="question">❓ Question</SelectItem>
                  <SelectItem value="approval">✅ Approval</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {replyingTo && (
              <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                <Reply className="h-4 w-4" />
                <span>Replying to comment</span>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setReplyingTo(null)}
                  className="h-5 px-2 text-xs"
                >
                  Cancel
                </Button>
              </div>
            )}

            <Textarea
              ref={textareaRef}
              placeholder="Add a comment to this review..."
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              className="min-h-[100px]"
            />

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Button size="sm" variant="outline">
                  <Paperclip className="h-4 w-4" />
                </Button>
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setNewComment('')
                    setReplyingTo(null)
                    setCommentType('general')
                  }}
                  disabled={!newComment.trim()}
                >
                  Cancel
                </Button>
                <Button
                  size="sm"
                  onClick={handleSubmitComment}
                  disabled={!newComment.trim() || isSubmitting}
                >
                  <Send className="h-4 w-4 mr-2" />
                  {isSubmitting ? 'Posting...' : 'Post Comment'}
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Comments List */}
      <div className="space-y-6">
        {filteredThreads.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <MessageSquare className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
              <h3 className="text-lg font-medium mb-2">No comments yet</h3>
              <p className="text-muted-foreground">
                {filter === 'all' 
                  ? "Be the first to start a discussion about this review"
                  : `No ${filter} comments found`
                }
              </p>
            </CardContent>
          </Card>
        ) : (
          filteredThreads.map(({ comment, replies }) => (
            <Card key={comment.id}>
              <CardContent className="p-6 space-y-4">
                <CommentItem comment={comment} />

                {/* Replies */}
                {replies.length > 0 && (
                  <div className="space-y-4">
                    {replies.map(reply => (
                      <CommentItem key={reply.id} comment={reply} isReply />
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}
