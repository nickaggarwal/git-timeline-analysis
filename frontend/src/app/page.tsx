"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Github, Clock, Users, GitBranch, Search, ArrowRight, Database, FileText } from "lucide-react";

interface PreviousAnalysis {
  id: string;
  name: string;
  git_url: string;
  total_commits?: number;
  total_developers?: number;
  last_analyzed?: string;
}

export default function Home() {
  const [gitUrl, setGitUrl] = useState("");
  const [maxCommits, setMaxCommits] = useState(100);
  const [isLoading, setIsLoading] = useState(false);
  const [previousAnalyses, setPreviousAnalyses] = useState<PreviousAnalysis[]>([]);
  const [loadingPrevious, setLoadingPrevious] = useState(true);
  const router = useRouter();

  // Fetch previous analyses on component mount
  useEffect(() => {
    const fetchPreviousAnalyses = async () => {
      try {
        const response = await fetch("http://localhost:8001/codebases");
        if (response.ok) {
          const data = await response.json();
          setPreviousAnalyses(data);
        }
      } catch (error) {
        console.error("Failed to fetch previous analyses:", error);
      } finally {
        setLoadingPrevious(false);
      }
    };

    fetchPreviousAnalyses();
  }, []);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!gitUrl.trim()) return;

    setIsLoading(true);
    
    try {
      // Call backend API to start analysis
      const response = await fetch("http://localhost:8001/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          git_url: gitUrl,
          include_llm_analysis: true,
          max_commits: maxCommits,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        // Navigate to dashboard with codebase ID
        router.push(`/dashboard/${result.codebase_id}?jobId=${result.analysis_summary.job_id}`);
      } else {
        console.error("Analysis failed");
        alert("Failed to start analysis. Please check the URL and try again.");
      }
    } catch (error) {
      console.error("Error starting analysis:", error);
      alert("Error starting analysis. Please make sure the backend is running.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <div className="text-center space-y-6">
        <div className="space-y-4">
          <h1 className="text-5xl font-bold text-gray-900 tracking-tight">
            Codebase Time Machine
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
            Navigate any codebase through time, understanding the evolution of features and architectural decisions
          </p>
        </div>

        {/* Feature Icons */}
        <div className="flex justify-center items-center space-x-8 pt-8">
          <div className="flex items-center space-x-2 text-blue-600">
            <Clock className="w-6 h-6" />
            <span className="font-medium">Time Travel</span>
          </div>
          <div className="flex items-center space-x-2 text-green-600">
            <Users className="w-6 h-6" />
            <span className="font-medium">Developer Insights</span>
          </div>
          <div className="flex items-center space-x-2 text-purple-600">
            <GitBranch className="w-6 h-6" />
            <span className="font-medium">Code Evolution</span>
          </div>
          <div className="flex items-center space-x-2 text-orange-600">
            <Search className="w-6 h-6" />
            <span className="font-medium">AI-Powered Chat</span>
          </div>
        </div>
      </div>

      {/* Previous Analyses Section */}
      {!loadingPrevious && previousAnalyses.length > 0 && (
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center space-x-3 mb-6">
            <Database className="w-6 h-6 text-blue-600" />
            <h2 className="text-2xl font-bold text-gray-900">Previous Analyses</h2>
            <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
              {previousAnalyses.length} codebase{previousAnalyses.length !== 1 ? 's' : ''}
            </span>
          </div>
          
          <div className="grid md:grid-cols-2 gap-4 mb-12">
            {previousAnalyses.map((analysis) => (
              <div 
                key={analysis.id}
                onClick={() => router.push(`/dashboard/${analysis.id}`)}
                className="bg-white rounded-xl p-6 border border-gray-200 hover:shadow-lg hover:border-blue-300 transition-all cursor-pointer group"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                      <Github className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                        {analysis.name}
                      </h3>
                      <p className="text-sm text-gray-500 truncate max-w-xs">
                        {analysis.git_url}
                      </p>
                    </div>
                  </div>
                  <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-blue-600 transform group-hover:translate-x-1 transition-all" />
                </div>
                
                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  {analysis.total_commits && (
                    <div className="flex items-center space-x-1">
                      <FileText className="w-4 h-4" />
                      <span>{analysis.total_commits} commits</span>
                    </div>
                  )}
                  {analysis.total_developers && (
                    <div className="flex items-center space-x-1">
                      <Users className="w-4 h-4" />
                      <span>{analysis.total_developers} developers</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Input Section */}
      <div className="max-w-2xl mx-auto">
        <form onSubmit={handleAnalyze} className="space-y-6">
          <div className="relative">
            <label htmlFor="git-url" className="block text-sm font-medium text-gray-700 mb-2">
              Enter GitHub Repository URL
            </label>
            <div className="relative">
              <Github className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                id="git-url"
                type="url"
                value={gitUrl}
                onChange={(e) => setGitUrl(e.target.value)}
                placeholder="https://github.com/username/repository"
                className="w-full pl-12 pr-4 py-4 border border-gray-300 rounded-xl text-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                required
              />
            </div>
            <p className="mt-2 text-sm text-gray-500">
              We&apos;ll analyze the repository&apos;s commit history, developers, and code evolution
            </p>
          </div>

          {/* Commit Limit Selector */}
          <div className="space-y-3">
            <label htmlFor="max-commits" className="block text-sm font-medium text-gray-700">
              Maximum commits to analyze
            </label>
            <div className="flex items-center space-x-4">
              <input
                id="max-commits"
                type="range"
                min="10"
                max="1000"
                step="10"
                value={maxCommits}
                onChange={(e) => setMaxCommits(parseInt(e.target.value))}
                className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
              />
              <div className="flex items-center space-x-2">
                <input
                  type="number"
                  min="10"
                  max="1000"
                  value={maxCommits}
                  onChange={(e) => setMaxCommits(parseInt(e.target.value) || 100)}
                  className="w-20 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <span className="text-sm text-gray-500">commits</span>
              </div>
            </div>
            <div className="flex justify-between text-xs text-gray-500">
              <span>Faster analysis</span>
              <span className="font-medium">
                {maxCommits <= 50 ? "Quick (~1 min)" : 
                 maxCommits <= 200 ? "Medium (~3 min)" : 
                 "Detailed (~5+ min)"}
              </span>
              <span>More comprehensive</span>
            </div>
            <p className="text-sm text-gray-500">
              Higher limits provide more detailed insights but take longer to process. 
              Recommended: 100-200 commits for most repositories.
            </p>
          </div>

          <button
            type="submit"
            disabled={isLoading || !gitUrl.trim()}
            className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-500 text-white font-medium py-4 px-6 rounded-xl transition-all transform hover:scale-[1.02] disabled:scale-100 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            {isLoading ? (
              <>
                <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                <span>Analyzing Repository...</span>
              </>
            ) : (
              <>
                <span>Start Time Machine Analysis</span>
                <ArrowRight className="w-5 h-5" />
              </>
            )}
          </button>
        </form>

        {/* Sample URLs */}
        <div className="mt-8 p-6 bg-white/70 rounded-xl border border-gray-200">
          <h3 className="font-medium text-gray-900 mb-3">Try with sample repositories:</h3>
          <div className="space-y-2">
            {[
              "https://github.com/microsoft/vscode",
              "https://github.com/facebook/react", 
              "https://github.com/vercel/next.js"
            ].map((url) => (
              <button
                key={url}
                onClick={() => setGitUrl(url)}
                className="block text-left text-blue-600 hover:text-blue-800 text-sm hover:underline"
              >
                {url}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 pt-12">
        {[
          {
            icon: Clock,
            title: "Time Travel",
            description: "Navigate through commit history and see how your codebase evolved over time",
            color: "text-blue-600 bg-blue-50"
          },
          {
            icon: Users,
            title: "Developer Insights", 
            description: "Understand who contributed what, expertise areas, and collaboration patterns",
            color: "text-green-600 bg-green-50"
          },
          {
            icon: GitBranch,
            title: "Code Evolution",
            description: "Visualize how features were built, refactored, and how complexity grew",
            color: "text-purple-600 bg-purple-50"
          },
          {
            icon: Search,
            title: "AI-Powered Chat",
            description: "Ask questions about your codebase history and get intelligent answers",
            color: "text-orange-600 bg-orange-50"
          }
        ].map((feature, index) => {
          const IconComponent = feature.icon;
          return (
            <div key={index} className="bg-white rounded-xl p-6 border border-gray-200 hover:shadow-lg transition-shadow">
              <div className={`w-12 h-12 rounded-lg ${feature.color} flex items-center justify-center mb-4`}>
                <IconComponent className="w-6 h-6" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">{feature.title}</h3>
              <p className="text-gray-600 text-sm">{feature.description}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}