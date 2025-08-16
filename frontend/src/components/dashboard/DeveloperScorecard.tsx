'use client'

import { useState, useMemo } from 'react'
import { User, Trophy, Code, GitCommit, TrendingUp, Star, Award, Target } from 'lucide-react'

interface Developer {
  name: string
  email: string
  expertise_areas: string[]
  contribution_score: number
  total_commits: number
  lines_added: number
  lines_removed: number
}

interface DeveloperScorecardProps {
  developers: Developer[]
  codebaseId: string
}

interface ScorecardData extends Developer {
  rank: number
  productivity_score: number
  impact_score: number
  consistency_score: number
  collaboration_score: number
  overall_grade: string
  strengths: string[]
  improvements: string[]
}

export function DeveloperScorecard({ developers, codebaseId }: DeveloperScorecardProps) {
  const [selectedDeveloper, setSelectedDeveloper] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState<'contribution_score' | 'total_commits' | 'productivity' | 'impact'>('contribution_score')

  // Calculate advanced metrics and scorecards
  const scorecards = useMemo(() => {
    const totalCommits = developers.reduce((sum, dev) => sum + dev.total_commits, 0)
    const totalLinesChanged = developers.reduce((sum, dev) => sum + dev.lines_added + dev.lines_removed, 0)
    
    return developers.map((dev, index) => {
      // Calculate scores (0-100 scale)
      const productivity_score = Math.min(100, (dev.total_commits / Math.max(totalCommits, 1)) * 100 * developers.length)
      const impact_score = Math.min(100, ((dev.lines_added + dev.lines_removed) / Math.max(totalLinesChanged, 1)) * 100 * developers.length)
      const consistency_score = dev.total_commits > 0 ? Math.min(100, (dev.total_commits / 30) * 100) : 0 // Assuming 30 days
      const collaboration_score = Math.min(100, dev.expertise_areas.length * 25) // Max 4 areas for 100
      
      // Overall grade calculation
      const average = (productivity_score + impact_score + consistency_score + collaboration_score) / 4
      const overall_grade = 
        average >= 90 ? 'A+' :
        average >= 80 ? 'A' :
        average >= 70 ? 'B+' :
        average >= 60 ? 'B' :
        average >= 50 ? 'C+' :
        average >= 40 ? 'C' : 'D'

      // Determine strengths and improvements
      const scores = {
        productivity: productivity_score,
        impact: impact_score,
        consistency: consistency_score,
        collaboration: collaboration_score
      }
      
      const sortedScores = Object.entries(scores).sort(([,a], [,b]) => b - a)
      const strengths = sortedScores.slice(0, 2).map(([key]) => {
        switch (key) {
          case 'productivity': return 'High Commit Frequency'
          case 'impact': return 'High Code Impact'
          case 'consistency': return 'Consistent Contributor'
          case 'collaboration': return 'Multi-domain Expertise'
          default: return key
        }
      })
      
      const improvements = sortedScores.slice(-2).map(([key]) => {
        switch (key) {
          case 'productivity': return 'Increase Commit Frequency'
          case 'impact': return 'Expand Code Contributions'
          case 'consistency': return 'More Consistent Activity'
          case 'collaboration': return 'Diversify Expertise Areas'
          default: return key
        }
      })

      return {
        ...dev,
        rank: index + 1,
        productivity_score,
        impact_score,
        consistency_score,
        collaboration_score,
        overall_grade,
        strengths,
        improvements
      } as ScorecardData
    }).sort((a, b) => {
      switch (sortBy) {
        case 'contribution_score': return b.contribution_score - a.contribution_score
        case 'total_commits': return b.total_commits - a.total_commits
        case 'productivity': return b.productivity_score - a.productivity_score
        case 'impact': return b.impact_score - a.impact_score
        default: return b.contribution_score - a.contribution_score
      }
    }).map((dev, index) => ({ ...dev, rank: index + 1 }))
  }, [developers, sortBy])

  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'A+': return 'text-green-600 bg-green-100'
      case 'A': return 'text-green-600 bg-green-100'
      case 'B+': return 'text-blue-600 bg-blue-100'
      case 'B': return 'text-blue-600 bg-blue-100'
      case 'C+': return 'text-yellow-600 bg-yellow-100'
      case 'C': return 'text-yellow-600 bg-yellow-100'
      default: return 'text-red-600 bg-red-100'
    }
  }

  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1: return <Trophy className="w-5 h-5 text-yellow-500" />
      case 2: return <Award className="w-5 h-5 text-gray-400" />
      case 3: return <Star className="w-5 h-5 text-amber-600" />
      default: return <Target className="w-5 h-5 text-gray-500" />
    }
  }

  const ScoreBar = ({ label, score, color }: { label: string; score: number; color: string }) => (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-gray-600">{label}</span>
        <span className="font-medium">{Math.round(score)}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className={`h-2 rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${Math.min(score, 100)}%` }}
        ></div>
      </div>
    </div>
  )

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 flex items-center space-x-2">
              <User className="w-6 h-6 text-green-600" />
              <span>Developer Scorecards</span>
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Comprehensive performance analysis and expertise evaluation
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            <label className="text-sm text-gray-600">Sort by:</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="text-sm border border-gray-300 rounded-lg px-3 py-1 focus:outline-none focus:ring-2 focus:ring-green-500"
            >
              <option value="contribution_score">Contribution Score</option>
              <option value="total_commits">Total Commits</option>
              <option value="productivity">Productivity</option>
              <option value="impact">Impact</option>
            </select>
          </div>
        </div>
        
        <div className="mt-4 flex flex-wrap gap-4 text-sm text-gray-600">
          <span>Total Developers: {developers.length}</span>
          <span>Top Performer: {scorecards[0]?.name || 'N/A'}</span>
        </div>
      </div>

      {/* Scorecards Grid */}
      <div className="p-6">
        {developers.length === 0 ? (
          <div className="text-center py-12">
            <User className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No developer data available</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {scorecards.map((developer) => (
              <div 
                key={developer.email} 
                className={`bg-gradient-to-br from-white to-gray-50 rounded-xl border-2 transition-all duration-200 hover:shadow-lg cursor-pointer ${
                  selectedDeveloper === developer.email ? 'border-green-500 shadow-lg' : 'border-gray-200 hover:border-green-300'
                }`}
                onClick={() => setSelectedDeveloper(selectedDeveloper === developer.email ? null : developer.email)}
              >
                {/* Header */}
                <div className="p-4 border-b border-gray-100">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-green-400 to-blue-500 rounded-full flex items-center justify-center text-white font-bold">
                        {developer.name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">{developer.name}</h3>
                        <p className="text-xs text-gray-500">Rank #{developer.rank}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      {getRankIcon(developer.rank)}
                      <div className={`inline-block px-2 py-1 rounded-full text-xs font-semibold mt-1 ${getGradeColor(developer.overall_grade)}`}>
                        {developer.overall_grade}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Key Metrics */}
                <div className="p-4 space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-center">
                    <div>
                      <div className="text-2xl font-bold text-gray-900">{developer.total_commits}</div>
                      <div className="text-xs text-gray-500">Commits</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-gray-900">{developer.contribution_score}</div>
                      <div className="text-xs text-gray-500">Score</div>
                    </div>
                  </div>

                  {/* Score Bars */}
                  <div className="space-y-3">
                    <ScoreBar 
                      label="Productivity" 
                      score={developer.productivity_score} 
                      color="bg-blue-500" 
                    />
                    <ScoreBar 
                      label="Impact" 
                      score={developer.impact_score} 
                      color="bg-green-500" 
                    />
                    <ScoreBar 
                      label="Consistency" 
                      score={developer.consistency_score} 
                      color="bg-purple-500" 
                    />
                    <ScoreBar 
                      label="Collaboration" 
                      score={developer.collaboration_score} 
                      color="bg-orange-500" 
                    />
                  </div>

                  {/* Expertise Areas */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Expertise Areas</h4>
                    <div className="flex flex-wrap gap-1">
                      {developer.expertise_areas.slice(0, 3).map((area, index) => (
                        <span key={index} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                          {area}
                        </span>
                      ))}
                      {developer.expertise_areas.length > 3 && (
                        <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                          +{developer.expertise_areas.length - 3}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Expanded Details */}
                {selectedDeveloper === developer.email && (
                  <div className="border-t border-gray-100 p-4 bg-gray-50">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Strengths */}
                      <div>
                        <h4 className="text-sm font-medium text-green-700 mb-2 flex items-center space-x-1">
                          <TrendingUp className="w-3 h-3" />
                          <span>Strengths</span>
                        </h4>
                        <ul className="space-y-1">
                          {developer.strengths.map((strength, index) => (
                            <li key={index} className="text-xs text-green-600 flex items-center space-x-1">
                              <span className="w-1 h-1 bg-green-500 rounded-full"></span>
                              <span>{strength}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Areas for Improvement */}
                      <div>
                        <h4 className="text-sm font-medium text-orange-700 mb-2 flex items-center space-x-1">
                          <Target className="w-3 h-3" />
                          <span>Growth Areas</span>
                        </h4>
                        <ul className="space-y-1">
                          {developer.improvements.map((improvement, index) => (
                            <li key={index} className="text-xs text-orange-600 flex items-center space-x-1">
                              <span className="w-1 h-1 bg-orange-500 rounded-full"></span>
                              <span>{improvement}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    {/* Detailed Stats */}
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <div className="grid grid-cols-3 gap-4 text-center">
                        <div>
                          <div className="text-lg font-bold text-green-600">+{developer.lines_added.toLocaleString()}</div>
                          <div className="text-xs text-gray-500">Lines Added</div>
                        </div>
                        <div>
                          <div className="text-lg font-bold text-red-600">-{developer.lines_removed.toLocaleString()}</div>
                          <div className="text-xs text-gray-500">Lines Removed</div>
                        </div>
                        <div>
                          <div className="text-lg font-bold text-gray-900">{developer.expertise_areas.length}</div>
                          <div className="text-xs text-gray-500">Expertise Areas</div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Summary Stats */}
      {developers.length > 0 && (
        <div className="border-t border-gray-200 p-6 bg-gray-50">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Team Summary</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {Math.round(scorecards.reduce((sum, dev) => sum + dev.productivity_score, 0) / scorecards.length)}
              </div>
              <div className="text-sm text-gray-600">Avg Productivity</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {Math.round(scorecards.reduce((sum, dev) => sum + dev.impact_score, 0) / scorecards.length)}
              </div>
              <div className="text-sm text-gray-600">Avg Impact</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {Math.round(scorecards.reduce((sum, dev) => sum + dev.consistency_score, 0) / scorecards.length)}
              </div>
              <div className="text-sm text-gray-600">Avg Consistency</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {Math.round(scorecards.reduce((sum, dev) => sum + dev.collaboration_score, 0) / scorecards.length)}
              </div>
              <div className="text-sm text-gray-600">Avg Collaboration</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}