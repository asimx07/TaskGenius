"use client"

import { useState, useEffect } from "react"
import {
  Plus,
  Search,
  Sparkles,
  Filter,
  Grid3X3,
  List,
  Calendar,
  Activity,
  Wifi,
  WifiOff,
  RefreshCw,
  AlertTriangle,
  Bot,
  Zap,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { TaskList } from "@/components/task-list"
import { TaskGrid } from "@/components/task-grid"
import { TaskSummary } from "@/components/task-summary"
import { CreateTaskDialog } from "@/components/create-task-dialog"
import { CharacterAvatar } from "@/components/character-avatar"
import { DateRangeFilter } from "@/components/date-range-filter"
import { api, filterTasksByDateRange } from "@/libs/api"

interface Task {
  id: number
  title: string
  description: string
  label: string
  due_date: string | null
  created_at: string
  updated_at: string
}

export default function TaskGenius() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [allTasks, setAllTasks] = useState<Task[]>([])
  const [labels, setLabels] = useState<string[]>([])
  const [selectedLabel, setSelectedLabel] = useState<string>("all")
  const [selectedDateRange, setSelectedDateRange] = useState<string>("all")
  const [searchQuery, setSearchQuery] = useState("")
  const [viewMode, setViewMode] = useState<"list" | "grid">("grid")
  const [isLoading, setIsLoading] = useState(true)
  const [isDemoMode, setIsDemoMode] = useState(false)
  const [demoModeReason, setDemoModeReason] = useState("")
  const [isCheckingConnection, setIsCheckingConnection] = useState(false)

  useEffect(() => {
    fetchTasks()
    fetchLabels()
  }, [selectedLabel])

  useEffect(() => {
    const filtered = filterTasksByDateRange(allTasks, selectedDateRange)
    setTasks(filtered)
  }, [selectedDateRange, allTasks])

  const fetchTasks = async () => {
    try {
      setIsLoading(true)
      console.log("🔄 Fetching tasks...")

      const data = await api.getTasks(selectedLabel !== "all" ? selectedLabel : undefined)
      setAllTasks(data.tasks || [])
      setTasks(data.tasks || [])

      // Update demo mode status
      setIsDemoMode(api.isDemoMode())
      setDemoModeReason(api.getDemoModeReason())

      if (!api.isDemoMode()) {
        console.log("✅ Connected to backend API successfully")
      } else {
        console.log("📱 Running in demo mode:", api.getDemoModeReason())
      }
    } catch (error) {
      // This should rarely happen now since API functions handle their own errors
      console.error("❌ Unexpected error in fetchTasks:", error)
      setIsDemoMode(true)
      setDemoModeReason("Unexpected error occurred")
    } finally {
      setIsLoading(false)
    }
  }

  const fetchLabels = async () => {
    try {
      const data = await api.getLabels()
      setLabels(data)
    } catch (error) {
      console.error("Failed to fetch labels:", error)
    }
  }

  const handleRetryConnection = async () => {
    setIsCheckingConnection(true)
    console.log("🔄 Manually checking API connection...")

    try {
      // Force exit demo mode and try health check
      api.exitDemoMode()
      const isHealthy = await api.checkHealth()

      if (isHealthy) {
        console.log("✅ API is healthy, refreshing data...")
        await fetchTasks()
        await fetchLabels()
        setIsDemoMode(false)
        setDemoModeReason("")
      } else {
        console.log("❌ API health check failed")
        setIsDemoMode(true)
        setDemoModeReason("Backend server unavailable")
      }
    } catch (error) {
      console.error("Connection check failed:", error)
      setIsDemoMode(true)
      setDemoModeReason("Connection check failed")
    } finally {
      setIsCheckingConnection(false)
    }
  }

  const filteredTasks = tasks.filter(
    (task) =>
      task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      task.description.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  const handleTaskCreated = () => {
    fetchTasks()
    fetchLabels()
    // Update demo mode status after task creation
    setIsDemoMode(api.isDemoMode())
    setDemoModeReason(api.getDemoModeReason())
  }

  const handleTaskUpdated = () => {
    fetchTasks()
    setIsDemoMode(api.isDemoMode())
    setDemoModeReason(api.getDemoModeReason())
  }

  const handleTaskDeleted = () => {
    fetchTasks()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-800">
      {/* Animated background grid */}
      <div className="fixed inset-0 bg-[linear-gradient(rgba(0,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(0,255,255,0.03)_1px,transparent_1px)] bg-[size:50px_50px] animate-pulse"></div>

      <div className="relative z-10 container mx-auto px-4 py-8 max-w-7xl">
        {/* Enhanced Demo Mode Alert */}
        {isDemoMode && (
          <Alert className="mb-6 bg-gradient-to-r from-amber-500/10 to-orange-500/10 border-amber-500/30 text-amber-300 shadow-lg">
            <div className="flex items-center gap-2">
              <div className="relative">
                <Bot className="h-5 w-5 text-amber-400" />
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
              </div>
              <Zap className="h-4 w-4 text-amber-400 animate-pulse" />
            </div>
            <AlertDescription className="flex items-center justify-between">
              <div>
                <div className="font-semibold text-amber-200 mb-1">🤖 AI Demo Mode Active</div>
                <div className="text-sm">
                  <strong>Reason:</strong> {demoModeReason}
                  <br />
                  <span className="text-amber-400">
                    Your tasks are being processed with basic AI simulation. Full AI features will restore automatically
                    when the backend reconnects.
                  </span>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRetryConnection}
                disabled={isCheckingConnection}
                className="ml-4 border-amber-500/30 text-amber-300 hover:bg-amber-500/10 bg-amber-500/5"
              >
                {isCheckingConnection ? (
                  <RefreshCw className="h-3 w-3 animate-spin" />
                ) : (
                  <RefreshCw className="h-3 w-3" />
                )}
                Retry Connection
              </Button>
            </AlertDescription>
          </Alert>
        )}

        {/* Connection Status Alert (for non-demo mode failures) */}
        {!isDemoMode && api.isUsingMockData() && (
          <Alert className="mb-6 bg-red-500/10 border-red-500/20 text-red-300">
            <WifiOff className="h-4 w-4" />
            <AlertDescription className="flex items-center justify-between">
              <span>
                Unable to connect to API server at localhost:8000. Using offline mode.
                <br />
                <span className="text-xs text-red-400 mt-1 block">
                  Check: 1) Backend server is running, 2) CORS is configured, 3) No firewall blocking localhost:8000
                </span>
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRetryConnection}
                disabled={isCheckingConnection}
                className="ml-4 border-red-500/30 text-red-300 hover:bg-red-500/10"
              >
                {isCheckingConnection ? (
                  <RefreshCw className="h-3 w-3 animate-spin" />
                ) : (
                  <RefreshCw className="h-3 w-3" />
                )}
                Retry
              </Button>
            </AlertDescription>
          </Alert>
        )}

        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-6">
              <CharacterAvatar />
              <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 bg-clip-text text-transparent">
                  TaskGenius
                </h1>
                <div className="flex items-center gap-2 mt-2">
                  <p className="text-gray-400">AI-powered task management system</p>
                  {isDemoMode ? (
                    <div className="flex items-center gap-1 text-amber-400 text-sm">
                      <Bot className="w-3 h-3" />
                      <span className="relative">
                        AI Demo Mode
                        <div className="absolute -top-1 -right-1 w-2 h-2 bg-amber-400 rounded-full animate-ping"></div>
                      </span>
                    </div>
                  ) : api.isUsingMockData() ? (
                    <div className="flex items-center gap-1 text-red-400 text-sm">
                      <WifiOff className="w-3 h-3" />
                      Offline Mode
                    </div>
                  ) : (
                    <div className="flex items-center gap-1 text-green-400 text-sm">
                      <Wifi className="w-3 h-3" />
                      Connected
                    </div>
                  )}
                </div>
              </div>
            </div>
            <CreateTaskDialog onTaskCreated={handleTaskCreated}>
              <Button className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white border-0 shadow-lg shadow-cyan-500/25">
                <Plus className="w-4 h-4 mr-2" />
                New Task
              </Button>
            </CreateTaskDialog>
          </div>

          {/* Control Panel */}
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6 mb-6">
            <div className="flex flex-col lg:flex-row gap-4 mb-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Search tasks..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 bg-gray-900/50 border-gray-600 text-gray-100 placeholder-gray-500 focus:border-cyan-500 focus:ring-cyan-500/20"
                />
              </div>

              <Select value={selectedLabel} onValueChange={setSelectedLabel}>
                <SelectTrigger className="w-full lg:w-48 bg-gray-900/50 border-gray-600 text-gray-100">
                  <Filter className="w-4 h-4 mr-2 text-cyan-400" />
                  <SelectValue placeholder="Filter by label" />
                </SelectTrigger>
                <SelectContent className="bg-gray-800 border-gray-700">
                  <SelectItem value="all" className="text-gray-100">
                    All Labels
                  </SelectItem>
                  {labels.map((label) => (
                    <SelectItem key={label} value={label} className="text-gray-100">
                      {label.charAt(0).toUpperCase() + label.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <DateRangeFilter value={selectedDateRange} onChange={setSelectedDateRange} />
            </div>

            {/* View Controls */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-400">View:</span>
                <div className="flex bg-gray-900/50 rounded-lg p-1 border border-gray-700">
                  <Button
                    variant={viewMode === "grid" ? "default" : "ghost"}
                    size="sm"
                    onClick={() => setViewMode("grid")}
                    className={viewMode === "grid" ? "bg-cyan-600 text-white" : "text-gray-400 hover:text-gray-200"}
                  >
                    <Grid3X3 className="w-4 h-4" />
                  </Button>
                  <Button
                    variant={viewMode === "list" ? "default" : "ghost"}
                    size="sm"
                    onClick={() => setViewMode("list")}
                    className={viewMode === "list" ? "bg-cyan-600 text-white" : "text-gray-400 hover:text-gray-200"}
                  >
                    <List className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              <div className="flex items-center gap-4">
                {isDemoMode && (
                  <div className="flex items-center gap-1 text-xs text-amber-400 bg-amber-500/10 px-2 py-1 rounded-full border border-amber-500/20">
                    <AlertTriangle className="w-3 h-3" />
                    Demo Mode
                  </div>
                )}
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <Activity className="w-4 h-4 text-cyan-400" />
                  {filteredTasks.length} Tasks
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <Tabs defaultValue="tasks" className="w-full">
          <TabsList className="grid w-full grid-cols-2 mb-8 bg-gray-800/50 border border-gray-700/50">
            <TabsTrigger
              value="tasks"
              className="flex items-center gap-2 data-[state=active]:bg-cyan-600 data-[state=active]:text-white text-gray-400"
            >
              <Calendar className="w-4 h-4" />
              Tasks
            </TabsTrigger>
            <TabsTrigger
              value="summary"
              className="flex items-center gap-2 data-[state=active]:bg-cyan-600 data-[state=active]:text-white text-gray-400"
            >
              <Sparkles className="w-4 h-4" />
              Summary
              {isDemoMode && <div className="w-2 h-2 bg-amber-400 rounded-full animate-pulse ml-1"></div>}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="tasks">
            {viewMode === "grid" ? (
              <TaskGrid
                tasks={filteredTasks}
                isLoading={isLoading}
                onTaskUpdated={handleTaskUpdated}
                onTaskDeleted={handleTaskDeleted}
              />
            ) : (
              <TaskList
                tasks={filteredTasks}
                isLoading={isLoading}
                onTaskUpdated={handleTaskUpdated}
                onTaskDeleted={handleTaskDeleted}
              />
            )}
          </TabsContent>

          <TabsContent value="summary">
            <TaskSummary />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
