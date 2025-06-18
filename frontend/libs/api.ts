interface Task {
  id: number
  title: string
  description: string
  label: string
  due_date: string | null
  created_at: string
  updated_at: string
}

interface CreateTaskRequest {
  description: string
}

interface SummaryRequest {
  start_date: string
  end_date: string
}

interface SummaryResponse {
  summary: string
  start_date: string
  end_date: string
  task_count: number
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Enhanced mock data storage with persistence
const mockTasks: Task[] = [
  {
    id: 1,
    title: "Sample Task",
    description: "This is a sample task shown when API is unavailable",
    label: "personal",
    due_date: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
]

let nextId = 2
let isUsingMockData = false
let isDemoMode = false
let demoModeReason = ""

// Demo mode management
const setDemoMode = (enabled: boolean, reason = "") => {
  isDemoMode = enabled
  demoModeReason = reason
  isUsingMockData = enabled

  if (enabled) {
    console.warn(`🔄 Entering demo mode: ${reason}`)
  } else {
    console.log("✅ Exiting demo mode")
  }
}

// Enhanced task processing for mock data
const processTaskDescription = (description: string): Partial<Task> => {
  const lowerDesc = description.toLowerCase()

  // Extract title with better processing
  let title = description.split(/[.!?]/)[0].substring(0, 50).trim()
  if (!title) title = description.substring(0, 50).trim()

  // Determine label based on keywords
  let label = "personal"
  if (
    lowerDesc.includes("work") ||
    lowerDesc.includes("meeting") ||
    lowerDesc.includes("report") ||
    lowerDesc.includes("project") ||
    lowerDesc.includes("client") ||
    lowerDesc.includes("presentation")
  ) {
    label = "work"
  } else if (
    lowerDesc.includes("buy") ||
    lowerDesc.includes("shop") ||
    lowerDesc.includes("grocery") ||
    lowerDesc.includes("purchase") ||
    lowerDesc.includes("store")
  ) {
    label = "shopping"
  } else if (
    lowerDesc.includes("doctor") ||
    lowerDesc.includes("dentist") ||
    lowerDesc.includes("health") ||
    lowerDesc.includes("appointment") ||
    lowerDesc.includes("medical") ||
    lowerDesc.includes("hospital")
  ) {
    label = "health"
  } else if (
    lowerDesc.includes("urgent") ||
    lowerDesc.includes("asap") ||
    lowerDesc.includes("immediately") ||
    lowerDesc.includes("critical") ||
    lowerDesc.includes("emergency")
  ) {
    label = "urgent"
  }

  // Extract due date with enhanced parsing
  let due_date: string | null = null
  const now = new Date()

  if (lowerDesc.includes("tomorrow")) {
    const tomorrow = new Date(now)
    tomorrow.setDate(tomorrow.getDate() + 1)
    due_date = tomorrow.toISOString()
  } else if (lowerDesc.includes("next week")) {
    const nextWeek = new Date(now)
    nextWeek.setDate(nextWeek.getDate() + 7)
    due_date = nextWeek.toISOString()
  } else if (lowerDesc.includes("friday")) {
    const friday = new Date(now)
    const daysUntilFriday = (5 - friday.getDay() + 7) % 7 || 7
    friday.setDate(friday.getDate() + daysUntilFriday)
    due_date = friday.toISOString()
  } else if (lowerDesc.includes("next month")) {
    const nextMonth = new Date(now)
    nextMonth.setMonth(nextMonth.getMonth() + 1)
    due_date = nextMonth.toISOString()
  } else if (lowerDesc.includes("monday")) {
    const monday = new Date(now)
    const daysUntilMonday = (1 - monday.getDay() + 7) % 7 || 7
    monday.setDate(monday.getDate() + daysUntilMonday)
    due_date = monday.toISOString()
  }

  return { title, label, due_date }
}

// Enhanced error handling with better fetch failure detection
const handleApiError = (error: any, operation: string, statusCode?: number): boolean => {
  console.warn(`API ${operation} failed:`, error);

  // Handle different types of errors
  const errorMessage = error?.message || error?.toString() || "";
  const errorName = error?.name || "";

  // Check for 422 errors (AI processing failures)
  if (statusCode === 422 || errorMessage.includes("422") || error?.status === 422) {
    setDemoMode(true, "AI processing temporarily unavailable (422 error)");
    return true;
  }

  // Check for fetch/network errors (common in v0 preview environment)
  if (
    errorMessage.includes("Failed to fetch") ||
    errorMessage.includes("NetworkError") ||
    errorMessage.includes("TypeError: fetch") ||
    errorMessage.includes("CORS") ||
    errorName === "AbortError" ||
    errorName === "TypeError" ||
    errorMessage.includes("ERR_NETWORK") ||
    errorMessage.includes("ERR_INTERNET_DISCONNECTED") ||
    errorMessage.includes("net::") ||
    !navigator.onLine
  ) {
    setDemoMode(true, "Backend server connection failed")
    return true
  }

  // Check for HTTP errors
  if (errorMessage.includes("HTTP") && (errorMessage.includes("500") || errorMessage.includes("503"))) {
    setDemoMode(true, "Backend server error")
    return true
  }

  // Default fallback for any other errors
  setDemoMode(true, "API temporarily unavailable")
  return true
}

// API functions with enhanced 422 error handling
export const api = {
  async getTasks(
    label?: string,
    skip = 0,
    limit = 50,
  ): Promise<{ tasks: Task[]; total: number; skip: number; limit: number }> {
    // If already in demo mode, skip API call
    if (isDemoMode) {
      console.log("📱 Using demo mode - skipping API call")
      await new Promise((resolve) => setTimeout(resolve, 300))

      let filteredTasks = [...mockTasks]
      if (label && label !== "all") {
        filteredTasks = mockTasks.filter((task) => task.label === label)
      }

      return {
        tasks: filteredTasks.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()),
        total: filteredTasks.length,
        skip: 0,
        limit: 50,
      }
    }

    try {
      const params = new URLSearchParams()
      if (label && label !== "all") params.append("label", label)
      params.append("skip", skip.toString())
      params.append("limit", limit.toString())

      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000) // Reduced timeout

      const response = await fetch(`${API_BASE_URL}/api/v1/tasks/?${params}`, {
        method: "GET",
        signal: controller.signal,
        mode: "cors",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()

      // Successfully connected - exit demo mode if we were in it
      if (isDemoMode) {
        setDemoMode(false)
      }

      return data
    } catch (error) {
      // Always handle the error and return mock data
      handleApiError(error, "getTasks")

      // Simulate API delay
      await new Promise((resolve) => setTimeout(resolve, 300))

      let filteredTasks = [...mockTasks]
      if (label && label !== "all") {
        filteredTasks = mockTasks.filter((task) => task.label === label)
      }

      return {
        tasks: filteredTasks.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()),
        total: filteredTasks.length,
        skip: 0,
        limit: 50,
      }
    }
  },

  async getTask(id: number): Promise<Task> {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000)

      const response = await fetch(`${API_BASE_URL}/api/v1/tasks/${id}`, {
        method: "GET",
        signal: controller.signal,
        mode: "cors",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      handleApiError(error, "getTask")

      const task = mockTasks.find((task) => task.id === id)
      if (!task) {
        throw new Error("Task not found")
      }
      return task
    }
  },

  async createTask(request: CreateTaskRequest): Promise<Task> {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10000)

      const response = await fetch(`${API_BASE_URL}/api/v1/tasks/`, {
        method: "POST",
        signal: controller.signal,
        mode: "cors",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        const errorText = await response.text();
        const error = new Error(`HTTP ${response.status}: ${errorText}`);
        throw error;
      }

      const newTask = await response.json();
      console.log("✅ Task created successfully:", newTask);
      return newTask;
    } catch (error) {
      const shouldUseMock = handleApiError(error, "createTask");

      if (shouldUseMock) {
        // Seamlessly integrate failed task into mock data
        console.log("🔄 Integrating failed task into demo mode...")
        await new Promise((resolve) => setTimeout(resolve, 800))

        const processed = processTaskDescription(request.description)
        const now = new Date().toISOString()

        const newTask: Task = {
          id: nextId++,
          title: processed.title || request.description.substring(0, 50),
          description: request.description,
          label: processed.label || "personal",
          due_date: processed.due_date ?? null, // Ensure it's string | null
          created_at: now,
          updated_at: now,
        };

        mockTasks.push(newTask)
        console.log("✅ Task integrated into demo mode:", newTask)
        return newTask
      }

      throw error
    }
  },

