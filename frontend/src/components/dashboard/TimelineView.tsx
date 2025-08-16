'use client'

import { useState, useEffect, useMemo } from 'react'
import { Clock, GitCommit, User, Filter, Calendar, ChevronDown, ChevronUp } from 'lucide-react'

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

export function TimelineView({ commits, milestones = [] }: TimelineViewProps) {
  const [filterAuthor, setFilterAuthor] = useState<string>('all')
  const [dateRange, setDateRange] = useState<'all' | '7d' | '30d' | '90d'>('all')
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set())

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
          
          {/* Filters */}
          <div className="flex flex-wrap items-center space-x-4">
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

      {/* Timeline */}
      <div className="p-6">
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
      </div>
    </div>
  )
}