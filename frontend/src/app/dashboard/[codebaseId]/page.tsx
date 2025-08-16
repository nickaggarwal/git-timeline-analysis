"use client";

import { useParams, useSearchParams } from "next/navigation";
import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { 
  MessageSquare, 
  GitBranch, 
  Clock, 
  Users, 
  Activity,
  CheckCircle,
  Loader,
  AlertCircle
} from "lucide-react";
import { DeveloperScorecard } from "@/components/dashboard/DeveloperScorecard";
import { TimelineView } from "@/components/dashboard/TimelineView";
import { GraphView } from "@/components/dashboard/GraphView";

// Tabs for dashboard navigation
const tabs = [
  { id: "chat", name: "Chat", icon: MessageSquare },
  { id: "graph", name: "Graph", icon: GitBranch },
  { id: "timeline", name: "Timeline", icon: Clock },
  { id: "developers", name: "Developers", icon: Users },
] as const;

type TabId = typeof tabs[number]["id"];

export default function Dashboard() {
  const params = useParams();
  const searchParams = useSearchParams();
  const codebaseId = params.codebaseId as string;
  const jobId = searchParams.get("jobId");
  
  const [activeTab, setActiveTab] = useState<TabId>("chat");
  const [analysisComplete, setAnalysisComplete] = useState(false);

  // Poll for analysis status if we have a job ID
  const { data: analysisStatus, isLoading: statusLoading } = useQuery({
    queryKey: ["analysisStatus", jobId],
    queryFn: async () => {
      if (!jobId) return null;
      const response = await fetch(`http://localhost:8001/status/${jobId}`);
      if (!response.ok) throw new Error("Failed to fetch status");
      return response.json();
    },
    enabled: !!jobId && !analysisComplete,
    refetchInterval: analysisComplete ? false : 2000, // Poll every 2 seconds until complete
  });

  // Fetch codebase summary once analysis is complete
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ["codebaseSummary", codebaseId],
    queryFn: async () => {
      const response = await fetch(`http://localhost:8001/codebase/${codebaseId}/summary`);
      if (!response.ok) throw new Error("Failed to fetch summary");
      return response.json();
    },
    enabled: analysisComplete || !jobId, // Enable immediately if no jobId (already analyzed)
  });

  useEffect(() => {
    if (analysisStatus?.status === "completed") {
      setAnalysisComplete(true);
    }
  }, [analysisStatus]);

  // Show analysis progress
  if (jobId && !analysisComplete) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center space-y-6 max-w-md">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
            {statusLoading ? (
              <Loader className="w-8 h-8 text-blue-600 animate-spin" />
            ) : analysisStatus?.status === "failed" ? (
              <AlertCircle className="w-8 h-8 text-red-600" />
            ) : (
              <Activity className="w-8 h-8 text-blue-600 animate-pulse" />
            )}
          </div>
          
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              {analysisStatus?.status === "failed" ? "Analysis Failed" : "Analyzing Repository"}
            </h2>
            <p className="text-gray-600 mb-4">
              {analysisStatus?.progress || "Starting analysis..."}
            </p>
            
            {analysisStatus?.status === "failed" && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-left">
                <p className="text-red-700 text-sm">
                  {analysisStatus.error || "Unknown error occurred"}
                </p>
              </div>
            )}
          </div>

          {analysisStatus?.status !== "failed" && (
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: "60%" }}></div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl p-6 border border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {codebaseId}
            </h1>
            <p className="text-gray-600 mt-1">
              Repository analysis and time machine dashboard
            </p>
          </div>
          <div className="flex items-center space-x-2 text-green-600">
            <CheckCircle className="w-5 h-5" />
            <span className="text-sm font-medium">Analysis Complete</span>
          </div>
        </div>

        {/* Stats */}
        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-gray-100">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {summary.graph_data?.stats?.total_nodes || 0}
              </div>
              <div className="text-sm text-gray-600">Total Nodes</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {summary.developer_expertise?.length || 0}
              </div>
              <div className="text-sm text-gray-600">Developers</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {summary.graph_data?.stats?.total_relationships || 0}
              </div>
              <div className="text-sm text-gray-600">Relationships</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {summary.graph_data?.nodes?.filter((n: any) => n.type === "commit")?.length || 0}
              </div>
              <div className="text-sm text-gray-600">Commits</div>
            </div>
          </div>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-xl border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? "border-blue-500 text-blue-600"
                      : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.name}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === "chat" && <ChatTab codebaseId={codebaseId} />}
          {activeTab === "graph" && <GraphTab codebaseId={codebaseId} />}
          {activeTab === "timeline" && <TimelineTab codebaseId={codebaseId} />}
          {activeTab === "developers" && <DevelopersTab codebaseId={codebaseId} />}
        </div>
      </div>
    </div>
  );
}

