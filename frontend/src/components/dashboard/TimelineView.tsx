'use client'

import { useState, useEffect, useMemo } from 'react'
import { Clock, GitCommit, User, Filter, Calendar, ChevronDown, ChevronUp, BarChart3, TrendingUp, Activity } from 'lucide-react'

interface TimelineViewProps {
  commits: CommitData[]
  milestones?: MilestoneData[]
}

interface MilestoneData {
  name: string
  description: string
  date: string
  type: string
  version?: string
}

interface CommitData {
  sha: string
  message: string
  author_name?: string
  timestamp: string
  feature_summary?: string
  business_impact?: string
}

interface TimelineGroup {
  date: string
  commits: CommitData[]
  uniqueAuthors: string[]
}

interface MonthlyData {
  month: string
  year: number
  commits: CommitData[]
  totalCommits: number
  uniqueAuthors: string[]
  additions: number
  deletions: number
  businessImpacts: string[]
  mostActiveDay: string
}

interface ActivityHeatmapData {
  month: string
  commitCount: number
  intensity: number
}

export function TimelineView({ commits, milestones = [] }: TimelineViewProps) {
  const [filterAuthor, setFilterAuthor] = useState<string>('all')
  const [dateRange, setDateRange] = useState<'all' | '7d' | '30d' | '90d'>('all')
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set())
  const [viewMode, setViewMode] = useState<'daily' | 'monthly' | 'heatmap'>('daily')

  // Filter commits based on author and date range
  const filteredCommits = useMemo(() => {
    let filtered = commits

    if (filterAuthor !== 'all') {
      filtered = filtered.filter(commit => commit.author_name === filterAuthor)
    }

    if (dateRange !== 'all') {
      const now = new Date()
      const cutoffDate = new Date()
      
      switch (dateRange) {
        case '7d':
          cutoffDate.setDate(now.getDate() - 7)
          break
        case '30d':
          cutoffDate.setDate(now.getDate() - 30)
          break
        case '90d':
          cutoffDate.setDate(now.getDate() - 90)
          break
      }
      
      filtered = filtered.filter(commit => new Date(commit.timestamp) >= cutoffDate)
    }

    return filtered
  }, [commits, filterAuthor, dateRange])

  // Group commits by date
  const timelineGroups = useMemo(() => {
    const groups = new Map<string, TimelineGroup>()

    filteredCommits.forEach(commit => {
      const date = new Date(commit.timestamp).toDateString()
      
      if (!groups.has(date)) {
        groups.set(date, {
          date,
          commits: [],
          uniqueAuthors: []
        })
      }

      const group = groups.get(date)!
      group.commits.push(commit)
      
      if (commit.author_name && !group.uniqueAuthors.includes(commit.author_name)) {
        group.uniqueAuthors.push(commit.author_name)
      }
    })

    return Array.from(groups.values()).sort((a, b) => 
      new Date(b.date).getTime() - new Date(a.date).getTime()
    )
  }, [filteredCommits])

  const uniqueAuthors = useMemo(() => {
    const authors = new Set(commits.map(commit => commit.author_name).filter(Boolean))
    return Array.from(authors).sort()
  }, [commits])

  // Group commits by month for monthly summary
  const monthlyData = useMemo(() => {
    const monthlyMap = new Map<string, MonthlyData>()

    filteredCommits.forEach(commit => {
      const date = new Date(commit.timestamp)
      const monthKey = `${date.getFullYear()}-${date.getMonth()}`
      const monthName = date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })

      if (!monthlyMap.has(monthKey)) {
        monthlyMap.set(monthKey, {
          month: monthName,
          year: date.getFullYear(),
          commits: [],
          totalCommits: 0,
          uniqueAuthors: [],
          additions: 0,
          deletions: 0,
          businessImpacts: [],
          mostActiveDay: ''
        })
      }

      const monthData = monthlyMap.get(monthKey)!
      monthData.commits.push(commit)
      monthData.totalCommits++
      
      if (commit.author_name && !monthData.uniqueAuthors.includes(commit.author_name)) {
        monthData.uniqueAuthors.push(commit.author_name)
      }

      if (commit.business_impact && !monthData.businessImpacts.includes(commit.business_impact)) {
        monthData.businessImpacts.push(commit.business_impact)
      }
    })

    // Calculate most active day for each month
    monthlyMap.forEach(monthData => {
      const dayCount = new Map<string, number>()
      monthData.commits.forEach(commit => {
        const day = new Date(commit.timestamp).toLocaleDateString('en-US', { weekday: 'long' })
        dayCount.set(day, (dayCount.get(day) || 0) + 1)
      })
      
      let maxCount = 0
      monthData.mostActiveDay = 'None'
      dayCount.forEach((count, day) => {
        if (count > maxCount) {
          maxCount = count
          monthData.mostActiveDay = day
        }
      })
    })

    return Array.from(monthlyMap.values()).sort((a, b) => b.year - a.year)
  }, [filteredCommits])

  // Generate activity heatmap data
  const heatmapData = useMemo(() => {
    const monthlyCommits = new Map<string, number>()
    
    commits.forEach(commit => {
      const date = new Date(commit.timestamp)
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
      monthlyCommits.set(monthKey, (monthlyCommits.get(monthKey) || 0) + 1)
    })

    const maxCommits = Math.max(...Array.from(monthlyCommits.values()), 1)
    const heatmapArray: ActivityHeatmapData[] = []
    
    const startDate = new Date()
    startDate.setMonth(startDate.getMonth() - 11)
    
    for (let i = 0; i < 12; i++) {
      const date = new Date(startDate)
      date.setMonth(startDate.getMonth() + i)
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
      const commitCount = monthlyCommits.get(monthKey) || 0
      
      heatmapArray.push({
        month: date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
        commitCount,
        intensity: Math.round((commitCount / maxCommits) * 4)
      })
    }
    
    return heatmapArray
  }, [commits])

  const toggleGroupExpansion = (date: string) => {
    const newExpanded = new Set(expandedGroups)
    if (newExpanded.has(date)) {
      newExpanded.delete(date)
    } else {
      newExpanded.add(date)
    }
    setExpandedGroups(newExpanded)
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const today = new Date()
    const yesterday = new Date()
    yesterday.setDate(today.getDate() - 1)

    if (date.toDateString() === today.toDateString()) {
      return 'Today'
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday'
    } else {
      return date.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    }
  }

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getBusinessImpactColor = (impact: string) => {
    if (impact?.toLowerCase().includes('feature')) return 'bg-blue-100 text-blue-800'
    if (impact?.toLowerCase().includes('bug')) return 'bg-red-100 text-red-800'
    if (impact?.toLowerCase().includes('enhancement')) return 'bg-green-100 text-green-800'
    if (impact?.toLowerCase().includes('refactor')) return 'bg-purple-100 text-purple-800'
    return 'bg-gray-100 text-gray-800'
  }


  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 flex items-center space-x-2">
              <Clock className="w-6 h-6 text-purple-600" />
              <span>Development Timeline</span>
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Chronological view of repository changes and development activity
            </p>
          </div>
          
          {/* View Mode Toggles and Filters */}
          <div className="flex flex-wrap items-center space-x-4">
            {/* View Mode */}
            <div className="flex items-center bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('daily')}
                className={`flex items-center space-x-1 px-3 py-1 rounded-md text-sm transition-colors ${
                  viewMode === 'daily' ? 'bg-white text-purple-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Clock className="w-4 h-4" />
                <span>Daily</span>
              </button>
              <button
                onClick={() => setViewMode('monthly')}
                className={`flex items-center space-x-1 px-3 py-1 rounded-md text-sm transition-colors ${
                  viewMode === 'monthly' ? 'bg-white text-purple-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <BarChart3 className="w-4 h-4" />
                <span>Monthly</span>
              </button>
              <button
                onClick={() => setViewMode('heatmap')}
                className={`flex items-center space-x-1 px-3 py-1 rounded-md text-sm transition-colors ${
                  viewMode === 'heatmap' ? 'bg-white text-purple-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Activity className="w-4 h-4" />
                <span>Heatmap</span>
              </button>
            </div>

            <div className="flex items-center space-x-2">
              <User className="w-4 h-4 text-gray-500" />
              <select
                value={filterAuthor}
                onChange={(e) => setFilterAuthor(e.target.value)}
                className="text-sm border border-gray-300 rounded-lg px-3 py-1 focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="all">All Authors</option>
                {uniqueAuthors.map(author => (
                  <option key={author} value={author}>
                    {author}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="flex items-center space-x-2">
              <Calendar className="w-4 h-4 text-gray-500" />
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value as any)}
                className="text-sm border border-gray-300 rounded-lg px-3 py-1 focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="all">All Time</option>
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
                <option value="90d">Last 90 Days</option>
              </select>
            </div>
          </div>
        </div>
        
        {/* Stats */}
        <div className="mt-4 flex flex-wrap gap-4 text-sm text-gray-600">
          <span>Showing: {filteredCommits.length} commits</span>
          <span>Groups: {timelineGroups.length} days</span>
          <span>Total: {commits.length} commits</span>
        </div>
      </div>

      {/* Content based on view mode */}
      <div className="p-6">
        {viewMode === 'daily' && (
          <>
            {timelineGroups.length === 0 ? (
              <div className="text-center py-12">
                <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No commits found for the selected filters</p>
              </div>
            ) : (
              <div className="space-y-6">
                {timelineGroups.map((group) => (
                  <div key={group.date} className="relative">
                    {/* Date Header */}
                    <div 
                      className="flex items-center justify-between cursor-pointer bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors"
                      onClick={() => toggleGroupExpansion(group.date)}
                    >
                      <div className="flex items-center space-x-3">
                        <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                        <div>
                          <h3 className="font-medium text-gray-900">{formatDate(group.date)}</h3>
                          <p className="text-sm text-gray-500">
                            {group.commits.length} commit{group.commits.length > 1 ? 's' : ''} • 
                            {group.uniqueAuthors.length} author{group.uniqueAuthors.length > 1 ? 's' : ''}
                          </p>
                        </div>
                      </div>
                      {expandedGroups.has(group.date) ? (
                        <ChevronUp className="w-5 h-5 text-gray-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-gray-400" />
                      )}
                    </div>

                    {/* Commits */}
                    {expandedGroups.has(group.date) && (
                      <div className="ml-6 mt-4 space-y-4 border-l-2 border-gray-200 pl-6">
                        {group.commits.map((commit) => (
                          <div key={commit.sha} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center space-x-2 mb-2">
                                  <GitCommit className="w-4 h-4 text-blue-500" />
                                  <code className="text-sm bg-gray-100 px-2 py-1 rounded font-mono">
                                    {commit.sha.slice(0, 8)}
                                  </code>
                                  <span className="text-sm text-gray-500">{formatTime(commit.timestamp)}</span>
                                </div>
                                
                                <h4 className="font-medium text-gray-900 mb-2">
                                  {commit.message.split('\n')[0]}
                                </h4>
                                
                                {commit.author_name && (
                                  <div className="flex items-center space-x-4 text-sm text-gray-600 mb-3">
                                    <span className="flex items-center space-x-1">
                                      <User className="w-3 h-3" />
                                      <span>{commit.author_name}</span>
                                    </span>
                                  </div>
                                )}
                                
                                {commit.feature_summary && (
                                  <div className="mb-2">
                                    <p className="text-sm text-gray-700 italic">{commit.feature_summary}</p>
                                  </div>
                                )}
                                
                                {commit.business_impact && (
                                  <div className="mb-2">
                                    <span className={`inline-block px-2 py-1 text-xs rounded-full ${getBusinessImpactColor(commit.business_impact)}`}>
                                      {commit.business_impact.split(':')[0]}
                                    </span>
                                  </div>
                                )}
                                
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {viewMode === 'monthly' && (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Monthly Development Summary</h3>
              <p className="text-sm text-gray-600">Comprehensive overview of development activity by month</p>
            </div>
            {monthlyData.map((monthData) => (
              <div key={monthData.month} className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-bold text-gray-900">{monthData.month}</h3>
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <span className="flex items-center space-x-1">
                      <GitCommit className="w-4 h-4" />
                      <span>{monthData.totalCommits} commits</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <User className="w-4 h-4" />
                      <span>{monthData.uniqueAuthors.length} contributors</span>
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <div className="flex items-center space-x-2 mb-2">
                      <TrendingUp className="w-4 h-4 text-green-500" />
                      <span className="font-medium text-gray-700">Most Active Day</span>
                    </div>
                    <p className="text-lg font-semibold text-green-600">{monthData.mostActiveDay}</p>
                  </div>

                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <div className="flex items-center space-x-2 mb-2">
                      <Activity className="w-4 h-4 text-blue-500" />
                      <span className="font-medium text-gray-700">Contributors</span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {monthData.uniqueAuthors.slice(0, 3).map(author => (
                        <span key={author} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                          {author}
                        </span>
                      ))}
                      {monthData.uniqueAuthors.length > 3 && (
                        <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                          +{monthData.uniqueAuthors.length - 3} more
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <div className="flex items-center space-x-2 mb-2">
                      <BarChart3 className="w-4 h-4 text-purple-500" />
                      <span className="font-medium text-gray-700">Business Impact</span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {monthData.businessImpacts.slice(0, 2).map((impact, i) => (
                        <span key={i} className={`px-2 py-1 text-xs rounded-full ${getBusinessImpactColor(impact)}`}>
                          {impact.split(':')[0]}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-lg p-4 border border-gray-200">
                  <h4 className="font-medium text-gray-800 mb-3">Recent Commits ({monthData.commits.length})</h4>
                  <div className="space-y-2">
                    {monthData.commits.slice(0, 3).map(commit => (
                      <div key={commit.sha} className="flex items-center space-x-3 text-sm">
                        <code className="bg-gray-100 px-2 py-1 rounded text-xs font-mono">
                          {commit.sha.slice(0, 7)}
                        </code>
                        <span className="text-gray-600">{commit.author_name}</span>
                        <span className="text-gray-800 truncate flex-1">{commit.message.split('\n')[0]}</span>
                      </div>
                    ))}
                    {monthData.commits.length > 3 && (
                      <p className="text-xs text-gray-500 text-center pt-2">
                        +{monthData.commits.length - 3} more commits
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {viewMode === 'heatmap' && (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Activity Heatmap</h3>
              <p className="text-sm text-gray-600">Visual representation of development activity over the past 12 months</p>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="grid grid-cols-4 md:grid-cols-6 lg:grid-cols-12 gap-2">
                {heatmapData.map((data, index) => (
                  <div key={index} className="text-center">
                    <div 
                      className={`w-full h-16 rounded-lg border-2 flex items-center justify-center text-xs font-medium transition-all hover:scale-105 cursor-pointer ${
                        data.intensity === 0 ? 'bg-gray-100 border-gray-200 text-gray-400' :
                        data.intensity === 1 ? 'bg-green-100 border-green-200 text-green-700' :
                        data.intensity === 2 ? 'bg-green-200 border-green-300 text-green-800' :
                        data.intensity === 3 ? 'bg-green-400 border-green-500 text-white' :
                        'bg-green-600 border-green-700 text-white'
                      }`}
                      title={`${data.month}: ${data.commitCount} commits`}
                    >
                      <div>
                        <div className="font-semibold">{data.commitCount}</div>
                        <div className="text-xs opacity-75">commits</div>
                      </div>
                    </div>
                    <div className="text-xs text-gray-600 mt-1">{data.month}</div>
                  </div>
                ))}
              </div>
              
              <div className="mt-6 flex items-center justify-center space-x-4 text-xs text-gray-600">
                <span>Less active</span>
                <div className="flex space-x-1">
                  <div className="w-3 h-3 bg-gray-100 border border-gray-200 rounded-sm"></div>
                  <div className="w-3 h-3 bg-green-100 border border-green-200 rounded-sm"></div>
                  <div className="w-3 h-3 bg-green-200 border border-green-300 rounded-sm"></div>
                  <div className="w-3 h-3 bg-green-400 border border-green-500 rounded-sm"></div>
                  <div className="w-3 h-3 bg-green-600 border border-green-700 rounded-sm"></div>
                </div>
                <span>More active</span>
              </div>
            </div>

            {/* Activity Insights */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <TrendingUp className="w-5 h-5 text-blue-600" />
                  <h4 className="font-medium text-blue-900">Peak Activity</h4>
                </div>
                <p className="text-sm text-blue-700">
                  {heatmapData.reduce((max, curr) => curr.commitCount > max.commitCount ? curr : max, heatmapData[0])?.month} with {heatmapData.reduce((max, curr) => Math.max(max, curr.commitCount), 0)} commits
                </p>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <Activity className="w-5 h-5 text-green-600" />
                  <h4 className="font-medium text-green-900">Total Activity</h4>
                </div>
                <p className="text-sm text-green-700">
                  {heatmapData.reduce((sum, curr) => sum + curr.commitCount, 0)} commits across {heatmapData.filter(d => d.commitCount > 0).length} active months
                </p>
              </div>

              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <BarChart3 className="w-5 h-5 text-purple-600" />
                  <h4 className="font-medium text-purple-900">Average</h4>
                </div>
                <p className="text-sm text-purple-700">
                  {Math.round(heatmapData.reduce((sum, curr) => sum + curr.commitCount, 0) / heatmapData.length)} commits per month
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}