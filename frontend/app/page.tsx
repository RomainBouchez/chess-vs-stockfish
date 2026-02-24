"use client";

import { useEffect, useState, useCallback } from "react";
import dynamic from "next/dynamic";
const Chessboard = dynamic(() => import("react-chessboard").then((mod) => mod.Chessboard), {
    ssr: false
});
import { Chess } from "chess.js";
import { socket, BACKEND_API } from "@/lib/socket";
import GameControls from "@/components/GameControls";
import SettingsModal from "@/components/SettingsModal";
import { Trophy, Users, Shield, Swords, Crown, Lightbulb, RefreshCw, Settings, Bot } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Card } from "@/components/ui";
import RobotDebugPanel from "@/components/RobotDebugPanel"; // DEBUG - remove after testing


interface GameState {
    fen: string;
    turn: string;
    is_check: boolean;
    is_checkmate: boolean;
    is_game_over: boolean;
    winner: string | null;
    white_captured: string[];
    black_captured: string[];
}

// Piece symbols mapping
const pieceSymbols: Record<string, string> = {
    'p': '♟', 'P': '♙',
    'n': '♞', 'N': '♘',
    'b': '♝', 'B': '♗',
    'r': '♜', 'R': '♖',
    'q': '♛', 'Q': '♕',
    'k': '♚', 'K': '♔'
};

