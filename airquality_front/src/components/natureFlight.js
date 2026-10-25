const entries = ["west", "east", "north-west", "north-east", "south-west", "south-east"];
const formations = [[0, 0], [-58, -27], [-66, 33], [-116, -54], [-132, 65]];

export function createNatureFlight(width, height, previousEntry, random = Math.random) {
  const pick = list => list[Math.floor(random() * list.length)];
  const between = (min, max) => min + random() * (max - min);
  const entry = pick(entries.filter(value => value !== previousEntry));
  const direction = entry.endsWith("east") || entry === "east" ? -1 : 1;
  const margin = 230;
  const exitX = direction === 1 ? width + margin : -margin;
  const exitY = between(height * .12, height * .82);
  let startX = direction === 1 ? -margin : width + margin;
  let startY = between(height * .18, height * .76);
  let controlY = between(height * .1, height * .8);
  if (entry.startsWith("north")) {
    startX = between(width * .15, width * .85);
    startY = -margin;
    controlY = height * .22;
  } else if (entry.startsWith("south")) {
    startX = between(width * .15, width * .85);
    startY = height + margin;
    controlY = height * .6;
  }
  const point = (x, y) => `${Math.round(x)} ${Math.round(y)}`;
  const path = `M${point(startX, startY)} C${point(startX + (exitX - startX) * .32, controlY)} ${point(startX + (exitX - startX) * .72, exitY - height * .15)} ${point(exitX, exitY)}`;
  const count = pick([1, 3, 3, 5]);
  const scale = width < 600 ? .67 : between(.8, 1.08);
  return {
    entry, direction, path, count,
    duration: between(9000, 13500),
    opacity: between(.55, .76),
    birds: formations.slice(0, count).map(([x, y]) => ({
      x: x * scale * direction, y: y * scale, size: between(34, 52) * scale,
      flap: between(340, 430), delay: between(-1000, 0), tilt: between(-10, 10),
    })),
  };
}
