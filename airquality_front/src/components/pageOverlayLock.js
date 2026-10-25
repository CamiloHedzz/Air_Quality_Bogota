const inertLocks = new WeakMap();
const bodies = new WeakMap();

// Menu-to-home navigation can briefly have both overlays mounted.
export function lockPageForOverlay(shell, overlay) {
  if (!shell) return () => {};
  const body = shell.ownerDocument.body;
  const targets = [...new Set([shell, ...body.querySelectorAll(':scope > [role="dialog"][aria-modal="true"]')])].filter(node => node !== overlay);
  const records = targets.map(node => {
    const record = inertLocks.get(node) || { count: 0, previous: node.inert };
    record.count += 1;
    inertLocks.set(node, record);
    node.inert = true;
    return { node, record };
  });
  const bodyLock = bodies.get(body) || { count: 0, previous: body.style.overflow };
  bodyLock.count += 1;
  bodies.set(body, bodyLock);
  body.style.overflow = "hidden";
  let released = false;
  return () => {
    if (released) return;
    released = true;
    records.forEach(({ node, record }) => {
      if (--record.count === 0) { node.inert = record.previous; inertLocks.delete(node); }
    });
    if (--bodyLock.count === 0) { body.style.overflow = bodyLock.previous; bodies.delete(body); }
  };
}
