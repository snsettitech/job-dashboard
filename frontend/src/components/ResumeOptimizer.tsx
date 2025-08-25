// src/components/ResumeOptimizer.tsx - AI Resume Optimization Interface
import React, { useState, useCallback } from 'react';
import { 
  Upload, 
  FileText, 
  Zap, 
  Download, 
  CheckCircle, 
  AlertCircle, 
  Loader2,
  TrendingUp,
  Target,
  Star,
  ArrowRight,
  Copy,
  RefreshCw
} from 'lucide-react';

// Types
interface OptimizationResult {
  status: string;
  processing_date: string;
  file_info: {
    filename: string;
    content_type: string;
    word_count: number;
  };
  original_resume: {
    text: string;
    word_count: number;
    quality_analysis: {
      quality_score: number;
      grade: string;
      feedback: string[];
    };
    structured_info: any;
  };
  job_match_analysis: {
    scores: {
      overall: number;
      skills: number;
      experience: number;
      location: number;
      salary: number;
    };
    recommendation: string;
    top_matching_skills: string[];
  };
  optimization: {
    optimized_resume: string;
    improvements_made: string[];
    keywords_added: string[];
    ats_score_improvement: string;
    match_score_prediction: number;
    optimization_summary: string;
    improvement_summary: {
      original_words: number;
      optimized_words: number;
      keywords_improvement: number;
      estimated_callback_improvement: string;
    };
  };
  next_steps: string[];
}

