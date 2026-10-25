import "../assets/styles/bird_silhouettes.css";

// Eight reviewed, hand-drawn pigeon poses. The anatomy stays fixed between frames.
const bodyPath = "M28 39C37 34 48 34 59 37C63 38 67 36 69 32C71 27 75 26 79 28C82 29 83 31 82 33L88 35L81 36C78 39 75 38 73 40C68 47 62 50 52 50C44 50 38 48 33 46L14 50L10 49L11 46L8 44L11 41L10 39L12 36Z";
const poses = [
  {
    "back": "M54 38C55 25 57 18 59 10C62 19 63 27 65 36L63 40Z",
    "front": "M47 41C43 34 41 27 39 19L31 3Q33 2 36 7L42 15L39 6Q41 5 44 12L49 20L49 12Q51 13 54 23L55 28C60 32 63 36 63 40C58 44 52 45 47 41Z"
  },
  {
    "back": "M53 38C59 28 68 16 76 13L75 20L81 17L77 26L70 37L63 41Z",
    "front": "M47 41C40 35 35 26 29 21L18 11L25 13L21 8L30 12L28 7L38 16C45 19 54 28 63 38C61 44 53 45 47 41Z"
  },
  {
    "back": "M54 38C58 29 63 24 69 20L73 18L70 25L74 23L69 31L63 40Z",
    "front": "M46 40C35 39 26 35 17 32L4 29Q6 26 13 27L7 24L17 25L12 22L24 25C37 24 50 30 64 38C60 44 52 44 46 40Z"
  },
  {
    "back": "M54 37C63 38 69 42 74 47L77 52L70 50L72 55L63 50L57 43Z",
    "front": "M48 37C37 37 28 42 19 49L10 55L18 54L15 59L24 56L24 61L34 56C47 54 56 48 64 40C59 36 53 35 48 37Z"
  },
  {
    "back": "M54 37C60 41 63 46 65 52L66 60L61 56L60 60L56 52L53 44Z",
    "front": "M48 37C39 40 33 47 29 55L26 62L33 59L33 64L39 60L42 63L46 58C56 53 62 46 64 39C59 35 53 35 48 37Z"
  },
  {
    "back": "M55 38C61 41 65 47 66 53L64 58L58 49L54 43Z",
    "front": "M48 38C44 43 40 48 40 54L40 60L45 56L47 60L52 55C59 51 64 45 63 39C58 35 53 35 48 38Z"
  },
  {
    "back": "M54 38C59 32 64 29 70 29L74 33L67 38L61 41Z",
    "front": "M48 39C41 35 35 33 30 34L22 39L28 42L34 44C46 48 56 46 64 40L58 35Z"
  },
  {
    "back": "M54 38C55 29 60 19 65 14L67 11L68 20L66 31L64 40Z",
    "front": "M47 40C42 34 43 25 44 20L44 9L49 16L50 10L54 19L57 17L60 29L65 39C60 44 53 45 47 40Z"
  }
];

export function BirdSilhouette({ variant = 0 }) {
  const index = Math.abs(Math.trunc(Number(variant) || 0)) % 3;
  return <g className={`bird-silhouette bird-silhouette--${index}`} fill="currentColor" stroke="none">
    {poses.map((pose, frame) => <g key={frame} className={`bird-pose bird-pose--${frame}`}
      style={{ "--bird-pose-phase": frame / poses.length }}>
      <path d={pose.back} />
      <path d={bodyPath} />
      <path d={pose.front} />
    </g>)}
  </g>;
}

BirdSilhouette.propTypes = { variant: () => null };
