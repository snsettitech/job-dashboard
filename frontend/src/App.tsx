import {
  AlertCircle,
  Bot,
  Briefcase,
  CheckCircle,
  Clock,
  DollarSign,
  MapPin,
  Pause,
  Play,
  Search,
  Send,
  Settings,
  Target,
  TrendingUp,
  Wifi,
  WifiOff,
  Zap
} from 'lucide-react';
import React, { useCallback, useEffect, useState } from 'react';
import { AutoApply } from './components/AutoApply';
import { JobScraper } from './components/JobScraper';
import ResumeOptimizer from './components/ResumeOptimizer';

// Types
interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  posted_date: string;
  salary_range?: number[];
  required_skills: string[];
  quality_score: number;
  source_url: string;
}

interface Scores {
  overall: number;
  skills: number;
  experience: number;
  location: number;
  salary: number;
}

interface Match {
  match_id: string;
  job: Job;
  scores: Scores;
  rank: number;
  already_applied: boolean;
}

interface Application {
  id: string;
  job: {
    title: string;
    company: string;
    location: string;
  };
  status: string;
  application_method: string;
  submitted_at: string;
  last_status_update: string;
  needs_follow_up: boolean;
  follow_up_sent: boolean;
}

interface DashboardData {
  total_applications: number;
  applications_this_month: number;
  pending_applications: number;
  interviews_scheduled: number;
  current_matches: number;
  auto_apply_enabled: boolean;
  last_activity: string;
}

// Real API service
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = {
  async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  },

  async getDashboard(): Promise<DashboardData> {
    return this.request<DashboardData>('/api/dashboard');
  },

  async getMatches(): Promise<{ matches: Match[]; total_matches: number }> {
    return this.request<{ matches: Match[]; total_matches: number }>('/api/matches');
  },

  async getApplications(): Promise<{ applications: Application[] }> {
    return this.request<{ applications: Application[] }>('/api/applications');
  },

  async applyToJob(jobId: string): Promise<{ message: string; task_id: string }> {
    return this.request<{ message: string; task_id: string }>(`/api/jobs/${jobId}/apply`, {
      method: 'POST',
    });
  },

  async healthCheck(): Promise<{ status: string; version: string }> {
    return this.request<{ status: string; version: string }>('/health');
  }
};