  async updateTask(id: number, request: CreateTaskRequest): Promise<Task> {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 8000)

      const response = await fetch(`${API_BASE_URL}/api/v1/tasks/${id}`, {
        method: "PUT",
        signal: controller.signal,
        mode: "cors",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        const errorText = await response.text();
        const error = new Error(`HTTP ${response.status}: ${errorText}`);
        throw error;
      }

      return await response.json();
    } catch (error) {
      const shouldUseMock = handleApiError(error, "updateTask");

      if (shouldUseMock) {
        // Seamlessly update task in mock data
        await new Promise((resolve) => setTimeout(resolve, 600))

        const taskIndex = mockTasks.findIndex((task) => task.id === id)
        if (taskIndex === -1) {
          throw new Error("Task not found")
        }

        const processed = processTaskDescription(request.description)
        const updatedTask: Task = {
          ...mockTasks[taskIndex],
          title: processed.title || request.description.substring(0, 50),
          description: request.description,
          label: processed.label || mockTasks[taskIndex].label,
          due_date: processed.due_date ?? null, // Ensure it's string | null
          updated_at: new Date().toISOString(),
        };

        mockTasks[taskIndex] = updatedTask
        console.log("✅ Task updated in demo mode:", updatedTask)
        return updatedTask
      }

      throw error
    }
  },

  async deleteTask(id: number): Promise<void> {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000)

      const response = await fetch(`${API_BASE_URL}/api/v1/tasks/${id}`, {
        method: "DELETE",
        signal: controller.signal,
        mode: "cors",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
    } catch (error) {
      handleApiError(error, "deleteTask")

      // Delete from mock data
      await new Promise((resolve) => setTimeout(resolve, 300))
      const taskIndex = mockTasks.findIndex((task) => task.id === id)
      if (taskIndex !== -1) {
        mockTasks.splice(taskIndex, 1)
        console.log("✅ Task deleted from demo mode")
      }
    }
  },

  async getLabels(): Promise<string[]> {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000)

      const response = await fetch(`${API_BASE_URL}/api/v1/tasks/labels/`, {
        method: "GET",
        signal: controller.signal,
        mode: "cors",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      handleApiError(error, "getLabels")

      await new Promise((resolve) => setTimeout(resolve, 200))
      const labels = Array.from(new Set(mockTasks.map((task) => task.label)))
      return labels.sort()
    }
  },

  async generateSummary(request: SummaryRequest): Promise<SummaryResponse> {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 15000)

      const response = await fetch(`${API_BASE_URL}/api/v1/tasks/summary`, {
        method: "POST",
        signal: controller.signal,
        mode: "cors",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        const errorText = await response.text();
        const error = new Error(`HTTP ${response.status}: ${errorText}`);
        throw error;
      }

      return await response.json();
    } catch (error) {
      handleApiError(error, "generateSummary");

      // Enhanced mock summary for demo mode
      await new Promise((resolve) => setTimeout(resolve, 2000))

      const startDate = new Date(request.start_date)
      const endDate = new Date(request.end_date)

      const tasksInRange = mockTasks.filter((task) => {
        const taskDate = new Date(task.created_at)
        return taskDate >= startDate && taskDate <= endDate
      })

      const labelCounts = tasksInRange.reduce(
        (acc, task) => {
          acc[task.label] = (acc[task.label] || 0) + 1
          return acc
        },
        {} as Record<string, number>,
      )

      const summary = `DEMO MODE ANALYSIS - AI TEMPORARILY UNAVAILABLE

Task Analysis for Selected Period:
• Total Tasks: ${tasksInRange.length}
• Categories: ${Object.keys(labelCounts).length}

Distribution:
${Object.entries(labelCounts)
  .map(([label, count]) => `• ${label.toUpperCase()}: ${count} task${count > 1 ? "s" : ""}`)
  .join("\n")}

⚠️ NOTE: This is a simplified analysis generated in demo mode. 
Full AI-powered insights will be available when the backend service is restored.

Basic Recommendations:
• Review high-priority tasks first
• Group similar tasks for efficiency
• Set realistic deadlines for pending items
• Regular task review helps maintain productivity

Demo mode provides basic task management functionality while AI services are temporarily unavailable.`

      return {
        summary,
        start_date: request.start_date,
        end_date: request.end_date,
        task_count: tasksInRange.length,
      }
    }
  },

  // Status check functions
  isUsingMockData: () => isUsingMockData,
  isDemoMode: () => isDemoMode,
  getDemoModeReason: () => demoModeReason,

  // Manual health check function
  checkHealth: async (): Promise<boolean> => {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 2000)

      const response = await fetch(`${API_BASE_URL}/health`, {
        method: "GET",
        signal: controller.signal,
        mode: "cors",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
      })

      clearTimeout(timeoutId)

      if (response.ok && isDemoMode) {
        setDemoMode(false) // Exit demo mode if health check passes
      }

      return response.ok
    } catch (error) {
      console.warn("API health check failed:", error)
      return false
    }
  },

  // Force exit demo mode (for manual retry)
  exitDemoMode: () => {
    setDemoMode(false)
  },
}

// Utility functions remain the same
export const filterTasksByDateRange = (tasks: Task[], dateRange: string): Task[] => {
  if (dateRange === "all") return tasks

  const now = new Date()
  const startDate = new Date()

  switch (dateRange) {
    case "1d":
      startDate.setDate(now.getDate() - 1)
      break
    case "3d":
      startDate.setDate(now.getDate() - 3)
      break
    case "7d":
      startDate.setDate(now.getDate() - 7)
      break
    case "30d":
      startDate.setDate(now.getDate() - 30)
      break
    default:
      return tasks
  }

  return tasks.filter((task) => {
    const taskDate = new Date(task.created_at)
    return taskDate >= startDate
  })
}

export const getDateRangeValues = (range: string): { start: string; end: string } => {
  const now = new Date()
  const end = now.toISOString().slice(0, 16)

  let start: Date

  switch (range) {
    case "1d":
      start = new Date(now.getTime() - 24 * 60 * 60 * 1000)
      break
    case "3d":
      start = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000)
      break
    case "7d":
      start = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
      break
    case "30d":
      start = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
      break
    default:
      start = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
  }

  return {
    start: start.toISOString().slice(0, 16),
    end,
  }
}
