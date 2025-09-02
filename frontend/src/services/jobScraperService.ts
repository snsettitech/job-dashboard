export interface JobListing {
  id: string;
  title: string;
  company: string;
  location: string;
  salary: string;
  description: string;
  url: string;
  postedDate: string;
  platform: string;
  scrapedAt: string;
}

export interface ScrapeRequest {
  keywords?: string;
  location?: string;
  platforms?: string[];
  maxResults?: number;
}

export interface ScrapeResponse {
  success: boolean;
  totalJobs: number;
  results: JobListing[];
  timestamp: string;
  error?: string;
}

export class JobScraperService {
  private baseUrl: string;

  constructor() {
    // Use Netlify function URL in production, localhost for development
    this.baseUrl = process.env.NODE_ENV === 'production'
      ? '/api/scrape-jobs'
      : 'http://localhost:8888/.netlify/functions/scrape-jobs';
  }

  async scrapeJobs(request: ScrapeRequest): Promise<ScrapeResponse> {
    try {
      const response = await fetch(this.baseUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          keywords: request.keywords || 'software engineer',
          location: request.location || 'remote',
          platforms: request.platforms || ['indeed', 'linkedin', 'glassdoor'],
          maxResults: request.maxResults || 10
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ScrapeResponse = await response.json();
      return data;
    } catch (error) {
      console.error('Error scraping jobs:', error);
      return {
        success: false,
        totalJobs: 0,
        results: [],
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  // Helper method to get jobs by platform
  getJobsByPlatform(results: JobListing[], platform: string): JobListing[] {
    return results.filter(job => job.platform.toLowerCase() === platform.toLowerCase());
  }

  // Helper method to filter jobs by keywords
  filterJobsByKeywords(jobs: JobListing[], keywords: string[]): JobListing[] {
    const lowerKeywords = keywords.map(k => k.toLowerCase());
    return jobs.filter(job =>
      lowerKeywords.some(keyword =>
        job.title.toLowerCase().includes(keyword) ||
        job.company.toLowerCase().includes(keyword) ||
        job.description.toLowerCase().includes(keyword)
      )
    );
  }

  // Helper method to sort jobs by date
  sortJobsByDate(jobs: JobListing[], ascending: boolean = false): JobListing[] {
    return [...jobs].sort((a, b) => {
      const dateA = new Date(a.postedDate).getTime();
      const dateB = new Date(b.postedDate).getTime();
      return ascending ? dateA - dateB : dateB - dateA;
    });
  }
}

// Export a singleton instance
export const jobScraperService = new JobScraperService();

