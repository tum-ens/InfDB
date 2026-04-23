# Development Workflow

1. **Define tool name:**
    - Think of a tool name
    - Use kebab-case naming convention as for example "choose-a-name" 

2. **Create Dev Container:**
   ```bash
   # Replace choose-a-name
   bash tools/_infdb-template/create_new_tool.sh choose-a-name
   ```

5. **Add dependencies:**
    - Add needed package into **dependencies** in `tools/choose-a-name/pyproject.toml`.
    - Run `uv sync` in order to update virtual environment with new packages or (re-start) docker via `docker compose -f tools/choose-a-name/compose.yml up`

6. **Implement your code:**
    - **pypackage**: You can use the preinstalled infdb python package to interact with the InfDB database and services. See [API -> pyinfdb](../api/pyinfdb/index.md) for more information.
    - **Python:** Add your code to `src/`
    - **SQL:** Add your scripts to `sql/` - We recommend adding numbers according to the execution order (executed in alphabetical order)
    - **Execution:** Start your added python code btw. sql scripts in `main.py`. The sql files can be easily executed as shown in `src/demo.py`. This spllting ensures clarity and easy overview what is executed.

7. **Document your code:**
    - Add docstrings and comments to your code
    - Update Readme_template.md for user of your tool