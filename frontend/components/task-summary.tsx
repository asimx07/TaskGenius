"use client"

import { useState } from "react"
import { Calendar, Sparkles, TrendingUp, Bot, Activity } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { api, getDateRangeValues } from "@/libs/api"

interface SummaryData {
  summary: string
  start_date: string
  end_date: string
  task_count: number
}

export function TaskSummary() {
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")
  const [summaryData, setSummaryData] = useState<SummaryData | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)

  const handleQuickRange = (range: string) => {
    if (range === "custom") return

    const { start, end } = getDateRangeValues(range)
    setStartDate(start)
    setEndDate(end)
  }

  const handleGenerateSummary = async () => {
    if (!startDate || !endDate) return

    try {
      setIsGenerating(true)
      const data = await api.generateSummary({
        start_date: new Date(startDate).toISOString(),
        end_date: new Date(endDate).toISOString(),
      })
      setSummaryData(data)
    } catch (error) {
      console.error("Failed to generate summary:", error)
    } finally {
      setIsGenerating(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
    })
  }

  return (
    <div className="space-y-6">
      <Card className="bg-gray-800/50 border-gray-700/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-gray-100">
            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 flex items-center justify-center">
              <Bot className="w-4 h-4 text-white" />
            </div>
            Task Summary Generator
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Quick Range Selector */}
          <div>
            <Label className="text-gray-300">Quick Date Range</Label>
            <Select onValueChange={handleQuickRange}>
              <SelectTrigger className="mt-1 bg-gray-900/50 border-gray-600 text-gray-100">
                <SelectValue placeholder="Select a quick range or set custom dates" />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-700">
                <SelectItem value="1d" className="text-gray-100">
                  Last 24 Hours
                </SelectItem>
                <SelectItem value="3d" className="text-gray-100">
                  Last 3 Days
                </SelectItem>
                <SelectItem value="7d" className="text-gray-100">
                  Last 7 Days
                </SelectItem>
                <SelectItem value="30d" className="text-gray-100">
                  Last 30 Days
                </SelectItem>
                <SelectItem value="custom" className="text-gray-100">
                  Custom Range
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="start-date" className="text-gray-300">
                Start Date & Time
              </Label>
              <Input
                id="start-date"
                type="datetime-local"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="mt-1 bg-gray-900/50 border-gray-600 text-gray-100"
              />
            </div>
            <div>
              <Label htmlFor="end-date" className="text-gray-300">
                End Date & Time
              </Label>
              <Input
                id="end-date"
                type="datetime-local"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="mt-1 bg-gray-900/50 border-gray-600 text-gray-100"
              />
            </div>
          </div>
          <Button
            onClick={handleGenerateSummary}
            disabled={!startDate || !endDate || isGenerating}
            className="w-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700"
          >
            {isGenerating ? (
              <>
                <Bot className="w-4 h-4 mr-2 animate-spin" />
                Generating Summary...
              </>
            ) : (
              <>
                <TrendingUp className="w-4 h-4 mr-2" />
                Generate Summary
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {summaryData && (
        <Card className="bg-gray-800/50 border-gray-700/50">
          <CardHeader>
            <CardTitle className="flex items-center justify-between text-gray-100">
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-cyan-400" />
                Task Summary Report
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <Calendar className="w-4 h-4" />
                {formatDate(summaryData.start_date)} - {formatDate(summaryData.end_date)}
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-6">
              <div className="inline-flex items-center px-4 py-2 rounded-full bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-500/30">
                <Sparkles className="w-4 h-4 text-cyan-400 mr-2" />
                <span className="text-cyan-300 text-sm">
                  {summaryData.task_count} Task{summaryData.task_count === 1 ? "" : "s"} Analyzed
                </span>
              </div>
            </div>
            <div className="bg-gray-900/50 rounded-lg p-6 border border-gray-700/50">
              <p className="text-gray-300 leading-relaxed whitespace-pre-wrap">{summaryData.summary}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {!summaryData && (
        <Card className="text-center py-16 bg-gray-800/30 border-gray-700/50">
          <CardContent>
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-cyan-500/20 to-blue-500/20 flex items-center justify-center">
              <Sparkles className="w-8 h-8 text-cyan-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-100 mb-2">AI Task Analysis</h3>
            <p className="text-gray-400 max-w-md mx-auto">
              Select a date range to generate intelligent insights about your task patterns and productivity trends.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
