"use client";

import { useEffect, useState, useCallback, useRef } from "react";
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
    const [selectedSquare, setSelectedSquare] = useState<string | null>(null);
    const [possibleMoves, setPossibleMoves] = useState<string[]>([]);

    // ResizeObserver pour boardWidth dynamique
    const boardRef = useRef(null);

    useEffect(() => {
        function onGameState(state: GameState) {
            console.log("Received state:", state);
            setFen(state.fen);
            const newGame = new Chess(state.fen);
            setGame(newGame);
            setSelectedSquare(null); // Réinitialiser la sélection
            setPossibleMoves([]); // Réinitialiser les coups possibles
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

    // Fonction pour gérer le clic sur une case
    const handleSquareClick = useCallback(({ square }: { square: string }) => {
        console.log("Square clicked:", square);
        
        // Vérifier si c'est le tour des blancs
        if (game.turn() !== 'w') {
            console.log("Not white's turn");
            return;
        }

        // Si aucune pièce n'est sélectionnée
        if (!selectedSquare) {
            const piece = game.get(square as any);
            if (piece && piece.color === 'w') {
                // Sélectionner une pièce blanche
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
                // Sélectionner une nouvelle pièce si c'est une pièce blanche
                const piece = game.get(square as any);
                if (piece && piece.color === 'w') {
                    setSelectedSquare(square);
                    const moves = game.moves({ square: square as any, verbose: true }) as any[];
                    const moveTargets = moves.map(move => move.to);
                    setPossibleMoves(moveTargets);
                    console.log("Selected new piece at", square, "Possible moves:", moveTargets);
                } else {
                    // Désélectionner si on clique sur une case vide ou pièce noire
                    setSelectedSquare(null);
                    setPossibleMoves([]);
                }
            }
        }
    }, [game, selectedSquare, possibleMoves]);

    // Fonction pour jouer un coup
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

    // Fonction pour obtenir le style d'une case
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

    const onDrop = useCallback(({ sourceSquare, targetSquare, piece }: { piece: any, sourceSquare: string, targetSquare: string | null }) => {
        if (!targetSquare) return false;
        
        console.log("onDrop called:", { sourceSquare, targetSquare, piece, currentTurn: game.turn(), fen: game.fen() });
        console.log("Socket connected:", socket.connected);
        
        // Vérifier si c'est le tour des blancs
        if (game.turn() !== 'w') {
            console.log("Not white's turn");
            return false;
        }
        
        try {
            // Créer une copie du jeu pour tester le coup
            const gameCopy = new Chess(game.fen());
            const move = gameCopy.move({
                from: sourceSquare,
                to: targetSquare,
                promotion: "q", // Promotion par défaut à dame
            });

            if (move === null) {
                console.log("Invalid move");
                return false;
            }

            // Si le coup est valide, l'envoyer au serveur
            const uci = move.from + move.to + (move.promotion ? move.promotion : "");
            console.log("Sending move:", uci);
            socket.emit("make_move", { uci });
            return true;

        } catch (error) {
            console.error("Move error:", error);
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
            return "bg-gradient-to-r from-accent-gold/10 to-accent-gold-hover/10 border-accent-gold/30 text-accent-blue border-elegant-gold";
        }
        if (gameStatus.includes("Check")) {
            return "bg-gradient-to-r from-red-500/10 to-rose-500/10 border-red-500/30 text-red-600 border-elegant animate-pulse";
        }
        return "bg-card-background border-border-color text-foreground border-elegant";
    };

    const getStatusIcon = () => {
        if (gameStatus.includes("Checkmate")) return <Crown className="w-4 h-4" />;
        if (gameStatus.includes("Check")) return <Shield className="w-4 h-4" />;
        return <Swords className="w-4 h-4 opacity-50" />;
    };

    return (
        <main className="h-dvh bg-elegant-gradient flex flex-col font-roboto select-none overflow-hidden text-foreground relative">
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
                        className="w-8 h-8 lg:w-12 lg:h-12 rounded-lg lg:rounded-xl bg-gradient-to-br from-accent-gold to-accent-gold-hover flex items-center justify-center shadow-lg border-elegant-gold"
                    >
                        <Trophy className="text-white w-4 h-4 lg:w-6 lg:h-6" />
                    </motion.div>
                    <div>
                        <h1 className="text-lg lg:text-2xl font-black font-playfair tracking-tight">
                            CHESS<span className="text-gradient-gold">ROBOT</span>
                        </h1>
                        <p className="text-[8px] lg:text-[10px] text-foreground-muted uppercase tracking-[0.2em] font-medium hidden sm:block">
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
                        border shadow-lg
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
                            <div className="w-6 h-6 lg:w-8 lg:h-8 rounded-lg bg-subtle-bg border border-border-color flex items-center justify-center">
                                <span className="text-sm lg:text-lg">🤖</span>
                            </div>
                            <div>
                                <p className="text-xs lg:text-sm font-semibold text-foreground">Stockfish</p>
                                <p className="text-[8px] lg:text-[10px] text-foreground-muted hidden sm:block">Engine</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-0.5 bg-subtle-bg rounded-lg px-2 py-1 lg:px-3 lg:py-1.5 min-w-[60px] lg:min-w-[80px] justify-end border border-border-color">
                            <AnimatePresence mode="popLayout">
                                {capturedBlack.map((p, i) => (
                                    <motion.span
                                        key={`${p}-${i}`}
                                        initial={{ scale: 0, opacity: 0 }}
                                        animate={{ scale: 1, opacity: 1 }}
                                        exit={{ scale: 0, opacity: 0 }}
                                        className="captured-piece text-sm lg:text-lg text-foreground-muted -ml-1 lg:-ml-1.5 cursor-default"
                                        title={p}
                                    >
                                        {pieceSymbols[p] || '♟'}
                                    </motion.span>
                                ))}
                            </AnimatePresence>
                        </div>
                    </div>

                    {/* Chess Board - responsive to height on mobile */}
                    <div
                        ref={boardRef}
                        className="bg-card-background p-0 chess-board-container"
                        style={{ 
                            width: "400px",
                            height: "400px",
                            margin: "auto"
                        }}
                    >
                        <Chessboard
                            options={{
                                position: fen,
                                onPieceDrop: onDrop,
                                onSquareClick: handleSquareClick,
                                boardOrientation: "white",
                                darkSquareStyle: { backgroundColor: "#8B7355" },
                                lightSquareStyle: { backgroundColor: "#F0D9B5" },
                                squareStyles: getSquareStyles(),
                                animationDurationInMs: 300,
                            }}
                        />
                    </div>

                    {/* Player Info */}
                    <div className="flex-none flex justify-between items-center px-1">
                        <div className="flex items-center gap-2">
                            <div className="w-6 h-6 lg:w-8 lg:h-8 rounded-lg bg-gradient-to-br from-accent-gold/10 to-accent-gold-hover/10 border border-accent-gold/20 flex items-center justify-center">
                                <Users className="w-3 h-3 lg:w-4 lg:h-4 text-accent-gold" />
                            </div>
                            <div>
                                <p className="text-xs lg:text-sm font-semibold text-foreground">You</p>
                                <p className="text-[8px] lg:text-[10px] text-foreground-muted hidden sm:block">White pieces</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-0.5 bg-subtle-bg rounded-lg px-2 py-1 lg:px-3 lg:py-1.5 min-w-[60px] lg:min-w-[80px] justify-end border border-border-color">
                            <AnimatePresence mode="popLayout">
                                {capturedWhite.map((p, i) => (
                                    <motion.span
                                        key={`${p}-${i}`}
                                        initial={{ scale: 0, opacity: 0 }}
                                        animate={{ scale: 1, opacity: 1 }}
                                        exit={{ scale: 0, opacity: 0 }}
                                        className="captured-piece text-sm lg:text-lg text-foreground -ml-1 lg:-ml-1.5 cursor-default"
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
                    <Card variant="default" className="relative overflow-hidden glass border-elegant">
                        <div className="absolute top-0 right-0 w-24 h-24 bg-accent-gold/5 rounded-full blur-2xl" />
                        <div className="relative">
                            <div className="flex items-center gap-2 mb-3">
                                <div className="w-7 h-7 rounded-lg bg-accent-gold/10 border border-accent-gold/20 flex items-center justify-center">
                                    <Lightbulb className="w-3.5 h-3.5 text-accent-gold" />
                                </div>
                                <h3 className="text-sm font-semibold text-foreground font-playfair">Pro Tip</h3>
                            </div>
                            <p className="text-xs text-foreground-muted leading-relaxed font-roboto">
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