const ResumeOptimizer: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState<OptimizationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'upload' | 'results'>('upload');

  const handleFileChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      // Validate file type
      const validTypes = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'
      ];
      
      if (!validTypes.includes(selectedFile.type)) {
        setError('Please upload a PDF, DOCX, or TXT file');
        return;
      }
      
      // Validate file size (5MB max)
      if (selectedFile.size > 5 * 1024 * 1024) {
        setError('File size must be less than 5MB');
        return;
      }
      
      setFile(selectedFile);
      setError(null);
    }
  }, []);

  const handleOptimization = useCallback(async () => {
    if (!file || !jobDescription.trim()) {
      setError('Please upload a resume and provide a job description');
      return;
    }

    setProcessing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('job_description', jobDescription);
      formData.append('company_name', companyName);
      formData.append('job_title', jobTitle);

      const response = await fetch('http://localhost:8000/api/ai/upload-analyze-optimize', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Optimization failed');
      }

      const resultData: OptimizationResult = await response.json();
      setResult(resultData);
      setActiveTab('results');
      
    } catch (err) {
      console.error('Optimization error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred during optimization');
    } finally {
      setProcessing(false);
    }
  }, [file, jobDescription, companyName, jobTitle]);

  const downloadOptimizedResume = useCallback(async () => {
    if (!result) return;

    try {
      const formData = new FormData();
      formData.append('optimized_text', result.optimization.optimized_resume);
      formData.append('filename', `optimized_${result.file_info.filename.replace(/\.[^/.]+$/, '')}.txt`);

      const response = await fetch('http://localhost:8000/api/ai/download-optimized-resume', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `optimized_${result.file_info.filename.replace(/\.[^/.]+$/, '')}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Download error:', error);
      setError('Failed to download optimized resume');
    }
  }, [result]);

  const copyToClipboard = useCallback((text: string) => {
    navigator.clipboard.writeText(text);
    // You could add a toast notification here
  }, []);

  const resetOptimizer = useCallback(() => {
    setFile(null);
    setJobDescription('');
    setCompanyName('');
    setJobTitle('');
    setResult(null);
    setError(null);
    setActiveTab('upload');
  }, []);

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center justify-center">
          <Zap className="h-8 w-8 text-yellow-500 mr-3" />
          AI Resume Optimizer
        </h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Upload your resume and a job description to get an AI-optimized version that increases your interview chances by up to 40%
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex justify-center">
        <div className="flex bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setActiveTab('upload')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'upload'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Upload & Optimize
          </button>
          <button
            onClick={() => setActiveTab('results')}
            disabled={!result}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'results' && result
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-400 cursor-not-allowed'
            }`}
          >
            Results & Download
          </button>
        </div>
      </div>

      {/* Upload Tab */}
      {activeTab === 'upload' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Resume Upload */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <Upload className="h-5 w-5 mr-2" />
              Upload Your Resume
            </h3>
            
            <div className="space-y-4">
              <div 
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  file 
                    ? 'border-green-300 bg-green-50' 
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <input
                  type="file"
                  onChange={handleFileChange}
                  accept=".pdf,.docx,.txt"
                  className="hidden"
                  id="resume-upload"
                />
                <label htmlFor="resume-upload" className="cursor-pointer">
                  {file ? (
                    <div className="space-y-2">
                      <CheckCircle className="h-12 w-12 text-green-600 mx-auto" />
                      <p className="text-sm font-medium text-green-800">
                        {file.name}
                      </p>
                      <p className="text-xs text-green-600">
                        {(file.size / 1024).toFixed(1)} KB • Click to change
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <FileText className="h-12 w-12 text-gray-400 mx-auto" />
                      <p className="text-sm font-medium text-gray-900">
                        Click to upload resume
                      </p>
                      <p className="text-xs text-gray-500">
                        PDF, DOCX, or TXT • Max 5MB
                      </p>
                    </div>
                  )}
                </label>
              </div>

              {/* Job Details Form */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Job Title (Optional)
                  </label>
                  <input
                    type="text"
                    value={jobTitle}
                    onChange={(e) => setJobTitle(e.target.value)}
                    placeholder="e.g., Senior Software Engineer"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Company Name (Optional)
                  </label>
                  <input
                    type="text"
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    placeholder="e.g., Google, Microsoft"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Job Description */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <Target className="h-5 w-5 mr-2" />
              Job Description
            </h3>
            
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the complete job description here. Include requirements, responsibilities, and preferred qualifications for best optimization results..."
              className="w-full h-64 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
            
            <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
              <span>{jobDescription.length} characters</span>
              <span>{jobDescription.split(/\s+/).length - 1} words</span>
            </div>
          </div>
        </div>
      )}

      {/* Results Tab */}
      {activeTab === 'results' && result && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-green-100">Match Score</p>
                  <p className="text-3xl font-bold">
                    {Math.round(result.job_match_analysis.scores.overall * 100)}%
                  </p>
                </div>
                <Target className="h-10 w-10 text-green-200" />
              </div>
            </div>

            <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-blue-100">ATS Improvement</p>
                  <p className="text-3xl font-bold">
                    {result.optimization.ats_score_improvement}
                  </p>
                </div>
                <TrendingUp className="h-10 w-10 text-blue-200" />
              </div>
            </div>

            <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-100">Keywords Added</p>
                  <p className="text-3xl font-bold">
                    {result.optimization.keywords_added.length}
                  </p>
                </div>
                <Star className="h-10 w-10 text-purple-200" />
              </div>
            </div>
          </div>

          {/* Optimized Resume */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">
                  🚀 Your Optimized Resume
                </h3>
                <div className="flex space-x-2">
                  <button
                    onClick={() => copyToClipboard(result.optimization.optimized_resume)}
                    className="px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors flex items-center"
                  >
                    <Copy className="h-4 w-4 mr-1" />
                    Copy
                  </button>
                  <button
                    onClick={downloadOptimizedResume}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download
                  </button>
                </div>
              </div>
            </div>
            
            <div className="p-6">
              <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
                <pre className="whitespace-pre-wrap text-sm text-gray-800 font-mono">
                  {result.optimization.optimized_resume}
                </pre>
              </div>
            </div>
          </div>

          {/* Improvements Summary */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <CheckCircle className="h-5 w-5 mr-2 text-green-600" />
                Improvements Made
              </h3>
              <ul className="space-y-2">
                {result.optimization.improvements_made.map((improvement, index) => (
                  <li key={index} className="flex items-start">
                    <ArrowRight className="h-4 w-4 mr-2 mt-0.5 text-green-600 flex-shrink-0" />
                    <span className="text-sm text-gray-700">{improvement}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <Star className="h-5 w-5 mr-2 text-yellow-500" />
                Keywords Added
              </h3>
              <div className="flex flex-wrap gap-2">
                {result.optimization.keywords_added.map((keyword, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
              
              {result.optimization.keywords_added.length === 0 && (
                <p className="text-sm text-gray-500 italic">
                  Your resume already contained most relevant keywords for this position.
                </p>
              )}
            </div>
          </div>

          {/* Next Steps */}
          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              🎯 Recommended Next Steps
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {result.next_steps.map((step, index) => (
                <div key={index} className="flex items-start">
                  <span className="flex-shrink-0 w-6 h-6 bg-indigo-600 text-white rounded-full flex items-center justify-center text-sm font-medium mr-3">
                    {index + 1}
                  </span>
                  <span className="text-sm text-gray-700">{step}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      {activeTab === 'upload' && (
        <div className="flex justify-center space-x-4">
          <button
            onClick={handleOptimization}
            disabled={!file || !jobDescription.trim() || processing}
            className="px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center"
          >
            {processing ? (
              <>
                <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                Processing Magic...
              </>
            ) : (
              <>
                <Zap className="h-5 w-5 mr-2" />
                Optimize My Resume
              </>
            )}
          </button>
        </div>
      )}

      {activeTab === 'results' && (
        <div className="flex justify-center">
          <button
            onClick={resetOptimizer}
            className="px-6 py-3 bg-gray-600 text-white rounded-lg font-medium hover:bg-gray-700 transition-colors flex items-center"
          >
            <RefreshCw className="h-5 w-5 mr-2" />
            Optimize Another Resume
          </button>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
          <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
          <span className="text-red-800">{error}</span>
        </div>
      )}
    </div>
  );
};

export default ResumeOptimizer;