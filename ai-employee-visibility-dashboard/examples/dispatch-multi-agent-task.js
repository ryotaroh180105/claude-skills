#!/usr/bin/env node
/**
 * Mission Control Multi-Agent Task Dispatcher
 * Connect to Mission Control dashboard and dispatch parallel tasks to Claude + Hermes
 *
 * Usage:
 *   node examples/dispatch-multi-agent-task.js "your task description here"
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

function loadEnv() {
  const envPath = path.join(__dirname, '..', '.env.local');
  const env = {};

  if (fs.existsSync(envPath)) {
    const content = fs.readFileSync(envPath, 'utf8');
    content.split('\n').forEach(line => {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) return;
      const [key, ...valueParts] = trimmed.split('=');
      if (key) {
        env[key.trim()] = valueParts.join('=').trim();
      }
    });
  }

  return env;
}

const envLocal = loadEnv();
const MC_URL = process.env.MC_URL || envLocal.MC_URL || 'http://localhost:3000';
const MC_API_KEY = process.env.MC_API_KEY || envLocal.MC_API_KEY || '';

if (!MC_API_KEY) {
  console.error('Error: MC_API_KEY not set in .env.local');
  process.exit(1);
}

const taskDescription = process.argv[2] || 'Analyze codebase and generate performance report';

async function makeRequest(method, path, body = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(MC_URL + path);
    const options = {
      hostname: url.hostname,
      port: url.port || 3000,
      path: url.pathname + url.search,
      method,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': MC_API_KEY,
      },
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, data: JSON.parse(data) });
        } catch (e) {
          resolve({ status: res.statusCode, data });
        }
      });
    });

    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

async function dispatchTask(agentName, taskDesc) {
  console.log(`[${agentName}] Dispatching task...`);
  const result = await makeRequest('POST', '/api/tasks', {
    agent: agentName,
    prompt: taskDesc,
    max_capacity: 1,
  });
  return result.data;
}

async function main() {
  console.log(`🚀 Mission Control Multi-Agent Dispatcher`);
  console.log(`URL: ${MC_URL}`);
  console.log(`Task: "${taskDescription}"\n`);

  // Dispatch to Claude Code
  const claudeTask = dispatchTask('Claude', taskDescription);

  // Dispatch to Hermes Agent in parallel
  const hermesTask = dispatchTask('Hermes', taskDescription);

  const [claudeResult, hermesResult] = await Promise.all([claudeTask, hermesTask]);

  console.log('\n📊 Task Status:');
  console.log(`Claude: ${JSON.stringify(claudeResult, null, 2)}`);
  console.log(`Hermes: ${JSON.stringify(hermesResult, null, 2)}`);

  console.log('\n✅ Open http://localhost:3000 to see tasks in Fleet Status & Activity panels');
}

main().catch(console.error);
