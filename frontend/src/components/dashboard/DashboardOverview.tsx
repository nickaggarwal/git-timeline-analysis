'use client'

import { GitBranch, Users, GitCommit, Calendar, Code, TrendingUp, Activity } from 'lucide-react'

interface GraphData {
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

interface Developer {
  name: string
  email: string
  expertise_areas: string[]
  contribution_score: number
  total_commits: number
  lines_added: number
  lines_removed: number
}

interface DashboardOverviewProps {
  codebaseId: string
  graphData: GraphData
  developers: Developer[]
}

export function DashboardOverview({ codebaseId, graphData, developers }: DashboardOverviewProps) {
  const commits = graphData.nodes.filter(node => node.type === 'commit')
  const devNodes = graphData.nodes.filter(node => node.type === 'developer')
  
  const totalCommits = commits.length
  const totalDevelopers = developers.length
  const totalLinesChanged = developers.reduce((sum, dev) => sum + dev.lines_added + dev.lines_removed, 0)
  const avgCommitsPerDev = totalDevelopers > 0 ? Math.round(totalCommits / totalDevelopers) : 0

  const topDevelopers = [...developers]
    .sort((a, b) => b.contribution_score - a.contribution_score)
    .slice(0, 5)

  const expertiseAreas = developers
    .flatMap(dev => dev.expertise_areas)
    .reduce((acc, area) => {
      acc[area] = (acc[area] || 0) + 1
      return acc
    }, {} as Record<string, number>)

  const topExpertise = Object.entries(expertiseAreas)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 6)

  const recentActivity = commits
    .filter(commit => commit.properties.timestamp)
    .sort((a, b) => new Date(b.properties.timestamp).getTime() - new Date(a.properties.timestamp).getTime())
    .slice(0, 5)

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  const formatNumber = (num: number) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
    return num.toString()
  }

  return (
    <div className="space-y-8">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Commits</p>
              <p className="text-3xl font-bold text-gray-900">{formatNumber(totalCommits)}</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <GitCommit className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Contributors</p>
              <p className="text-3xl font-bold text-gray-900">{totalDevelopers}</p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <Users className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Lines Changed</p>
              <p className="text-3xl font-bold text-gray-900">{formatNumber(totalLinesChanged)}</p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <Code className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Commits/Dev</p>
              <p className="text-3xl font-bold text-gray-900">{avgCommitsPerDev}</p>
            </div>
            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-orange-600" />
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Top Contributors */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
              <Users className="w-5 h-5 text-blue-600" />
              <span>Top Contributors</span>
            </h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {topDevelopers.map((developer, index) => (
                <div key={developer.email} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white font-medium text-sm">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{developer.name}</p>
                      <p className="text-sm text-gray-500">{developer.total_commits} commits</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">
                      Score: {developer.contribution_score}
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

        {/* Expertise Areas */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
              <Code className="w-5 h-5 text-green-600" />
              <span>Expertise Areas</span>
            </h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {topExpertise.map(([area, count], index) => (
                <div key={area} className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm font-medium text-gray-900">{area}</span>
                      <span className="text-sm text-gray-500">{count} developer{count > 1 ? 's' : ''}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-gradient-to-r from-green-400 to-blue-500 h-2 rounded-full transition-all duration-300" 
                        style={{ width: `${(count / Math.max(...topExpertise.map(([,c]) => c))) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
            <Activity className="w-5 h-5 text-purple-600" />
            <span>Recent Activity</span>
          </h3>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            {recentActivity.map((commit) => (
              <div key={commit.id} className="flex items-start space-x-4 p-4 bg-gray-50 rounded-lg">
                <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {commit.properties.message?.split('\n')[0] || 'No message'}
                    </p>
                    <span className="text-xs text-gray-500 flex-shrink-0 ml-2">
                      {commit.properties.timestamp && formatDate(commit.properties.timestamp)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    by {commit.properties.author_name || 'Unknown'} • {commit.properties.sha?.slice(0, 8)}
                  </p>
                  {commit.properties.feature_summary && (
                    <p className="text-xs text-gray-500 mt-1 italic">
                      {commit.properties.feature_summary}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Graph Statistics */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
            <GitBranch className="w-5 h-5 text-orange-600" />
            <span>Graph Statistics</span>
          </h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{graphData.stats.total_nodes}</div>
              <div className="text-sm text-gray-500">Total Nodes</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{graphData.stats.total_relationships}</div>
              <div className="text-sm text-gray-500">Relationships</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{commits.length}</div>
              <div className="text-sm text-gray-500">Commit Nodes</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{devNodes.length}</div>
              <div className="text-sm text-gray-500">Developer Nodes</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}