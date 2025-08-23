import React, { useState, useEffect, useCallback } from 'react';import { 
  Upload, 
  Search, 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  TrendingUp,
  Briefcase,
  MapPin,
  DollarSign,
  Target,
  Settings,
  Play,
  Pause
} from 'lucide-react';

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

// Mock API service
const api = {
  async getDashboard(): Promise<DashboardData> {
    return {
      total_applications: 23,
      applications_this_month: 8,
      pending_applications: 3,
      interviews_scheduled: 2,
      current_matches: 15,
      auto_apply_enabled: true,
      last_activity: '2024-03-15T10:30:00Z'
    };
  },
  
  async getMatches(): Promise<{ matches: Match[]; total_matches: number }> {
    return {
      matches: [
        {
          match_id: '1',
          job: {
            id: '1',
            title: 'Senior Python Developer',
            company: 'TechCorp Inc',
            location: 'San Francisco, CA (Remote)',
            posted_date: '2024-03-10T00:00:00Z',
            salary_range: [120000, 180000],
            required_skills: ['Python', 'Django', 'PostgreSQL', 'AWS'],
            quality_score: 0.92,
            source_url: 'https://jobs.techcorp.com/senior-python-dev'
          },
          scores: {
            overall: 0.89,
            skills: 0.95,
            experience: 0.85,
            location: 1.0,
            salary: 0.78
          },
          rank: 1,
          already_applied: false
        },
        {
          match_id: '2',
          job: {
            id: '2',
            title: 'Full Stack Engineer',
            company: 'StartupXYZ',
            location: 'New York, NY',
            posted_date: '2024-03-12T00:00:00Z',
            salary_range: [90000, 130000],
            required_skills: ['React', 'Node.js', 'MongoDB', 'Docker'],
            quality_score: 0.87,
            source_url: 'https://startupxyz.com/careers/fullstack'
          },
          scores: {
            overall: 0.82,
            skills: 0.88,
            experience: 0.80,
            location: 0.75,
            salary: 0.85
          },
          rank: 2,
          already_applied: false
        }
      ],
      total_matches: 15
    };
  },
  
  async getApplications(): Promise<{ applications: Application[] }> {
    return {
      applications: [
        {
          id: '1',
          job: {
            title: 'Senior Python Developer',
            company: 'Previous Corp',
            location: 'Remote'
          },
          status: 'interview_scheduled',
          application_method: 'automated',
          submitted_at: '2024-03-08T14:30:00Z',
          last_status_update: '2024-03-10T09:15:00Z',
          needs_follow_up: false,
          follow_up_sent: false
        },
        {
          id: '2',
          job: {
            title: 'Backend Developer',
            company: 'Another Tech Co',
            location: 'San Francisco, CA'
          },
          status: 'submitted',
          application_method: 'automated',
          submitted_at: '2024-03-05T11:20:00Z',
          last_status_update: '2024-03-05T11:20:00Z',
          needs_follow_up: true,
          follow_up_sent: false
        }
      ]
    };
  },
  
  async applyToJob(jobId: string): Promise<{ message: string; task_id: string }> {
    return new Promise(resolve => {
      setTimeout(() => {
        resolve({ message: 'Application process started', task_id: 'task_123' });
      }, 1000);
    });
  }
};

