// Public display labels for trade partners. Data keys keep the real names;
// this maps a name to its label where the UI renders it beside a dollar
// figure. Source: reference/retailer_display_labels.json, vendored from
// cinderhaven-data-platform by scripts/refresh_canonical.py.
import labels from '../../../reference/retailer_display_labels.json'

const ENTRIES = [
  ...Object.values(labels.retailers),
  ...Object.values(labels.distributors),
]

const LABEL_BY_NAME = Object.fromEntries(ENTRIES.map((e) => [e.name, e.label]))

/** Label for a partner name, mid-sentence form. Unknown names pass through. */
export function partnerLabel(name) {
  return LABEL_BY_NAME[name] ?? name
}

/** Label with its first letter capitalized, for sentence starts and chart entries. */
export function partnerLabelCap(name) {
  const l = partnerLabel(name)
  return l.charAt(0).toUpperCase() + l.slice(1)
}

/** Labels of the retailers and distributors that are relabeled, in map order. */
export const RETAILER_LABELS = Object.values(labels.retailers)
  .filter((e) => e.label !== e.name)
  .map((e) => e.label)
export const DISTRIBUTOR_LABELS = Object.values(labels.distributors).map((e) => e.label)
