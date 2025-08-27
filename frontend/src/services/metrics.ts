// frontend/src/services/metrics.ts - Frontend Metrics Tracking
interface MetricEvent {
  event_type: string;
  data: Record<string, any>;
  user_id?: string;
  session_id?: string;
}

interface MetricsConfig {
  apiUrl: string;
  userId?: string;
  sessionId: string;
  enabled: boolean;
}

class MetricsService {
  private config: MetricsConfig;
  private queue: MetricEvent[] = [];
  private flushInterval: NodeJS.Timeout | null = null;

  constructor(config: Partial<MetricsConfig> = {}) {
    this.config = {
      apiUrl: config.apiUrl || 'http://localhost:8000/api/metrics',
      userId: config.userId,
      sessionId: config.sessionId || this.generateSessionId(),
      enabled: config.enabled !== false, // Default to enabled
    };

    // Start auto-flush
    this.startAutoFlush();
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private startAutoFlush(): void {
    if (this.flushInterval) {
      clearInterval(this.flushInterval);
    }

    // Flush metrics every 30 seconds
    this.flushInterval = setInterval(() => {
      this.flush();
    }, 30000);
  }

  public setUserId(userId: string): void {
    this.config.userId = userId;
  }

  public async track(eventType: string, data: Record<string, any> = {}): Promise<void> {
    if (!this.config.enabled) {
      return;
    }

    const event: MetricEvent = {
      event_type: eventType,
      data: {
        ...data,
        timestamp: new Date().toISOString(),
        url: window.location.href,
        user_agent: navigator.userAgent,
      },
      user_id: this.config.userId,
      session_id: this.config.sessionId,
    };

    this.queue.push(event);

    // Flush immediately for important events
    if (this.isImportantEvent(eventType)) {
      await this.flush();
    }
  }

  private isImportantEvent(eventType: string): boolean {
    const importantEvents = [
      'resume_optimization',
      'job_match',
      'user_signup',
      'user_login',
      'error',
    ];
    return importantEvents.includes(eventType);
  }

  public async flush(): Promise<void> {
    if (this.queue.length === 0) {
      return;
    }

    const events = [...this.queue];
    this.queue = [];

    try {
      // Send events in batch
      await Promise.all(
        events.map(event => this.sendEvent(event))
      );
    } catch (error) {
      console.warn('Failed to send metrics:', error);
      // Re-queue failed events (up to a limit)
      if (this.queue.length < 100) {
        this.queue.unshift(...events);
      }
    }
  }

  private async sendEvent(event: MetricEvent): Promise<void> {
    try {
      const response = await fetch(`${this.config.apiUrl}/record`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(event),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      // Silently fail for metrics to avoid disrupting user experience
      console.debug('Metric send failed:', error);
    }
  }

  // Convenience methods for common events
  public async trackPageView(page: string, additionalData: Record<string, any> = {}): Promise<void> {
    await this.track('page_view', {
      page,
      ...additionalData,
    });
  }

  public async trackButtonClick(buttonId: string, page: string, additionalData: Record<string, any> = {}): Promise<void> {
    await this.track('button_click', {
      button_id: buttonId,
      page,
      ...additionalData,
    });
  }

  public async trackFeatureUsage(feature: string, action: string, additionalData: Record<string, any> = {}): Promise<void> {
    await this.track('feature_usage', {
      feature,
      feature_action: action,
      ...additionalData,
    });
  }

  public async trackError(error: Error, context: string, additionalData: Record<string, any> = {}): Promise<void> {
    await this.track('error', {
      error_message: error.message,
      error_stack: error.stack,
      context,
      ...additionalData,
    });
  }

  public async trackPerformance(operation: string, duration: number, additionalData: Record<string, any> = {}): Promise<void> {
    await this.track('performance', {
      operation,
      duration_ms: duration,
      ...additionalData,
    });
  }

  public async trackResumeOptimization(jobTitle: string, success: boolean, duration: number): Promise<void> {
    await this.track('resume_optimization', {
      job_title: jobTitle,
      success,
      duration_ms: duration,
    });
  }

  public async trackJobMatch(matchScore: number, jobType: string): Promise<void> {
    await this.track('job_match', {
      match_score: matchScore,
      job_type: jobType,
    });
  }

  public destroy(): void {
    if (this.flushInterval) {
      clearInterval(this.flushInterval);
      this.flushInterval = null;
    }
    this.flush(); // Final flush
  }
}

// Create global metrics instance
const metrics = new MetricsService({
  enabled: process.env.NODE_ENV === 'production' || process.env.REACT_APP_ENABLE_METRICS === 'true',
});

// Performance timing helper
export function withMetrics<T>(
  operation: string,
  fn: () => Promise<T>,
  additionalData: Record<string, any> = {}
): Promise<T> {
  const start = performance.now();
  
  return fn()
    .then(result => {
      const duration = performance.now() - start;
      metrics.trackPerformance(operation, duration, additionalData);
      return result;
    })
    .catch(error => {
      const duration = performance.now() - start;
      metrics.trackError(error, operation, { duration_ms: duration, ...additionalData });
      throw error;
    });
}

// React hook for metrics
export function useMetrics() {
  return {
    track: metrics.track.bind(metrics),
    trackPageView: metrics.trackPageView.bind(metrics),
    trackButtonClick: metrics.trackButtonClick.bind(metrics),
    trackFeatureUsage: metrics.trackFeatureUsage.bind(metrics),
    trackError: metrics.trackError.bind(metrics),
    trackPerformance: metrics.trackPerformance.bind(metrics),
    trackResumeOptimization: metrics.trackResumeOptimization.bind(metrics),
    trackJobMatch: metrics.trackJobMatch.bind(metrics),
    setUserId: metrics.setUserId.bind(metrics),
  };
}

export default metrics;