const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [applying, setApplying] = useState<Record<string, boolean>>({});
  
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      if (activeTab === 'dashboard') {
        const data = await api.getDashboard();
        setDashboardData(data);
        const matchData = await api.getMatches();
        setMatches(matchData.matches.slice(0, 3));
      } else if (activeTab === 'matches') {
        const data = await api.getMatches();
        setMatches(data.matches);
      } else if (activeTab === 'applications') {
        const data = await api.getApplications();
        setApplications(data.applications);
      }
    } catch (error) {
      console.error('Error loading data:', error);
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
      await api.applyToJob(jobId);
      setMatches(prev => prev.map(match => 
        match.job.id === jobId 
          ? { ...match, already_applied: true }
          : match
      ));
    } catch (error) {
      console.error('Application failed:', error);
    } finally {
      setApplying(prev => ({ ...prev, [jobId]: false }));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
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
              <h1 className="ml-3 text-xl font-semibold text-gray-900">JobBot</h1>
            </div>
            
            <nav className="flex space-x-8">
              {[
                { key: 'dashboard', label: 'Dashboard', icon: TrendingUp },
                { key: 'matches', label: 'Matches', icon: Target },
                { key: 'applications', label: 'Applications', icon: Briefcase },
                { key: 'settings', label: 'Settings', icon: Settings }
              ].map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  onClick={() => setActiveTab(key)}
                  className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === key
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
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[
                {
                  label: 'Total Applications',
                  value: dashboardData?.total_applications || 0,
                  icon: Briefcase,
                  color: 'blue'
                },
                {
                  label: 'This Month',
                  value: dashboardData?.applications_this_month || 0,
                  icon: TrendingUp,
                  color: 'green'
                },
                {
                  label: 'Interviews',
                  value: dashboardData?.interviews_scheduled || 0,
                  icon: CheckCircle,
                  color: 'purple'
                },
                {
                  label: 'Pending',
                  value: dashboardData?.pending_applications || 0,
                  icon: Clock,
                  color: 'yellow'
                }
              ].map(({ label, value, icon: Icon, color }) => (
                <div key={label} className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">{label}</p>
                      <p className="text-2xl font-semibold text-gray-900">{value}</p>
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
                    <h3 className="text-lg font-medium text-gray-900">Auto-Apply</h3>
                    <p className="text-sm text-gray-600">
                      {dashboardData?.auto_apply_enabled 
                        ? 'Automatically applying to high-match jobs'
                        : 'Auto-apply is paused'
                      }
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-semibold text-blue-600">
                    {dashboardData?.current_matches || 0}
                  </p>
                  <p className="text-sm text-gray-600">Current Matches</p>
                </div>
              </div>
            </div>

            {/* Top Matches Preview */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-gray-900">Top Matches</h3>
                  <button
                    onClick={() => setActiveTab('matches')}
                    className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                  >
                    View All
                  </button>
                </div>
              </div>
              <div className="divide-y divide-gray-200">
                {matches.map((match) => (
                  <JobCard key={match.match_id} match={match} onApply={handleApply} applying={applying} />
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'matches' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-semibold text-gray-900">Job Matches</h2>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <Search className="h-4 w-4 text-gray-400" />
                  <span className="text-sm text-gray-600">
                    {matches.length} matches found
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
            <h2 className="text-2xl font-semibold text-gray-900">My Applications</h2>
            
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
            <h2 className="text-2xl font-semibold text-gray-900">Settings</h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Job Preferences</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Preferred Locations
                    </label>
                    <input
                      type="text"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="San Francisco, New York, Remote"
                      defaultValue="San Francisco, Remote"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Minimum Salary
                    </label>
                    <input
                      type="number"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="90000"
                      defaultValue="90000"
                    />
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="remote_ok"
                      className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      defaultChecked
                    />
                    <label htmlFor="remote_ok" className="ml-2 text-sm text-gray-700">
                      Open to remote work
                    </label>
                  </div>
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Auto-Apply Settings</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">Enable Auto-Apply</span>
                    <button
                      className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                        dashboardData?.auto_apply_enabled ? 'bg-blue-600' : 'bg-gray-200'
                      }`}
                    >
                      <span
                        className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition duration-200 ease-in-out ${
                          dashboardData?.auto_apply_enabled ? 'translate-x-5' : 'translate-x-0'
                        }`}
                      />
                    </button>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Minimum Match Score
                    </label>
                    <input
                      type="range"
                      min="0.5"
                      max="1.0"
                      step="0.05"
                      defaultValue="0.7"
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>50%</span>
                      <span>70%</span>
                      <span>100%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Resume Upload</h3>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-sm text-gray-600 mb-2">
                  Drop your resume here, or click to browse
                </p>
                <p className="text-xs text-gray-500">
                  Supports PDF and DOCX files up to 10MB
                </p>
                <button className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
                  Choose File
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

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
  
  return (
    <div className="p-6">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-2">
            <h3 className="text-lg font-medium text-gray-900 truncate">
              {job.title}
            </h3>
            <div className="flex-shrink-0">
              <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                scores.overall >= 0.8 ? 'bg-green-100 text-green-800' :
                scores.overall >= 0.6 ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {Math.round(scores.overall * 100)}% match
              </div>
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
            {job.required_skills.slice(0, 4).map((skill) => (
              <span
                key={skill}
                className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
              >
                {skill}
              </span>
            ))}
            {job.required_skills.length > 4 && (
              <span className="text-xs text-gray-500">
                +{job.required_skills.length - 4} more
              </span>
            )}
          </div>
          
          <div className="grid grid-cols-4 gap-4 text-center">
            {[
              { label: 'Skills', score: scores.skills },
              { label: 'Experience', score: scores.experience },
              { label: 'Location', score: scores.location },
              { label: 'Salary', score: scores.salary }
            ].map(({ label, score }) => (
              <div key={label}>
                <div className="text-xs text-gray-500">{label}</div>
                <div className="text-sm font-medium text-gray-900">
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
              <div className="px-4 py-2 bg-green-100 text-green-800 rounded-md text-sm font-medium text-center">
                Applied
              </div>
            ) : (
              <button
                onClick={() => onApply(job.id)}
                disabled={applying[job.id]}
                className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:bg-blue-400 transition-colors"
              >
                {applying[job.id] ? 'Applying...' : 'Quick Apply'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

interface ApplicationCardProps {
  application: Application;
}

const ApplicationCard: React.FC<ApplicationCardProps> = ({ application }) => {
  const { job, status, submitted_at, application_method } = application;
  
  const getStatusColor = (status: string): string => {
    const colors: Record<string, string> = {
      'pending': 'text-yellow-600 bg-yellow-50 border-yellow-200',
      'submitted': 'text-blue-600 bg-blue-50 border-blue-200',
      'interview_scheduled': 'text-green-600 bg-green-50 border-green-200',
      'rejected': 'text-red-600 bg-red-50 border-red-200',
      'offer': 'text-purple-600 bg-purple-50 border-purple-200'
    };
    return colors[status] || 'text-gray-600 bg-gray-50 border-gray-200';
  };
  
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  return (
    <div className="p-6">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-medium text-gray-900">
            {job.title}
          </h3>
          <div className="flex items-center text-sm text-gray-600 space-x-4 mt-1">
            <span>{job.company}</span>
            <span>{job.location}</span>
          </div>
          <div className="flex items-center space-x-4 mt-3">
            <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(status)}`}>
              {status.replace('_', ' ').toUpperCase()}
            </div>
            <span className="text-xs text-gray-500">
              Applied {formatDate(submitted_at)} • {application_method}
            </span>
          </div>
        </div>
        
        <div className="flex-shrink-0">
          {application.needs_follow_up && !application.follow_up_sent && (
            <div className="flex items-center text-yellow-600">
              <AlertCircle className="h-4 w-4 mr-1" />
              <span className="text-xs">Follow-up due</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;