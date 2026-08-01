import type { CSSProperties } from "react";
import type { Status } from "../lib/api";
import "./roombie.css";

export type RoombieMood = "idle" | "happy" | "cleaning" | "charging" | "error" | "thinking";

/** Shared status -> mood mapping, so every Roombie on the page (header, Command
 * Center, anywhere else) agrees on what the robot's current state "looks like." */
export function statusMood(status: Status | null): RoombieMood {
  if (!status) return "thinking";
  if (status.error_code) return "error";
  if (status.phase === "run") return "cleaning";
  if (status.phase === "charge") return status.battery_pct === 100 ? "happy" : "charging";
  return "idle";
}

interface RoombieProps {
  mood: RoombieMood;
  size?: number;
  className?: string;
}

const MOOD_COLOR: Record<RoombieMood, string> = {
  idle: "var(--text-secondary)",
  happy: "var(--teal)",
  cleaning: "var(--cyan)",
  charging: "var(--amber)",
  error: "var(--red)",
  thinking: "var(--indigo)",
};

const MOOD_ANIMATION: Record<RoombieMood, string> = {
  idle: "roombie-bob",
  happy: "roombie-bob",
  cleaning: "roombie-bob-active",
  charging: "roombie-breathe",
  error: "roombie-shake",
  thinking: "roombie-bob",
};

/** Roombie: the dashboard's mascot. A single SVG whose face/rim color/animation
 * change with `mood`, driven by real robot state wherever it's used — not just
 * decoration. Reused at hero size (Command Center) and icon size (header,
 * inline reactions) so the character reads as one consistent identity. */
export default function Roombie({ mood, size = 96, className }: RoombieProps) {
  const color = MOOD_COLOR[mood];
  const animation = MOOD_ANIMATION[mood];

  return (
    <svg
      viewBox="0 0 100 100"
      width={size}
      height={size}
      className={`roombie ${animation}${className ? ` ${className}` : ""}`}
      style={{ "--roombie-color": color } as CSSProperties}
      role="img"
      aria-label={`Roombie, ${mood}`}
    >
      <defs>
        <radialGradient id="roombie-body" cx="40%" cy="35%" r="75%">
          <stop offset="0%" stopColor="#1b2334" />
          <stop offset="100%" stopColor="#0a0e17" />
        </radialGradient>
        <linearGradient id="roombie-rim" x1="10" y1="6" x2="90" y2="94" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#2dd4ee" />
          <stop offset="55%" stopColor="#7c8cf8" />
          <stop offset="100%" stopColor="#b083f7" />
        </linearGradient>
      </defs>

      {/* antenna */}
      <g className="roombie-antenna">
        <line x1="50" y1="14" x2="50" y2="4" stroke="url(#roombie-rim)" strokeWidth="2" strokeLinecap="round" />
        <circle cx="50" cy="4" r="3" fill="url(#roombie-rim)" />
      </g>

      {/* body */}
      <circle cx="50" cy="54" r="42" fill="url(#roombie-body)" />
      <circle cx="50" cy="54" r="42" fill="none" stroke={color} strokeWidth="2.5" className="roombie-rim-glow" />
      <circle cx="50" cy="54" r="42" fill="none" stroke="url(#roombie-rim)" strokeWidth="1" opacity="0.5" />

      {/* bottom bumper hint */}
      <path d="M22 78 A30 30 0 0 0 78 78" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="2" />

      {/* face plate */}
      <ellipse cx="50" cy="50" rx="27" ry="20" fill="#050914" stroke="rgba(255,255,255,0.06)" />

      {/* face */}
      <g stroke={color} fill={color}>
        {mood === "idle" && (
          <>
            <rect x="33" y="45" width="10" height="5" rx="2.5" stroke="none" />
            <rect x="57" y="45" width="10" height="5" rx="2.5" stroke="none" />
            <path d="M41 61 Q50 64 59 61" fill="none" strokeWidth="2.5" strokeLinecap="round" />
          </>
        )}

        {mood === "happy" && (
          <>
            <path d="M32 49 Q37.5 41 43 49" fill="none" strokeWidth="2.8" strokeLinecap="round" />
            <path d="M57 49 Q62.5 41 68 49" fill="none" strokeWidth="2.8" strokeLinecap="round" />
            <path d="M38 58 Q50 70 62 58" fill="none" strokeWidth="3" strokeLinecap="round" />
            <circle cx="30" cy="56" r="3" opacity="0.35" stroke="none" />
            <circle cx="70" cy="56" r="3" opacity="0.35" stroke="none" />
          </>
        )}

        {mood === "cleaning" && (
          <>
            <circle cx="38" cy="48" r="5" stroke="none" />
            <circle cx="62" cy="48" r="5" stroke="none" />
            <circle cx="39.5" cy="46.5" r="1.4" fill="#050914" stroke="none" />
            <circle cx="63.5" cy="46.5" r="1.4" fill="#050914" stroke="none" />
            <ellipse cx="50" cy="62" rx="6" ry="5" fill="#050914" strokeWidth="2.5" />
            <g className="roombie-sparkle">
              <path d="M18 30 l1.6 4 4 1.6 -4 1.6 -1.6 4 -1.6 -4 -4 -1.6 4 -1.6Z" stroke="none" opacity="0.8" />
            </g>
            <g className="roombie-sparkle roombie-sparkle-b">
              <path d="M84 40 l1.2 3 3 1.2 -3 1.2 -1.2 3 -1.2 -3 -3 -1.2 3 -1.2Z" stroke="none" opacity="0.7" />
            </g>
          </>
        )}

        {mood === "charging" && (
          <>
            <path d="M32 47 Q37.5 51 43 47" fill="none" strokeWidth="2.8" strokeLinecap="round" />
            <path d="M57 47 Q62.5 51 68 47" fill="none" strokeWidth="2.8" strokeLinecap="round" />
            <path d="M44 61 Q50 63 56 61" fill="none" strokeWidth="2.5" strokeLinecap="round" />
            <g className="roombie-zzz" fontFamily="var(--font-display)" stroke="none">
              <text x="66" y="30" fontSize="9" fontWeight="700">
                z
              </text>
              <text x="72" y="22" fontSize="6.5" fontWeight="700" opacity="0.75">
                z
              </text>
            </g>
          </>
        )}

        {mood === "error" && (
          <>
            <path d="M31 42 L43 46" fill="none" strokeWidth="2.4" strokeLinecap="round" />
            <path d="M69 42 L57 46" fill="none" strokeWidth="2.4" strokeLinecap="round" />
            <circle cx="38" cy="50" r="3.6" stroke="none" />
            <circle cx="62" cy="50" r="3.6" stroke="none" />
            <path d="M40 65 Q50 57 60 65" fill="none" strokeWidth="3" strokeLinecap="round" />
          </>
        )}

        {mood === "thinking" && (
          <>
            <rect x="33" y="45" width="10" height="5" rx="2.5" stroke="none" />
            <rect x="57" y="45" width="10" height="5" rx="2.5" stroke="none" />
            <g className="roombie-dots" stroke="none">
              <circle cx="43" cy="62" r="2.4" />
              <circle cx="50" cy="62" r="2.4" />
              <circle cx="57" cy="62" r="2.4" />
            </g>
          </>
        )}
      </g>
    </svg>
  );
}
