"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { BACKEND_API } from "@/lib/socket";

const ADMIN_PASSWORD = "PST4AECHECAMR";
const SESSION_KEY = "admin_auth";

// ─── Types ───────────────────────────────────────────────────────────────────

interface PlayerInfo {
  sid: string;
  color: "white" | "black";
  connected: boolean;
  ready: boolean;
  wait_seconds: number;
  disconnect_seconds: number | null;
}

interface QueueEntry {
  sid: string;
  color: "white" | "black";
  position: number;
  wait_seconds: number;
}

interface AdminState {
  game_in_progress: boolean;
  white_player: PlayerInfo | null;
  black_player: PlayerInfo | null;
  queue: QueueEntry[];
  pve_count: number;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatTime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}m${s.toString().padStart(2, "0")}s`;
}

function shortSid(sid: string): string {
  return sid.length > 10 ? `${sid.slice(0, 8)}…` : sid;
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function ColorBadge({ color }: { color: "white" | "black" }) {
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold ${
        color === "white"
          ? "bg-gray-100 text-gray-900"
          : "bg-gray-800 text-gray-100 border border-gray-600"
      }`}
    >
      {color === "white" ? "♔" : "♚"} {color === "white" ? "Blanc" : "Noir"}
    </span>
  );
}

function StatusDot({ connected }: { connected: boolean }) {
  return (
    <span
      className={`inline-block w-2 h-2 rounded-full ${
        connected ? "bg-emerald-400" : "bg-red-400"
      }`}
    />
  );
}

function PlayerCard({
  label,
  player,
  onKick,
  kicking,
}: {
  label: string;
  player: PlayerInfo | null;
  onKick: (sid: string) => void;
  kicking: string | null;
}) {
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 flex flex-col gap-3">
      <div className="text-xs font-semibold uppercase tracking-widest text-gray-500">
        {label}
      </div>

      {player ? (
        <>
          <div className="flex items-center gap-2 flex-wrap">
            <StatusDot connected={player.connected} />
            <span className="font-mono text-sm text-gray-200 truncate max-w-[160px]">
              {shortSid(player.sid)}
            </span>
            <ColorBadge color={player.color} />
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs text-gray-400">
            <div>
              <span className="text-gray-600">Durée&nbsp;</span>
              <span className="text-amber-400 font-mono">
                {formatTime(player.wait_seconds)}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Prêt&nbsp;</span>
              <span className={player.ready ? "text-emerald-400" : "text-gray-500"}>
                {player.ready ? "Oui" : "Non"}
              </span>
            </div>
            {player.disconnect_seconds !== null && (
              <div className="col-span-2">
                <span className="text-gray-600">Déconnecté depuis&nbsp;</span>
                <span className="text-red-400 font-mono">
                  {formatTime(player.disconnect_seconds)}
                </span>
              </div>
            )}
          </div>

          <button
            onClick={() => onKick(player.sid)}
            disabled={kicking === player.sid}
            className="mt-auto w-full py-1.5 rounded-lg bg-red-900/40 hover:bg-red-800/60 border border-red-700/50 text-red-300 text-xs font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {kicking === player.sid ? "Déconnexion…" : "Déconnecter"}
          </button>
        </>
      ) : (
        <div className="flex-1 flex items-center justify-center text-gray-600 text-sm py-4">
          — Vide —
        </div>
      )}
    </div>
  );
}

// ─── Auth Gate ────────────────────────────────────────────────────────────────

function LoginScreen({ onSuccess }: { onSuccess: () => void }) {
  const [pwInput, setPwInput] = useState("");
  const [pwError, setPwError] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setTimeout(() => inputRef.current?.focus(), 50);
  }, []);

  const submit = () => {
    if (pwInput === ADMIN_PASSWORD) {
      safeSession("set", "1");
      onSuccess();
    } else {
      setPwError(true);
      setPwInput("");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-animate flex items-center justify-center p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl p-8 w-full max-w-sm space-y-5">
        <div className="text-center">
          <div className="text-3xl mb-2">🔒</div>
          <h1 className="text-lg font-bold text-amber-400">Admin — Accès restreint</h1>
          <p className="text-xs text-gray-500 mt-1">Entrez le mot de passe administrateur</p>
        </div>
        <input
          ref={inputRef}
          type="password"
          value={pwInput}
          onChange={(e) => { setPwInput(e.target.value); setPwError(false); }}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          placeholder="Mot de passe"
          className={`w-full bg-gray-800 border rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-600 outline-none focus:border-amber-500/60 transition-colors ${pwError ? "border-red-500/60" : "border-gray-700"}`}
        />
        {pwError && <p className="text-xs text-red-400 text-center -mt-2">Mot de passe incorrect</p>}
        <button
          onClick={submit}
          className="w-full py-2.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-300 text-sm font-semibold transition-colors"
        >
          Connexion
        </button>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

function safeSession(action: "get" | "set", value?: string): string | null {
  try {
    if (action === "get") return sessionStorage.getItem(SESSION_KEY);
    if (value !== undefined) sessionStorage.setItem(SESSION_KEY, value);
  } catch { /* blocked (iframe, privacy mode) */ }
  return null;
}

export default function AdminPage() {
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    if (safeSession("get") === "1") setAuthed(true);
  }, []);

  if (!authed) return <LoginScreen onSuccess={() => setAuthed(true)} />;

  return <AdminDashboard />;
}

