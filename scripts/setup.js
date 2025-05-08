const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

console.log('Setting up Live Language Translator...');

// Install Node.js dependencies
console.log('\n📦 Installing frontend dependencies...');
try {
  execSync('npm install', { stdio: 'inherit' });
  console.log('✅ Frontend dependencies installed successfully.');
} catch (error) {
  console.error('❌ Failed to install frontend dependencies:', error.message);
  process.exit(1);
}

// Check if Python is installed
console.log('\n🐍 Checking for Python installation...');
try {
  const pythonVersion = execSync('python --version', { encoding: 'utf8' });
  console.log(`✅ Python found: ${pythonVersion.trim()}`);
} catch (error) {
  console.error('❌ Python not found. Please install Python 3.6 or higher.');
  process.exit(1);
}

// Install Python dependencies
console.log('\n📦 Installing backend dependencies...');
try {
  execSync('pip install -r backend/requirements.txt', { stdio: 'inherit' });
  console.log('✅ Backend dependencies installed successfully.');
} catch (error) {
  console.error('❌ Failed to install backend dependencies:', error.message);
  process.exit(1);
}

// Create .env file if it doesn't exist
const envPath = path.join(__dirname, '..', 'backend', '.env');
if (!fs.existsSync(envPath)) {
  console.log('\n🔑 Creating .env file for API keys...');
  const envContent = `# API Keys for Live Language Translator
# Replace with your actual keys
DEEPGRAM_API_KEY=""
DEEPL_API_KEY=""
OPENAI_API_KEY=""
`;
  fs.writeFileSync(envPath, envContent);
  console.log(`✅ Created .env file at ${envPath}`);
  console.log('⚠️ Please edit this file to add your API keys before running the app.');
}

console.log('\n🎉 Setup complete! You can now run the app with:');
console.log('npm start'); 