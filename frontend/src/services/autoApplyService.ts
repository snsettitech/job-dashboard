export interface ResumeData {
  personal: {
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
    address: {
      street: string;
      city: string;
      state: string;
      zipCode: string;
    };
  };
  experience: Array<{
    title: string;
    company: string;
    startDate: string;
    endDate?: string;
    description: string;
    skills: string[];
  }>;
  education: Array<{
    degree: string;
    institution: string;
    graduationYear: string;
    gpa?: string;
  }>;
  skills: string[];
  summary: string;
}

export interface UserProfile {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  address: {
    street: string;
    city: string;
    state: string;
    zipCode: string;
  };
  preferences: {
    salaryExpectation: string;
    workType: 'remote' | 'hybrid' | 'onsite';
    relocation: boolean;
    visaSponsorship: boolean;
  };
  customAnswers: Record<string, string>;
  currentApplication?: {
    jobTitle: string;
    companyName: string;
  };
}

export type ApplicationStrategy = 'smart' | 'quick' | 'detailed';

export interface AutoApplyRequest {
  jobUrl: string;
  resumeData: ResumeData;
  userProfile: UserProfile;
  applicationStrategy?: ApplicationStrategy;
}

export interface AutoApplyResponse {
  success: boolean;
  result: {
    platform: string;
    status: 'applied' | 'failed' | 'completed' | 'error';
    message?: string;
    error?: string;
    details?: {
      fieldsFilled: number;
      fieldsSkipped: number;
      errors: string[];
      strategy: ApplicationStrategy;
      status: string;
    };
  };
  timestamp: string;
  error?: string;
}

export class AutoApplyService {
  private baseUrl: string;

  constructor() {
    // Use Netlify function URL in production, localhost for development
    this.baseUrl = process.env.NODE_ENV === 'production'
      ? '/api/auto-apply'
      : 'http://localhost:8888/.netlify/functions/auto-apply';
  }

  async autoApply(request: AutoApplyRequest): Promise<AutoApplyResponse> {
    try {
      const response = await fetch(this.baseUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jobUrl: request.jobUrl,
          resumeData: request.resumeData,
          userProfile: request.userProfile,
          applicationStrategy: request.applicationStrategy || 'smart'
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: AutoApplyResponse = await response.json();
      return data;
    } catch (error) {
      console.error('Error auto-applying:', error);
      return {
        success: false,
        result: {
          platform: 'unknown',
          status: 'failed',
          error: error instanceof Error ? error.message : 'Unknown error occurred'
        },
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  // Helper method to validate resume data
  validateResumeData(resumeData: ResumeData): string[] {
    const errors: string[] = [];

    if (!resumeData.personal?.firstName) errors.push('First name is required');
    if (!resumeData.personal?.lastName) errors.push('Last name is required');
    if (!resumeData.personal?.email) errors.push('Email is required');
    if (!resumeData.personal?.phone) errors.push('Phone is required');

    if (!resumeData.experience || resumeData.experience.length === 0) {
      errors.push('At least one work experience is required');
    }

    if (!resumeData.education || resumeData.education.length === 0) {
      errors.push('At least one education entry is required');
    }

    if (!resumeData.skills || resumeData.skills.length === 0) {
      errors.push('At least one skill is required');
    }

    return errors;
  }

  // Helper method to validate user profile
  validateUserProfile(userProfile: UserProfile): string[] {
    const errors: string[] = [];

    if (!userProfile.firstName) errors.push('First name is required');
    if (!userProfile.lastName) errors.push('Last name is required');
    if (!userProfile.email) errors.push('Email is required');
    if (!userProfile.phone) errors.push('Phone is required');

    if (!userProfile.address?.street) errors.push('Street address is required');
    if (!userProfile.address?.city) errors.push('City is required');
    if (!userProfile.address?.state) errors.push('State is required');
    if (!userProfile.address?.zipCode) errors.push('ZIP code is required');

    return errors;
  }

  // Helper method to generate default resume data
  generateDefaultResumeData(): ResumeData {
    return {
      personal: {
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
        address: {
          street: '',
          city: '',
          state: '',
          zipCode: ''
        }
      },
      experience: [],
      education: [],
      skills: [],
      summary: ''
    };
  }

  // Helper method to generate default user profile
  generateDefaultUserProfile(): UserProfile {
    return {
      firstName: '',
      lastName: '',
      email: '',
      phone: '',
      address: {
        street: '',
        city: '',
        state: '',
        zipCode: ''
      },
      preferences: {
        salaryExpectation: '',
        workType: 'remote',
        relocation: false,
        visaSponsorship: false
      },
      customAnswers: {}
    };
  }

  // Helper method to merge resume data with user profile
  mergeResumeWithProfile(resumeData: ResumeData, userProfile: UserProfile): ResumeData {
    return {
      ...resumeData,
      personal: {
        ...resumeData.personal,
        firstName: userProfile.firstName || resumeData.personal.firstName,
        lastName: userProfile.lastName || resumeData.personal.lastName,
        email: userProfile.email || resumeData.personal.email,
        phone: userProfile.phone || resumeData.personal.phone,
        address: {
          ...resumeData.personal.address,
          street: userProfile.address.street || resumeData.personal.address.street,
          city: userProfile.address.city || resumeData.personal.address.city,
          state: userProfile.address.state || resumeData.personal.address.state,
          zipCode: userProfile.address.zipCode || resumeData.personal.address.zipCode
        }
      }
    };
  }

  // Helper method to get application strategy description
  getStrategyDescription(strategy: ApplicationStrategy): string {
    switch (strategy) {
      case 'quick':
        return 'Fast application with minimal customization';
      case 'detailed':
        return 'Comprehensive application with full customization';
      case 'smart':
      default:
        return 'Balanced approach with intelligent field mapping';
    }
  }

  // Helper method to estimate application time
  estimateApplicationTime(strategy: ApplicationStrategy): number {
    switch (strategy) {
      case 'quick':
        return 30; // 30 seconds
      case 'detailed':
        return 180; // 3 minutes
      case 'smart':
      default:
        return 90; // 1.5 minutes
    }
  }
}

// Export a singleton instance
export const autoApplyService = new AutoApplyService();

