import sys
import asyncio
sys.path.append('app')

from services.enhanced_resume_optimizer import EnhancedResumeOptimizer

async def main():
    sample_resume = '''John Doe
Software Engineer
john.doe@email.com | (555) 123-4567 | linkedin.com/in/johndoe

Summary
Experienced software engineer with 3 years of experience in web development.

Experience
Software Engineer at Tech Corp
• Built web applications using React
• Worked with databases and APIs
• Collaborated with team members

Skills
JavaScript, HTML, CSS, React

Education
Bachelor of Science in Computer Science
University of Technology'''

    sample_job = '''Senior Software Engineer
We are looking for a Senior Software Engineer with 5+ years of experience in:
• Python development
• React and JavaScript
• AWS cloud services
• Docker and Kubernetes
• Machine learning experience
• Leadership and team management skills'''

    print("🚀 Testing Enhanced Resume Optimizer...")
    print("=" * 50)
    
    optimizer = EnhancedResumeOptimizer()
    result = await optimizer.optimize_resume(sample_resume, sample_job)
    
    print("📊 OPTIMIZATION RESULTS:")
    print(f"Original length: {result['original_length']} words")
    print(f"Optimized length: {result['optimized_length']} words")
    print(f"Match score: {result['match_score_prediction']:.1%}")
    print(f"ATS improvement: {result['ats_score_improvement']}")
    print(f"Keywords added: {result['keywords_added']}")
    print(f"Improvements: {result['improvements_made']}")
    print(f"Model used: {result['model_used']}")
    print(f"Confidence: {result['confidence_score']}% ({result['confidence_level']})")
    
    print("\n" + "=" * 50)
    print("📄 ORIGINAL RESUME:")
    print(sample_resume)
    
    print("\n" + "=" * 50)
    print("✨ OPTIMIZED RESUME:")
    print(result['optimized_resume'])
    
    print("\n" + "=" * 50)
    print("✅ Test completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
