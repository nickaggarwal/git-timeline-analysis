'use client'

import { useState, useEffect } from 'react'
import { Clock, TrendingUp, Calendar, Award, GitCommit, User, Code, Bug, Zap, ChevronDown, ChevronUp, BarChart3, Target, Milestone } from 'lucide-react'

interface BusinessTimelineViewProps {
  codebaseId: string
}

interface MilestoneData {
  id: string
  name: string
  description: string
  date: string
  type: string
  version?: string
  related_commits?: string[]
}

interface CommitData {
  sha: string
  message: string
  author_name?: string
  timestamp: string
  feature_summary?: string
  business_impact?: string
  insertions?: number
  deletions?: number
}

interface MonthlyBusinessSummary {
  month_key: string
  month_name: string
  year: number
  month: number
  total_commits: number
  unique_authors: string[]
  author_count: number
  insertions: number
  deletions: number
  net_changes: number
  business_impacts: string[]
  features_added: string[]
  bugs_fixed: string[]
  performance_improvements: string[]
  milestones: MilestoneData[]
  milestone_count: number
  top_commits: CommitData[]
}

interface BusinessTimelineData {
  monthly_summaries: MonthlyBusinessSummary[]
  milestones: MilestoneData[]
  total_months: number
  total_milestones: number
  total_commits: number
}

