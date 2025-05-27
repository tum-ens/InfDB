import yaml
from jinja2 import Environment, StrictUndefined


def render_template(template_str, context):
    env = Environment(undefined=StrictUndefined)
    template = env.from_string(template_str)
    return template.render(**context)


def recursive_resolve(config_dict):
    def _resolve(value, context):
        if isinstance(value, str):
            try:
                return render_template(value, context)
            except Exception:
                return value
        elif isinstance(value, dict):
            return {k: _resolve(v, context) for k, v in value.items()}
        elif isinstance(value, list):
            return [_resolve(v, context) for v in value]
        else:
            return value

    prev = None
    while prev != config_dict:
        prev = yaml.safe_load(yaml.dump(config_dict))
        config_dict = _resolve(config_dict, config_dict)
    return config_dict


def load_config_with_recursive_context(filename):
    with open(filename, 'r') as f:
        raw = f.read()

    initial = yaml.safe_load(raw)
    return recursive_resolve(initial)


def write_env_file(config, file_path=".env"):
    def flatten(d, parent_key=""):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}_{k}".upper() if parent_key else k.upper()
            if isinstance(v, dict):
                items.extend(flatten(v, new_key))
            else:
                items.append((new_key, v))
        return items

    flat_config = flatten(config)

    with open(file_path, "w") as f:
        for key, value in flat_config:
            f.write(f"{key}={value}\n")


config = load_config_with_recursive_context("CONFIG.yaml")

