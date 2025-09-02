# Auto-Apply Form Automation

A serverless function built with Puppeteer to automate job application form submissions with intelligent field mapping and resume data integration.

## 🚀 Features

- **Multi-platform support**: Indeed, LinkedIn, Glassdoor, and generic job sites
- **Intelligent form filling**: Automatic field detection and mapping
- **Resume data integration**: Structured resume data with experience, education, and skills
- **Multiple strategies**: Quick, Smart, and Detailed application modes
- **Real-time validation**: Form validation and error handling
- **Cover letter generation**: AI-powered cover letter creation
- **Anti-detection measures**: Browser fingerprinting and request delays

## 📁 Project Structure

```
frontend/
├── netlify/
│   ├── functions/
│   │   ├── auto-apply.js          # Main auto-apply function
│   │   ├── scrape-jobs.js         # Job scraping function
│   │   └── package.json           # Function dependencies
│   └── netlify.toml              # Netlify configuration
├── src/
│   ├── components/
│   │   ├── AutoApply.tsx         # React component
│   │   └── JobScraper.tsx        # Job scraper component
│   └── services/
│       ├── autoApplyService.ts   # TypeScript service
│       └── jobScraperService.ts  # Job scraper service
└── AUTO_APPLY_README.md          # This file
```

## 🛠️ Setup Instructions

### 1. Install Dependencies

Update the setup script to include Puppeteer:

```powershell
# Windows
.\setup-scraper.ps1

# Or manually:
cd netlify/functions
npm install
npx playwright install chromium
npx puppeteer browsers install chrome
cd ../..
npm install
```

### 2. Development

Start the development server:

```bash
npm start
```

Navigate to the "Auto Apply" tab in the application.

## 🔧 Configuration

### Function Configuration

The auto-apply function accepts the following parameters:

```typescript
interface AutoApplyRequest {
  jobUrl: string;                    // Job posting URL
  resumeData: ResumeData;            // Structured resume data
  userProfile: UserProfile;          // User profile and preferences
  applicationStrategy?: 'smart' | 'quick' | 'detailed';
}
```

### Resume Data Structure

```typescript
interface ResumeData {
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
```

### User Profile Structure

```typescript
interface UserProfile {
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
```

## 📊 Application Strategies

### Quick Apply (30 seconds)
- Minimal field customization
- Basic cover letter
- Fastest application time
- Suitable for high-volume applications

### Smart Apply (90 seconds)
- Intelligent field mapping
- Balanced customization
- Generated cover letter
- Recommended for most applications

### Detailed Apply (3 minutes)
- Comprehensive field filling
- Detailed cover letter
- Full customization
- Best for important applications

## 🌐 Supported Platforms

### Indeed
- **Apply Button Detection**: Multiple selector strategies
- **Form Fields**: Personal info, experience, education
- **Cover Letter**: Auto-generated based on job context
- **File Upload**: Resume upload support

### LinkedIn
- **Apply Button Detection**: LinkedIn-specific selectors
- **Form Fields**: Profile data mapping
- **Cover Letter**: LinkedIn-style formatting
- **Platform Integration**: LinkedIn profile data

### Glassdoor
- **Apply Button Detection**: Glassdoor-specific patterns
- **Form Fields**: Company-specific forms
- **Salary Information**: Salary expectation handling
- **Company Research**: Glassdoor company data

### Generic Job Sites
- **Universal Detection**: Common apply button patterns
- **Flexible Mapping**: Adaptive field detection
- **Fallback Strategies**: Multiple selector approaches
- **Error Handling**: Graceful failure recovery

## 🔒 Anti-Detection Measures

### Browser Fingerprinting
- **User Agent Rotation**: Realistic browser user agents
- **Viewport Settings**: Standard desktop resolutions
- **Header Customization**: Accept headers and encoding
- **Cookie Handling**: Session management

### Request Patterns
- **Natural Delays**: Human-like timing between actions
- **Mouse Movements**: Simulated user interactions
- **Form Filling**: Realistic typing patterns
- **Error Recovery**: Graceful handling of failures

