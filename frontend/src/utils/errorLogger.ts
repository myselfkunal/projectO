/**
 * Error logging utility for production monitoring
 * Logs errors with context for debugging
 */

interface ErrorContext {
  component?: string;
  action?: string;
  userId?: string;
  timestamp?: string;
  userAgent?: string;
  url?: string;
}

interface ErrorLog {
  message: string;
  stack?: string;
  context?: ErrorContext;
  level: 'error' | 'warning' | 'info';
  isDevelopment: boolean;
}

class ErrorLogger {
  private isDevelopment = import.meta.env.DEV;
  private logQueue: ErrorLog[] = [];

  /**
   * Log an error with context
   */
  logError(error: Error | string, context?: ErrorContext): void {
    const errorLog: ErrorLog = {
      message: error instanceof Error ? error.message : error,
      stack: error instanceof Error ? error.stack : undefined,
      context: {
        ...context,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
      },
      level: 'error',
      isDevelopment: this.isDevelopment,
    };

    this.logQueue.push(errorLog);
    this.printLog(errorLog);

    // In production, optionally send to monitoring service
    if (!this.isDevelopment) {
      this.sendToMonitoring(errorLog);
    }
  }

  /**
   * Log a warning
   */
  logWarning(message: string, context?: ErrorContext): void {
    const log: ErrorLog = {
      message,
      context: {
        ...context,
        timestamp: new Date().toISOString(),
      },
      level: 'warning',
      isDevelopment: this.isDevelopment,
    };

    this.logQueue.push(log);
    this.printLog(log);
  }

  /**
   * Log an info message
   */
  logInfo(message: string, context?: ErrorContext): void {
    const log: ErrorLog = {
      message,
      context: {
        ...context,
        timestamp: new Date().toISOString(),
      },
      level: 'info',
      isDevelopment: this.isDevelopment,
    };

    if (this.isDevelopment) {
      this.printLog(log);
    }
  }

  /**
   * Print log to console with formatting
   */
  private printLog(log: ErrorLog): void {
    const prefix = `[${log.level.toUpperCase()}] ${log.context?.timestamp}`;
    const message = log.context?.component
      ? `${prefix} [${log.context.component}] ${log.message}`
      : `${prefix} ${log.message}`;

    switch (log.level) {
      case 'error':
        console.error(message, log.stack);
        break;
      case 'warning':
        console.warn(message);
        break;
      case 'info':
        console.log(message);
        break;
    }
  }

  /**
   * Send error to monitoring service (e.g., Sentry, DataDog)
   * Implement based on your monitoring solution
   */
  private sendToMonitoring(errorLog: ErrorLog): void {
    // TODO: Implement integration with error tracking service
    // Example: Sentry.captureException(errorLog)
  }

  /**
   * Get all logged errors
   */
  getLogs(): ErrorLog[] {
    return this.logQueue;
  }

  /**
   * Clear log queue
   */
  clearLogs(): void {
    this.logQueue = [];
  }
}

export const errorLogger = new ErrorLogger();
