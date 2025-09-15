# Monitoring Setup Guide

This guide covers the setup and configuration of monitoring and analytics for the CADS Research Visualization system using Sentry and Vercel Analytics.

## Overview

The monitoring system includes:
- **Sentry**: Error tracking, performance monitoring, and session replay
- **Vercel Analytics**: User analytics, Core Web Vitals, and custom event tracking
- **Custom Performance Monitoring**: Application-specific metrics and user interaction tracking

## Sentry Setup

### 1. Create Sentry Project

1. Go to [sentry.io](https://sentry.io) and create an account
2. Create a new project for "JavaScript" platform
3. Copy the DSN (Data Source Name) from the project settings

### 2. Configure Sentry DSN

Update the DSN in both HTML files:

**In `index.html` and `visuals/public/index.html`:**
```javascript
// Replace this line:
dsn: 'https://your-sentry-dsn@sentry.io/project-id',
// With your actual DSN:
dsn: 'https://abc123@o123456.ingest.sentry.io/123456',
```

### 3. Sentry Features Enabled

- **Error Tracking**: Automatic capture of JavaScript errors and unhandled promise rejections
- **Performance Monitoring**: 10% sampling of user sessions for performance data
- **Session Replay**: 10% of normal sessions, 100% of error sessions recorded
- **Release Tracking**: Correlate errors with deployments
- **Custom Context**: Browser info, device info, user interactions

### 4. Environment Configuration

The system automatically detects environments:
- `localhost` → `development` (errors filtered out)
- All other domains → `production` (full error reporting)

## Vercel Analytics Setup

### 1. Enable Vercel Analytics

1. In your Vercel dashboard, go to your project
2. Navigate to the "Analytics" tab
3. Enable Vercel Analytics for your project

### 2. Analytics Features

The system automatically tracks:
- **Page Views**: Automatic tracking of page loads
- **Core Web Vitals**: LCP, FID, CLS metrics
- **Custom Events**: User interactions, errors, performance metrics
- **User Flow**: Navigation patterns and engagement

### 3. Custom Event Tracking

The application tracks these custom events:
- `App Initialization`: Application startup metrics
- `Data Load Complete`: Data loading performance
- `Data Load Failed`: Loading error details
- `User Interaction`: Filter usage, clicks, searches
- `Performance Metric`: Render times, memory usage
- `Application Error`: Error occurrences and context

## Performance Monitoring

### Core Web Vitals Tracking

Automatically monitors and reports:
- **Largest Contentful Paint (LCP)**: Loading performance
- **First Input Delay (FID)**: Interactivity
- **Cumulative Layout Shift (CLS)**: Visual stability

### Custom Performance Metrics

- **Data Load Time**: Time to load visualization data
- **Render Performance**: Deck.gl rendering performance
- **Memory Usage**: JavaScript heap usage monitoring
- **Filter Performance**: Time to apply filters and update visualization

### User Interaction Tracking

- **Filter Usage**: Which filters are used most frequently
- **Paper Clicks**: Research paper engagement
- **Keyword Searches**: Search behavior analysis
- **Navigation Patterns**: How users explore the visualization

## Monitoring Dashboard

### Sentry Dashboard

Access your Sentry dashboard to view:
- **Issues**: Error reports with stack traces and context
- **Performance**: Transaction performance and slow operations
- **Releases**: Error rates by deployment version
- **Replays**: Session recordings of user interactions

### Vercel Analytics Dashboard

View analytics in Vercel dashboard:
- **Overview**: Page views, unique visitors, top pages
- **Web Vitals**: Core Web Vitals scores and trends
- **Custom Events**: Your tracked events and their frequency
- **Real User Monitoring**: Actual user experience data

## Alert Configuration

### Sentry Alerts

Recommended alert rules:
1. **High Error Rate**: >10 errors in 5 minutes
2. **Performance Degradation**: >2s average response time
3. **New Error Types**: First occurrence of new error
4. **Memory Issues**: High memory usage events

### Setting Up Alerts

1. In Sentry, go to Alerts → Create Alert Rule
2. Choose conditions based on error frequency or performance
3. Configure notification channels (email, Slack, etc.)
4. Test alerts to ensure they work correctly

## Troubleshooting

### Common Issues

1. **Sentry Not Loading**
   - Check if Sentry SDK script is loaded correctly
   - Verify DSN is correct and project exists
   - Check browser console for initialization errors

2. **Events Not Appearing**
   - Verify environment configuration (dev vs prod)
   - Check beforeSend filters aren't blocking events
   - Ensure proper sampling rates

3. **Performance Data Missing**
   - Confirm tracesSampleRate is set (0.1 = 10%)
   - Check if BrowserTracing integration is enabled
   - Verify performance API is available in browser

### Debug Mode

Enable debug logging in development:
```javascript
// Add to Sentry config for debugging
debug: window.location.hostname === 'localhost',
```

## Privacy and Compliance

### Data Collection

The monitoring system collects:
- **Technical Data**: Errors, performance metrics, browser info
- **Usage Data**: Feature usage, interaction patterns
- **No Personal Data**: No PII, user names, or sensitive content

### Data Retention

- **Sentry**: 90 days for errors, 30 days for performance data
- **Vercel Analytics**: 30 days for detailed data, 1 year for aggregated data

### GDPR Compliance

- No personal data is collected
- Users can opt-out via browser settings
- Data is processed for legitimate technical interests

## Maintenance

### Regular Tasks

1. **Weekly**: Review error trends and fix critical issues
2. **Monthly**: Analyze performance trends and optimize slow operations
3. **Quarterly**: Review alert configurations and update thresholds
4. **Release**: Tag releases in Sentry for better error correlation

### Performance Optimization

Monitor these metrics for optimization opportunities:
- Data loading times >3 seconds
- Filter application times >500ms
- Memory usage >100MB
- High error rates >1% of sessions

## Integration with CI/CD

The monitoring system integrates with the CI/CD pipeline:
- **Release Tracking**: Automatic release tagging in Sentry
- **Error Correlation**: Link errors to specific deployments
- **Performance Regression**: Track performance changes between releases

## Support

For monitoring setup issues:
1. Check this documentation first
2. Review browser console for errors
3. Check Sentry/Vercel documentation
4. Contact the development team with specific error messages