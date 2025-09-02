import {
  AlertCircle,
  CheckCircle,
  Clock,
  Edit3,
  FileText,
  Loader2,
  Send,
  Target,
  User,
  Zap
} from 'lucide-react';
import React, { useState } from 'react';
import {
  ApplicationStrategy,
  AutoApplyRequest,
  autoApplyService,
  ResumeData,
  UserProfile
} from '../services/autoApplyService';

interface AutoApplyProps {
  jobUrl?: string;
  jobTitle?: string;
  companyName?: string;
  onApplicationComplete?: (result: any) => void;
}

export const AutoApply: React.FC<AutoApplyProps> = ({
  jobUrl,
  jobTitle,
  companyName,
  onApplicationComplete
}) => {
  const [activeTab, setActiveTab] = useState<'profile' | 'resume' | 'apply'>('profile');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Form data
  const [userProfile, setUserProfile] = useState<UserProfile>(
    autoApplyService.generateDefaultUserProfile()
  );
  const [resumeData, setResumeData] = useState<ResumeData>(
    autoApplyService.generateDefaultResumeData()
  );
  const [applicationStrategy, setApplicationStrategy] = useState<ApplicationStrategy>('smart');
  const [customJobUrl, setCustomJobUrl] = useState(jobUrl || '');

  const strategies = [
    {
      id: 'quick' as ApplicationStrategy,
      name: 'Quick Apply',
      description: 'Fast application with minimal customization',
      icon: Zap,
      color: 'bg-green-500',
      time: '30s'
    },
    {
      id: 'smart' as ApplicationStrategy,
      name: 'Smart Apply',
      description: 'Balanced approach with intelligent field mapping',
      icon: Target,
      color: 'bg-blue-500',
      time: '90s'
    },
    {
      id: 'detailed' as ApplicationStrategy,
      name: 'Detailed Apply',
      description: 'Comprehensive application with full customization',
      icon: Edit3,
      color: 'bg-purple-500',
      time: '3m'
    }
  ];

  const handleProfileChange = (field: keyof UserProfile, value: any) => {
    setUserProfile(prev => ({ ...prev, [field]: value }));
  };

  const handleAddressChange = (field: keyof UserProfile['address'], value: string) => {
    setUserProfile(prev => ({
      ...prev,
      address: { ...prev.address, [field]: value }
    }));
  };

  const handlePreferencesChange = (field: keyof UserProfile['preferences'], value: any) => {
    setUserProfile(prev => ({
      ...prev,
      preferences: { ...prev.preferences, [field]: value }
    }));
  };

  const handleResumeChange = (field: keyof ResumeData, value: any) => {
    setResumeData(prev => ({ ...prev, [field]: value }));
  };

  const handlePersonalChange = (field: keyof ResumeData['personal'], value: string) => {
    setResumeData(prev => ({
      ...prev,
      personal: { ...prev.personal, [field]: value }
    }));
  };

  const handleAddressResumeChange = (field: keyof ResumeData['personal']['address'], value: string) => {
    setResumeData(prev => ({
      ...prev,
      personal: {
        ...prev.personal,
        address: { ...prev.personal.address, [field]: value }
      }
    }));
  };

  const addExperience = () => {
    setResumeData(prev => ({
      ...prev,
      experience: [
        ...prev.experience,
        {
          title: '',
          company: '',
          startDate: '',
          endDate: '',
          description: '',
          skills: []
        }
      ]
    }));
  };

  const updateExperience = (index: number, field: string, value: any) => {
    setResumeData(prev => ({
      ...prev,
      experience: prev.experience.map((exp, i) =>
        i === index ? { ...exp, [field]: value } : exp
      )
    }));
  };

  const removeExperience = (index: number) => {
    setResumeData(prev => ({
      ...prev,
      experience: prev.experience.filter((_, i) => i !== index)
    }));
  };

  const addEducation = () => {
    setResumeData(prev => ({
      ...prev,
      education: [
        ...prev.education,
        {
          degree: '',
          institution: '',
          graduationYear: '',
          gpa: ''
        }
      ]
    }));
  };

  const updateEducation = (index: number, field: string, value: string) => {
    setResumeData(prev => ({
      ...prev,
      education: prev.education.map((edu, i) =>
        i === index ? { ...edu, [field]: value } : edu
      )
    }));
  };

  const removeEducation = (index: number) => {
    setResumeData(prev => ({
      ...prev,
      education: prev.education.filter((_, i) => i !== index)
    }));
  };

  const addSkill = () => {
    setResumeData(prev => ({
      ...prev,
      skills: [...prev.skills, '']
    }));
  };

  const updateSkill = (index: number, value: string) => {
    setResumeData(prev => ({
      ...prev,
      skills: prev.skills.map((skill, i) => i === index ? value : skill)
    }));
  };

  const removeSkill = (index: number) => {
    setResumeData(prev => ({
      ...prev,
      skills: prev.skills.filter((_, i) => i !== index)
    }));
  };

  const validateForm = (): string[] => {
    const profileErrors = autoApplyService.validateUserProfile(userProfile);
    const resumeErrors = autoApplyService.validateResumeData(resumeData);

    if (!customJobUrl) {
      profileErrors.push('Job URL is required');
    }

    return [...profileErrors, ...resumeErrors];
  };

  const handleSubmit = async () => {
    const errors = validateForm();
    if (errors.length > 0) {
      setError(errors.join(', '));
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      // Merge resume data with user profile
      const mergedResumeData = autoApplyService.mergeResumeWithProfile(resumeData, userProfile);

      // Update user profile with current application context
      const updatedUserProfile = {
        ...userProfile,
        currentApplication: {
          jobTitle: jobTitle || 'Software Engineer',
          companyName: companyName || 'Company'
        }
      };

      const request: AutoApplyRequest = {
        jobUrl: customJobUrl,
        resumeData: mergedResumeData,
        userProfile: updatedUserProfile,
        applicationStrategy
      };

      const response = await autoApplyService.autoApply(request);

      if (response.success) {
        setResult(response.result);
        onApplicationComplete?.(response.result);
      } else {
        setError(response.error || 'Application failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'applied':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-blue-600" />;
      default:
        return <Clock className="w-5 h-5 text-yellow-600" />;
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <Send className="w-6 h-6" />
          Auto-Apply Assistant
        </h2>

        {jobTitle && companyName && (
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-4">
            <p className="text-sm text-blue-800">
              <strong>Applying to:</strong> {jobTitle} at {companyName}
            </p>
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="flex space-x-1 mb-6">
          {[
            { key: 'profile', label: 'Profile', icon: User },
            { key: 'resume', label: 'Resume', icon: FileText },
            { key: 'apply', label: 'Apply', icon: Send }
          ].map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key as any)}
              className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === key
                ? 'bg-blue-600 text-white'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
            >
              <Icon className="w-4 h-4 mr-2" />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Profile Tab */}
      {activeTab === 'profile' && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Personal Profile</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                First Name *
              </label>
              <input
                type="text"
                value={userProfile.firstName}
                onChange={(e) => handleProfileChange('firstName', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Last Name *
              </label>
              <input
                type="text"
                value={userProfile.lastName}
                onChange={(e) => handleProfileChange('lastName', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email *
              </label>
              <input
                type="email"
                value={userProfile.email}
                onChange={(e) => handleProfileChange('email', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Phone *
              </label>
              <input
                type="tel"
                value={userProfile.phone}
                onChange={(e) => handleProfileChange('phone', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <h4 className="text-md font-semibold mt-6 mb-4">Address</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Street Address *
              </label>
              <input
                type="text"
                value={userProfile.address.street}
                onChange={(e) => handleAddressChange('street', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                City *
              </label>
              <input
                type="text"
                value={userProfile.address.city}
                onChange={(e) => handleAddressChange('city', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                State *
              </label>
              <input
                type="text"
                value={userProfile.address.state}
                onChange={(e) => handleAddressChange('state', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ZIP Code *
              </label>
              <input
                type="text"
                value={userProfile.address.zipCode}
                onChange={(e) => handleAddressChange('zipCode', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <h4 className="text-md font-semibold mt-6 mb-4">Preferences</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Salary Expectation
              </label>
              <input
                type="text"
                value={userProfile.preferences.salaryExpectation}
                onChange={(e) => handlePreferencesChange('salaryExpectation', e.target.value)}
                placeholder="e.g., $80,000 - $100,000"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Work Type
              </label>
              <select
                value={userProfile.preferences.workType}
                onChange={(e) => handlePreferencesChange('workType', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="remote">Remote</option>
                <option value="hybrid">Hybrid</option>
                <option value="onsite">On-site</option>
              </select>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="relocation"
                checked={userProfile.preferences.relocation}
                onChange={(e) => handlePreferencesChange('relocation', e.target.checked)}
                className="mr-2"
              />
              <label htmlFor="relocation" className="text-sm text-gray-700">
                Willing to relocate
              </label>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="visa"
                checked={userProfile.preferences.visaSponsorship}
                onChange={(e) => handlePreferencesChange('visaSponsorship', e.target.checked)}
                className="mr-2"
              />
              <label htmlFor="visa" className="text-sm text-gray-700">
                Need visa sponsorship
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Resume Tab */}
      {activeTab === 'resume' && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Resume Data</h3>

          {/* Experience Section */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-md font-semibold">Work Experience</h4>
              <button
                onClick={addExperience}
                className="px-3 py-1 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700"
              >
                Add Experience
              </button>
            </div>

            {resumeData.experience.map((exp, index) => (
              <div key={index} className="border border-gray-200 rounded-md p-4 mb-4">
                <div className="flex justify-between items-start mb-3">
                  <h5 className="font-medium">Experience #{index + 1}</h5>
                  <button
                    onClick={() => removeExperience(index)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Remove
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Job Title
                    </label>
                    <input
                      type="text"
                      value={exp.title}
                      onChange={(e) => updateExperience(index, 'title', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Company
                    </label>
                    <input
                      type="text"
                      value={exp.company}
                      onChange={(e) => updateExperience(index, 'company', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Start Date
                    </label>
                    <input
                      type="date"
                      value={exp.startDate}
                      onChange={(e) => updateExperience(index, 'startDate', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      End Date
                    </label>
                    <input
                      type="date"
                      value={exp.endDate}
                      onChange={(e) => updateExperience(index, 'endDate', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={exp.description}
                    onChange={(e) => updateExperience(index, 'description', e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Education Section */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-md font-semibold">Education</h4>
              <button
                onClick={addEducation}
                className="px-3 py-1 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700"
              >
                Add Education
              </button>
            </div>

            {resumeData.education.map((edu, index) => (
              <div key={index} className="border border-gray-200 rounded-md p-4 mb-4">
                <div className="flex justify-between items-start mb-3">
                  <h5 className="font-medium">Education #{index + 1}</h5>
                  <button
                    onClick={() => removeEducation(index)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Remove
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Degree
                    </label>
                    <input
                      type="text"
                      value={edu.degree}
                      onChange={(e) => updateEducation(index, 'degree', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Institution
                    </label>
                    <input
                      type="text"
                      value={edu.institution}
                      onChange={(e) => updateEducation(index, 'institution', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Graduation Year
                    </label>
                    <input
                      type="text"
                      value={edu.graduationYear}
                      onChange={(e) => updateEducation(index, 'graduationYear', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      GPA (Optional)
                    </label>
                    <input
                      type="text"
                      value={edu.gpa}
                      onChange={(e) => updateEducation(index, 'gpa', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Skills Section */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-md font-semibold">Skills</h4>
              <button
                onClick={addSkill}
                className="px-3 py-1 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700"
              >
                Add Skill
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {resumeData.skills.map((skill, index) => (
                <div key={index} className="flex items-center">
                  <input
                    type="text"
                    value={skill}
                    onChange={(e) => updateSkill(index, e.target.value)}
                    placeholder="e.g., JavaScript, React, Python"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    onClick={() => removeSkill(index)}
                    className="ml-2 text-red-600 hover:text-red-800"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Summary Section */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Professional Summary
            </label>
            <textarea
              value={resumeData.summary}
              onChange={(e) => handleResumeChange('summary', e.target.value)}
              rows={4}
              placeholder="Brief professional summary..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      )}

      {/* Apply Tab */}
      {activeTab === 'apply' && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Auto-Apply Configuration</h3>

          {/* Job URL */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Job URL *
            </label>
            <input
              type="url"
              value={customJobUrl}
              onChange={(e) => setCustomJobUrl(e.target.value)}
              placeholder="https://www.indeed.com/jobs/..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Strategy Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-4">
              Application Strategy
            </label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {strategies.map((strategy) => {
                const Icon = strategy.icon;
                return (
                  <div
                    key={strategy.id}
                    onClick={() => setApplicationStrategy(strategy.id)}
                    className={`border rounded-lg p-4 cursor-pointer transition-colors ${applicationStrategy === strategy.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                      }`}
                  >
                    <div className="flex items-center mb-2">
                      <div className={`w-8 h-8 rounded-full ${strategy.color} flex items-center justify-center mr-3`}>
                        <Icon className="w-4 h-4 text-white" />
                      </div>
                      <div>
                        <h4 className="font-medium">{strategy.name}</h4>
                        <p className="text-xs text-gray-500">~{strategy.time}</p>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600">{strategy.description}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Validation Summary */}
          <div className="mb-6">
            <h4 className="text-md font-semibold mb-3">Validation Summary</h4>
            {(() => {
              const errors = validateForm();
              if (errors.length === 0) {
                return (
                  <div className="bg-green-50 border border-green-200 rounded-md p-4">
                    <div className="flex items-center">
                      <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                      <span className="text-green-800">All required fields are filled</span>
                    </div>
                  </div>
                );
              } else {
                return (
                  <div className="bg-red-50 border border-red-200 rounded-md p-4">
                    <div className="flex items-center mb-2">
                      <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
                      <span className="text-red-800 font-medium">Please fix the following issues:</span>
                    </div>
                    <ul className="text-red-700 text-sm space-y-1">
                      {errors.map((error, index) => (
                        <li key={index}>• {error}</li>
                      ))}
                    </ul>
                  </div>
                );
              }
            })()}
          </div>

          {/* Submit Button */}
          <button
            onClick={handleSubmit}
            disabled={isLoading || validateForm().length > 0}
            className="w-full px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Applying...
              </>
            ) : (
              <>
                <Send className="w-5 h-5" />
                Start Auto-Apply
              </>
            )}
          </button>

          {/* Error Display */}
          {error && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex items-center">
                <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
                <span className="text-red-800">{error}</span>
              </div>
            </div>
          )}

          {/* Result Display */}
          {result && (
            <div className="mt-4 bg-blue-50 border border-blue-200 rounded-md p-4">
              <div className="flex items-center mb-2">
                {getStatusIcon(result.status)}
                <span className="ml-2 font-medium text-blue-800">
                  Application {result.status}
                </span>
              </div>
              {result.message && (
                <p className="text-blue-700">{result.message}</p>
              )}
              {result.error && (
                <p className="text-red-700">{result.error}</p>
              )}
              {result.details && (
                <div className="mt-2 text-sm text-blue-600">
                  <p>Fields filled: {result.details.fieldsFilled}</p>
                  <p>Strategy: {result.details.strategy}</p>
                  {result.details.errors.length > 0 && (
                    <div className="mt-2">
                      <p className="font-medium">Errors:</p>
                      <ul className="list-disc list-inside">
                        {result.details.errors.map((error: string, index: number) => (
                          <li key={index}>{error}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

