"use client";

import { useEffect, useState, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
const Chessboard = dynamic(() => import("react-chessboard").then((mod) => mod.Chessboard), {
    ssr: false
});
import { Chess } from "chess.js";
import { socket } from "@/lib/socket";
import { Trophy, Users, Shield, Swords, Crown, Flag } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import {
    WaitingScreen,
    QueueScreen,
    ReadyScreen,
    DisconnectedScreen,
    GameOverScreen,
} from "@/components/PvPScreens";
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
    forfeit?: boolean;
}

const pieceSymbols: Record<string, string> = {
    'p': '♟', 'P': '♙',
    'n': '♞', 'N': '♘',
    'b': '♝', 'B': '♗',
    'r': '♜', 'R': '♖',
    'q': '♛', 'Q': '♕',
    'k': '♚', 'K': '♔'
};

type PvPPhase = "connecting" | "waiting" | "queued" | "ready" | "playing" | "game_over" | "opponent_disconnected";

function PvPGame() {
    const searchParams = useSearchParams();
    const playerColor = searchParams.get("color") as "white" | "black" | null;

    const [phase, setPhase] = useState<PvPPhase>("connecting");
    const [queuePosition, setQueuePosition] = useState(1);
    const [game, setGame] = useState(new Chess());
    const [fen, setFen] = useState("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
    const [capturedWhite, setCapturedWhite] = useState<string[]>([]);
    const [capturedBlack, setCapturedBlack] = useState<string[]>([]);
    const [gameStatus, setGameStatus] = useState<string>("En attente");
    const [selectedSquare, setSelectedSquare] = useState<string | null>(null);
    const [possibleMoves, setPossibleMoves] = useState<string[]>([]);
    const [gameOverData, setGameOverData] = useState<{ winner: string | null; forfeit?: boolean } | null>(null);
    const [disconnectTimeout, setDisconnectTimeout] = useState(60);

    console.log("PvPGame Render:", { phase, hasGameOverData: !!gameOverData });

    // Validate color param
    if (!playerColor || !["white", "black"].includes(playerColor)) {
        return (
            <main className="h-dvh bg-gradient-animate flex items-center justify-center p-4 text-white">
                <div className="text-center">
                    <h1 className="text-xl font-bold text-red-400 mb-2">Couleur invalide</h1>
                    <p className="text-sm text-gray-400">Utilisez ?color=white ou ?color=black</p>
                </div>
            </main>
        );
    }

    /* eslint-disable react-hooks/rules-of-hooks */

    useEffect(() => {
        function onPvpStatus(data: { status: string; position?: number }) {
            console.log("onPvpStatus:", data);
            setPhase((prevPhase) => {
                // Prevent overwriting game_over unless it's a specific reset-like transition
                // (though usually we'd want to stay in game_over until user interaction or new game start)
                if (prevPhase === "game_over") {
                    console.log("onPvpStatus: blocked phase change from game_over to", data.status);
                    return prevPhase;
                }

                switch (data.status) {
                    case "waiting":
                        return "waiting";
                    case "queued":
                        if (data.position) setQueuePosition(data.position);
                        return "queued";
                    case "ready":
                        return "ready";
                    case "playing":
                        return "playing";
                    default:
                        return prevPhase;
                }
            });
        }

        function onGameStart() {
            setPhase("playing");
            setGameOverData(null);
        }

        function onGameState(state: GameState) {
            console.log("onGameState:", state);

            // Protect game_over phase from being overwritten by late game_state updates
            setPhase((prevPhase) => {
                if (prevPhase === "game_over") {
                    console.log("onGameState: blocked phase change from game_over");
                    return prevPhase;
                }

                setFen(state.fen);
                const newGame = new Chess(state.fen);
                setGame(newGame);
                setSelectedSquare(null); // Réinitialiser la sélection
                setPossibleMoves([]); // Réinitialiser les coups possibles
                setCapturedWhite(state.white_captured);
                setCapturedBlack(state.black_captured);

                if (state.is_checkmate) {
                    setGameStatus(`Echec et mat ! ${state.winner === "white" ? "Blancs" : "Noirs"} gagnent`);
                    setGameOverData({ winner: state.winner, forfeit: false });
                    return "game_over";
                } else if (state.forfeit) {
                    console.log("onGameState: forfeit detected");
                    const isWinner = state.winner === playerColor;
                    setGameStatus(isWinner ? `Victoire par forfait` : `Defaite par forfait`);
                    setGameOverData({ winner: state.winner, forfeit: true });
                    return "game_over";
                } else if (state.is_game_over) {
                    setGameStatus("Partie terminee");
                    setGameOverData({ winner: state.winner });
                    return "game_over";
                } else if (state.is_check) {
                    setGameStatus("Echec !");
                } else {
                    const isMyTurn = state.turn === playerColor;
                    setGameStatus(isMyTurn ? "A vous de jouer" : "Tour adverse");
                }
                return prevPhase;
            });
        }

        function onOpponentDisconnected(data: { timeout: number }) {
            setDisconnectTimeout(data.timeout);
            setPhase("opponent_disconnected");
        }

        function onOpponentReconnected() {
            setPhase("playing");
        }

        function onQueueUpdate(data: { position: number }) {
            setQueuePosition(data.position);
        }

        socket.on("pvp_status", onPvpStatus);
        socket.on("game_start", onGameStart);
        socket.on("game_state", onGameState);
        socket.on("opponent_disconnected", onOpponentDisconnected);
        socket.on("opponent_reconnected", onOpponentReconnected);
        socket.on("queue_update", onQueueUpdate);

        // Join PvP on connect
        const doJoin = () => socket.emit("join_pvp", { color: playerColor });
        socket.on("connect", doJoin);
        if (socket.connected) doJoin();

        return () => {
            socket.off("pvp_status", onPvpStatus);
            socket.off("game_start", onGameStart);
            socket.off("game_state", onGameState);
            socket.off("opponent_disconnected", onOpponentDisconnected);
            socket.off("opponent_reconnected", onOpponentReconnected);
            socket.off("queue_update", onQueueUpdate);
            socket.off("connect", doJoin);
        };
    }, [playerColor]);

    const handleSquareClick = useCallback(({ square }: { square: string }) => {
        console.log("Square clicked:", square);

        if (phase !== "playing") return;

        // Only allow moves on player's turn
        const currentTurn = game.turn() === "w" ? "white" : "black";
        if (currentTurn !== playerColor) {
            console.log("Not player's turn");
            return;
        }

        // Si aucune pièce n'est sélectionnée
        if (!selectedSquare) {
            const piece = game.get(square as any);
            if (piece && piece.color === playerColor[0]) {
                // Sélectionner une pièce de la bonne couleur
                setSelectedSquare(square);
                const moves = game.moves({ square: square as any, verbose: true }) as any[];
                const moveTargets = moves.map(move => move.to);
                setPossibleMoves(moveTargets);
                console.log("Selected piece at", square, "Possible moves:", moveTargets);
            }
        } else {
            // Une pièce est déjà sélectionnée
            if (square === selectedSquare) {
                // Désélectionner si on clique sur la même case
                setSelectedSquare(null);
                setPossibleMoves([]);
            } else if (possibleMoves.includes(square)) {
                // Jouer le coup si c'est une destination valide
                makeMove(selectedSquare, square);
            } else {
                // Sélectionner une nouvelle pièce si c'est la bonne couleur
                const piece = game.get(square as any);
                if (piece && piece.color === playerColor[0]) {
                    setSelectedSquare(square);
                    const moves = game.moves({ square: square as any, verbose: true }) as any[];
                    const moveTargets = moves.map(move => move.to);
                    setPossibleMoves(moveTargets);
                    console.log("Selected new piece at", square, "Possible moves:", moveTargets);
                } else {
                    // Désélectionner si on clique sur une case vide ou pièce adverse
                    setSelectedSquare(null);
                    setPossibleMoves([]);
                }
            }
        }
    }, [game, selectedSquare, possibleMoves, phase, playerColor]);

    const makeMove = useCallback((from: string, to: string) => {
        try {
            const gameCopy = new Chess(game.fen());
            const move = gameCopy.move({
                from,
                to,
                promotion: "q",
            });

            if (move === null) {
                console.log("Invalid move");
                return;
            }

            const uci = move.from + move.to + (move.promotion ? move.promotion : "");
            console.log("Sending move:", uci);
            socket.emit("make_move", { uci });

            // Réinitialiser la sélection
            setSelectedSquare(null);
            setPossibleMoves([]);
        } catch (error) {
            console.error("Move error:", error);
        }
    }, [game]);

    const getSquareStyles = useCallback(() => {
        const styles: Record<string, any> = {};

        // Style pour la case sélectionnée
        if (selectedSquare) {
            styles[selectedSquare] = {
                backgroundColor: 'rgba(59, 130, 246, 0.5)', // Bleu semi-transparent
                boxShadow: 'inset 0 0 0 3px rgba(59, 130, 246, 0.8)'
            };
        }

        // Styles pour les coups possibles
        possibleMoves.forEach(move => {
            const piece = game.get(move as any);
            if (piece) {
                // Case avec pièce ennemie (capture)
                styles[move] = {
                    backgroundColor: 'rgba(239, 68, 68, 0.5)', // Rouge semi-transparent
                    boxShadow: 'inset 0 0 0 3px rgba(239, 68, 68, 0.8)'
                };
            } else {
                // Case vide (déplacement)
                styles[move] = {
                    backgroundColor: 'rgba(34, 197, 94, 0.5)', // Vert semi-transparent
                    boxShadow: 'inset 0 0 0 3px rgba(34, 197, 94, 0.8)'
                };
            }
        });

        return styles;
    }, [selectedSquare, possibleMoves, game]);

    const onDrop = useCallback(({ sourceSquare, targetSquare }: { piece: unknown; sourceSquare: string; targetSquare: string | null }) => {
        if (!targetSquare) return false;
        if (phase !== "playing") return false;

        // Only allow moves on player's turn
        const currentTurn = game.turn() === "w" ? "white" : "black";
        if (currentTurn !== playerColor) return false;

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
    }, [game, phase, playerColor]);

    const handleReady = () => {
        socket.emit("player_ready", {});
    };

    const handleResign = () => {
        socket.emit("resign", {});
    };

    const handleGameEndTimerComplete = () => {
        setPhase("connecting");
        setGameOverData(null);
        setGame(new Chess());
        setFen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
        setCapturedWhite([]);
        setCapturedBlack([]);
        setGameStatus("En attente");
        // Re-join PvP logic is triggered by "connecting" -> "connect" effect or manual emission
        socket.emit("join_pvp", { color: playerColor });
    };

    /* eslint-enable react-hooks/rules-of-hooks */

    // Phase-based rendering
    if (phase === "connecting" || phase === "waiting") {
        return <WaitingScreen playerColor={playerColor} />;
    }
    if (phase === "queued") {
        return <QueueScreen position={queuePosition} playerColor={playerColor} />;
    }
    if (phase === "ready") {
        return <ReadyScreen playerColor={playerColor} onReady={handleReady} />;
    }

    // Status badge styling
    const getStatusStyle = () => {
        if (gameStatus.includes("mat") || gameStatus.includes("Victoire")) {
            return "bg-gradient-to-r from-amber-500/20 to-yellow-500/20 border-amber-500/30 text-amber-200 glow-amber-soft";
        }
        if (gameStatus.includes("Echec") || gameStatus.includes("Defaite")) {
            return "bg-gradient-to-r from-red-500/20 to-rose-500/20 border-red-500/30 text-red-200 glow-red animate-pulse";
        }
        if (gameStatus.includes("vous")) {
            return "bg-gradient-to-r from-green-500/20 to-emerald-500/20 border-green-500/30 text-green-200";
        }
        return "bg-white/5 border-white/10 text-gray-300";
    };

    const getStatusIcon = () => {
        if (gameStatus.includes("mat") || gameStatus.includes("Victoire")) return <Crown className="w-4 h-4" />;
        if (gameStatus.includes("Echec") || gameStatus.includes("Defaite")) return <Shield className="w-4 h-4" />;
        if (gameStatus.includes("vous")) return <Swords className="w-4 h-4" />;
        return <Swords className="w-4 h-4 opacity-50" />;
    };

    const opponentColor = playerColor === "white" ? "black" : "white";
    const opponentLabel = opponentColor === "white" ? "Blancs" : "Noirs";
    const playerLabel = playerColor === "white" ? "Blancs" : "Noirs";

    // Captured pieces depend on orientation
    const topCaptured = playerColor === "white" ? capturedBlack : capturedWhite;
    const bottomCaptured = playerColor === "white" ? capturedWhite : capturedBlack;

    return (
        <main className="h-dvh bg-gradient-animate flex flex-col font-sans select-none overflow-hidden text-white relative
                         p-2 lg:p-8 lg:items-center lg:gap-8 lg:h-auto lg:min-h-screen lg:overflow-auto">

            {/* Decorative Elements */}
            <div className="fixed inset-0 pointer-events-none overflow-hidden">
                <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl" />
                <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-amber-500/5 rounded-full blur-3xl" />
            </div>

            {/* Header */}
            <motion.header
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="flex-none w-full max-w-6xl flex flex-row justify-between items-center z-20 py-1 lg:py-0 lg:gap-4"
            >
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
                            CHESS<span className="text-gradient-amber">ROBOT</span>
                        </h1>
                        <p className="text-[8px] lg:text-[10px] text-gray-500 uppercase tracking-[0.2em] font-medium hidden sm:block">
                            Joueur vs Joueur
                        </p>
                    </div>
                </div>

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

            {/* Mobile Toolbar - Resign only */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.3 }}
                className="flex-none flex lg:hidden items-center justify-center z-20 w-full"
                style={{ gap: "1.5rem", paddingBottom: "0.5rem", paddingTop: "0.25rem" }}
            >
                <button
                    onClick={handleResign}
                    className="mobile-toolbar-btn"
                    title="Abandonner"
                    disabled={phase !== "playing"}
                >
                    <Flag className="w-5 h-5 text-red-400" />
                    <span className="text-[10px] font-medium">Abandonner</span>
                </button>
            </motion.div>

            {/* Main Content */}
            <div className="flex-1 min-h-0 flex flex-col lg:flex-row gap-2 lg:gap-12 items-center lg:items-start w-full max-w-6xl justify-center relative z-10
                           lg:flex-initial">

                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.8, delay: 0.1 }}
                    className="flex flex-col gap-1 lg:gap-3 w-full max-w-[600px] mx-auto lg:mx-0 flex-1 min-h-0 lg:flex-initial"
                >
                    {/* Opponent Info (top) */}
                    <div className="flex-none flex justify-between items-center px-1">
                        <div className="flex items-center gap-2">
                            <div className="w-6 h-6 lg:w-8 lg:h-8 rounded-lg bg-gray-800 border border-white/10 flex items-center justify-center">
                                <Users className="w-3 h-3 lg:w-4 lg:h-4 text-gray-400" />
                            </div>
                            <div>
                                <p className="text-xs lg:text-sm font-semibold text-gray-300">Adversaire</p>
                                <p className="text-[8px] lg:text-[10px] text-gray-600 hidden sm:block">{opponentLabel}</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-0.5 bg-black/30 rounded-lg px-2 py-1 lg:px-3 lg:py-1.5 min-w-[60px] lg:min-w-[80px] justify-end">
                            <AnimatePresence mode="popLayout">
                                {topCaptured.map((p, i) => (
                                    <motion.span
                                        key={`${p}-${i}`}
                                        initial={{ scale: 0, opacity: 0 }}
                                        animate={{ scale: 1, opacity: 1 }}
                                        exit={{ scale: 0, opacity: 0 }}
                                        className="captured-piece text-sm lg:text-lg text-gray-400 -ml-1 lg:-ml-1.5 cursor-default"
                                        title={p}
                                    >
                                        {pieceSymbols[p] || pieceSymbols[p.toLowerCase()] || '♟'}
                                    </motion.span>
                                ))}
                            </AnimatePresence>
                        </div>
                    </div>

                    {/* Chess Board */}
                    <div className="chess-board-container shadow-2xl bg-[#1a1a2e]" style={{ width: "400px", height: "400px", margin: "auto" }}>
                        <Chessboard
                            options={{
                                position: fen,
                                onPieceDrop: onDrop,
                                onSquareClick: handleSquareClick,
                                boardOrientation: playerColor,
                                darkSquareStyle: { backgroundColor: "#8B7355" },
                                lightSquareStyle: { backgroundColor: "#F0D9B5" },
                                squareStyles: getSquareStyles(),
                                animationDurationInMs: 300,
                            }}
                        />
                    </div>

                    {/* Player Info (bottom) */}
                    <div className="flex-none flex justify-between items-center px-1">
                        <div className="flex items-center gap-2">
                            <div className="w-6 h-6 lg:w-8 lg:h-8 rounded-lg bg-gradient-to-br from-amber-500/20 to-orange-500/20 border border-amber-500/20 flex items-center justify-center">
                                <Users className="w-3 h-3 lg:w-4 lg:h-4 text-amber-500" />
                            </div>
                            <div>
                                <p className="text-xs lg:text-sm font-semibold text-amber-100">Vous</p>
                                <p className="text-[8px] lg:text-[10px] text-gray-600 hidden sm:block">{playerLabel}</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-0.5 bg-black/30 rounded-lg px-2 py-1 lg:px-3 lg:py-1.5 min-w-[60px] lg:min-w-[80px] justify-end">
                            <AnimatePresence mode="popLayout">
                                {bottomCaptured.map((p, i) => (
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

                {/* Desktop sidebar - Resign button */}
                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.8, delay: 0.2 }}
                    className="hidden lg:block w-full lg:max-w-xs lg:sticky lg:top-8 space-y-6"
                >
                    <div className="rounded-2xl p-6" style={{
                        background: "rgba(255, 255, 255, 0.05)",
                        border: "1px solid rgba(255, 255, 255, 0.1)",
                        backdropFilter: "blur(20px)",
                    }}>
                        <h3 className="text-sm font-semibold text-gray-300 mb-4">Partie PvP</h3>
                        <button
                            onClick={handleResign}
                            disabled={phase !== "playing"}
                            className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-semibold transition-all"
                            style={{
                                background: "linear-gradient(to right, #dc2626, #e11d48)",
                                color: "white",
                                opacity: phase !== "playing" ? 0.5 : 1,
                                cursor: phase !== "playing" ? "not-allowed" : "pointer",
                            }}
                        >
                            <Flag className="w-4 h-4" />
                            Abandonner
                        </button>
                    </div>
                </motion.div>
            </div>

            {/* Overlays */}
            {phase === "opponent_disconnected" && (
                <DisconnectedScreen timeout={disconnectTimeout} />
            )}
            {phase === "game_over" && gameOverData && (
                <GameOverScreen
                    winner={gameOverData.winner}
                    playerColor={playerColor}
                    forfeit={gameOverData.forfeit}
                    onTimerComplete={handleGameEndTimerComplete}
                />
            )}

            {/* DEBUG - remove after testing */}
            <RobotDebugPanel />
        </main>
    );
}

// Wrap with Suspense for useSearchParams
export default function PvPPage() {
    return (
        <Suspense fallback={
            <main className="h-dvh bg-gradient-animate flex items-center justify-center text-white">
                <div className="text-center">
                    <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-sm text-gray-400">Chargement...</p>
                </div>
            </main>
        }>
            <PvPGame />
        </Suspense>
    );
}
