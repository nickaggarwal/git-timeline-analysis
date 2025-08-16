'use client'

import { useState, useEffect } from 'react'
import { Brain, TrendingUp, Users, Calendar, Award, GitCommit, Code, Bug, Zap, Sparkles, Activity, BarChart3, Target } from 'lucide-react'

interface AISummaryViewProps {
  codebaseId: string
}

interface HeatmapData {
  month: string
  month_key: string
  commit_count: number
  activity_level: 'high' | 'medium' | 'low'
}

interface Developer {
  name: string
  email: string
  expertise_areas: string[]
  contribution_score: number
  total_commits: number
  lines_added: number
  lines_removed: number
}

interface BusinessUpdate {
  month_key: string
  month_name: string
  total_commits: number
  features_added: string[]
  bugs_fixed: string[]
  performance_improvements: string[]
  milestones: any[]
  top_commits: any[]
}

interface AISummaryData {
  heatmap_data: HeatmapData[]
  top_developers: Developer[]
  recent_business_updates: BusinessUpdate[]
  ai_insights: string | null
  summary_stats: {
    total_commits: number
    recent_commits: number
    total_developers: number
    total_milestones: number
    activity_trend: string
  }
}

export function AISummaryView({ codebaseId }: AISummaryViewProps) {
  const [summaryData, setSummaryData] = useState<AISummaryData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchAISummary()
  }, [codebaseId])

  const fetchAISummary = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await fetch(`http://localhost:8001/codebase/${codebaseId}/ai-summary`)
      
      if (!response.ok) {
        throw new Error(`Failed to fetch AI summary: ${response.statusText}`)
      }
      
      const data = await response.json()
      setSummaryData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load AI summary')
      console.error('Error fetching AI summary:', err)
    } finally {
      setLoading(false)
    }
  }

  const getActivityColor = (level: string) => {
    switch (level) {
      case 'high': return 'bg-green-600 border-green-700'
      case 'medium': return 'bg-green-400 border-green-500'
      case 'low': return 'bg-green-200 border-green-300'
      default: return 'bg-gray-100 border-gray-200'
    }
  }

  const getActivityTextColor = (level: string) => {
    switch (level) {
      case 'high': return 'text-white'
      case 'medium': return 'text-white'
      case 'low': return 'text-green-800'
      default: return 'text-gray-400'
    }
  }

  const getTrendIcon = (trend: string) => {
    return trend === 'increasing' ? (
      <TrendingUp className="w-5 h-5 text-green-600" />
    ) : (
      <BarChart3 className="w-5 h-5 text-blue-600" />
    )
  }

  const formatNumber = (num: number) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
    return num.toString()
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
          <div className="flex items-center space-x-2">
            <Brain className="w-6 h-6 text-purple-600" />
            <span className="text-lg font-semibold text-gray-900">Generating AI Summary...</span>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map(i => (
            <div key={i} className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
              <div className="h-12 bg-gray-200 rounded mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-6">
          <div className="text-center py-8">
            <Brain className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <div className="text-red-500 text-sm mb-2">Error loading AI summary</div>
            <div className="text-gray-600 text-xs mb-4">{error}</div>
            <button 
              onClick={fetchAISummary}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!summaryData) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-6">
          <div className="text-center py-8">
            <Brain className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No summary data available</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with AI Insights */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl p-6 border border-purple-200">
        <div className="flex items-start space-x-4">
          <div className="flex items-center space-x-2">
            <Brain className="w-8 h-8 text-purple-600" />
            <Sparkles className="w-5 h-5 text-blue-500" />
          </div>
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-900 mb-3">AI Repository Summary</h2>
            
            {summaryData.ai_insights && summaryData.ai_insights.trim() ? (
              <div className="bg-white rounded-lg p-4 border border-purple-100">
                <div className="flex items-center space-x-2 mb-3">
                  <Sparkles className="w-4 h-4 text-purple-600" />
                  <span className="text-sm font-medium text-purple-800">AI Insights</span>
                </div>
                <p className="text-gray-700 leading-relaxed whitespace-pre-line">
                  {summaryData.ai_insights}
                </p>
              </div>
            ) : null}
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Commits</p>
              <p className="text-2xl font-bold text-blue-600">{formatNumber(summaryData.summary_stats.total_commits)}</p>
            </div>
            <GitCommit className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Recent Activity</p>
              <p className="text-2xl font-bold text-green-600">{summaryData.summary_stats.recent_commits}</p>
              <p className="text-xs text-gray-500">Last 2 months</p>
            </div>
            <Activity className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Contributors</p>
              <p className="text-2xl font-bold text-purple-600">{summaryData.summary_stats.total_developers}</p>
            </div>
            <Users className="w-8 h-8 text-purple-500" />
          </div>
        </div>

        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Trend</p>
              <p className="text-lg font-bold text-gray-900 capitalize">{summaryData.summary_stats.activity_trend}</p>
            </div>
            {getTrendIcon(summaryData.summary_stats.activity_trend)}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Activity Heatmap */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
              <Activity className="w-5 h-5 text-green-600" />
              <span>Activity Heatmap</span>
            </h3>
            <p className="text-sm text-gray-500 mt-1">Development activity over the past 12 months</p>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-3 md:grid-cols-4 gap-2">
              {summaryData.heatmap_data.map((data, index) => (
                <div key={index} className="text-center">
                  <div 
                    className={`w-full h-12 rounded-lg border-2 flex items-center justify-center text-xs font-medium transition-all hover:scale-105 cursor-pointer ${
                      getActivityColor(data.activity_level)
                    } ${getActivityTextColor(data.activity_level)}`}
                    title={`${data.month}: ${data.commit_count} commits`}
                  >
                    <div>
                      <div className="font-semibold">{data.commit_count}</div>
                    </div>
                  </div>
                  <div className="text-xs text-gray-600 mt-1">{data.month}</div>
                </div>
              ))}
            </div>
            
            <div className="mt-4 flex items-center justify-center space-x-4 text-xs text-gray-600">
              <span>Less active</span>
              <div className="flex space-x-1">
                <div className="w-3 h-3 bg-gray-100 border border-gray-200 rounded-sm"></div>
                <div className="w-3 h-3 bg-green-200 border border-green-300 rounded-sm"></div>
                <div className="w-3 h-3 bg-green-400 border border-green-500 rounded-sm"></div>
                <div className="w-3 h-3 bg-green-600 border border-green-700 rounded-sm"></div>
              </div>
              <span>More active</span>
            </div>
          </div>
        </div>

        {/* Top 3 Developers */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
              <Users className="w-5 h-5 text-blue-600" />
              <span>Top Contributors</span>
            </h3>
            <p className="text-sm text-gray-500 mt-1">Leading developers by contribution score</p>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {summaryData.top_developers.map((developer, index) => (
                <div key={developer.email} className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-100">
                  <div className="flex items-center space-x-4">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-lg ${
                      index === 0 ? 'bg-gradient-to-r from-yellow-400 to-orange-500' :
                      index === 1 ? 'bg-gradient-to-r from-gray-400 to-gray-500' :
                      'bg-gradient-to-r from-orange-400 to-red-500'
                    }`}>
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900">{developer.name}</p>
                      <p className="text-sm text-gray-600">{developer.total_commits} commits</p>
                      {developer.expertise_areas && developer.expertise_areas.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {developer.expertise_areas.slice(0, 2).map((area, i) => (
                            <span key={i} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                              {area}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-purple-600">
                      {developer.contribution_score}
                    </div>
                    <div className="text-xs text-gray-500">
                      +{formatNumber(developer.lines_added)} -{formatNumber(developer.lines_removed)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Business Updates (Last 2 Months) */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
            <Calendar className="w-5 h-5 text-orange-600" />
            <span>Recent Business Updates</span>
          </h3>
          <p className="text-sm text-gray-500 mt-1">Key developments from the last 2 months</p>
        </div>
        <div className="p-6">
          {summaryData.recent_business_updates.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {summaryData.recent_business_updates.map((update) => (
                <div key={update.month_key} className="bg-gradient-to-br from-orange-50 to-red-50 border border-orange-200 rounded-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-xl font-bold text-gray-900">{update.month_name}</h4>
                    <div className="flex items-center space-x-2 text-sm text-gray-600">
                      <GitCommit className="w-4 h-4" />
                      <span>{update.total_commits} commits</span>
                    </div>
                  </div>

                  <div className="space-y-4">
                    {update.features_added.length > 0 && (
                      <div>
                        <div className="flex items-center space-x-2 mb-2">
                          <Code className="w-4 h-4 text-blue-600" />
                          <span className="font-medium text-blue-900">Features Added ({update.features_added.length})</span>
                        </div>
                        <div className="space-y-1">
                          {update.features_added.map((feature, i) => (
                            <div key={i} className="text-sm text-gray-700 bg-blue-50 rounded p-2 border border-blue-100">
                              {feature}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {update.bugs_fixed.length > 0 && (
                      <div>
                        <div className="flex items-center space-x-2 mb-2">
                          <Bug className="w-4 h-4 text-red-600" />
                          <span className="font-medium text-red-900">Bugs Fixed ({update.bugs_fixed.length})</span>
                        </div>
                        <div className="space-y-1">
                          {update.bugs_fixed.map((bug, i) => (
                            <div key={i} className="text-sm text-gray-700 bg-red-50 rounded p-2 border border-red-100">
                              {bug}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {update.performance_improvements.length > 0 && (
                      <div>
                        <div className="flex items-center space-x-2 mb-2">
                          <Zap className="w-4 h-4 text-green-600" />
                          <span className="font-medium text-green-900">Performance ({update.performance_improvements.length})</span>
                        </div>
                        <div className="space-y-1">
                          {update.performance_improvements.map((improvement, i) => (
                            <div key={i} className="text-sm text-gray-700 bg-green-50 rounded p-2 border border-green-100">
                              {improvement}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {update.milestones.length > 0 && (
                      <div>
                        <div className="flex items-center space-x-2 mb-2">
                          <Award className="w-4 h-4 text-yellow-600" />
                          <span className="font-medium text-yellow-900">Milestones ({update.milestones.length})</span>
                        </div>
                        <div className="space-y-2">
                          {update.milestones.map((milestone, i) => (
                            <div key={i} className="bg-yellow-50 rounded p-2 border border-yellow-100">
                              <div className="font-medium text-sm text-gray-900">{milestone.name}</div>
                              <div className="text-xs text-gray-600">{milestone.description}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No recent business updates available</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}