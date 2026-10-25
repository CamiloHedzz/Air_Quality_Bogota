"""Presentation-only localization shared with the React site's message catalog."""
from functools import lru_cache
import json
from pathlib import Path
import re


CATALOG = Path(__file__).resolve().parents[1] / "airquality_front/src/i18n/messages.json"
DISPLAY_ATTRIBUTES = {"aria-label", "aria-description", "title", "placeholder", "alt", "label"}
WEEKDAYS = dict(zip(["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"],
                    ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]))


@lru_cache(maxsize=1)
def catalog():
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    messages = data["messages"]
    rules = []
    for rule in sorted(data["patterns"], key=lambda item: len(re.sub(r"\{\w+\}", "", item["source"])), reverse=True):
        names = []
        previous = 0
        parts = []
        for match in re.finditer(r"\{(\w+)\}", rule["source"]):
            parts.append(re.escape(rule["source"][previous:match.start()]))
            names.append(match.group(1))
            parts.append(r"(\d{4})" if match.group(1) == "year" else "(.+?)")
            previous = match.end()
        parts.append(re.escape(rule["source"][previous:]))
        rules.append((re.compile("^" + "".join(parts) + "$"), names, rule["target"]))
    fragments = sorted((source for source, target in messages.items() if source != target), key=len, reverse=True)
    expression = re.compile("|".join(r"(?<![\w])" + re.escape(source) + r"(?![\w])" for source in fragments))
    return messages, rules, expression


def translate(value, language="es", depth=0):
    if language != "en" or not isinstance(value, str) or not value.strip():
        return value
    leading, core, trailing = re.fullmatch(r"(\s*)([\s\S]*?)(\s*)", value).groups()
    source = re.sub(r"\s+", " ", core).strip()
    messages, rules, fragments = catalog()
    translated = messages.get(source)
    if translated is None:
        for expression, names, target in rules:
            match = expression.fullmatch(source)
            if match:
                values = dict(zip(names, match.groups()))
                for name, captured in values.items():
                    if name in {"n", "total", "days", "sources", "filled", "records"} and re.fullmatch(r"\d{1,3}(?:\.\d{3})+", captured):
                        values[name] = captured.replace(".", ",")
                translated = re.sub(r"\{(\w+)\}", lambda item: (translate(values[item[1]], language, depth + 1) if depth < 3 else values[item[1]]), target)
                break
    if translated is None:
        translated = fragments.sub(lambda match: messages[match[0]], source)
    translated = re.sub(r"\b(0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/(\d{4})\b", r"\3-\2-\1", translated)
    return leading + translated + trailing


def options(items, language):
    if isinstance(items, dict):
        return {key: translate(label, language) for key, label in items.items()}
    if not isinstance(items, list):
        return items
    result = []
    for item in items:
        if isinstance(item, str):
            result.append({"label": translate(item, language), "value": item})
        elif isinstance(item, dict):
            result.append({**item, "label": nodes(item.get("label", item.get("value")), language)})
        else:
            result.append(item)
    return result


def plot_text(value, language, field=None):
    """Walk only Plotly display metadata, never geometry or measurement arrays."""
    if isinstance(value, str):
        if field in {"tickformat", "hoverformat", "hovertemplate"} and language == "en":
            value = value.replace("%d/%m/%Y", "%Y-%m-%d").replace("%d/%m", "%b %d")
        return translate(value, language)
    if isinstance(value, list):
        return [plot_text(item, language, field) for item in value]
    if isinstance(value, dict):
        result = dict(value)
        for key, item in value.items():
            if key in {"text", "title", "name", "hovertemplate", "ticktext", "hovertext", "tickformat", "hoverformat", "annotations", "legend", "legendgrouptitle", "colorbar"} or re.fullmatch(r"[xy]axis\d*", key):
                result[key] = plot_text(item, language, key)
        return result
    return value


def figure(value, language):
    if not isinstance(value, dict):
        return value
    if "__dash_patch_update" in value:
        result = {**value, "operations": []}
        for operation in value.get("operations", []):
            translated = {**operation, "params": dict(operation.get("params", {}))}
            location = operation.get("location", [])
            if location and location[-1] in {"name", "title", "text", "hovertemplate", "annotations", "colorbar", "customdata"}:
                translated["params"]["value"] = plot_text(translated["params"].get("value"), language, location[-1])
            result["operations"].append(translated)
        return result
    result = {**value, "layout": plot_text(value.get("layout", {}), language), "data": []}
    for trace in value.get("data", []):
        translated = plot_text(trace, language)
        if "customdata" in trace:
            translated["customdata"] = plot_text(trace["customdata"], language, "customdata")
        # Strings on category axes are display labels; numeric values, locations,
        # station IDs, geometry, colors and source records are left untouched.
        for axis in ("x", "y"):
            values = trace.get(axis)
            if isinstance(values, list) and all(isinstance(item, str) for item in values):
                translated[axis] = [WEEKDAYS.get(item, translate(item, language)) if language == "en" else item for item in values]
        result["data"].append(translated)
    return result


def props(properties, language, component_type=None, namespace=None):
    result = dict(properties)
    for key, value in properties.items():
        if key == "children":
            result[key] = nodes(value, language)
        elif key in DISPLAY_ATTRIBUTES:
            result[key] = nodes(value, language)
        elif key == "options":
            result[key] = options(value, language)
        elif key == "figure":
            result[key] = figure(value, language)
    if namespace == "dash_core_components" and component_type == "Graph":
        result["config"] = {**properties.get("config", {}), "locale": language}
    if namespace == "dash_core_components" and component_type in {"Dropdown", "RadioItems", "Tabs"}:
        result.setdefault("persistence", "site-language-v1")
        result.setdefault("persistence_type", "session")
    if namespace == "dash_core_components" and component_type == "Store" and properties.get("id") == "selected-neighborhoods":
        result["storage_type"] = "session"
    return result


def nodes(value, language):
    if isinstance(value, str):
        return translate(value, language)
    if isinstance(value, list):
        return [nodes(item, language) for item in value]
    if isinstance(value, dict) and "namespace" in value and "props" in value:
        return {**value, "props": props(value["props"], language, value.get("type"), value["namespace"])}
    return value


def payload(value, language):
    if isinstance(value, dict) and isinstance(value.get("response"), dict):
        return {**value, "response": {key: props(item, language) for key, item in value["response"].items()}}
    return nodes(value, language)
