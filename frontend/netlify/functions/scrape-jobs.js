const { chromium } = require('playwright');

exports.handler = async (event, context) => {
  // Enable CORS
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
  };

  // Handle preflight requests
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers,
      body: ''
    };
  }

  try {
    // Parse request body
    const body = JSON.parse(event.body || '{}');
    const {
      keywords = 'software engineer',
      location = 'remote',
      platforms = ['indeed', 'linkedin', 'glassdoor'],
      maxResults = 10
    } = body;

    console.log(`Starting job scrape for: ${keywords} in ${location}`);

    // Launch browser
    const browser = await chromium.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--no-first-run',
        '--no-zygote',
        '--disable-gpu'
      ]
    });

    const results = [];

    // Scrape each platform
    for (const platform of platforms) {
      try {
        console.log(`Scraping ${platform}...`);
        const platformResults = await scrapePlatform(browser, platform, keywords, location, maxResults);
        results.push(...platformResults);
      } catch (error) {
        console.error(`Error scraping ${platform}:`, error);
        results.push({
          platform,
          error: error.message,
          jobs: []
        });
      }
    }

    await browser.close();

    return {
      statusCode: 200,
      headers: {
        ...headers,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        success: true,
        totalJobs: results.length,
        results,
        timestamp: new Date().toISOString()
      })
    };

  } catch (error) {
    console.error('Serverless function error:', error);
    return {
      statusCode: 500,
      headers: {
        ...headers,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        success: false,
        error: error.message
      })
    };
  }
};

async function scrapePlatform(browser, platform, keywords, location, maxResults) {
  const page = await browser.newPage();

  // Set user agent to avoid detection
  await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');

  // Set viewport
  await page.setViewportSize({ width: 1920, height: 1080 });

  let jobs = [];

  try {
    switch (platform.toLowerCase()) {
      case 'indeed':
        jobs = await scrapeIndeed(page, keywords, location, maxResults);
        break;
      case 'linkedin':
        jobs = await scrapeLinkedIn(page, keywords, location, maxResults);
        break;
      case 'glassdoor':
        jobs = await scrapeGlassdoor(page, keywords, location, maxResults);
        break;
      default:
        throw new Error(`Unsupported platform: ${platform}`);
    }
  } finally {
    await page.close();
  }

  return jobs.map(job => ({
    ...job,
    platform,
    scrapedAt: new Date().toISOString()
  }));
}

async function scrapeIndeed(page, keywords, location, maxResults) {
  const searchQuery = encodeURIComponent(`${keywords} ${location}`);
  const url = `https://www.indeed.com/jobs?q=${searchQuery}&l=${encodeURIComponent(location)}`;

  console.log(`Navigating to Indeed: ${url}`);
  await page.goto(url, { waitUntil: 'networkidle' });

  // Wait for job listings to load
  await page.waitForSelector('[data-jk]', { timeout: 10000 });

  // Extract job listings
  const jobs = await page.evaluate((maxResults) => {
    const jobCards = document.querySelectorAll('[data-jk]');
    const results = [];

    for (let i = 0; i < Math.min(jobCards.length, maxResults); i++) {
      const card = jobCards[i];
      const jobId = card.getAttribute('data-jk');

      const titleElement = card.querySelector('[data-testid="jobsearch-SerpJobCard"] h2 a');
      const companyElement = card.querySelector('[data-testid="jobsearch-SerpJobCard"] .companyName');
      const locationElement = card.querySelector('[data-testid="jobsearch-SerpJobCard"] .companyLocation');
      const salaryElement = card.querySelector('[data-testid="jobsearch-SerpJobCard"] .salary-snippet');
      const descriptionElement = card.querySelector('[data-testid="jobsearch-SerpJobCard"] .job-snippet');

      if (titleElement) {
        results.push({
          id: jobId,
          title: titleElement.textContent?.trim() || '',
          company: companyElement?.textContent?.trim() || '',
          location: locationElement?.textContent?.trim() || '',
          salary: salaryElement?.textContent?.trim() || '',
          description: descriptionElement?.textContent?.trim() || '',
          url: `https://www.indeed.com/viewjob?jk=${jobId}`,
          postedDate: new Date().toISOString() // Indeed doesn't always show exact dates
        });
      }
    }

    return results;
  }, maxResults);

  return jobs;
}

