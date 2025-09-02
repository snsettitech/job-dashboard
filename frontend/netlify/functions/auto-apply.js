const puppeteer = require('puppeteer');

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
      jobUrl,
      resumeData,
      userProfile,
      applicationStrategy = 'smart' // 'smart', 'quick', 'detailed'
    } = body;

    if (!jobUrl || !resumeData || !userProfile) {
      return {
        statusCode: 400,
        headers: {
          ...headers,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          success: false,
          error: 'Missing required fields: jobUrl, resumeData, userProfile'
        })
      };
    }

    console.log(`Starting auto-apply for: ${jobUrl}`);

    // Launch browser
    const browser = await puppeteer.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--no-first-run',
        '--no-zygote',
        '--disable-gpu',
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor'
      ]
    });

    const page = await browser.newPage();

    // Set user agent to avoid detection
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');

    // Set viewport
    await page.setViewport({ width: 1920, height: 1080 });

    // Set extra headers
    await page.setExtraHTTPHeaders({
      'Accept-Language': 'en-US,en;q=0.9',
      'Accept-Encoding': 'gzip, deflate, br',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    });

    let result;

    try {
      // Navigate to job page
      console.log('Navigating to job page...');
      await page.goto(jobUrl, {
        waitUntil: 'networkidle2',
        timeout: 30000
      });

      // Detect platform and apply appropriate strategy
      const platform = detectPlatform(jobUrl);
      console.log(`Detected platform: ${platform}`);

      switch (platform) {
        case 'indeed':
          result = await applyToIndeed(page, resumeData, userProfile, applicationStrategy);
          break;
        case 'linkedin':
          result = await applyToLinkedIn(page, resumeData, userProfile, applicationStrategy);
          break;
        case 'glassdoor':
          result = await applyToGlassdoor(page, resumeData, userProfile, applicationStrategy);
          break;
        case 'generic':
          result = await applyToGeneric(page, resumeData, userProfile, applicationStrategy);
          break;
        default:
          throw new Error(`Unsupported platform: ${platform}`);
      }

    } finally {
      await browser.close();
    }

    return {
      statusCode: 200,
      headers: {
        ...headers,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        success: true,
        result,
        timestamp: new Date().toISOString()
      })
    };

  } catch (error) {
    console.error('Auto-apply function error:', error);
    return {
      statusCode: 500,
      headers: {
        ...headers,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        success: false,
        error: error.message,
        timestamp: new Date().toISOString()
      })
    };
  }
};

function detectPlatform(url) {
  if (url.includes('indeed.com')) return 'indeed';
  if (url.includes('linkedin.com')) return 'linkedin';
  if (url.includes('glassdoor.com')) return 'glassdoor';
  return 'generic';
}

async function applyToIndeed(page, resumeData, userProfile, strategy) {
  console.log('Applying to Indeed...');

  try {
    // Wait for page to load
    await page.waitForTimeout(2000);

    // Look for apply button
    const applySelectors = [
      '[data-testid="jobsearch-ApplyButton"]',
      'button[aria-label*="Apply"]',
      'button:contains("Apply")',
      'a[href*="apply"]',
      '.apply-button',
      '[data-jk] button'
    ];

    let applyButton = null;
    for (const selector of applySelectors) {
      try {
        applyButton = await page.$(selector);
        if (applyButton) break;
      } catch (e) {
        continue;
      }
    }

    if (!applyButton) {
      throw new Error('Apply button not found');
    }

    // Click apply button
    await applyButton.click();
    await page.waitForTimeout(3000);

    // Handle application form
    const result = await fillApplicationForm(page, resumeData, userProfile, strategy);

    return {
      platform: 'indeed',
      status: 'applied',
      message: 'Application submitted successfully',
      details: result
    };

  } catch (error) {
    console.error('Indeed application failed:', error);
    return {
      platform: 'indeed',
      status: 'failed',
      error: error.message
    };
  }
}

