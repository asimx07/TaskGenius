"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Sparkles, Bot, Settings, AlertTriangle } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { api } from "@/libs/api"

interface CreateTaskDialogProps {
  children: React.ReactNode
  onTaskCreated: () => void
}

export function CreateTaskDialog({ children, onTaskCreated }: CreateTaskDialogProps) {
  const [open, setOpen] = useState(false)
  const [description, setDescription] = useState("")
  const [isCreating, setIsCreating] = useState(false)
  const [showManualMode, setShowManualMode] = useState(false)
  const [aiError, setAiError] = useState<string | null>(null)

  // Manual mode fields
  const [manualTitle, setManualTitle] = useState("")
  const [manualLabel, setManualLabel] = useState("personal")
  const [manualDueDate, setManualDueDate] = useState("")

  const resetForm = () => {
    setDescription("")
    setManualTitle("")
    setManualLabel("personal")
    setManualDueDate("")
    setShowManualMode(false)
    setAiError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!description.trim()) return

    try {
      setIsCreating(true)
      setAiError(null)
      await api.createTask({ description: description.trim() })
      resetForm()
      setOpen(false)
      onTaskCreated()
    } catch (error) {
      console.error("Failed to create task:", error)
      setAiError("AI processing failed. You can create the task manually below.")
      setShowManualMode(true)
      // Pre-fill manual title with description
      setManualTitle(description.substring(0, 50))
    } finally {
      setIsCreating(false)
    }
  }

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!manualTitle.trim()) return

    try {
      setIsCreating(true)
      // Create task with manual details by using a structured description
      const structuredDescription = `${description}

Manual Details:
- Title: ${manualTitle}
- Category: ${manualLabel}
${manualDueDate ? `- Due: ${new Date(manualDueDate).toLocaleString()}` : ""}`

      await api.createTask({ description: structuredDescription })
      resetForm()
      setOpen(false)
      onTaskCreated()
    } catch (error) {
      console.error("Failed to create manual task:", error)
      setAiError("Failed to create task. Please try again.")
    } finally {
      setIsCreating(false)
    }
  }

  const handleDialogClose = (isOpen: boolean) => {
    setOpen(isOpen)
    if (!isOpen) {
      resetForm()
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleDialogClose}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-md bg-gray-800 border-gray-700">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-gray-100">
            <div className="w-6 h-6 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 flex items-center justify-center">
              {showManualMode ? <Settings className="w-3 h-3 text-white" /> : <Bot className="w-3 h-3 text-white" />}
            </div>
            {showManualMode ? "Create Task Manually" : "Create New Task"}
          </DialogTitle>
        </DialogHeader>

        {!showManualMode ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="description" className="text-gray-300">
                Task Description
              </Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe your task... (e.g., 'Finish the quarterly report by Friday at 2pm')"
                className="mt-1 bg-gray-900/50 border-gray-600 text-gray-100 placeholder-gray-500 focus:border-cyan-500 focus:ring-cyan-500/20"
                rows={4}
                required
              />
              <div className="mt-2 p-3 bg-cyan-500/10 border border-cyan-500/20 rounded-lg">
                <div className="flex items-center gap-2 text-sm text-cyan-300">
                  <Sparkles className="w-4 h-4" />
                  AI Processing
                </div>
                <p className="text-xs text-gray-400 mt-1">
                  AI will automatically extract the title, due date, and category from your description.
                </p>
              </div>
            </div>

            {aiError && (
              <Alert className="bg-amber-500/10 border-amber-500/20">
                <AlertTriangle className="h-4 w-4 text-amber-400" />
                <AlertDescription className="text-amber-300">{aiError}</AlertDescription>
              </Alert>
            )}

            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => handleDialogClose(false)}
                className="border-gray-600 text-gray-300 hover:bg-gray-700"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isCreating || !description.trim()}
                className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white"
              >
                {isCreating ? (
                  <>
                    <Bot className="w-4 h-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Create Task
                  </>
                )}
              </Button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleManualSubmit} className="space-y-4">
            <div>
              <Label htmlFor="manual-title" className="text-gray-300">
                Task Title *
              </Label>
              <Input
                id="manual-title"
                value={manualTitle}
                onChange={(e) => setManualTitle(e.target.value)}
                placeholder="Enter task title"
                className="mt-1 bg-gray-900/50 border-gray-600 text-gray-100 placeholder-gray-500 focus:border-cyan-500 focus:ring-cyan-500/20"
                required
              />
            </div>

            <div>
              <Label htmlFor="manual-label" className="text-gray-300">
                Category
              </Label>
              <Select value={manualLabel} onValueChange={setManualLabel}>
                <SelectTrigger className="mt-1 bg-gray-900/50 border-gray-600 text-gray-100">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-gray-800 border-gray-700">
                  <SelectItem value="personal" className="text-gray-100">
                    Personal
                  </SelectItem>
                  <SelectItem value="work" className="text-gray-100">
                    Work
                  </SelectItem>
                  <SelectItem value="shopping" className="text-gray-100">
                    Shopping
                  </SelectItem>
                  <SelectItem value="health" className="text-gray-100">
                    Health
                  </SelectItem>
                  <SelectItem value="urgent" className="text-gray-100">
                    Urgent
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="manual-due-date" className="text-gray-300">
                Due Date (Optional)
              </Label>
              <Input
                id="manual-due-date"
                type="datetime-local"
                value={manualDueDate}
                onChange={(e) => setManualDueDate(e.target.value)}
                className="mt-1 bg-gray-900/50 border-gray-600 text-gray-100 focus:border-cyan-500 focus:ring-cyan-500/20"
              />
            </div>

            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowManualMode(false)}
                className="border-gray-600 text-gray-300 hover:bg-gray-700"
              >
                Back to AI
              </Button>
              <Button
                type="submit"
                disabled={isCreating || !manualTitle.trim()}
                className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white"
              >
                {isCreating ? (
                  <>
                    <Settings className="w-4 h-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Settings className="w-4 h-4 mr-2" />
                    Create Task
                  </>
                )}
              </Button>
            </div>
          </form>
        )}
      </DialogContent>
    </Dialog>
  )
}
