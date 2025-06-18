"use client"

import { Calendar, Clock } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface DateRangeFilterProps {
  value: string
  onChange: (value: string) => void
}

export function DateRangeFilter({ value, onChange }: DateRangeFilterProps) {
  const dateRanges = [
    { value: "all", label: "All Time", icon: Calendar },
    { value: "1d", label: "Last 24 Hours", icon: Clock },
    { value: "3d", label: "Last 3 Days", icon: Clock },
    { value: "7d", label: "Last 7 Days", icon: Clock },
    { value: "30d", label: "Last 30 Days", icon: Clock },
  ]

  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-full lg:w-48 bg-gray-900/50 border-gray-600 text-gray-100">
        
        <SelectValue placeholder="Date range" />
      </SelectTrigger>
      <SelectContent className="bg-gray-800 border-gray-700">
        {dateRanges.map((range) => {
          const Icon = range.icon
          return (
            <SelectItem key={range.value} value={range.value} className="text-gray-100">
              <div className="flex items-center gap-2">
                <Icon className="w-4 h-4 text-cyan-400" />
                {range.label}
              </div>
            </SelectItem>
          )
        })}
      </SelectContent>
    </Select>
  )
}
