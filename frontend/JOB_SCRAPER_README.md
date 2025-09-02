# Job Scraper Serverless Function

A serverless function built with Playwright to scrape job listings from Indeed, LinkedIn, and Glassdoor.

## 🚀 Features

- **Multi-platform scraping**: Indeed, LinkedIn, and Glassdoor
- **Serverless architecture**: Deployed on Netlify Functions
- **Real-time job data**: Extract job titles, companies, locations, salaries, and descriptions
- **Configurable search**: Customize keywords, location, and result limits
- **Modern UI**: React component with filtering and sorting capabilities

## 📁 Project Structure

```
frontend/
├── netlify/
│   ├── functions/
│   │   ├── scrape-jobs.js          # Main serverless function
│   │   └── package.json            # Function dependencies
│   └── netlify.toml               # Netlify configuration
├── src/
│   ├── components/
│   │   └── JobScraper.tsx         # React component
│   └── services/
│       └── jobScraperService.ts   # TypeScript service
└── setup-scraper.ps1              # Setup script
```

## 🛠️ Setup Instructions

### 1. Install Dependencies

Run the setup script to install all necessary dependencies:

```powershell
# Windows
.\setup-scraper.ps1

# Or manually:
cd netlify/functions
npm install
npx playwright install chromium
cd ../..
npm install
```

### 2. Development

Start the development server:

```bash
npm start
```

Navigate to the "Job Scraper" tab in the application.

### 3. Production Deployment

The serverless function is automatically deployed when you push to your Netlify-connected repository.

## 🔧 Configuration

### Function Configuration

The serverless function accepts the following parameters:

```typescript
interface ScrapeRequest {
  keywords?: string;        // Job search keywords
  location?: string;        // Location preference
  platforms?: string[];     // Platforms to scrape
  maxResults?: number;      // Maximum results per platform
}
```

### Example Usage

```typescript
const response = await jobScraperService.scrapeJobs({
  keywords: "software engineer",
  location: "remote",
  platforms: ["indeed", "linkedin", "glassdoor"],
  maxResults: 10
});
```

## 📊 Response Format

```typescript
interface ScrapeResponse {
  success: boolean;
  totalJobs: number;
  results: JobListing[];
  timestamp: string;
  error?: string;
}

interface JobListing {
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
```

## 🌐 Supported Platforms

### Indeed
- **URL Pattern**: `https://www.indeed.com/jobs?q={keywords}&l={location}`
- **Data Extracted**: Title, company, location, salary, description
- **Rate Limiting**: Built-in delays and user agent rotation

### LinkedIn
- **URL Pattern**: `https://www.linkedin.com/jobs/search/?keywords={keywords}&location={location}`
- **Data Extracted**: Title, company, location, posting date
- **Note**: Salary information not always available

### Glassdoor
- **URL Pattern**: `https://www.glassdoor.com/Job/jobs.htm?sc.keyword={keywords}&locT=N&locId=1`
- **Data Extracted**: Title, company, location, salary estimate, posting date

## 🔒 Anti-Detection Measures

The scraper includes several measures to avoid detection:

- **User Agent Rotation**: Uses realistic browser user agents
- **Request Delays**: Built-in delays between requests
- **Headless Browser**: Uses Playwright's headless mode
- **Error Handling**: Graceful handling of rate limits and blocks

## ⚠️ Legal Considerations

⚠️ **Important**: Web scraping may be subject to terms of service and legal restrictions:

1. **Terms of Service**: Check each platform's ToS before scraping
2. **Rate Limiting**: Respect rate limits to avoid being blocked
3. **Data Usage**: Only use scraped data for legitimate purposes
4. **Attribution**: Consider providing attribution when using scraped data

## 🚨 Limitations

- **Dynamic Content**: Some job details may require clicking into individual listings
- **Rate Limiting**: Platforms may block requests if too frequent
- **Structure Changes**: Selectors may break if websites update their structure
- **Geographic Restrictions**: Some platforms may show different results based on location

## 🔧 Troubleshooting

### Common Issues

1. **Function Timeout**: Increase timeout in Netlify configuration
2. **Browser Installation**: Ensure Playwright browsers are installed
3. **CORS Issues**: Check that CORS headers are properly set
4. **Rate Limiting**: Add delays between requests

### Debug Mode

Enable debug logging by setting environment variables:

```bash
DEBUG=pw:api  # Playwright debug logs
```

## 📈 Performance Optimization

- **Parallel Scraping**: Scrapes multiple platforms concurrently
- **Result Limiting**: Configurable max results to control response size
- **Caching**: Consider implementing Redis caching for repeated searches
- **Pagination**: Future enhancement for large result sets

## 🔮 Future Enhancements

- [ ] **More Platforms**: Add support for ZipRecruiter, Monster, etc.
- [ ] **Advanced Filtering**: Filter by salary range, job type, experience level
- [ ] **Email Alerts**: Set up job alerts for specific criteria
- [ ] **Data Export**: Export results to CSV/JSON
- [ ] **Resume Matching**: Integrate with resume optimization features
- [ ] **Application Tracking**: Track applications to scraped jobs

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the browser console for error messages
3. Check Netlify function logs for server-side issues
4. Ensure all dependencies are properly installed

## 📄 License

This project is part of the Recruitly job dashboard. Please ensure compliance with all applicable laws and terms of service when using this scraper.