async function scrapeLinkedIn(page, keywords, location, maxResults) {
  const searchQuery = encodeURIComponent(`${keywords} ${location}`);
  const url = `https://www.linkedin.com/jobs/search/?keywords=${searchQuery}&location=${encodeURIComponent(location)}`;

  console.log(`Navigating to LinkedIn: ${url}`);
  await page.goto(url, { waitUntil: 'networkidle' });

  // Wait for job listings to load
  await page.waitForSelector('.job-search-card', { timeout: 10000 });

  // Extract job listings
  const jobs = await page.evaluate((maxResults) => {
    const jobCards = document.querySelectorAll('.job-search-card');
    const results = [];

    for (let i = 0; i < Math.min(jobCards.length, maxResults); i++) {
      const card = jobCards[i];

      const titleElement = card.querySelector('.job-search-card__title');
      const companyElement = card.querySelector('.job-search-card__subtitle');
      const locationElement = card.querySelector('.job-search-card__location');
      const timeElement = card.querySelector('.job-search-card__listdate');
      const linkElement = card.querySelector('a');

      if (titleElement) {
        results.push({
          id: card.getAttribute('data-job-id') || `linkedin-${i}`,
          title: titleElement.textContent?.trim() || '',
          company: companyElement?.textContent?.trim() || '',
          location: locationElement?.textContent?.trim() || '',
          salary: '', // LinkedIn doesn't always show salary
          description: '', // Would need to click into each job for full description
          url: linkElement?.href || '',
          postedDate: timeElement?.textContent?.trim() || new Date().toISOString()
        });
      }
    }

    return results;
  }, maxResults);

  return jobs;
}

async function scrapeGlassdoor(page, keywords, location, maxResults) {
  const searchQuery = encodeURIComponent(`${keywords} ${location}`);
  const url = `https://www.glassdoor.com/Job/jobs.htm?sc.keyword=${searchQuery}&locT=N&locId=1&jobType=&fromAge=-1&minSalary=0&includeNoSalaryJobs=true&radius=100&cityId=-1&minRating=0.0&industryId=-1&sgocId=-1&seniorityType=all&companyId=-1&employerSizes=0&applicationType=0&remoteWorkType=0`;

  console.log(`Navigating to Glassdoor: ${url}`);
  await page.goto(url, { waitUntil: 'networkidle' });

  // Wait for job listings to load
  await page.waitForSelector('[data-test="jobListing"]', { timeout: 10000 });

  // Extract job listings
  const jobs = await page.evaluate((maxResults) => {
    const jobCards = document.querySelectorAll('[data-test="jobListing"]');
    const results = [];

    for (let i = 0; i < Math.min(jobCards.length, maxResults); i++) {
      const card = jobCards[i];

      const titleElement = card.querySelector('[data-test="job-link"]');
      const companyElement = card.querySelector('[data-test="employer-name"]');
      const locationElement = card.querySelector('[data-test="location"]');
      const salaryElement = card.querySelector('[data-test="salary-estimate"]');
      const timeElement = card.querySelector('[data-test="job-age"]');
      const linkElement = card.querySelector('a');

      if (titleElement) {
        results.push({
          id: card.getAttribute('data-id') || `glassdoor-${i}`,
          title: titleElement.textContent?.trim() || '',
          company: companyElement?.textContent?.trim() || '',
          location: locationElement?.textContent?.trim() || '',
          salary: salaryElement?.textContent?.trim() || '',
          description: '', // Would need to click into each job for full description
          url: linkElement?.href || '',
          postedDate: timeElement?.textContent?.trim() || new Date().toISOString()
        });
      }
    }

    return results;
  }, maxResults);

  return jobs;
}