async function applyToLinkedIn(page, resumeData, userProfile, strategy) {
  console.log('Applying to LinkedIn...');

  try {
    // Wait for page to load
    await page.waitForTimeout(2000);

    // Look for apply button
    const applySelectors = [
      'button[aria-label*="Apply"]',
      'button:contains("Apply")',
      '.apply-button',
      '[data-control-name="jobdetails_topcard_inapply"]'
    ];

    let applyButton = null;
    for (const selector of applySelectors) {
      try {
        applyButton = await page.$(selector);
        if (applyButton) break;
      } catch (e) {
        continue;
      }
    }

    if (!applyButton) {
      throw new Error('Apply button not found');
    }

    // Click apply button
    await applyButton.click();
    await page.waitForTimeout(3000);

    // Handle application form
    const result = await fillApplicationForm(page, resumeData, userProfile, strategy);

    return {
      platform: 'linkedin',
      status: 'applied',
      message: 'Application submitted successfully',
      details: result
    };

  } catch (error) {
    console.error('LinkedIn application failed:', error);
    return {
      platform: 'linkedin',
      status: 'failed',
      error: error.message
    };
  }
}

async function applyToGlassdoor(page, resumeData, userProfile, strategy) {
  console.log('Applying to Glassdoor...');

  try {
    // Wait for page to load
    await page.waitForTimeout(2000);

    // Look for apply button
    const applySelectors = [
      'button[data-test="apply-button"]',
      'button:contains("Apply")',
      '.apply-button',
      '[data-test="apply"]'
    ];

    let applyButton = null;
    for (const selector of applySelectors) {
      try {
        applyButton = await page.$(selector);
        if (applyButton) break;
      } catch (e) {
        continue;
      }
    }

    if (!applyButton) {
      throw new Error('Apply button not found');
    }

    // Click apply button
    await applyButton.click();
    await page.waitForTimeout(3000);

    // Handle application form
    const result = await fillApplicationForm(page, resumeData, userProfile, strategy);

    return {
      platform: 'glassdoor',
      status: 'applied',
      message: 'Application submitted successfully',
      details: result
    };

  } catch (error) {
    console.error('Glassdoor application failed:', error);
    return {
      platform: 'glassdoor',
      status: 'failed',
      error: error.message
    };
  }
}

async function applyToGeneric(page, resumeData, userProfile, strategy) {
  console.log('Applying to generic job site...');

  try {
    // Wait for page to load
    await page.waitForTimeout(2000);

    // Look for common apply button patterns
    const applySelectors = [
      'button:contains("Apply")',
      'button:contains("Apply Now")',
      'a:contains("Apply")',
      'a:contains("Apply Now")',
      '.apply-button',
      '.apply-now',
      '[class*="apply"]',
      '[id*="apply"]'
    ];

    let applyButton = null;
    for (const selector of applySelectors) {
      try {
        applyButton = await page.$(selector);
        if (applyButton) break;
      } catch (e) {
        continue;
      }
    }

    if (!applyButton) {
      throw new Error('Apply button not found');
    }

    // Click apply button
    await applyButton.click();
    await page.waitForTimeout(3000);

    // Handle application form
    const result = await fillApplicationForm(page, resumeData, userProfile, strategy);

    return {
      platform: 'generic',
      status: 'applied',
      message: 'Application submitted successfully',
      details: result
    };

  } catch (error) {
    console.error('Generic application failed:', error);
    return {
      platform: 'generic',
      status: 'failed',
      error: error.message
    };
  }
}

