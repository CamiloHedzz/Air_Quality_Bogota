import catalog from "./messages.json";

const normalize = value => value.replace(/\s+/g, " ").trim();
const escape = value => value.replace(/[.*+?^\x24{}()|[\]\\]/g, "\\$&");
const messages = catalog.messages;
const fragments = Object.entries(messages).filter(([source, target]) => source !== target)
  .sort((a, b) => b[0].length - a[0].length);
const fragmentExpression = new RegExp(fragments.map(([text]) => "(?<![\\p{L}\\p{N}_])" + escape(text) + "(?![\\p{L}\\p{N}_])").join("|"), "gu");
const literalLength = rule => rule.source.replace(/\{\w+\}/g, "").length;
const patternRules = [...catalog.patterns].sort((a, b) => literalLength(b) - literalLength(a)).map(rule => {
  const names = [];
  let expression = "";
  let previous = 0;
  for (const match of rule.source.matchAll(/\{(\w+)\}/g)) {
    expression += escape(rule.source.slice(previous, match.index));
    names.push(match[1]);
    expression += match[1] === "year" ? "(\\d{4})" : "(.+?)";
    previous = match.index + match[0].length;
  }
  expression += escape(rule.source.slice(previous));
  return { ...rule, names, expression: new RegExp("^" + expression + "$") };
});

export function translate(value, language = "es", depth = 0) {
  if (typeof value !== "string" || language !== "en" || !value.trim()) return value;
  const whitespace = value.match(/^(\s*)([\s\S]*?)(\s*)$/);
  const source = normalize(whitespace[2]);
  let result = messages[source];
  if (result === undefined) {
    for (const rule of patternRules) {
      const match = source.match(rule.expression);
      if (!match) continue;
      const values = Object.fromEntries(rule.names.map((name, index) => {
        let captured = match[index + 1];
        if (["n", "total", "days", "sources", "filled", "records"].includes(name) && /^\d{1,3}(?:\.\d{3})+$/.test(captured)) captured = captured.replace(/\./g, ",");
        return [name, captured];
      }));
      result = rule.target.replace(/\{(\w+)\}/g, (_, name) => (depth < 3 ? translate(values[name], language, depth + 1) : values[name]));
      break;
    }
  }
  if (result === undefined) {
    // One pass prevents translated words from being translated a second time.
    result = source.replace(fragmentExpression, match => messages[match]);
  }
  result = result.replace(/\b(0[1-9]|[12]\d|3[01])\/(0[1-9]|1[0-2])\/(\d{4})\b/g, "$3-$2-$1");
  return whitespace[1] + result + whitespace[3];
}
