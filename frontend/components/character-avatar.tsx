"use client"

import { useState, useEffect } from "react"
import { Bot } from "lucide-react"

export function CharacterAvatar() {
  const [isActive, setIsActive] = useState(false)
  const [eyeGlow, setEyeGlow] = useState(false)

  useEffect(() => {
    const interval = setInterval(() => {
      setEyeGlow((prev) => !prev)
    }, 2000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div
      className="relative group cursor-pointer"
      onMouseEnter={() => setIsActive(true)}
      onMouseLeave={() => setIsActive(false)}
    >
      {/* Main Avatar Container */}
      <div className="relative w-16 h-16 rounded-full bg-gradient-to-br from-gray-800 to-black border-2 border-cyan-500/50 shadow-lg shadow-cyan-500/25 transition-all duration-300 hover:shadow-cyan-500/50 hover:border-cyan-400">
        {/* Inner Glow */}
        <div className="absolute inset-1 rounded-full bg-gradient-to-br from-cyan-900/30 to-blue-900/30 animate-pulse"></div>

        {/* Face Elements */}
        <div className="absolute inset-0 flex items-center justify-center">
          {/* Eyes */}
          <div className="flex gap-2">
            <div
              className={`w-2 h-2 rounded-full transition-all duration-300 ${
                eyeGlow ? "bg-cyan-400 shadow-lg shadow-cyan-400/50" : "bg-cyan-600"
              }`}
            ></div>
            <div
              className={`w-2 h-2 rounded-full transition-all duration-300 ${
                eyeGlow ? "bg-cyan-400 shadow-lg shadow-cyan-400/50" : "bg-cyan-600"
              }`}
            ></div>
          </div>
        </div>

        {/* Activity Pattern */}
        <div className="absolute inset-0 rounded-full overflow-hidden">
          <div className="absolute top-2 left-2 w-1 h-1 bg-cyan-400/30 rounded-full animate-ping"></div>
          <div
            className="absolute bottom-3 right-2 w-1 h-1 bg-blue-400/30 rounded-full animate-ping"
            style={{ animationDelay: "0.5s" }}
          ></div>
          <div
            className="absolute top-4 right-3 w-1 h-1 bg-purple-400/30 rounded-full animate-ping"
            style={{ animationDelay: "1s" }}
          ></div>
        </div>

        {/* Hover Effect - Circuit Lines */}
        <div
          className={`absolute inset-0 rounded-full transition-opacity duration-300 ${
            isActive ? "opacity-100" : "opacity-0"
          }`}
        >
          <div className="absolute top-1/2 left-0 w-full h-px bg-gradient-to-r from-transparent via-cyan-400 to-transparent"></div>
          <div className="absolute top-0 left-1/2 w-px h-full bg-gradient-to-b from-transparent via-cyan-400 to-transparent"></div>
        </div>
      </div>

      {/* Status Indicators */}
      <div className="absolute -bottom-1 -right-1 flex gap-1">
        <div className="w-3 h-3 rounded-full bg-green-500 border-2 border-gray-900 animate-pulse"></div>
      </div>

      {/* Tooltip */}
      <div
        className={`absolute -top-12 left-1/2 transform -translate-x-1/2 px-3 py-1 bg-gray-800 text-cyan-400 text-xs rounded-lg border border-cyan-500/30 transition-all duration-300 ${
          isActive ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2 pointer-events-none"
        }`}
      >
        <div className="flex items-center gap-1">
          <Bot className="w-3 h-3" />
          TGM Online
        </div>
        <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-800"></div>
      </div>

      {/* Scanning Effect */}
      <div
        className={`absolute inset-0 rounded-full border-2 border-cyan-400/50 transition-all duration-1000 ${
          isActive ? "scale-150 opacity-0" : "scale-100 opacity-100"
        }`}
      ></div>
    </div>
  )
}