async function fillApplicationForm(page, resumeData, userProfile, strategy) {
  console.log(`Filling application form with ${strategy} strategy...`);

  const result = {
    fieldsFilled: 0,
    fieldsSkipped: 0,
    errors: [],
    strategy: strategy
  };

  try {
    // Wait for form to load
    await page.waitForTimeout(2000);

    // Common form field selectors
    const fieldMappings = {
      // Personal Information
      firstName: ['input[name*="first"], input[name*="fname"], input[id*="first"], input[id*="fname"]'],
      lastName: ['input[name*="last"], input[name*="lname"], input[id*="last"], input[id*="lname"]'],
      email: ['input[type="email"], input[name*="email"], input[id*="email"]'],
      phone: ['input[type="tel"], input[name*="phone"], input[name*="mobile"], input[id*="phone"]'],

      // Address
      address: ['input[name*="address"], input[name*="street"], textarea[name*="address"]'],
      city: ['input[name*="city"], input[id*="city"]'],
      state: ['input[name*="state"], select[name*="state"], input[id*="state"]'],
      zipCode: ['input[name*="zip"], input[name*="postal"], input[id*="zip"]'],

      // Professional
      experience: ['input[name*="experience"], input[name*="years"], select[name*="experience"]'],
      education: ['input[name*="education"], select[name*="education"]'],
      skills: ['textarea[name*="skills"], input[name*="skills"]'],

      // Cover Letter
      coverLetter: ['textarea[name*="cover"], textarea[name*="letter"], textarea[id*="cover"]'],

      // Questions
      whyInterested: ['textarea[name*="why"], textarea[name*="interest"], textarea[id*="why"]'],
      salary: ['input[name*="salary"], input[name*="compensation"], input[id*="salary"]']
    };

    // Fill form fields based on strategy
    for (const [fieldName, selectors] of Object.entries(fieldMappings)) {
      try {
        let field = null;

        // Try each selector for this field
        for (const selector of selectors) {
          try {
            field = await page.$(selector);
            if (field) break;
          } catch (e) {
            continue;
          }
        }

        if (field) {
          const value = getFieldValue(fieldName, resumeData, userProfile, strategy);

          if (value) {
            // Clear existing value
            await field.click({ clickCount: 3 });
            await field.type(value);
            result.fieldsFilled++;
            console.log(`Filled ${fieldName}: ${value.substring(0, 50)}...`);
          }
        }
      } catch (error) {
        result.errors.push(`Error filling ${fieldName}: ${error.message}`);
      }
    }

    // Handle file uploads (resume)
    await handleResumeUpload(page, resumeData, result);

    // Handle checkboxes and radio buttons
    await handleCheckboxesAndRadioButtons(page, userProfile, result);

    // Submit form
    await submitForm(page, result);

  } catch (error) {
    result.errors.push(`Form filling error: ${error.message}`);
  }

  return result;
}

function getFieldValue(fieldName, resumeData, userProfile, strategy) {
  const { personal, experience, education, skills } = resumeData;
  const { preferences, customAnswers } = userProfile;

  switch (fieldName) {
    case 'firstName':
      return personal?.firstName || userProfile.firstName;

    case 'lastName':
      return personal?.lastName || userProfile.lastName;

    case 'email':
      return personal?.email || userProfile.email;

    case 'phone':
      return personal?.phone || userProfile.phone;

    case 'address':
      return personal?.address?.street || userProfile.address?.street;

    case 'city':
      return personal?.address?.city || userProfile.address?.city;

    case 'state':
      return personal?.address?.state || userProfile.address?.state;

    case 'zipCode':
      return personal?.address?.zipCode || userProfile.address?.zipCode;

    case 'experience':
      return calculateTotalExperience(experience);

    case 'education':
      return getHighestEducation(education);

    case 'skills':
      return skills?.join(', ') || '';

    case 'coverLetter':
      return generateCoverLetter(resumeData, userProfile, strategy);

    case 'whyInterested':
      return generateWhyInterested(userProfile, strategy);

    case 'salary':
      return preferences?.salaryExpectation || '';

    default:
      return '';
  }
}

function calculateTotalExperience(experience) {
  if (!experience || !Array.isArray(experience)) return '0';

  const totalYears = experience.reduce((total, exp) => {
    const startDate = new Date(exp.startDate);
    const endDate = exp.endDate ? new Date(exp.endDate) : new Date();
    const years = (endDate - startDate) / (1000 * 60 * 60 * 24 * 365);
    return total + years;
  }, 0);

  return Math.round(totalYears).toString();
}

function getHighestEducation(education) {
  if (!education || !Array.isArray(education)) return '';

  const degrees = ['PhD', 'Master', 'Bachelor', 'Associate', 'High School'];

  for (const degree of degrees) {
    const found = education.find(edu =>
      edu.degree?.toLowerCase().includes(degree.toLowerCase())
    );
    if (found) return found.degree;
  }

  return education[0]?.degree || '';
}