function AdminDashboard() {
  const [state, setState] = useState<AdminState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [kicking, setKicking] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const fetchState = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND_API}/api/admin/state`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: AdminState = await res.json();
      setState(data);
      setLastRefresh(new Date());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur réseau");
    }
  }, []);

  // Auto-refresh every 2 seconds
  useEffect(() => {
    fetchState();
    const interval = setInterval(fetchState, 2000);
    return () => clearInterval(interval);
  }, [fetchState]);

  const kick = useCallback(
    async (sid: string) => {
      setKicking(sid);
      try {
        await fetch(`${BACKEND_API}/api/admin/kick`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sid }),
        });
        await fetchState();
      } finally {
        setKicking(null);
      }
    },
    [fetchState]
  );

  const reorder = useCallback(
    async (sid: string, direction: "up" | "down") => {
      await fetch(`${BACKEND_API}/api/admin/reorder`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sid, direction }),
      });
      await fetchState();
    },
    [fetchState]
  );

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-gradient-animate text-gray-100 p-4 md:p-8">
      {/* Header */}
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-amber-400 tracking-tight">
              ♟ Admin — File d&apos;attente
            </h1>
            <p className="text-xs text-gray-500 mt-1">
              {lastRefresh
                ? `Mis à jour à ${lastRefresh.toLocaleTimeString()}`
                : "Connexion…"}
            </p>
          </div>
          <button
            onClick={fetchState}
            className="px-3 py-1.5 rounded-lg border border-gray-700 hover:border-amber-500/50 text-xs text-gray-400 hover:text-amber-400 transition-colors"
          >
            ↻ Actualiser
          </button>
        </div>

        {error && (
          <div className="mb-6 p-3 rounded-lg bg-red-900/30 border border-red-700/50 text-red-300 text-sm">
            Erreur de connexion : {error}
          </div>
        )}

        {state && (
          <>
            {/* ── Stats bar ── */}
            <div className="grid grid-cols-3 gap-3 mb-8">
              <StatCard
                label="En jeu"
                value={state.game_in_progress ? "Oui" : "Non"}
                accent={state.game_in_progress ? "amber" : "gray"}
              />
              <StatCard
                label="En attente"
                value={String(state.queue.length)}
                accent={state.queue.length > 0 ? "violet" : "gray"}
              />
              <StatCard
                label="PvE actifs"
                value={String(state.pve_count)}
                accent="gray"
              />
            </div>

            {/* ── Current game slots ── */}
            <section className="mb-8">
              <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-3">
                Partie en cours
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <PlayerCard
                  label="Joueur Blanc"
                  player={state.white_player}
                  onKick={kick}
                  kicking={kicking}
                />
                <PlayerCard
                  label="Joueur Noir"
                  player={state.black_player}
                  onKick={kick}
                  kicking={kicking}
                />
              </div>
            </section>

            {/* ── Queue ── */}
            <section>
              <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-3">
                File d&apos;attente ({state.queue.length})
              </h2>

              {state.queue.length === 0 ? (
                <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center text-gray-600 text-sm">
                  File d&apos;attente vide
                </div>
              ) : (
                <div className="flex flex-col gap-2">
                  {state.queue.map((entry, idx) => (
                    <QueueRow
                      key={entry.sid}
                      entry={entry}
                      isFirst={idx === 0}
                      isLast={idx === state.queue.length - 1}
                      onKick={kick}
                      onReorder={reorder}
                      kicking={kicking}
                    />
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </div>
  );
}

// ─── Queue Row ────────────────────────────────────────────────────────────────

function QueueRow({
  entry,
  isFirst,
  isLast,
  onKick,
  onReorder,
  kicking,
}: {
  entry: QueueEntry;
  isFirst: boolean;
  isLast: boolean;
  onKick: (sid: string) => void;
  onReorder: (sid: string, direction: "up" | "down") => void;
  kicking: string | null;
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 hover:border-gray-700 rounded-xl px-4 py-3 flex items-center gap-4 transition-colors">
      {/* Position */}
      <div className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center text-sm font-bold text-amber-400 shrink-0">
        {entry.position}
      </div>

      {/* SID + color */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-mono text-sm text-gray-200 truncate max-w-[140px]">
            {shortSid(entry.sid)}
          </span>
          <ColorBadge color={entry.color} />
        </div>
        <div className="text-xs text-gray-500 mt-0.5">
          Attente :{" "}
          <span className="text-violet-400 font-mono">
            {formatTime(entry.wait_seconds)}
          </span>
        </div>
      </div>

      {/* Reorder arrows */}
      <div className="flex flex-col gap-0.5 shrink-0">
        <button
          onClick={() => onReorder(entry.sid, "up")}
          disabled={isFirst}
          title="Monter"
          className="w-6 h-6 flex items-center justify-center rounded hover:bg-gray-700 text-gray-400 hover:text-white disabled:opacity-20 disabled:cursor-not-allowed transition-colors text-xs"
        >
          ▲
        </button>
        <button
          onClick={() => onReorder(entry.sid, "down")}
          disabled={isLast}
          title="Descendre"
          className="w-6 h-6 flex items-center justify-center rounded hover:bg-gray-700 text-gray-400 hover:text-white disabled:opacity-20 disabled:cursor-not-allowed transition-colors text-xs"
        >
          ▼
        </button>
      </div>

      {/* Kick */}
      <button
        onClick={() => onKick(entry.sid)}
        disabled={kicking === entry.sid}
        className="shrink-0 px-3 py-1.5 rounded-lg bg-red-900/40 hover:bg-red-800/60 border border-red-700/50 text-red-300 text-xs font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {kicking === entry.sid ? "…" : "Kick"}
      </button>
    </div>
  );
}

// ─── Stat Card ────────────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent: "amber" | "violet" | "gray";
}) {
  const colors = {
    amber: "text-amber-400",
    violet: "text-violet-400",
    gray: "text-gray-400",
  };
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
      <div className={`text-2xl font-bold ${colors[accent]}`}>{value}</div>
      <div className="text-xs text-gray-500 mt-1">{label}</div>
    </div>
  );
}
