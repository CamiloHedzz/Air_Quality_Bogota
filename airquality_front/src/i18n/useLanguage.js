import { Children, cloneElement, isValidElement, useCallback, useContext } from "react";
import { LanguageContext } from "./LanguageContext";
import { translate } from "./translate";

const textAttributes = ["aria-label", "aria-description", "title", "placeholder", "alt"];

// Translate before reconciliation. Values, handlers, refs, keys, URLs and dataset
// identifiers remain exactly as the component created them.
export function localizeTree(node, language) {
  if (typeof node === "string") return translate(node, language);
  if (Array.isArray(node)) return Children.map(node, child => localizeTree(child, language));
  if (!isValidElement(node)) return node;
  const props = {};
  for (const name of textAttributes) {
    if (typeof node.props[name] === "string") props[name] = translate(node.props[name], language);
  }
  if (node.props.children !== undefined) props.children = localizeTree(node.props.children, language);
  return cloneElement(node, props);
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  const localize = useCallback(node => localizeTree(node, context.language), [context.language]);
  const t = useCallback(value => translate(value, context.language), [context.language]);
  return { ...context, localize, t };
}