### Platform-Specific
- **Indeed**: Respects rate limits and session management
- **LinkedIn**: LinkedIn-specific interaction patterns
- **Glassdoor**: Glassdoor form handling
- **Generic**: Universal form detection strategies

## ⚠️ Legal Considerations

⚠️ **Important**: Automated form submission may be subject to terms of service and legal restrictions:

1. **Terms of Service**: Check each platform's ToS before automation
2. **Rate Limiting**: Respect platform rate limits
3. **Data Usage**: Only use for legitimate job applications
4. **Consent**: Ensure user consent for automated actions
5. **Accuracy**: Verify all submitted information is accurate

## 🚨 Limitations

- **Dynamic Forms**: Some forms may change structure
- **CAPTCHA**: Automated systems may trigger CAPTCHA
- **Multi-step Processes**: Complex application flows
- **File Uploads**: Resume file upload limitations
- **Platform Changes**: Website structure updates

## 🔧 Troubleshooting

### Common Issues

1. **Apply Button Not Found**
   - Check if the job URL is valid
   - Verify the job is still active
   - Try different selector strategies

2. **Form Fields Not Filling**
   - Ensure resume data is complete
   - Check field validation requirements
   - Verify field selectors are current

3. **Application Submission Fails**
   - Check for required fields
   - Verify form validation
   - Review error messages

4. **Platform Detection Issues**
   - Verify job URL format
   - Check platform support
   - Use generic strategy as fallback

### Debug Mode

Enable debug logging:

```bash
DEBUG=puppeteer:*  # Puppeteer debug logs
```

## 📈 Performance Optimization

- **Parallel Processing**: Multiple applications simultaneously
- **Caching**: Resume data and user profile caching
- **Error Recovery**: Automatic retry mechanisms
- **Resource Management**: Browser instance optimization

## 🔮 Future Enhancements

- [ ] **AI-Powered Responses**: GPT-generated cover letters and answers
- [ ] **Multi-language Support**: International job applications
- [ ] **Advanced Form Detection**: Machine learning field mapping
- [ ] **Resume Parsing**: Automatic resume data extraction
- [ ] **Application Tracking**: Integration with ATS systems
- [ ] **Email Integration**: Application confirmation emails
- [ ] **Analytics Dashboard**: Application success metrics
- [ ] **Custom Templates**: User-defined application templates

## 📞 Support

For issues or questions:

1. Check the troubleshooting section above
2. Review browser console for error messages
3. Check Netlify function logs for server-side issues
4. Verify all dependencies are properly installed
5. Ensure job URLs are accessible and valid

## 📄 License

This project is part of the Recruitly job dashboard. Please ensure compliance with all applicable laws and terms of service when using this automation tool.

## 🔗 Integration

### With Job Scraper

The auto-apply function integrates seamlessly with the job scraper:

1. **Scrape Jobs**: Use the job scraper to find relevant positions
2. **Select Jobs**: Choose jobs to apply to
3. **Auto-Apply**: Use the auto-apply function to submit applications
4. **Track Results**: Monitor application status and responses

### Example Workflow

```typescript
// 1. Scrape jobs
const scrapedJobs = await jobScraperService.scrapeJobs({
  keywords: 'software engineer',
  location: 'remote',
  platforms: ['indeed', 'linkedin'],
  maxResults: 10
});

// 2. Filter and select jobs
const selectedJobs = scrapedJobs.results.filter(job => 
  job.title.toLowerCase().includes('react') || 
  job.title.toLowerCase().includes('frontend')
);

// 3. Auto-apply to selected jobs
for (const job of selectedJobs) {
  const result = await autoApplyService.autoApply({
    jobUrl: job.url,
    resumeData: userResumeData,
    userProfile: userProfile,
    applicationStrategy: 'smart'
  });
  
  console.log(`Applied to ${job.title}: ${result.result.status}`);
}
```

This creates a complete automated job application workflow from discovery to submission.

