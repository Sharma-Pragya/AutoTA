// Utility functions

export function validateFormat(expr, format) {
  if (!expr || !expr.trim()) return { valid: false, message: "Answer is empty." };

  const t = expr.trim();

  if (format === "value") {
    return /^[01]$/.test(t)
      ? { valid: true, message: "Format OK." }
      : { valid: false, message: "Enter 0 or 1." };
  }

  if (format === "number") {
    return /^\d+$/.test(t)
      ? { valid: true, message: "Format OK." }
      : { valid: false, message: "Enter a whole number." };
  }

  // Boolean expression validation
  let depth = 0;
  for (const c of t) {
    if (c === "(") depth++;
    if (c === ")") depth--;
    if (depth < 0) return { valid: false, message: "Unmatched closing parenthesis." };
  }
  if (depth !== 0) return { valid: false, message: "Unmatched opening parenthesis." };

  if (!/^[A-Da-d01\s+*()'^~]+$/.test(t)) {
    const bad = t.match(/[^A-Da-d01\s+*()'^~]/);
    return { valid: false, message: `Invalid character: '${bad?.[0]}'.` };
  }

  if (!/[A-Da-d]/.test(t)) {
    return { valid: false, message: "Must contain at least one variable." };
  }

  if (/\+\+/.test(t)) return { valid: false, message: "Double OR operator." };
  if (/\+\s*$/.test(t)) return { valid: false, message: "Ends with +." };
  if (/^\s*\+/.test(t)) return { valid: false, message: "Starts with +." };

  return { valid: true, message: "Format OK — valid Boolean expression." };
}

export function buildMenuStructure(problems) {
  const groups = [];
  let cur = null;
  for (const p of problems) {
    if (!cur || p.parent_label !== cur.parent) {
      cur = { parent: p.parent_label, items: [] };
      groups.push(cur);
    }
    cur.items.push(p);
  }
  return groups;
}

export function getQuestionLabel(problem) {
  return problem.sub_label
    ? `Q${problem.parent_label}${problem.sub_label}`
    : `Q${problem.parent_label}`;
}
