// ecosystem.config.js
module.exports = {
  apps: [
    {
      name: "agent",
      script: "asi_integritas_agent.py", // your Python script
      interpreter: "venv/bin/python", // use the Python from your virtualenv
      time: true, // show timestamps in logs
      autorestart: true, // restart on crash
      min_uptime: "5s", // process considered up after 5s
      restart_delay: 5000, // wait 5s before restarting
      max_restarts: 10, // avoid infinite restart loops
    },
  ],
};
