/**
 * Artillery processor for custom metrics and helpers.
 * Used by all Artillery test scenarios.
 */

// Track custom metrics
let requestCount = 0;
let errorCount = 0;

module.exports = {
  /**
   * Before request hook - can modify request
   */
  beforeRequest: (requestParams, context, ee, next) => {
    requestCount++;
    context.vars.requestId = `req-${requestCount}`;
    return next();
  },

  /**
   * After response hook - track metrics
   */
  afterResponse: (requestParams, response, context, ee, next) => {
    if (response.statusCode >= 400) {
      errorCount++;
    }

    // Emit custom metric every 1000 requests
    if (requestCount % 1000 === 0) {
      ee.emit('counter', 'total_requests', requestCount);
      ee.emit('counter', 'total_errors', errorCount);
      ee.emit('counter', 'error_rate', errorCount / requestCount);
    }

    return next();
  },

  /**
   * Custom metric reporter
   */
  onTestComplete: (report) => {
    console.log('\n=== Artillery Test Summary ===');
    console.log(`Total requests: ${report.codes ? Object.keys(report.codes).length : 0}`);
    console.log(`Duration: ${report.duration || 'N/A'}s`);
    console.log(`RPS: ${report.rps ? report.rps.mean : 'N/A'}`);
    console.log('=============================\n');
  },
};