export function BusinessTimelineView({ codebaseId }: BusinessTimelineViewProps) {
  const [timelineData, setTimelineData] = useState<BusinessTimelineData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedMonths, setExpandedMonths] = useState<Set<string>>(new Set())
  const [viewMode, setViewMode] = useState<'summary' | 'detailed'>('summary')

  useEffect(() => {
    fetchBusinessTimeline()
  }, [codebaseId])

  const fetchBusinessTimeline = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await fetch(`http://localhost:8001/codebase/${codebaseId}/business-timeline`)
      
      if (!response.ok) {
        throw new Error(`Failed to fetch business timeline: ${response.statusText}`)
      }
      
      const data = await response.json()
      setTimelineData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load business timeline')
      console.error('Error fetching business timeline:', err)
    } finally {
      setLoading(false)
    }
  }

  const toggleMonthExpansion = (monthKey: string) => {
    const newExpanded = new Set(expandedMonths)
    if (newExpanded.has(monthKey)) {
      newExpanded.delete(monthKey)
    } else {
      newExpanded.add(monthKey)
    }
    setExpandedMonths(newExpanded)
  }

  const getImpactColor = (impact: string) => {
    const lowerImpact = impact.toLowerCase()
    if (lowerImpact.includes('feature') || lowerImpact.includes('enhancement')) return 'bg-blue-100 text-blue-800'
    if (lowerImpact.includes('bug') || lowerImpact.includes('fix')) return 'bg-red-100 text-red-800'
    if (lowerImpact.includes('performance') || lowerImpact.includes('optimization')) return 'bg-green-100 text-green-800'
    if (lowerImpact.includes('security')) return 'bg-purple-100 text-purple-800'
    return 'bg-gray-100 text-gray-800'
  }

  const getMilestoneIcon = (type: string) => {
    const lowerType = type?.toLowerCase() || ''
    if (lowerType.includes('release')) return <Award className="w-4 h-4" />
    if (lowerType.includes('launch')) return <Target className="w-4 h-4" />
    if (lowerType.includes('beta')) return <Code className="w-4 h-4" />
    return <Milestone className="w-4 h-4" />
  }

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      })
    } catch {
      return dateString
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-600"></div>
            <span className="text-gray-600">Loading business timeline...</span>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-6">
          <div className="text-center py-8">
            <div className="text-red-500 text-sm mb-2">Error loading business timeline</div>
            <div className="text-gray-600 text-xs">{error}</div>
            <button 
              onClick={fetchBusinessTimeline}
              className="mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!timelineData || timelineData.monthly_summaries.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-6">
          <div className="text-center py-8">
            <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No business timeline data available</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 flex items-center space-x-2">
              <BarChart3 className="w-6 h-6 text-purple-600" />
              <span>Business Timeline</span>
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Monthly business updates, milestones, and development impact summary
            </p>
          </div>
          
          {/* View Mode Toggle */}
          <div className="flex items-center bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('summary')}
              className={`flex items-center space-x-1 px-3 py-1 rounded-md text-sm transition-colors ${
                viewMode === 'summary' ? 'bg-white text-purple-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              <span>Summary</span>
            </button>
            <button
              onClick={() => setViewMode('detailed')}
              className={`flex items-center space-x-1 px-3 py-1 rounded-md text-sm transition-colors ${
                viewMode === 'detailed' ? 'bg-white text-purple-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Calendar className="w-4 h-4" />
              <span>Detailed</span>
            </button>
          </div>
        </div>
        
        {/* Stats */}
        <div className="mt-4 flex flex-wrap gap-4 text-sm text-gray-600">
          <span className="flex items-center space-x-1">
            <Calendar className="w-4 h-4" />
            <span>{timelineData.total_months} months tracked</span>
          </span>
          <span className="flex items-center space-x-1">
            <Award className="w-4 h-4" />
            <span>{timelineData.total_milestones} milestones</span>
          </span>
          <span className="flex items-center space-x-1">
            <GitCommit className="w-4 h-4" />
            <span>{timelineData.total_commits} total commits</span>
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        <div className="space-y-6">
          {timelineData.monthly_summaries.map((monthSummary) => (
            <div key={monthSummary.month_key} className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-xl overflow-hidden">
              {/* Month Header */}
              <div 
                className="p-6 cursor-pointer hover:bg-blue-100/50 transition-colors"
                onClick={() => toggleMonthExpansion(monthSummary.month_key)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-900">{monthSummary.month_name}</h3>
                      <div className="flex items-center space-x-4 text-sm text-gray-600 mt-1">
                        <span className="flex items-center space-x-1">
                          <GitCommit className="w-4 h-4" />
                          <span>{monthSummary.total_commits} commits</span>
                        </span>
                        <span className="flex items-center space-x-1">
                          <User className="w-4 h-4" />
                          <span>{monthSummary.author_count} contributors</span>
                        </span>
                        {monthSummary.milestone_count > 0 && (
                          <span className="flex items-center space-x-1">
                            <Award className="w-4 h-4 text-yellow-600" />
                            <span className="text-yellow-700">{monthSummary.milestone_count} milestone{monthSummary.milestone_count > 1 ? 's' : ''}</span>
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    {/* Quick Stats */}
                    <div className="text-right text-sm text-gray-600">
                      <div className="flex items-center space-x-2">
                        <Code className="w-4 h-4 text-green-600" />
                        <span className="text-green-700">+{monthSummary.insertions.toLocaleString()}</span>
                        <Bug className="w-4 h-4 text-red-600" />
                        <span className="text-red-700">-{monthSummary.deletions.toLocaleString()}</span>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        Net: {monthSummary.net_changes >= 0 ? '+' : ''}{monthSummary.net_changes.toLocaleString()} lines
                      </div>
                    </div>
                    
                    {expandedMonths.has(monthSummary.month_key) ? (
                      <ChevronUp className="w-5 h-5 text-gray-400" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                </div>
              </div>

              {/* Expanded Content */}
              {expandedMonths.has(monthSummary.month_key) && (
                <div className="px-6 pb-6">
                  {/* Milestones */}
                  {monthSummary.milestones.length > 0 && (
                    <div className="mb-6">
                      <h4 className="font-medium text-gray-800 mb-3 flex items-center space-x-2">
                        <Award className="w-4 h-4 text-yellow-600" />
                        <span>Milestones Achieved</span>
                      </h4>
                      <div className="space-y-2">
                        {monthSummary.milestones.map((milestone) => (
                          <div key={milestone.id} className="bg-white rounded-lg p-4 border border-yellow-200 shadow-sm">
                            <div className="flex items-start space-x-3">
                              <div className="text-yellow-600 mt-0.5">
                                {getMilestoneIcon(milestone.type)}
                              </div>
                              <div className="flex-1">
                                <h5 className="font-medium text-gray-900">{milestone.name}</h5>
                                <p className="text-sm text-gray-600 mt-1">{milestone.description}</p>
                                <div className="flex items-center space-x-4 mt-2">
                                  <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full">
                                    {milestone.type}
                                  </span>
                                  {milestone.version && (
                                    <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                                      v{milestone.version}
                                    </span>
                                  )}
                                  <span className="text-xs text-gray-500">
                                    {formatDate(milestone.date)}
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Business Impact Categories */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    {/* Features Added */}
                    {monthSummary.features_added.length > 0 && (
                      <div className="bg-white rounded-lg p-4 border border-blue-200">
                        <h4 className="font-medium text-blue-900 mb-3 flex items-center space-x-2">
                          <Code className="w-4 h-4 text-blue-600" />
                          <span>Features Added ({monthSummary.features_added.length})</span>
                        </h4>
                        <div className="space-y-2">
                          {monthSummary.features_added.map((feature, i) => (
                            <div key={i} className="text-sm text-gray-700 bg-blue-50 rounded p-2">
                              {feature}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Bugs Fixed */}
                    {monthSummary.bugs_fixed.length > 0 && (
                      <div className="bg-white rounded-lg p-4 border border-red-200">
                        <h4 className="font-medium text-red-900 mb-3 flex items-center space-x-2">
                          <Bug className="w-4 h-4 text-red-600" />
                          <span>Bugs Fixed ({monthSummary.bugs_fixed.length})</span>
                        </h4>
                        <div className="space-y-2">
                          {monthSummary.bugs_fixed.map((bug, i) => (
                            <div key={i} className="text-sm text-gray-700 bg-red-50 rounded p-2">
                              {bug}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Performance Improvements */}
                    {monthSummary.performance_improvements.length > 0 && (
                      <div className="bg-white rounded-lg p-4 border border-green-200">
                        <h4 className="font-medium text-green-900 mb-3 flex items-center space-x-2">
                          <Zap className="w-4 h-4 text-green-600" />
                          <span>Performance ({monthSummary.performance_improvements.length})</span>
                        </h4>
                        <div className="space-y-2">
                          {monthSummary.performance_improvements.map((improvement, i) => (
                            <div key={i} className="text-sm text-gray-700 bg-green-50 rounded p-2">
                              {improvement}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Top Contributors */}
                  <div className="bg-white rounded-lg p-4 border border-gray-200 mb-4">
                    <h4 className="font-medium text-gray-800 mb-3 flex items-center space-x-2">
                      <User className="w-4 h-4 text-purple-600" />
                      <span>Contributors ({monthSummary.author_count})</span>
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {monthSummary.unique_authors.map((author) => (
                        <span key={author} className="px-3 py-1 bg-purple-100 text-purple-800 text-sm rounded-full">
                          {author}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Business Impacts */}
                  {monthSummary.business_impacts.length > 0 && (
                    <div className="bg-white rounded-lg p-4 border border-gray-200">
                      <h4 className="font-medium text-gray-800 mb-3 flex items-center space-x-2">
                        <TrendingUp className="w-4 h-4 text-orange-600" />
                        <span>Business Impacts</span>
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {monthSummary.business_impacts.map((impact, i) => (
                          <span key={i} className={`px-2 py-1 text-xs rounded-full ${getImpactColor(impact)}`}>
                            {impact.split(':')[0]}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}