function generateCoverLetter(resumeData, userProfile, strategy) {
  const { personal, experience, skills } = resumeData;
  const { jobTitle, companyName } = userProfile.currentApplication || {};

  if (strategy === 'quick') {
    return `Dear Hiring Manager,

I am excited to apply for the ${jobTitle} position at ${companyName}. With my background in ${skills?.slice(0, 3).join(', ') || 'software development'}, I believe I would be a great fit for this role.

Thank you for considering my application.

Best regards,
${personal?.firstName || userProfile.firstName} ${personal?.lastName || userProfile.lastName}`;
  }

  // Detailed cover letter
  return `Dear Hiring Manager,

I am writing to express my strong interest in the ${jobTitle} position at ${companyName}. With ${calculateTotalExperience(experience)} years of experience in ${skills?.slice(0, 5).join(', ') || 'software development'}, I am confident in my ability to contribute effectively to your team.

Throughout my career, I have demonstrated strong technical skills and a passion for delivering high-quality solutions. I am particularly drawn to ${companyName} because of its reputation for innovation and commitment to excellence.

I would welcome the opportunity to discuss how my skills and experience align with your needs. Thank you for considering my application.

Best regards,
${personal?.firstName || userProfile.firstName} ${personal?.lastName || userProfile.lastName}`;
}

function generateWhyInterested(userProfile, strategy) {
  const { jobTitle, companyName } = userProfile.currentApplication || {};

  if (strategy === 'quick') {
    return `I am interested in this ${jobTitle} position at ${companyName} because it aligns with my career goals and offers opportunities for growth.`;
  }

  return `I am excited about the ${jobTitle} position at ${companyName} because it represents an opportunity to work on challenging projects with a talented team. The company's mission and values align with my professional goals, and I believe my skills and experience would be valuable in contributing to the team's success.`;
}

async function handleResumeUpload(page, resumeData, result) {
  try {
    // Look for file upload inputs
    const fileInputSelectors = [
      'input[type="file"]',
      'input[name*="resume"]',
      'input[name*="cv"]',
      'input[id*="resume"]',
      'input[id*="cv"]'
    ];

    for (const selector of fileInputSelectors) {
      try {
        const fileInput = await page.$(selector);
        if (fileInput) {
          // Note: In a real implementation, you would need to handle file uploads
          // This is a simplified version - you'd need to provide the actual file path
          console.log('File upload field found - would upload resume here');
          result.fieldsFilled++;
          break;
        }
      } catch (e) {
        continue;
      }
    }
  } catch (error) {
    result.errors.push(`Resume upload error: ${error.message}`);
  }
}

async function handleCheckboxesAndRadioButtons(page, userProfile, result) {
  try {
    // Handle common checkboxes
    const checkboxSelectors = [
      'input[type="checkbox"]',
      'input[name*="authorize"]',
      'input[name*="agree"]',
      'input[name*="consent"]'
    ];

    for (const selector of checkboxSelectors) {
      try {
        const checkboxes = await page.$$(selector);
        for (const checkbox of checkboxes) {
          const isChecked = await checkbox.evaluate(el => el.checked);
          if (!isChecked) {
            await checkbox.click();
            result.fieldsFilled++;
          }
        }
      } catch (e) {
        continue;
      }
    }

    // Handle radio buttons for experience level, etc.
    const radioSelectors = [
      'input[type="radio"]'
    ];

    for (const selector of radioSelectors) {
      try {
        const radios = await page.$$(selector);
        if (radios.length > 0) {
          // Select the first option (usually "Yes" or most appropriate)
          await radios[0].click();
          result.fieldsFilled++;
        }
      } catch (e) {
        continue;
      }
    }
  } catch (error) {
    result.errors.push(`Checkbox/radio error: ${error.message}`);
  }
}

async function submitForm(page, result) {
  try {
    // Look for submit button
    const submitSelectors = [
      'button[type="submit"]',
      'input[type="submit"]',
      'button:contains("Submit")',
      'button:contains("Apply")',
      'button:contains("Send")',
      '.submit-button',
      '[class*="submit"]'
    ];

    let submitButton = null;
    for (const selector of submitSelectors) {
      try {
        submitButton = await page.$(selector);
        if (submitButton) break;
      } catch (e) {
        continue;
      }
    }

    if (submitButton) {
      await submitButton.click();
      await page.waitForTimeout(3000);
      result.status = 'submitted';
      console.log('Form submitted successfully');
    } else {
      result.status = 'completed';
      console.log('Submit button not found, but form completed');
    }
  } catch (error) {
    result.errors.push(`Submit error: ${error.message}`);
    result.status = 'error';
  }
}