const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [applying, setApplying] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);
  const [apiConnected, setApiConnected] = useState<boolean>(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Health check first
      await api.healthCheck();
      setApiConnected(true);

      if (activeTab === 'dashboard') {
        const data = await api.getDashboard();
        setDashboardData(data);
        const matchData = await api.getMatches();
        setMatches(matchData.matches.slice(0, 3)); // Show top 3 on dashboard
      } else if (activeTab === 'matches') {
        const data = await api.getMatches();
        setMatches(data.matches);
      } else if (activeTab === 'applications') {
        const data = await api.getApplications();
        setApplications(data.applications);
      }
    } catch (error) {
      console.error('Error loading data:', error);
      setApiConnected(false);
      setError('Failed to connect to Recruitly API. Make sure the backend server is running on http://localhost:8000');
    } finally {
      setLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleApply = async (jobId: string) => {
    setApplying(prev => ({ ...prev, [jobId]: true }));
    try {
      const result = await api.applyToJob(jobId);
      console.log('Application result:', result);

      // Update the match to show as applied
      setMatches(prev => prev.map(match =>
        match.job.id === jobId
          ? { ...match, already_applied: true }
          : match
      ));

      // Show success message (you could add a toast notification here)
      alert(`🎉 ${result.message}`);
    } catch (error) {
      console.error('Application failed:', error);
      setError('Failed to apply to job. Please try again.');
    } finally {
      setApplying(prev => ({ ...prev, [jobId]: false }));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Connecting to Recruitly API...</p>
        </div>
      </div>
    );
  }

  if (error && !apiConnected) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center max-w-md">
          <WifiOff className="h-16 w-16 text-red-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Backend Connection Error</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <div className="space-y-3">
            <button
              onClick={() => window.location.reload()}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors w-full"
            >
              Retry Connection
            </button>
            <div className="text-xs text-gray-500 space-y-1">
              <p>Make sure your backend is running:</p>
              <code className="bg-gray-100 px-2 py-1 rounded">python backend/main.py</code>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Briefcase className="h-8 w-8 text-blue-600" />
              <h1 className="ml-3 text-xl font-semibold text-gray-900">Recruitly</h1>
              <div className="ml-3 flex items-center space-x-2">
                <div className={`flex items-center px-2 py-1 rounded-full text-xs font-medium ${apiConnected
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
                  }`}>
                  {apiConnected ? (
                    <>
                      <Wifi className="h-3 w-3 mr-1" />
                      LIVE API
                    </>
                  ) : (
                    <>
                      <WifiOff className="h-3 w-3 mr-1" />
                      DISCONNECTED
                    </>
                  )}
                </div>
                <div className="flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                  <Zap className="h-3 w-3 mr-1" />
                  MVP
                </div>
              </div>
            </div>

            <nav className="flex space-x-8">
              {[
                { key: 'dashboard', label: 'Dashboard', icon: TrendingUp },
                { key: 'optimizer', label: 'AI Optimizer', icon: Bot },
                { key: 'scraper', label: 'Job Scraper', icon: Search },
                { key: 'auto-apply', label: 'Auto Apply', icon: Send },
                { key: 'matches', label: 'Matches', icon: Target },
                { key: 'applications', label: 'Applications', icon: Briefcase },
                { key: 'settings', label: 'Settings', icon: Settings }
              ].map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  onClick={() => setActiveTab(key)}
                  className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === key
                    ? 'text-blue-600 bg-blue-50'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }`}
                >
                  <Icon className="h-4 w-4 mr-2" />
                  {label}
                </button>
              ))}
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* Welcome Message */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-6 text-white">
              <h2 className="text-2xl font-bold mb-2">Welcome to Recruitly MVP! 🚀</h2>
              <p className="opacity-90">Your AI-powered job application assistant is now connected to live data. This is the foundation of your autonomous job search platform.</p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[
                {
                  label: 'Total Applications',
                  value: dashboardData?.total_applications || 0,
                  icon: Briefcase,
                  color: 'blue',
                  change: '+15%'
                },
                {
                  label: 'This Month',
                  value: dashboardData?.applications_this_month || 0,
                  icon: TrendingUp,
                  color: 'green',
                  change: '+23%'
                },
                {
                  label: 'Interviews',
                  value: dashboardData?.interviews_scheduled || 0,
                  icon: CheckCircle,
                  color: 'purple',
                  change: '+50%'
                },
                {
                  label: 'Pending',
                  value: dashboardData?.pending_applications || 0,
                  icon: Clock,
                  color: 'yellow',
                  change: '-12%'
                }
              ].map(({ label, value, icon: Icon, color, change }) => (
                <div key={label} className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">{label}</p>
                      <p className="text-2xl font-semibold text-gray-900">{value}</p>
                      <p className={`text-xs mt-1 ${change.startsWith('+') ? 'text-green-600' : 'text-red-600'
                        }`}>
                        {change} from last month
                      </p>
                    </div>
                    <Icon className={`h-8 w-8 text-${color}-600`} />
                  </div>
                </div>
              ))}
            </div>

            {/* Auto-Apply Status */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  {dashboardData?.auto_apply_enabled ? (
                    <Play className="h-5 w-5 text-green-600 mr-3" />
                  ) : (
                    <Pause className="h-5 w-5 text-yellow-600 mr-3" />
                  )}
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">AI Auto-Apply Engine</h3>
                    <p className="text-sm text-gray-600">
                      {dashboardData?.auto_apply_enabled
                        ? '🤖 Actively scanning and applying to matching jobs (Demo Mode)'
                        : 'Auto-apply is currently paused'
                      }
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-semibold text-blue-600">
                    {dashboardData?.current_matches || 0}
                  </p>
                  <p className="text-sm text-gray-600">Active Matches</p>
                </div>
              </div>
            </div>

            {/* Top Matches Preview */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-gray-900">🎯 Top AI-Matched Jobs</h3>
                  <button
                    onClick={() => setActiveTab('matches')}
                    className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                  >
                    View All {dashboardData?.current_matches} Matches →
                  </button>
                </div>
              </div>
              <div className="divide-y divide-gray-200">
                {matches.length > 0 ? (
                  matches.map((match) => (
                    <JobCard key={match.match_id} match={match} onApply={handleApply} applying={applying} />
                  ))
                ) : (
                  <div className="p-6 text-center text-gray-500">
                    Loading job matches...
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'optimizer' && (
          <ResumeOptimizer />
        )}

        {activeTab === 'scraper' && (
          <JobScraper />
        )}

        {activeTab === 'auto-apply' && (
          <AutoApply />
        )}

        {activeTab === 'matches' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-semibold text-gray-900">🎯 AI-Matched Jobs</h2>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <Search className="h-4 w-4 text-gray-400" />
                  <span className="text-sm text-gray-600">
                    {matches.length} high-quality matches found
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow divide-y divide-gray-200">
              {matches.map((match) => (
                <JobCard key={match.match_id} match={match} onApply={handleApply} applying={applying} />
              ))}
            </div>
          </div>
        )}

        {activeTab === 'applications' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-semibold text-gray-900">📋 My Applications</h2>

            <div className="bg-white rounded-lg shadow">
              <div className="divide-y divide-gray-200">
                {applications.map((app) => (
                  <ApplicationCard key={app.id} application={app} />
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-semibold text-gray-900">⚙️ Settings & Configuration</h2>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">🚀 Next Phase Features</h3>
                <div className="space-y-3">
                  <div className="flex items-center p-3 border rounded-lg">
                    <div className="flex-shrink-0">
                      <Zap className="h-5 w-5 text-yellow-500" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">Resume Optimization AI</p>
                      <p className="text-xs text-gray-500">OpenAI-powered resume tailoring for each job</p>
                    </div>
                  </div>

                  <div className="flex items-center p-3 border rounded-lg">
                    <div className="flex-shrink-0">
                      <Target className="h-5 w-5 text-blue-500" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">Semantic Job Matching</p>
                      <p className="text-xs text-gray-500">RAFT-powered matching beyond keywords</p>
                    </div>
                  </div>

                  <div className="flex items-center p-3 border rounded-lg">
                    <div className="flex-shrink-0">
                      <Search className="h-5 w-5 text-green-500" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">Automated Job Sourcing</p>
                      <p className="text-xs text-gray-500">Real-time scraping from major job boards</p>
                    </div>
                  </div>

                  <div className="flex items-center p-3 border rounded-lg">
                    <div className="flex-shrink-0">
                      <Briefcase className="h-5 w-5 text-purple-500" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">Agentic Auto-Apply</p>
                      <p className="text-xs text-gray-500">Multi-agent system for autonomous applications</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">📊 Current MVP Status</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">✅ FastAPI Backend</span>
                    <span className="text-xs text-green-600 font-medium">Connected</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">✅ React Frontend</span>
                    <span className="text-xs text-green-600 font-medium">Running</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">✅ Live API Integration</span>
                    <span className="text-xs text-green-600 font-medium">Active</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">🔄 OpenAI Integration</span>
                    <span className="text-xs text-yellow-600 font-medium">Pending</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">🔄 Database Setup</span>
                    <span className="text-xs text-yellow-600 font-medium">Pending</span>
                  </div>

                  <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-800">
                      <strong>🎯 Phase 1A Progress:</strong> Basic API connection established.
                      Ready to add AI matching engine and resume optimization.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">🔧 Technical Architecture</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Current Stack</h4>
                  <ul className="space-y-1 text-sm text-gray-600">
                    <li>• Frontend: React + TypeScript + Tailwind</li>
                    <li>• Backend: FastAPI + Python</li>
                    <li>• Hosting: Localhost (Development)</li>
                    <li>• Data: Mock API responses</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Next Phase</h4>
                  <ul className="space-y-1 text-sm text-gray-600">
                    <li>• AI: OpenAI GPT-4o-mini integration</li>
                    <li>• Database: PostgreSQL + SQLAlchemy</li>
                    <li>• Matching: RAFT-powered semantic search</li>
                    <li>• Deploy: Railway + Netlify</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

// JobCard Component
interface JobCardProps {
  match: Match;
  onApply: (jobId: string) => void;
  applying: Record<string, boolean>;
}

const JobCard: React.FC<JobCardProps> = ({ match, onApply, applying }) => {
  const { job, scores } = match;

  const formatSalary = (range?: number[]): string => {
    if (!range) return 'Not specified';
    return `${(range[0] / 1000).toFixed(0)}k - ${(range[1] / 1000).toFixed(0)}k`;
  };

  const getMatchColor = (score: number): string => {
    if (score >= 0.9) return 'bg-green-100 text-green-800 border-green-200';
    if (score >= 0.8) return 'bg-blue-100 text-blue-800 border-blue-200';
    if (score >= 0.7) return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    return 'bg-gray-100 text-gray-800 border-gray-200';
  };

  return (
    <div className="p-6 hover:bg-gray-50 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-3 mb-2">
            <h3 className="text-lg font-medium text-gray-900 truncate">
              {job.title}
            </h3>
            <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${getMatchColor(scores.overall)}`}>
              🎯 {Math.round(scores.overall * 100)}% match
            </div>
            <div className="flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
              Rank #{match.rank}
            </div>
          </div>

          <div className="flex items-center text-sm text-gray-600 space-x-4 mb-3">
            <div className="flex items-center">
              <Briefcase className="h-4 w-4 mr-1" />
              {job.company}
            </div>
            <div className="flex items-center">
              <MapPin className="h-4 w-4 mr-1" />
              {job.location}
            </div>
            <div className="flex items-center">
              <DollarSign className="h-4 w-4 mr-1" />
              {formatSalary(job.salary_range)}
            </div>
          </div>

          <div className="flex flex-wrap gap-2 mb-4">
            {job.required_skills.slice(0, 6).map((skill) => (
              <span
                key={skill}
                className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
              >
                {skill}
              </span>
            ))}
            {job.required_skills.length > 6 && (
              <span className="text-xs text-gray-500">
                +{job.required_skills.length - 6} more
              </span>
            )}
          </div>

          <div className="grid grid-cols-4 gap-4 text-center">
            {[
              { label: 'Skills', score: scores.skills, emoji: '🛠️' },
              { label: 'Experience', score: scores.experience, emoji: '📊' },
              { label: 'Location', score: scores.location, emoji: '📍' },
              { label: 'Salary', score: scores.salary, emoji: '💰' }
            ].map(({ label, score, emoji }) => (
              <div key={label}>
                <div className="text-xs text-gray-500">{emoji} {label}</div>
                <div className={`text-sm font-medium ${score >= 0.9 ? 'text-green-600' :
                  score >= 0.8 ? 'text-blue-600' :
                    score >= 0.7 ? 'text-yellow-600' : 'text-gray-600'
                  }`}>
                  {Math.round(score * 100)}%
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="flex-shrink-0 ml-6">
          <div className="flex flex-col space-y-2">
            <a
              href={job.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors text-center"
            >
              View Job
            </a>
            {match.already_applied ? (
              <div className="px-4 py-2 bg-green-100 text-green-800 rounded-md text-sm font-medium text-center border border-green-200">
                ✅ Applied
              </div>
            ) : (
              <button
                onClick={() => onApply(job.id)}
                disabled={applying[job.id]}
                className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:bg-blue-400 transition-colors flex items-center justify-center"
              >
                {applying[job.id] ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Applying...
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4 mr-1" />
                    Quick Apply
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// ApplicationCard Component
interface ApplicationCardProps {
  application: Application;
}

const ApplicationCard: React.FC<ApplicationCardProps> = ({ application }) => {
  const { job, status, submitted_at, application_method } = application;

  const getStatusConfig = (status: string) => {
    const configs: Record<string, { color: string; emoji: string; label: string }> = {
      'pending': { color: 'text-yellow-600 bg-yellow-50 border-yellow-200', emoji: '⏳', label: 'PENDING' },
      'submitted': { color: 'text-blue-600 bg-blue-50 border-blue-200', emoji: '📤', label: 'SUBMITTED' },
      'interview_scheduled': { color: 'text-green-600 bg-green-50 border-green-200', emoji: '🎯', label: 'INTERVIEW SCHEDULED' },
      'rejected': { color: 'text-red-600 bg-red-50 border-red-200', emoji: '❌', label: 'REJECTED' },
      'offer': { color: 'text-purple-600 bg-purple-50 border-purple-200', emoji: '🎉', label: 'OFFER RECEIVED' }
    };
    return configs[status] || { color: 'text-gray-600 bg-gray-50 border-gray-200', emoji: '📋', label: status.toUpperCase() };
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const statusConfig = getStatusConfig(status);

  return (
    <div className="p-6 hover:bg-gray-50 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-medium text-gray-900">
            {job.title}
          </h3>
          <div className="flex items-center text-sm text-gray-600 space-x-4 mt-1">
            <span className="flex items-center">
              <Briefcase className="h-4 w-4 mr-1" />
              {job.company}
            </span>
            <span className="flex items-center">
              <MapPin className="h-4 w-4 mr-1" />
              {job.location}
            </span>
          </div>
          <div className="flex items-center space-x-4 mt-3">
            <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${statusConfig.color}`}>
              {statusConfig.emoji} {statusConfig.label}
            </div>
            <span className="text-xs text-gray-500">
              Applied {formatDate(submitted_at)} • {application_method}
            </span>
          </div>
        </div>

        <div className="flex-shrink-0">
          {application.needs_follow_up && !application.follow_up_sent && (
            <div className="flex items-center text-yellow-600 bg-yellow-50 px-3 py-1 rounded-full text-xs">
              <AlertCircle className="h-4 w-4 mr-1" />
              Follow-up due
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;