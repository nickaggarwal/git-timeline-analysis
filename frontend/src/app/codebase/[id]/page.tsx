'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { Clock, Users, GitBranch, MessageSquare, BarChart3, History, Github } from 'lucide-react'
import { DashboardOverview } from '@/components/dashboard/DashboardOverview'
import { ChatInterface } from '@/components/dashboard/ChatInterface'
import { GraphView } from '@/components/dashboard/GraphView'
import { TimelineView } from '@/components/dashboard/TimelineView'
import { DeveloperScorecard } from '@/components/dashboard/DeveloperScorecard'

interface CodebaseData {
  codebase_id: string
  graph_data: {
    nodes: Array<{
      id: string
      type: string
      properties: any
    }>
    relationships: Array<{
      source: string
      target: string
      type: string
    }>
    stats: {
      total_nodes: number
      total_relationships: number
    }
  }
  developer_expertise: Array<{
    name: string
    email: string
    expertise_areas: string[]
    contribution_score: number
    total_commits: number
    lines_added: number
    lines_removed: number
  }>
  retrieved_at: string
}

const tabs = [
  { id: 'overview', name: 'Overview', icon: BarChart3, description: 'Repository insights & metrics' },
  { id: 'chat', name: 'Chat', icon: MessageSquare, description: 'AI-powered repository Q&A' },
  { id: 'graph', name: 'Graph', icon: GitBranch, description: 'Visual commit & developer network' },
  { id: 'timeline', name: 'Timeline', icon: History, description: 'Chronological development history' },
  { id: 'developers', name: 'Developers', icon: Users, description: 'Team expertise & scorecards' },
]

export default function CodebaseDashboard() {
  const params = useParams()
  const codebaseId = params.id as string
  const [activeTab, setActiveTab] = useState('overview')
  const [codebaseData, setCodebaseData] = useState<CodebaseData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchCodebaseData = async () => {
      try {
        const response = await fetch(`http://localhost:8001/codebase/${codebaseId}/summary`)
        if (!response.ok) {
          throw new Error(`Failed to fetch codebase data: ${response.statusText}`)
        }
        const data = await response.json()
        setCodebaseData(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch codebase data')
      } finally {
        setLoading(false)
      }
    }

    if (codebaseId) {
      fetchCodebaseData()
    }
  }, [codebaseId])

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <h2 className="text-xl font-semibold text-gray-700">Loading Codebase Analysis...</h2>
          <p className="text-gray-500">Fetching repository insights and graph data</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 flex items-center justify-center">
        <div className="text-center space-y-4 p-8 bg-white rounded-xl shadow-lg max-w-md">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto">
            <Github className="w-8 h-8 text-red-600" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900">Analysis Not Found</h2>
          <p className="text-gray-600">{error}</p>
          <button 
            onClick={() => window.location.href = '/'}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Back to Home
          </button>
        </div>
      </div>
    )
  }

  const repoName = codebaseId.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">CT</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">{repoName}</h1>
                <p className="text-sm text-gray-500">Codebase Time Machine</p>
              </div>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Clock className="w-4 h-4" />
              <span>Last analyzed: {new Date(codebaseData?.retrieved_at || '').toLocaleDateString()}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        <div className="flex space-x-1 bg-gray-100 p-1 rounded-xl mb-8">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 flex items-center justify-center space-x-2 py-3 px-4 rounded-lg text-sm font-medium transition-all ${
                  activeTab === tab.id
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="hidden sm:inline">{tab.name}</span>
              </button>
            )
          })}
        </div>

        {/* Tab Content */}
        <div className="pb-8">
          {activeTab === 'overview' && codebaseData && (
            <DashboardOverview 
              codebaseId={codebaseId}
              graphData={codebaseData.graph_data}
              developers={codebaseData.developer_expertise}
            />
          )}
          
          {activeTab === 'chat' && (
            <ChatInterface codebaseId={codebaseId} />
          )}
          
          {activeTab === 'graph' && codebaseData && (
            <GraphView 
              nodes={codebaseData.graph_data.nodes}
              relationships={codebaseData.graph_data.relationships}
              stats={codebaseData.graph_data.stats}
            />
          )}
          
          {activeTab === 'timeline' && (
            <TimelineView codebaseId={codebaseId} />
          )}
          
          {activeTab === 'developers' && codebaseData && (
            <DeveloperScorecard 
              developers={codebaseData.developer_expertise}
              codebaseId={codebaseId}
            />
          )}
        </div>
      </div>
    </div>
  )
}