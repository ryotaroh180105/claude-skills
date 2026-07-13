# Mission Control Integration Examples

## Multi-Agent Task Dispatcher

Dispatch tasks to multiple AI agents (Claude Code + Hermes) in parallel and watch them execute in the Mission Control dashboard.

### Setup

1. **Start Mission Control dashboard:**
   ```bash
   cd ai-employee-visibility-dashboard
   pnpm dev  # http://localhost:3000
   ```

2. **Copy API key from dashboard:**
   - Open http://localhost:3000
   - Right-click settings (⚙️) → General → scroll down to "API Key"
   - Set in `.env.local`:
     ```
     MC_API_KEY=<your-api-key>
     MC_URL=http://localhost:3000
     ```

### Run Multi-Agent Task

```bash
node examples/dispatch-multi-agent-task.js "Analyze code quality in /src directory"
```

**What happens:**
1. Task dispatched to Claude Code agent
2. Task dispatched to Hermes agent (parallel)
3. Both agents execute simultaneously
4. Watch Fleet Status panel update in real-time
5. Activity panel shows execution logs

### Expected Dashboard Output

- **Fleet Status** → Claude & Hermes showing active task counts
- **Activity** → Log entries for each agent's prompt execution
- **Agent Squad** → Real-time heartbeat indicators

### API Integration

The script uses Mission Control REST API:
- `POST /api/tasks` — Create task and assign to agent
- `GET /api/tasks` — List active tasks
- `GET /api/agents` — List registered agents with status

See `dispatch-multi-agent-task.js` for implementation.
