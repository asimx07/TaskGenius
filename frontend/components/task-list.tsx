"use client"

import { useState } from "react"
import { Calendar, Clock, Edit2, Trash2, Tag, Hash } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { api } from "@/libs/api"

interface Task {
  id: number
  title: string
  description: string
  label: string
  due_date: string | null
  created_at: string
  updated_at: string
}

interface TaskListProps {
  tasks: Task[]
  isLoading: boolean
  onTaskUpdated: () => void
  onTaskDeleted: () => void
}

export function TaskList({ tasks, isLoading, onTaskUpdated, onTaskDeleted }: TaskListProps) {
  const [editingTask, setEditingTask] = useState<Task | null>(null)
  const [editDescription, setEditDescription] = useState("")
  const [isUpdating, setIsUpdating] = useState(false)
  const [isDeleting, setIsDeleting] = useState<number | null>(null)

  const formatDate = (dateString: string | null) => {
    if (!dateString) return null
    const date = new Date(dateString)
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  const getLabelColor = (label: string) => {
    const colors: Record<string, string> = {
      work: "bg-blue-500/20 text-blue-300 border-blue-500/30",
      personal: "bg-green-500/20 text-green-300 border-green-500/30",
      shopping: "bg-purple-500/20 text-purple-300 border-purple-500/30",
      health: "bg-red-500/20 text-red-300 border-red-500/30",
      urgent: "bg-orange-500/20 text-orange-300 border-orange-500/30",
      default: "bg-gray-500/20 text-gray-300 border-gray-500/30",
    }
    return colors[label] || colors.default
  }

  const handleEdit = (task: Task) => {
    setEditingTask(task)
    setEditDescription(task.description)
  }

  const handleUpdate = async () => {
    if (!editingTask) return

    try {
      setIsUpdating(true)
      await api.updateTask(editingTask.id, { description: editDescription })
      setEditingTask(null)
      onTaskUpdated()
    } catch (error) {
      console.error("Failed to update task:", error)
    } finally {
      setIsUpdating(false)
    }
  }

  const handleDelete = async (taskId: number) => {
    try {
      setIsDeleting(taskId)
      await api.deleteTask(taskId)
      onTaskDeleted()
    } catch (error) {
      console.error("Failed to delete task:", error)
    } finally {
      setIsDeleting(null)
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <Card key={i} className="animate-pulse bg-gray-800/50 border-gray-700/50">
            <CardContent className="p-6">
              <div className="h-4 bg-gray-700 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-700 rounded w-1/2 mb-4"></div>
              <div className="flex gap-2">
                <div className="h-6 bg-gray-700 rounded w-16"></div>
                <div className="h-6 bg-gray-700 rounded w-20"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (tasks.length === 0) {
    return (
      <Card className="text-center py-16 bg-gray-800/30 border-gray-700/50">
        <CardContent>
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-cyan-500/20 to-blue-500/20 flex items-center justify-center">
            <Tag className="w-8 h-8 text-cyan-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-100 mb-2">No Tasks Found</h3>
          <p className="text-gray-400">Create your first task to get started</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <>
      <div className="space-y-4">
        {tasks.map((task) => (
          <Card
            key={task.id}
            className="group hover:shadow-xl hover:shadow-cyan-500/10 transition-all duration-300 bg-gray-800/50 border-gray-700/50 hover:border-cyan-500/30 hover:bg-gray-800/70"
          >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-semibold text-gray-100 group-hover:text-cyan-300 transition-colors">
                      {task.title}
                    </h3>
                    <div className="flex items-center gap-1 text-xs text-gray-500">
                      <Hash className="w-3 h-3 text-cyan-400" />
                      {task.id}
                    </div>
                  </div>
                  <p className="text-gray-400 text-sm mb-4 leading-relaxed">{task.description}</p>

                  <div className="flex flex-wrap items-center gap-3">
                    <Badge variant="outline" className={getLabelColor(task.label)}>
                      <Tag className="w-3 h-3 mr-1" />
                      {task.label}
                    </Badge>

                    {task.due_date && (
                      <div className="flex items-center text-sm text-cyan-400">
                        <Calendar className="w-4 h-4 mr-1" />
                        {formatDate(task.due_date)}
                      </div>
                    )}

                    <div className="flex items-center text-sm text-gray-500">
                      <Clock className="w-4 h-4 mr-1" />
                      {formatDate(task.created_at)}
                    </div>

                    <div className="ml-auto flex items-center gap-1">
                      <div
                        className={`w-2 h-2 rounded-full animate-pulse ${
                          task.due_date && new Date(task.due_date) < new Date() ? "bg-red-500" : "bg-green-500"
                        }`}
                      ></div>
                      <span
                        className={`text-xs ${
                          task.due_date && new Date(task.due_date) < new Date() ? "text-red-400" : "text-gray-500"
                        }`}
                      >
                        {task.due_date && new Date(task.due_date) < new Date() ? "OVERDUE" : "ACTIVE"}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 ml-4 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleEdit(task)}
                    className="text-gray-500 hover:text-cyan-400"
                  >
                    <Edit2 className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(task.id)}
                    disabled={isDeleting === task.id}
                    className="text-gray-500 hover:text-red-400"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Edit Task Dialog */}
      <Dialog open={!!editingTask} onOpenChange={() => setEditingTask(null)}>
        <DialogContent className="sm:max-w-md bg-gray-800 border-gray-700">
          <DialogHeader>
            <DialogTitle className="text-gray-100">Edit Task</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="description" className="text-gray-300">
                Task Description
              </Label>
              <Textarea
                id="description"
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                placeholder="Update task description..."
                className="mt-1 bg-gray-900/50 border-gray-600 text-gray-100 placeholder-gray-500"
                rows={4}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setEditingTask(null)} className="border-gray-600 text-gray-300">
                Cancel
              </Button>
              <Button
                onClick={handleUpdate}
                disabled={isUpdating}
                className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700"
              >
                {isUpdating ? "Updating..." : "Update Task"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