export default function Home() {
    const [game, setGame] = useState(new Chess());
    const [fen, setFen] = useState("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
    const [robotConnected, setRobotConnected] = useState(false);
    const [capturedWhite, setCapturedWhite] = useState<string[]>([]);
    const [capturedBlack, setCapturedBlack] = useState<string[]>([]);
    const [gameStatus, setGameStatus] = useState<string>("Ready");
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);

    useEffect(() => {
        function onGameState(state: GameState) {
            console.log("Received state:", state);
            setFen(state.fen);
            const newGame = new Chess(state.fen);
            setGame(newGame);
            setCapturedWhite(state.white_captured);
            setCapturedBlack(state.black_captured);

            if (state.is_checkmate) setGameStatus(`Checkmate! ${state.winner} wins`);
            else if (state.is_game_over) setGameStatus("Game Over");
            else if (state.is_check) setGameStatus("Check!");
            else setGameStatus(`${state.turn === 'white' ? "White" : "Black"}'s Turn`);
        }

        socket.on("game_state", onGameState);
        socket.on("connect", () => {
            console.log("Socket connected");
            socket.emit("join_pve", {});
        });

        // If already connected, emit join_pve immediately
        if (socket.connected) {
            socket.emit("join_pve", {});
        }

        return () => {
            socket.off("game_state", onGameState);
            socket.off("connect");
        };
    }, []);

    const onDrop = useCallback(({ sourceSquare, targetSquare }: { piece: unknown, sourceSquare: string, targetSquare: string | null }) => {
        if (!targetSquare) return false;
        try {
            const move = game.move({
                from: sourceSquare,
                to: targetSquare,
                promotion: "q",
            });

            if (move === null) return false;

            const uci = move.from + move.to + (move.promotion ? move.promotion : "");
            socket.emit("make_move", { uci });
            return true;

        } catch {
            return false;
        }
    }, [game]);

    const handleReset = async () => {
        try {
            await fetch(`${BACKEND_API}/api/game/reset`, { method: "POST" });
        } catch (e) {
            console.error("Failed to reset", e);
        }
    };

    // Status badge styling
    const getStatusStyle = () => {
        if (gameStatus.includes("Checkmate")) {
            return "bg-gradient-to-r from-amber-500/20 to-yellow-500/20 border-amber-500/30 text-amber-200 glow-amber-soft";
        }
        if (gameStatus.includes("Check")) {
            return "bg-gradient-to-r from-red-500/20 to-rose-500/20 border-red-500/30 text-red-200 glow-red animate-pulse";
        }
        return "bg-white/5 border-white/10 text-gray-300";
    };

    const getStatusIcon = () => {
        if (gameStatus.includes("Checkmate")) return <Crown className="w-4 h-4" />;
        if (gameStatus.includes("Check")) return <Shield className="w-4 h-4" />;
        return <Swords className="w-4 h-4 opacity-50" />;
    };

    return (
        <main className="h-dvh bg-gradient-animate flex flex-col font-sans select-none overflow-hidden text-white relative
                         p-2 lg:p-8 lg:items-center lg:gap-8 lg:h-auto lg:min-h-screen lg:overflow-auto">

            {/* Decorative Elements */}
            <div className="fixed inset-0 pointer-events-none overflow-hidden">
                <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl" />
                <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-amber-500/5 rounded-full blur-3xl" />
            </div>

            {/* Header - Compact on mobile, full on desktop */}
            <motion.header
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="flex-none w-full max-w-6xl flex flex-row justify-between items-center z-20 py-1 lg:py-0 lg:gap-4"
            >
                {/* Logo */}
                <div className="flex items-center gap-2 lg:gap-4">
                    <motion.div
                        whileHover={{ rotate: [0, -10, 10, 0] }}
                        transition={{ duration: 0.5 }}
                        className="w-8 h-8 lg:w-12 lg:h-12 rounded-xl lg:rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shadow-lg shadow-amber-500/30"
                    >
                        <Trophy className="text-white w-4 h-4 lg:w-6 lg:h-6" />
                    </motion.div>
                    <div>
                        <h1 className="text-lg lg:text-2xl font-black tracking-tight">
                            CHESS <span className="text-gradient-amber">PRO</span>
                        </h1>
                        <p className="text-[8px] lg:text-[10px] text-gray-500 uppercase tracking-[0.2em] font-medium hidden sm:block">
                            Stockfish 16 • Robot Integration
                        </p>
                    </div>
                </div>

                {/* Status Badge */}
                <motion.div
                    key={gameStatus}
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className={`
                        status-badge
                        px-3 py-1.5 lg:px-5 lg:py-2.5 rounded-full
                        text-xs lg:text-sm font-bold
                        border backdrop-blur-md
                        shadow-lg
                        flex items-center gap-1.5 lg:gap-2.5
                        ${getStatusStyle()}
                    `}
                >
                    {getStatusIcon()}
                    {gameStatus}
                </motion.div>
            </motion.header>

            {/* Mobile Toolbar - Visible only on mobile */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.3 }}
                className="flex-none flex lg:hidden items-center justify-center z-20 w-full"
                style={{ gap: "1.5rem", paddingBottom: "0.5rem", paddingTop: "0.25rem" }}
            >
                <button
                    onClick={handleReset}
                    className="mobile-toolbar-btn"
                    title="New Game"
                >
                    <RefreshCw className="w-5 h-5" />
                    <span className="text-[10px] font-medium">New</span>
                </button>

                <button
                    onClick={() => setIsSettingsOpen(true)}
                    className="mobile-toolbar-btn"
                    title="Engine Settings"
                >
                    <Settings className="w-5 h-5" />
                    <span className="text-[10px] font-medium">Settings</span>
                </button>

                <button
                    onClick={async () => {
                        try {
                            const endpoint = robotConnected
                                ? `${BACKEND_API}/api/robot/disconnect`
                                : `${BACKEND_API}/api/robot/connect`;
                            const res = await fetch(endpoint, { method: "POST" });
                            if (res.ok) setRobotConnected(!robotConnected);
                        } catch (e) { console.error(e); }
                    }}
                    className={`mobile-toolbar-btn ${robotConnected ? 'mobile-toolbar-btn-active' : ''}`}
                    title="Robot"
                >
                    <Bot className={`w-5 h-5 ${robotConnected ? 'text-green-400' : ''}`} />
                    <span className="text-[10px] font-medium">{robotConnected ? 'Online' : 'Robot'}</span>
                </button>
            </motion.div>

            {/* Main Content */}
            <div className="flex-1 min-h-0 flex flex-col lg:flex-row gap-2 lg:gap-12 items-center lg:items-start w-full max-w-6xl justify-center relative z-10
                           lg:flex-initial">

                {/* Chess Board Section - fills available space on mobile */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.8, delay: 0.1 }}
                    className="flex flex-col gap-1 lg:gap-3 w-full max-w-[600px] mx-auto lg:mx-0 flex-1 min-h-0 lg:flex-initial"
                >
                    {/* Opponent Info */}
                    <div className="flex-none flex justify-between items-center px-1">
                        <div className="flex items-center gap-2">
                            <div className="w-6 h-6 lg:w-8 lg:h-8 rounded-lg bg-gray-800 border border-white/10 flex items-center justify-center">
                                <span className="text-sm lg:text-lg">🤖</span>
                            </div>
                            <div>
                                <p className="text-xs lg:text-sm font-semibold text-gray-300">Stockfish</p>
                                <p className="text-[8px] lg:text-[10px] text-gray-600 hidden sm:block">Engine</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-0.5 bg-black/30 rounded-lg px-2 py-1 lg:px-3 lg:py-1.5 min-w-[60px] lg:min-w-[80px] justify-end">
                            <AnimatePresence mode="popLayout">
                                {capturedBlack.map((p, i) => (
                                    <motion.span
                                        key={`${p}-${i}`}
                                        initial={{ scale: 0, opacity: 0 }}
                                        animate={{ scale: 1, opacity: 1 }}
                                        exit={{ scale: 0, opacity: 0 }}
                                        className="captured-piece text-sm lg:text-lg text-gray-400 -ml-1 lg:-ml-1.5 cursor-default"
                                        title={p}
                                    >
                                        {pieceSymbols[p] || '♟'}
                                    </motion.span>
                                ))}
                            </AnimatePresence>
                        </div>
                    </div>

                    {/* Chess Board - responsive to height on mobile */}
                    <div className="chess-board-container flex-1 min-h-0 shadow-2xl bg-[#1a1a2e] mobile-board-wrapper lg:aspect-square lg:flex-initial">
                        <Chessboard
                            options={{
                                position: fen,
                                onPieceDrop: onDrop,
                                boardOrientation: "white",
                                darkSquareStyle: { backgroundColor: "#4a5568" },
                                lightSquareStyle: { backgroundColor: "#a0aec0" },
                                animationDurationInMs: 300,
                            }}
                        />
                    </div>

                    {/* Player Info */}
                    <div className="flex-none flex justify-between items-center px-1">
                        <div className="flex items-center gap-2">
                            <div className="w-6 h-6 lg:w-8 lg:h-8 rounded-lg bg-gradient-to-br from-amber-500/20 to-orange-500/20 border border-amber-500/20 flex items-center justify-center">
                                <Users className="w-3 h-3 lg:w-4 lg:h-4 text-amber-500" />
                            </div>
                            <div>
                                <p className="text-xs lg:text-sm font-semibold text-amber-100">You</p>
                                <p className="text-[8px] lg:text-[10px] text-gray-600 hidden sm:block">White pieces</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-0.5 bg-black/30 rounded-lg px-2 py-1 lg:px-3 lg:py-1.5 min-w-[60px] lg:min-w-[80px] justify-end">
                            <AnimatePresence mode="popLayout">
                                {capturedWhite.map((p, i) => (
                                    <motion.span
                                        key={`${p}-${i}`}
                                        initial={{ scale: 0, opacity: 0 }}
                                        animate={{ scale: 1, opacity: 1 }}
                                        exit={{ scale: 0, opacity: 0 }}
                                        className="captured-piece text-sm lg:text-lg text-white -ml-1 lg:-ml-1.5 cursor-default"
                                        title={p}
                                    >
                                        {pieceSymbols[p.toUpperCase()] || '♙'}
                                    </motion.span>
                                ))}
                            </AnimatePresence>
                        </div>
                    </div>
                </motion.div>

                {/* Controls Panel - Hidden on mobile, visible on desktop */}
                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.8, delay: 0.2 }}
                    className="hidden lg:block w-full lg:max-w-xs lg:sticky lg:top-8 space-y-6"
                >
                    <GameControls
                        onReset={handleReset}
                        robotConnected={robotConnected}
                        onRobotConnectionChange={setRobotConnected}
                        onOpenSettings={() => setIsSettingsOpen(true)}
                    />

                    {/* Tips Card */}
                    <Card variant="default" className="relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-24 h-24 bg-amber-500/5 rounded-full blur-2xl" />
                        <div className="relative">
                            <div className="flex items-center gap-2 mb-3">
                                <div className="w-7 h-7 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
                                    <Lightbulb className="w-3.5 h-3.5 text-amber-500" />
                                </div>
                                <h3 className="text-sm font-semibold text-gray-300">Pro Tip</h3>
                            </div>
                            <p className="text-xs text-gray-500 leading-relaxed">
                                Connect the robot to play on the physical board.
                                Moves will synchronize automatically between the digital and physical boards.
                            </p>
                        </div>
                    </Card>
                </motion.div>
            </div>

            {/* Settings Modal */}
            <SettingsModal
                isOpen={isSettingsOpen}
                onClose={() => setIsSettingsOpen(false)}
            />

            {/* DEBUG - remove after testing */}
            <RobotDebugPanel />
        </main>
    );
}
