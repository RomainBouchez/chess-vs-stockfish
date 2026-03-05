"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Clock, Crown, Flag, Loader2, Users, WifiOff, Trophy, Swords } from "lucide-react";
import { Button, Card } from "@/components/ui";

interface WaitingScreenProps {
    playerColor: string;
}

export function WaitingScreen({ playerColor }: WaitingScreenProps) {
    return (
        <main className="h-dvh bg-gradient-animate flex flex-col items-center justify-center p-4 text-white">
            <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex flex-col items-center gap-6 max-w-sm w-full"
            >
                <motion.div
                    animate={{ scale: [1, 1.1, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="w-20 h-20 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shadow-lg glow-amber"
                >
                    <Users className="w-10 h-10 text-white" />
                </motion.div>

                <Card variant="elevated" className="text-center w-full">
                    <h2 className="text-xl font-bold mb-2">En attente de l&apos;adversaire</h2>
                    <p className="text-sm text-gray-400 mb-4">
                        Vous jouez les <span className="font-semibold text-amber-400">{playerColor === "white" ? "Blancs" : "Noirs"}</span>
                    </p>
                    <div className="flex items-center justify-center gap-2 text-gray-500">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span className="text-xs">En attente du scan du QR code adverse...</span>
                    </div>
                </Card>
            </motion.div>
        </main>
    );
}

interface QueueScreenProps {
    position: number;
    playerColor: string;
}

export function QueueScreen({ position, playerColor }: QueueScreenProps) {
    return (
        <main className="h-dvh bg-gradient-animate flex flex-col items-center justify-center p-4 text-white">
            <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex flex-col items-center gap-6 max-w-sm w-full"
            >
                <motion.div
                    animate={{ rotate: [0, 5, -5, 0] }}
                    transition={{ duration: 3, repeat: Infinity }}
                    className="w-20 h-20 rounded-2xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shadow-lg glow-purple"
                >
                    <Clock className="w-10 h-10 text-white" />
                </motion.div>

                <Card variant="elevated" className="text-center w-full">
                    <h2 className="text-xl font-bold mb-2">Partie en cours</h2>
                    <p className="text-sm text-gray-400 mb-4">
                        Vous etes en file d&apos;attente ({playerColor === "white" ? "Blancs" : "Noirs"})
                    </p>
                    <div className="flex items-center justify-center gap-3">
                        <div className="text-4xl font-black text-gradient-amber">#{position}</div>
                        <div className="text-left">
                            <p className="text-xs text-gray-500">Position dans</p>
                            <p className="text-sm font-semibold text-gray-300">la file</p>
                        </div>
                    </div>
                </Card>
            </motion.div>
        </main>
    );
}

interface ReadyScreenProps {
    playerColor: string;
    onReady: () => void;
}

export function ReadyScreen({ playerColor, onReady }: ReadyScreenProps) {
    const [isReady, setIsReady] = useState(false);

    const handleClick = () => {
        setIsReady(true);
        onReady();
    };

    return (
        <main className="h-dvh bg-gradient-animate flex flex-col items-center justify-center p-4 text-white">
            <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex flex-col items-center gap-6 max-w-sm w-full"
            >
                <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                    className="text-center"
                >
                    <h1 className="text-2xl font-black tracking-tight text-white">
                        PST <span className="text-gradient-amber">joueur d&apos;échec</span>
                    </h1>
                </motion.div>

                <Card variant="elevated" className="text-center w-full">
                    <motion.div
                        key={isReady ? "ready" : "waiting"}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                    >
                        <h2 className="text-xl font-bold mb-2">
                            {isReady ? "Vous êtes prêt !" : "Les deux joueurs sont là !"}
                        </h2>
                        <p className="text-sm text-gray-400 mb-6">
                            {isReady
                                ? <span className="text-amber-400 font-semibold">En attente de l&apos;adversaire...</span>
                                : <>Vous jouez les <span className="font-semibold text-amber-400">{playerColor === "white" ? "Blancs" : "Noirs"}</span></>
                            }
                        </p>
                    </motion.div>

                    <div className="flex justify-center">
                        {!isReady ? (
                            <Button
                                variant="primary"
                                size="lg"
                                onClick={handleClick}
                                className="px-10"
                            >
                                PRÊT
                            </Button>
                        ) : (
                            <Button
                                variant="primary"
                                size="lg"
                                disabled
                                className="px-10 opacity-40 cursor-not-allowed"
                                leftIcon={
                                    <div className="flex items-center gap-1">
                                        {[0, 1, 2].map((i) => (
                                            <motion.div
                                                key={i}
                                                className="w-1.5 h-1.5 rounded-full bg-white"
                                                animate={{ opacity: [0.3, 1, 0.3] }}
                                                transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
                                            />
                                        ))}
                                    </div>
                                }
                            >
                                Attente du joueur adverse
                            </Button>
                        )}
                    </div>
                </Card>
            </motion.div>
        </main>
    );
}

interface DisconnectedScreenProps {
    timeout: number;
}

export function DisconnectedScreen({ timeout }: DisconnectedScreenProps) {
    const [remaining, setRemaining] = useState(timeout);

    useEffect(() => {
        if (remaining <= 0) return;
        const timer = setInterval(() => {
            setRemaining((r) => Math.max(0, r - 1));
        }, 1000);
        return () => clearInterval(timer);
    }, [remaining]);

    return (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="max-w-sm w-full"
            >
                <Card variant="elevated" className="text-center">
                    <motion.div
                        animate={{ scale: [1, 1.1, 1] }}
                        transition={{ duration: 2, repeat: Infinity }}
                        className="w-16 h-16 rounded-2xl bg-gradient-to-br from-red-500 to-rose-600 flex items-center justify-center shadow-lg mx-auto mb-4"
                    >
                        <WifiOff className="w-8 h-8 text-white" />
                    </motion.div>

                    <h2 className="text-lg font-bold text-white mb-2">Adversaire deconnecte</h2>
                    <p className="text-sm text-gray-400 mb-4">En attente de reconnexion...</p>

                    <div className="text-3xl font-black text-red-400 mb-2">
                        {remaining}s
                    </div>
                    <p className="text-xs text-gray-500">
                        Victoire par forfait dans {remaining} secondes
                    </p>
                </Card>
            </motion.div>
        </div>
    );
}

interface GameOverScreenProps {
    winner: string | null;
    playerColor: string;
    forfeit?: boolean;
    onTimerComplete?: () => void;
}

export function GameOverScreen({ winner, playerColor, forfeit, onTimerComplete }: GameOverScreenProps) {
    const isWinner = winner === playerColor;
    const isDraw = winner === "draw";

    const [timer, setTimer] = useState(30);

    useEffect(() => {
        if (timer <= 0) {
            onTimerComplete?.();
            return;
        }
        const interval = setInterval(() => {
            setTimer((t) => t - 1);
        }, 1000);
        return () => clearInterval(interval);
    }, [timer, onTimerComplete]);

    const getMessage = () => {
        if (isDraw) return "Match nul !";
        if (forfeit) return isWinner ? "Victoire par forfait !" : "Défaite par forfait";
        return isWinner ? "Victoire !" : "Défaite";
    };

    return (
        <div style={{
            position: "fixed",
            inset: 0,
            zIndex: 9999,
            backgroundColor: "rgba(0,0,0,0.55)",
            backdropFilter: "blur(8px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "1rem",
        }}>
            <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ type: "spring", stiffness: 300, damping: 20 }}
                style={{ maxWidth: "24rem", width: "100%", position: "relative", zIndex: 10000 }}
            >
                <Card variant="elevated" className="text-center shadow-2xl border-white/20">
                    <motion.div
                        initial={{ rotate: -10 }}
                        animate={{ rotate: [0, -5, 5, 0] }}
                        transition={{ duration: 2, repeat: Infinity }}
                        className={`w-20 h-20 rounded-2xl flex items-center justify-center shadow-lg mx-auto mb-6 ${isWinner
                            ? "bg-gradient-to-br from-amber-500 to-orange-600 glow-amber"
                            : isDraw
                                ? "bg-gradient-to-br from-gray-500 to-gray-600"
                                : "bg-gradient-to-br from-red-500 to-rose-600"
                            }`}
                    >
                        {isWinner ? (
                            <Trophy className="w-10 h-10 text-white" />
                        ) : isDraw ? (
                            <Swords className="w-10 h-10 text-white" />
                        ) : (
                            <Flag className="w-10 h-10 text-white" />
                        )}
                    </motion.div>

                    <h2 className={`text-3xl font-black mb-3 ${isWinner ? "text-gradient-amber" : isDraw ? "text-gray-300" : "text-red-400"
                        }`}>
                        {getMessage()}
                    </h2>

                    {winner && !isDraw && (
                        <p className="text-sm text-gray-400 mb-6">
                            {isWinner ? (
                                <><Crown className="w-4 h-4 inline mr-1" />Les {winner === "white" ? "Blancs" : "Noirs"} remportent la partie</>
                            ) : (
                                <>Les {winner === "white" ? "Blancs" : "Noirs"} remportent la partie</>
                            )}
                        </p>
                    )}

                    <div className="mt-6 space-y-3">
                        <div className="flex justify-center">
                            <Button
                                variant="primary"
                                size="lg"
                                className="px-10"
                                onClick={onTimerComplete}
                            >
                                REJOUER
                            </Button>
                        </div>
                        <p className="text-xs text-gray-500 flex items-center justify-center gap-2">
                            <Clock className="w-3 h-3 animate-pulse" />
                            Retour automatique dans{" "}
                            <span className="font-bold text-amber-500">{timer}s</span>
                        </p>
                    </div>

                </Card>
            </motion.div>
        </div>
    );
}
