cp .env.template .env
cp configs/config-infdb-import.yml.by configs/config-infdb-import.yml
bash infdb-start.sh -d

bash infdb-import.sh

uv run python3 tools/run_ags.py