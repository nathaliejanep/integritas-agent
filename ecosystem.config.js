// ecosystem.config.js
module.exports = {
  apps: [
    {
      name: "agent",
      script: "app.agent", // module path (no .py)
      interpreter: "venv/bin/python", // your venv's python
      interpreter_args: "-m", // makes it: python -m app.agent
    },
  ],
};
