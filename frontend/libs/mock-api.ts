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

// Mock data with more diverse timestamps for date filtering
const mockTasks: Task[] = [
  {
    id: 1,
    title: "Neural Network Optimization",
    description: "Optimize the neural network architecture for the quarterly AI performance review next Friday at 2pm",
    label: "work",
    due_date: "2025-06-27T14:00:00",
    created_at: "2025-06-18T10:30:00.000000",
    updated_at: "2025-06-18T10:30:00.000000",
  },
  {
    id: 2,
    title: "Quantum Groceries Acquisition",
    description: "Acquire organic sustenance modules and carbon-based fuel from the bio-market tomorrow morning",
    label: "shopping",
    due_date: "2025-06-19T09:00:00",
    created_at: "2025-06-17T15:45:00.000000",
    updated_at: "2025-06-17T15:45:00.000000",
  },
  {
    id: 3,
    title: "Biometric Maintenance Protocol",
    description: "Schedule bio-enhancement appointment with Dr. Smith for routine system diagnostics next month",
    label: "health",
    due_date: "2025-07-15T10:00:00",
    created_at: "2025-06-16T08:20:00.000000",
    updated_at: "2025-06-16T08:20:00.000000",
  },
  {
    id: 4,
    title: "Project Genesis Review",
    description: "Analyze the new client project proposal and provide algorithmic feedback by end of week",
    label: "work",
    due_date: "2025-06-21T17:00:00",
    created_at: "2025-06-15T14:10:00.000000",
    updated_at: "2025-06-15T14:10:00.000000",
  },
  {
    id: 5,
    title: "Memory Core Backup",
    description: "Backup personal data archives to secure cloud matrix",
    label: "personal",
    due_date: null,
    created_at: "2025-06-18T09:15:00.000000",
    updated_at: "2025-06-18T09:15:00.000000",
  },
  {
    id: 6,
    title: "System Update Protocol",
    description: "Install critical security patches for home automation network",
    label: "urgent",
    due_date: "2025-06-19T12:00:00",
    created_at: "2025-06-18T16:30:00.000000",
    updated_at: "2025-06-18T16:30:00.000000",
  },
]

let nextId = 7

// Simulate AI processing for task creation/updates
const processTaskDescription = (description: string): Partial<Task> => {
  const lowerDesc = description.toLowerCase()

  // Extract title with futuristic flair
  let title = description.split(".")[0].substring(0, 50).trim()

  // Add some futuristic terminology
  if (lowerDesc.includes("report")) title = title.replace(/report/i, "Data Analysis")
  if (lowerDesc.includes("meeting")) title = title.replace(/meeting/i, "Neural Sync")
  if (lowerDesc.includes("buy") || lowerDesc.includes("shop")) title = title.replace(/buy|shop/i, "Acquire")

  let label = "personal"
  if (
    lowerDesc.includes("work") ||
    lowerDesc.includes("meeting") ||
    lowerDesc.includes("report") ||
    lowerDesc.includes("project") ||
    lowerDesc.includes("neural") ||
    lowerDesc.includes("algorithm")
  ) {
    label = "work"
  } else if (
    lowerDesc.includes("buy") ||
    lowerDesc.includes("shop") ||
    lowerDesc.includes("grocery") ||
    lowerDesc.includes("acquire")
  ) {
    label = "shopping"
  } else if (
    lowerDesc.includes("doctor") ||
    lowerDesc.includes("dentist") ||
    lowerDesc.includes("health") ||
    lowerDesc.includes("appointment") ||
    lowerDesc.includes("bio")
  ) {
    label = "health"
  } else if (
    lowerDesc.includes("urgent") ||
    lowerDesc.includes("asap") ||
    lowerDesc.includes("immediately") ||
    lowerDesc.includes("critical")
  ) {
    label = "urgent"
  }

  // Extract due date
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
  }

  return { title, label, due_date }
}

