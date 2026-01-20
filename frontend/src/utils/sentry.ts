/**
 * Sentry error tracking for frontend
 * Tracks errors, performance issues, and user interactions
 */

import * as Sentry from "@sentry/react";

export function initSentry() {
  if (!import.meta.env.VITE_SENTRY_DSN) {
    console.log("Sentry not configured (no DSN provided)");
    return;
  }

  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    environment: import.meta.env.VITE_ENVIRONMENT || "development",
    tracesSampleRate: parseFloat(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || "0.1"),
    debug: import.meta.env.DEV,
    
    // Performance monitoring
    integrations: [
      new Sentry.Replay({
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],
    
    // Capture 10% of replay events
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
    
    // Filter out certain errors
    beforeSend(event, hint) {
      // Skip network errors in development
      if (import.meta.env.DEV && hint.originalException?.message?.includes("Network")) {
        return null;
      }
      
      // Skip 404 errors from assets
      if (event.exception?.values?.[0]?.value?.includes("404")) {
        return null;
      }
      
      return event;
    },
  });

  console.log("Sentry initialized for error tracking");
}

/**
 * Capture a custom error with context
 */
export function captureException(error: Error, context?: Record<string, any>) {
  Sentry.withScope((scope) => {
    if (context) {
      Object.entries(context).forEach(([key, value]) => {
        scope.setContext(key, value);
      });
    }
    Sentry.captureException(error);
  });
}

/**
 * Capture a custom message
 */
export function captureMessage(message: string, level: "fatal" | "error" | "warning" | "info" | "debug" = "error") {
  Sentry.captureMessage(message, level);
}

/**
 * Set user context for error tracking
 */
export function setSentryUser(userId: string, email?: string, username?: string) {
  Sentry.setUser({
    id: userId,
    email,
    username,
  });
}

/**
 * Clear user context
 */
export function clearSentryUser() {
  Sentry.setUser(null);
}

/**
 * Add breadcrumb for debugging
 */
export function addBreadcrumb(message: string, data?: Record<string, any>, level: "info" | "warning" | "error" = "info") {
  Sentry.addBreadcrumb({
    message,
    data,
    level,
    timestamp: Date.now() / 1000,
  });
}
