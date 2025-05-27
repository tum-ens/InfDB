import os
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


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
config_path = os.path.join(BASE_DIR, "configs", "config.yaml")
config = load_config_with_recursive_context(config_path)