// Tab Components (placeholder implementations)
function ChatTab({ codebaseId }: { codebaseId: string }) {
  const [message, setMessage] = useState("");
  const [conversation, setConversation] = useState<Array<{
    type: "user" | "assistant";
    content: string;
  }>>([]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    const userMessage = { type: "user" as const, content: message };
    setConversation(prev => [...prev, userMessage]);
    setMessage("");

    try {
      const response = await fetch(`http://localhost:8001/codebase/${codebaseId}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message: message,
          conversation_history: conversation.map(msg => ({
            role: msg.type === "user" ? "user" : "assistant",
            content: msg.content
          }))
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setConversation(prev => [...prev, { type: "assistant", content: result.response || result.answer || "No response received" }]);
      }
    } catch (error) {
      setConversation(prev => [...prev, { 
        type: "assistant", 
        content: "Sorry, I couldn't process your question right now." 
      }]);
    }
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Chat with your codebase</h3>
      
      <div className="border border-gray-200 rounded-lg h-96 overflow-y-auto p-4 space-y-4">
        {conversation.length === 0 ? (
          <div className="text-center text-gray-500 mt-20">
            <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>Ask me anything about this repository!</p>
            <p className="text-sm mt-2">Try: "What features were added recently?" or "Who worked on authentication?"</p>
          </div>
        ) : (
          conversation.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.type === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                msg.type === "user" 
                  ? "bg-blue-500 text-white" 
                  : "bg-gray-100 text-gray-900"
              }`}>
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              </div>
            </div>
          ))
        )}
      </div>

      <form onSubmit={handleSendMessage} className="flex space-x-2">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Ask about the repository..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <button
          type="submit"
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          Send
        </button>
      </form>
    </div>
  );
}

function GraphTab({ codebaseId }: { codebaseId: string }) {
  const { data: graphData, isLoading } = useQuery({
    queryKey: ["graph", codebaseId],
    queryFn: async () => {
      const response = await fetch(`http://localhost:8001/codebase/${codebaseId}/graph`);
      if (!response.ok) throw new Error("Failed to fetch graph data");
      return response.json();
    },
  });

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <Loader className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-4" />
        <p className="text-gray-500">Loading graph data...</p>
      </div>
    );
  }

  if (!graphData) {
    return (
      <div className="text-center py-12">
        <GitBranch className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-700 mb-2">Graph Visualization</h3>
        <p className="text-gray-500">No graph data available</p>
      </div>
    );
  }

  return (
    <GraphView
      nodes={graphData.nodes || []}
      relationships={graphData.relationships || []}
      stats={graphData.stats || { total_nodes: 0, total_relationships: 0 }}
    />
  );
}

function TimelineTab({ codebaseId }: { codebaseId: string }) {
  const { data: timelineData, isLoading } = useQuery({
    queryKey: ["timeline", codebaseId],
    queryFn: async () => {
      const response = await fetch(`http://localhost:8001/codebase/${codebaseId}/timeline`);
      if (!response.ok) throw new Error("Failed to fetch timeline");
      return response.json();
    },
  });

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <Loader className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-4" />
        <p className="text-gray-500">Loading timeline...</p>
      </div>
    );
  }

  if (!timelineData?.commits?.length) {
    return (
      <div className="text-center py-12">
        <Clock className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-700 mb-2">Timeline View</h3>
        <p className="text-gray-500">No timeline data available</p>
      </div>
    );
  }

  return <TimelineView commits={timelineData.commits} milestones={timelineData.milestones || []} />;
}

function DevelopersTab({ codebaseId }: { codebaseId: string }) {
  const { data: developersData, isLoading } = useQuery({
    queryKey: ["developers", codebaseId],
    queryFn: async () => {
      const response = await fetch(`http://localhost:8001/codebase/${codebaseId}/developers`);
      if (!response.ok) throw new Error("Failed to fetch developers");
      return response.json();
    },
  });

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <Loader className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-4" />
        <p className="text-gray-500">Loading developer data...</p>
      </div>
    );
  }

  if (!developersData?.developers?.length) {
    return (
      <div className="text-center py-12">
        <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-700 mb-2">Developer Insights</h3>
        <p className="text-gray-500">No developer data available</p>
      </div>
    );
  }

  return <DeveloperScorecard developers={developersData.developers} codebaseId={codebaseId} />;
}