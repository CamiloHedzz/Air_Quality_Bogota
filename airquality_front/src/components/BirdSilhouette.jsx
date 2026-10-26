import "../assets/styles/bird_silhouettes.css";

// Fixed anatomy with separate wings: an open power stroke and a folded recovery.
// The matching path topology lets supporting browsers interpolate every contour.
const bodyPath = "M27 36C36 31 47 31 56 34C61 36 65 35 68 30C70 26 74 25 78 27C81 28 82 31 81 33L86 34L80 36C77 38 74 37 72 40C67 46 59 48 49 46C40 45 34 42 28 42L16 46L10 44L14 41L10 38L13 34L21 35Z";
const poses = [
  {
    "back": "M52 35C56 28 60 21 64 16C66 12 69 7 72 5L73 10L72 17L75 12L75 21L76 18L72 29C68 35 61 38 56 39Q52 39 52 35Z",
    "front": "M58 35C55 29 49 26 46 20C43 14 38 7 32 3L32 9L35 16L32 12L35 21L32 18L36 28C40 35 45 39 49 41Q54 42 58 35Z"
  },
  {
    "back": "M52 35C58 28 64 23 68 19C72 15 76 13 80 12L79 18L75 24L80 20L77 29L80 26L72 34C66 38 61 40 56 39Q52 38 52 35Z",
    "front": "M58 35C53 29 47 25 43 20C39 15 34 11 27 9L29 15L34 21L30 18L35 26L32 23L39 32C43 37 46 40 50 41Q55 41 58 35Z"
  },
  {
    "back": "M52 35C59 31 65 28 71 27C77 25 82 25 86 26L83 30L78 33L83 32L77 37L81 36L71 40C64 42 60 40 56 39Q52 38 52 35Z",
    "front": "M58 35C52 31 45 29 40 27C34 24 27 22 20 22L23 27L29 31L24 30L31 35L27 34L36 39C42 42 46 42 50 41Q55 40 58 35Z"
  },
  {
    "back": "M52 35C59 34 65 34 71 35C77 36 82 38 86 40L81 42L76 41L81 44L74 44L78 46L68 44C62 43 59 40 56 39Q52 38 52 35Z",
    "front": "M58 35C52 33 45 32 40 32C33 31 26 31 18 32L22 36L28 38L24 38L31 42L27 42L37 44C43 45 46 43 50 41Q55 39 58 35Z"
  },
  {
    "back": "M52 35C58 37 64 41 68 45C72 49 75 52 77 56L72 54L68 50L71 55L65 51L67 56L61 49C57 45 55 41 54 38Q52 36 52 35Z",
    "front": "M58 35C53 37 48 40 44 43C39 46 34 50 29 55L35 54L41 51L37 55L44 52L41 56L49 50C53 47 56 43 58 39Q60 36 58 35Z"
  },
  {
    "back": "M52 35C57 39 61 43 64 47C67 51 69 56 71 60L66 58L63 53L65 59L59 53L60 58L55 49C53 44 52 40 52 37Q51 35 52 35Z",
    "front": "M58 35C54 40 50 45 47 49C43 54 39 59 34 63L40 62L45 58L42 62L48 58L46 62L52 55C56 49 58 44 59 39Q60 36 58 35Z"
  },
  {
    "back": "M52 35C56 37 59 40 61 43C63 46 64 49 64 52L60 50L58 46L58 51L54 46L54 50L51 43C50 40 50 37 51 35Q52 34 52 35Z",
    "front": "M58 35C55 39 53 43 51 47C49 51 46 54 43 56L48 55L52 51L49 55L55 51L53 54L57 47C59 43 60 39 59 36Q59 34 58 35Z"
  },
  {
    "back": "M52 35C56 33 60 33 63 34C66 35 68 36 70 38L65 39L61 37L64 40L58 39L61 42L54 40C51 39 50 37 51 35Q52 34 52 35Z",
    "front": "M58 35C54 36 50 37 47 39C43 41 40 42 37 43L42 44L47 43L43 45L49 44L46 46L53 42C57 40 59 37 59 35Q59 34 58 35Z"
  },
  {
    "back": "M52 35C55 30 59 27 62 25C65 23 68 21 71 20L70 25L67 29L71 27L68 33L71 31L64 37C60 39 56 39 53 38Q51 37 52 35Z",
    "front": "M58 35C54 31 50 28 47 25C44 22 42 20 39 18L40 24L44 29L41 27L45 33L42 30L48 37C52 40 55 39 58 37Q59 36 58 35Z"
  },
  {
    "back": "M52 35C55 28 58 23 61 19C64 15 67 11 70 9L70 15L68 21L72 17L71 26L73 23L67 33C62 37 57 39 53 38Q51 37 52 35Z",
    "front": "M58 35C55 29 51 25 48 20C45 15 42 10 38 7L38 13L41 20L38 16L42 25L39 22L45 33C49 38 53 40 57 38Q59 36 58 35Z"
  }
];

export function BirdSilhouette({ variant = 0 }) {
  const index = Math.abs(Math.trunc(Number(variant) || 0)) % 3;
  const fallbackWing = side => poses.map((pose, frame) => <path key={frame}
    className={`bird-pose bird-pose--${frame}`} d={pose[side]}
    style={{ "--bird-pose-phase": frame / poses.length }} />);

  return <g className={`bird-silhouette bird-silhouette--${index}`} fill="currentColor" stroke="none">
    <g className="bird-wing-frames">{fallbackWing("back")}</g>
    <path className="bird-wing-smooth bird-wing-far" d={poses[3].back} />
    <path className="bird-body" d={bodyPath} />
    <g className="bird-wing-frames">{fallbackWing("front")}</g>
    <path className="bird-wing-smooth bird-wing-near" d={poses[3].front} />
  </g>;
}

BirdSilhouette.propTypes = { variant: () => null };
