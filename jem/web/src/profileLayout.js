// JEM — Balance profile widgets across the detail view's two columns.

function sectionWeight(section) {
  if (typeof section.weight === 'number') return section.weight;
  const len = (section.body || '').length;
  return 2 + Math.floor(len / 500);
}

/**
 * Assign profile sections to left/right columns by estimated height.
 * Preserves source order within each column.
 */
export function balanceProfileColumns(sections) {
  if (!sections.length) return { left: [], right: [] };

  const tagged = sections.map((section, order) => ({
    section,
    order,
    weight: sectionWeight(section),
  }));

  const sorted = [...tagged].sort((a, b) => b.weight - a.weight);

  const left = [];
  const right = [];
  let leftW = 0;
  let rightW = 0;

  for (const item of sorted) {
    if (leftW <= rightW) {
      left.push(item.section);
      leftW += item.weight;
    } else {
      right.push(item.section);
      rightW += item.weight;
    }
  }

  const byOrder = (a, b) => {
    const ai = sections.indexOf(a);
    const bi = sections.indexOf(b);
    return ai - bi;
  };
  left.sort(byOrder);
  right.sort(byOrder);
  return { left, right };
}
