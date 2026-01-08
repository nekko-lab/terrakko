// Load test environment variables
const dotenv = require('dotenv');
const path = require('path');

// Load .env.test file
dotenv.config({ path: path.resolve(__dirname, '.env.test') });

// Optional: Log that test environment is loaded
console.log('Test environment loaded from .env.test');
