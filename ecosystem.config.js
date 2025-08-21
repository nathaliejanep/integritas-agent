// ecosystem.config.js
module.exports = {
  apps: [
    {
      name: "agent",
      cwd: "/home/integritas-agent",
      script: "/home/integritas-agent/venv/bin/python", // run python itself
      args: "-m app.agent", // pass -m app.agent
      time: true,
    },
  ],
};
