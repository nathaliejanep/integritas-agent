// // ecosystem.config.js
module.exports = {
  apps: [
    {
      name: "agent",
      cwd: "/home/integritas-agent",
      script: "app.agent",
      interpreter: "/home/integritas-agent/venv/bin/python",
      interpreter_args: "-m",
      exec_mode: "fork",
      time: true,
      autorestart: true,
      min_uptime: "5s",
      restart_delay: 5000,
      max_restarts: 10,
    },
  ],
};
