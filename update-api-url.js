#!/usr/bin/env node

/**
 * Update API URL in backend-api.js
 * Usage: node update-api-url.js https://your-ngrok-url.ngrok.io
 */

const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
if (args.length === 0) {
    console.error('❌ Error: Please provide the ngrok URL');
    console.log('Usage: node update-api-url.js https://abc123.ngrok.io');
    process.exit(1);
}

const newUrl = args[0];
const filePath = path.join(__dirname, 'js', 'backend-api.js');

// Validate URL
if (!newUrl.startsWith('http://') && !newUrl.startsWith('https://')) {
    console.error('❌ Error: URL must start with http:// or https://');
    process.exit(1);
}

try {
    // Read the file
    let content = fs.readFileSync(filePath, 'utf8');

    // Update the API_BASE_URL
    const urlRegex = /const API_BASE_URL = .*?;/s;
    const newLine = `const API_BASE_URL = '${newUrl}';`;

    content = content.replace(urlRegex, newLine);

    // Write back
    fs.writeFileSync(filePath, content, 'utf8');

    console.log('✅ Updated API URL successfully!');
    console.log(`📡 New URL: ${newUrl}`);
    console.log('');
    console.log('🔄 Refresh your browser to apply changes');

} catch (error) {
    console.error('❌ Error updating file:', error.message);
    process.exit(1);
}
