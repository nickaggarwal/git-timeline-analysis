'use client'

import { useState, useEffect, useMemo } from 'react'
import dynamic from 'next/dynamic'
import { GitCommit, User, GitBranch, Filter, Download, RefreshCw, Info } from 'lucide-react'

// Dynamically import Neo4j NVL to avoid SSR issues
const InteractiveNvlWrapper = dynamic(
  () => import('@neo4j-nvl/react').then(mod => ({ default: mod.InteractiveNvlWrapper })),
  { 
    ssr: false,
    loading: () => <div className="flex items-center justify-center h-full">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
  }
)

interface Node {
  id: string
  type: string
  properties: any
}

interface Relationship {
  source: string
  target: string
  type: string
}

interface GraphViewProps {
  nodes: Node[]
  relationships: Relationship[]
  stats: {
    total_nodes: number
    total_relationships: number
  }
}

export function GraphView({ nodes, relationships, stats }: GraphViewProps) {
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [filterType, setFilterType] = useState<'all' | 'commit' | 'developer'>('all')
  const [searchTerm, setSearchTerm] = useState('')

  // Transform data for Neo4j NVL
  const nvlData = useMemo(() => {
    let filteredNodes = nodes
    let filteredRelationships = relationships

    // Apply filters
    if (filterType !== 'all') {
      filteredNodes = nodes.filter(node => node.type === filterType)
      const filteredNodeIds = new Set(filteredNodes.map(node => node.id))
      filteredRelationships = relationships.filter(rel => 
        filteredNodeIds.has(rel.source) && filteredNodeIds.has(rel.target)
      )
    }

    if (searchTerm) {
      filteredNodes = filteredNodes.filter(node => 
        node.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (node.properties.name && node.properties.name.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (node.properties.message && node.properties.message.toLowerCase().includes(searchTerm.toLowerCase()))
      )
      const filteredNodeIds = new Set(filteredNodes.map(node => node.id))
      filteredRelationships = filteredRelationships.filter(rel => 
        filteredNodeIds.has(rel.source) && filteredNodeIds.has(rel.target)
      )
    }

    // Transform to Neo4j NVL format
    const nvlNodes = filteredNodes.map(node => ({
      id: node.id,
      labels: [node.type],
      properties: {
        ...node.properties,
        caption: node.type === 'commit' 
          ? `${node.properties.sha?.slice(0, 8)}\n${node.properties.message?.slice(0, 30)}...`
          : node.type === 'developer'
          ? `${node.properties.name || node.properties.email?.split('@')[0]}\n${node.properties.total_commits || 0} commits`
          : node.id
      },
      style: {
        color: node.type === 'commit' ? '#3B82F6' : node.type === 'developer' ? '#10B981' : '#6B7280',
        'border-color': node.type === 'commit' ? '#1E40AF' : node.type === 'developer' ? '#059669' : '#4B5563',
        'text-color-internal': '#FFFFFF',
        'font-size': '12px'
      }
    }))

    const nvlRelationships = filteredRelationships.map((rel, index) => ({
      id: `${rel.source}-${rel.target}-${index}`,
      from: rel.source,
      to: rel.target,
      labels: [rel.type],
      properties: {
        type: rel.type
      },
      style: {
        'line-color': rel.type === 'AUTHORED' ? '#3B82F6' : '#9CA3AF',
        'target-arrow-color': rel.type === 'AUTHORED' ? '#3B82F6' : '#9CA3AF',
        'line-style': rel.type === 'PARENT_OF' ? 'dashed' : 'solid',
        width: rel.type === 'AUTHORED' ? 2 : 1
      }
    }))

    return {
      nodes: nvlNodes,
      relationships: nvlRelationships
    }
  }, [nodes, relationships, filterType, searchTerm])

  // Neo4j NVL Options
  const nvlOptions = {
    allowDynamicMinZoom: true,
    disableWebGL: false,
    maxZoom: 3,
    minZoom: 0.1,
    relationshipThreshold: 0.55,
    useWebGL: true,
    instanceId: 'codebase-graph',
    neo4jDesktopTheme: false,
    layout: {
      algorithm: 'force',
      options: {
        springLength: 200,
        springConstant: 0.0008,
        damping: 0.09,
        repulsion: 120000,
        theta: 0.9,
        gamma: 0.9,
        multiThreaded: false
      }
    }
  }

  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'commit': return GitCommit
      case 'developer': return User
      default: return GitBranch
    }
  }

  const handleNodeClick = (node: any) => {
    const originalNode = nodes.find(n => n.id === node.id)
    if (originalNode) {
      setSelectedNode(selectedNode?.id === originalNode.id ? null : originalNode)
    }
  }

  const handleDownloadGraph = () => {
    // This would typically trigger a download of the graph as an image
    console.log('Download graph functionality would be implemented here')
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      {/* Header with Controls */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 flex items-center space-x-2">
              <GitBranch className="w-6 h-6 text-blue-600" />
              <span>Repository Graph</span>
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Interactive visualization of commits, developers, and their relationships
            </p>
          </div>
          
          {/* Controls */}
          <div className="flex flex-wrap items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value as any)}
                className="text-sm border border-gray-300 rounded-lg px-3 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Nodes</option>
                <option value="commit">Commits Only</option>
                <option value="developer">Developers Only</option>
              </select>
            </div>
            
            <input
              type="text"
              placeholder="Search nodes..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="text-sm border border-gray-300 rounded-lg px-3 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            
            <div className="flex items-center space-x-1">
              <button
                onClick={handleDownloadGraph}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                title="Download Graph"
              >
                <Download className="w-4 h-4" />
              </button>
              <button
                onClick={() => window.location.reload()}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                title="Refresh"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
        
        {/* Stats */}
        <div className="mt-4 flex flex-wrap gap-4 text-sm text-gray-600">
          <span>Showing: {nvlData.nodes.length} nodes, {nvlData.relationships.length} relationships</span>
          <span>Total: {stats.total_nodes} nodes, {stats.total_relationships} relationships</span>
        </div>
      </div>

      {/* Graph Container */}
      <div className="p-6">
        <div className="flex gap-6">
          {/* Neo4j NVL Graph */}
          <div className="flex-1 bg-gray-50 rounded-lg border overflow-hidden">
            <div className="w-full h-[600px]">
              <InteractiveNvlWrapper
                nodes={nvlData.nodes}
                relationships={nvlData.relationships}
                nvlOptions={nvlOptions}
                interactionOptions={{
                  onNodeClick: handleNodeClick,
                  onRelationshipClick: (relationship: any) => {
                    console.log('Clicked relationship:', relationship)
                  },
                  onNodeHover: (node: any) => {
                    // Could show hover tooltip here
                  },
                  onCanvasClick: () => {
                    setSelectedNode(null)
                  }
                }}
                style={{ width: '100%', height: '100%' }}
              />
            </div>
          </div>

          {/* Node Details Panel */}
          {selectedNode && (
            <div className="w-80 bg-white border border-gray-200 rounded-lg p-4 space-y-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    selectedNode.type === 'commit' ? 'bg-blue-500' : 
                    selectedNode.type === 'developer' ? 'bg-green-500' : 'bg-gray-500'
                  }`}>
                    {(() => {
                      const NodeIcon = getNodeIcon(selectedNode.type)
                      return <NodeIcon className="w-4 h-4 text-white" />
                    })()}
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900 capitalize">{selectedNode.type}</h3>
                    <p className="text-xs text-gray-500">{selectedNode.id}</p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedNode(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
              
              <div className="space-y-3 text-sm">
                {selectedNode.type === 'commit' && (
                  <>
                    <div>
                      <label className="font-medium text-gray-700">Message:</label>
                      <p className="text-gray-600 break-words">{selectedNode.properties.message || 'No message'}</p>
                    </div>
                    <div>
                      <label className="font-medium text-gray-700">Author:</label>
                      <p className="text-gray-600">{selectedNode.properties.author_name}</p>
                    </div>
                    <div>
                      <label className="font-medium text-gray-700">Date:</label>
                      <p className="text-gray-600">
                        {selectedNode.properties.timestamp 
                          ? new Date(selectedNode.properties.timestamp).toLocaleDateString()
                          : 'Unknown'
                        }
                      </p>
                    </div>
                    <div>
                      <label className="font-medium text-gray-700">Changes:</label>
                      <p className="text-gray-600">
                        +{selectedNode.properties.insertions || 0} -{selectedNode.properties.deletions || 0}
                      </p>
                    </div>
                    {selectedNode.properties.feature_summary && (
                      <div>
                        <label className="font-medium text-gray-700">Summary:</label>
                        <p className="text-gray-600">{selectedNode.properties.feature_summary}</p>
                      </div>
                    )}
                  </>
                )}
                
                {selectedNode.type === 'developer' && (
                  <>
                    <div>
                      <label className="font-medium text-gray-700">Name:</label>
                      <p className="text-gray-600">{selectedNode.properties.name}</p>
                    </div>
                    <div>
                      <label className="font-medium text-gray-700">Email:</label>
                      <p className="text-gray-600 break-words">{selectedNode.properties.email}</p>
                    </div>
                    <div>
                      <label className="font-medium text-gray-700">Total Commits:</label>
                      <p className="text-gray-600">{selectedNode.properties.total_commits || 0}</p>
                    </div>
                    <div>
                      <label className="font-medium text-gray-700">Contribution Score:</label>
                      <p className="text-gray-600">{selectedNode.properties.contribution_score || 0}</p>
                    </div>
                    {selectedNode.properties.expertise_areas && (
                      <div>
                        <label className="font-medium text-gray-700">Expertise:</label>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {selectedNode.properties.expertise_areas.map((area: string, i: number) => (
                            <span key={i} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                              {area}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
              
              {/* Connected nodes */}
              <div>
                <label className="font-medium text-gray-700">Connected to:</label>
                <div className="mt-2 space-y-1">
                  {relationships
                    .filter(rel => rel.source === selectedNode.id || rel.target === selectedNode.id)
                    .slice(0, 5)
                    .map((rel, i) => {
                      const connectedId = rel.source === selectedNode.id ? rel.target : rel.source
                      const connectedNode = nodes.find(n => n.id === connectedId)
                      return (
                        <div key={i} className="flex items-center space-x-2 text-xs">
                          <div className={`w-2 h-2 rounded-full ${
                            connectedNode?.type === 'commit' ? 'bg-blue-500' : 
                            connectedNode?.type === 'developer' ? 'bg-green-500' : 'bg-gray-500'
                          }`}></div>
                          <span className="text-gray-600">{rel.type}</span>
                          <span className="text-gray-800">{connectedId.slice(0, 20)}...</span>
                        </div>
                      )
                    })}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Legend */}
        <div className="mt-6 flex items-center justify-center space-x-6 text-sm">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-blue-500 rounded-full"></div>
            <span className="text-gray-600">Commits</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-green-500 rounded-full"></div>
            <span className="text-gray-600">Developers</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-8 h-0.5 bg-blue-500"></div>
            <span className="text-gray-600">Authored</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-8 h-0.5 bg-gray-400" style={{ backgroundImage: 'repeating-linear-gradient(to right, transparent, transparent 2px, #9CA3AF 2px, #9CA3AF 4px)' }}></div>
            <span className="text-gray-600">Parent Of</span>
          </div>
        </div>
      </div>
    </div>
  )
}