// Mock API functions
export const mockApi = {
  async getTasks(
    label?: string,
    dateRange?: string,
  ): Promise<{ tasks: Task[]; total: number; skip: number; limit: number }> {
    await new Promise((resolve) => setTimeout(resolve, 500))

    let filteredTasks = [...mockTasks]

    // Filter by label
    if (label && label !== "all") {
      filteredTasks = filteredTasks.filter((task) => task.label === label)
    }

    // Filter by date range
    if (dateRange && dateRange !== "all") {
      const now = new Date()
      let startDate = new Date()

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
          startDate = new Date(0) // All time
      }

      filteredTasks = filteredTasks.filter((task) => {
        const taskDate = new Date(task.created_at)
        return taskDate >= startDate
      })
    }

    return {
      tasks: filteredTasks.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()),
      total: filteredTasks.length,
      skip: 0,
      limit: 50,
    }
  },

  async getTask(id: number): Promise<Task | null> {
    await new Promise((resolve) => setTimeout(resolve, 200))
    return mockTasks.find((task) => task.id === id) || null
  },

  async createTask(request: CreateTaskRequest): Promise<Task> {
    await new Promise((resolve) => setTimeout(resolve, 800))

    const processed = processTaskDescription(request.description)
    const now = new Date().toISOString()

    const newTask: Task = {
      id: nextId++,
      title: processed.title || request.description.substring(0, 50),
      description: request.description,
      label: processed.label || "personal",
      due_date: processed.due_date,
      created_at: now,
      updated_at: now,
    }

    mockTasks.push(newTask)
    return newTask
  },

  async updateTask(id: number, request: CreateTaskRequest): Promise<Task | null> {
    await new Promise((resolve) => setTimeout(resolve, 600))

    const taskIndex = mockTasks.findIndex((task) => task.id === id)
    if (taskIndex === -1) return null

    const processed = processTaskDescription(request.description)
    const updatedTask: Task = {
      ...mockTasks[taskIndex],
      title: processed.title || request.description.substring(0, 50),
      description: request.description,
      label: processed.label || mockTasks[taskIndex].label,
      due_date: processed.due_date,
      updated_at: new Date().toISOString(),
    }

    mockTasks[taskIndex] = updatedTask
    return updatedTask
  },

  async deleteTask(id: number): Promise<boolean> {
    await new Promise((resolve) => setTimeout(resolve, 300))

    const taskIndex = mockTasks.findIndex((task) => task.id === id)
    if (taskIndex === -1) return false

    mockTasks.splice(taskIndex, 1)
    return true
  },

  async getLabels(): Promise<string[]> {
    await new Promise((resolve) => setTimeout(resolve, 200))

    const labels = Array.from(new Set(mockTasks.map((task) => task.label)))
    return labels.sort()
  },

  async generateSummary(request: SummaryRequest): Promise<SummaryResponse> {
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

    const upcomingTasks = tasksInRange.filter((task) => task.due_date && new Date(task.due_date) > new Date())

    const summary = `NEURAL ANALYSIS COMPLETE
    
System has processed ${tasksInRange.length} task entities across ${Object.keys(labelCounts).length} operational categories during the specified temporal window.

TASK DISTRIBUTION MATRIX:
${Object.entries(labelCounts)
  .map(([label, count]) => `• ${label.toUpperCase()}: ${count} task${count > 1 ? "s" : ""} detected`)
  .join("\n")}

${upcomingTasks.length > 0 ? `TEMPORAL PRIORITY ALERTS: ${upcomingTasks.length} task${upcomingTasks.length > 1 ? "s" : ""} require immediate attention within deadline parameters.\n\n` : ""}OPTIMIZATION RECOMMENDATIONS:
• Prioritize high-frequency work protocols for maximum efficiency
• Implement batch processing for similar task categories
• Establish temporal boundaries for enhanced productivity cycles
• Regular system maintenance recommended for optimal performance

SYSTEM STATUS: Your neural task management matrix demonstrates balanced operational distribution across multiple life sectors. Continue current optimization protocols while maintaining focus on time-critical objectives.`

    return {
      summary,
      start_date: request.start_date,
      end_date: request.end_date,
      task_count: tasksInRange.length,
    }
  },
}
