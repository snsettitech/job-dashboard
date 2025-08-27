import React from 'react';
import { render, screen } from '@testing-library/react';
import ResumeOptimizer from './ResumeOptimizer';

// Mock fetch for API calls
global.fetch = jest.fn();

beforeEach(() => {
  (fetch as jest.Mock).mockClear();
});

describe('ResumeOptimizer Component', () => {
  test('renders resume optimizer interface', () => {
    render(<ResumeOptimizer />);

    // Check for main elements that definitely exist
    expect(screen.getByText(/AI Resume Optimizer/i)).toBeInTheDocument();
  });

  test('displays upload interface', () => {
    render(<ResumeOptimizer />);

    // Check for upload elements
    expect(screen.getByText(/Upload Your Resume/i)).toBeInTheDocument();
    expect(screen.getByText(/PDF, DOCX, or TXT/i)).toBeInTheDocument();
  });

  test('shows job description area', () => {
    render(<ResumeOptimizer />);

    // Check for job description section
    expect(screen.getByText(/Job Description/i)).toBeInTheDocument();
  });

  test('renders without crashing', () => {
    render(<ResumeOptimizer />);

    // Component should render without errors
    expect(screen.getByText(/AI Resume Optimizer/i)).toBeInTheDocument();
  });

  test('has file input element', () => {
    render(<ResumeOptimizer />);

    // Should have a file input
    const fileInput = document.querySelector('input[type="file"]');
    expect(fileInput).toBeInTheDocument();
  });

  test('has optimize button', () => {
    render(<ResumeOptimizer />);

    // Should have some kind of optimize button (might be disabled)
    const optimizeButton = screen.getByText(/Optimize My Resume/i);
    expect(optimizeButton).toBeInTheDocument();
  });
});
