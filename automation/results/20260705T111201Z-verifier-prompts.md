---
id: 20260705T111201Z-verifier-prompts
status: ok
executed_at: 2026-07-05T11:22:40Z
duration_seconds: 1
---

hermes.exe : usage: hermes [-h] [--version] [-z PROMPT] [-m MODEL] [--provider PROVIDER]
発生場所 行:6 文字:13
+             & $bin -z $q --accept-hooks 2>&1 | Out-String
+             ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (usage: hermes [...vider PROVIDER]:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
              [-t TOOLSETS] [--resume SESSION] [--continue [SESSION_NAME]]
              [--worktree] [--accept-hooks] [--skills SKILLS] [--yolo]
              [--pass-session-id] [--ignore-user-config] [--ignore-rules]
              [--tui] [--dev]
              {chat,model,fallback,secrets,migrate,gateway,proxy,lsp,setup,postinstall,whatsapp,slack,send,login,logout
,auth,status,cron,webhook,portal,kanban,hooks,doctor,dump,debug,backup,checkpoints,import,config,pairing,skills,bundles
,plugins,curator,memory,tools,computer-use,mcp,sessions,insights,claw,version,update,uninstall,acp,profile,completion,d
ashboard,logs}
              ...
hermes: error: argument command: invalid choice: 'prompt, judge' (choose from 'chat', 'model', 'fallback', 'secrets', '
migrate', 'gateway', 'proxy', 'lsp', 'setup', 'postinstall', 'whatsapp', 'slack', 'send', 'login', 'logout', 'auth', 's
tatus', 'cron', 'webhook', 'portal', 'kanban', 'hooks', 'doctor', 'dump', 'debug', 'backup', 'checkpoints', 'import', '
config', 'pairing', 'skills', 'bundles', 'plugins', 'curator', 'memory', 'tools', 'computer-use', 'mcp', 'sessions', 'i
nsights', 'claw', 'version', 'update', 'uninstall', 'acp', 'profile', 'completion', 'dashboard', 'logs')
