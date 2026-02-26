"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { motion } from "framer-motion";
import { Clock, Crown, Flag, Loader2, Users, Wifi, WifiOff, Trophy, Swords } from "lucide-react";
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

    const handleReady = () => {
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
                    animate={{ scale: [1, 1.05, 1] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                    className="w-20 h-20 rounded-2xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center shadow-lg glow-green"
                >
                    <Swords className="w-10 h-10 text-white" />
                </motion.div>

                <Card variant="elevated" className="text-center w-full">
                    <h2 className="text-xl font-bold mb-2">Les deux joueurs sont la !</h2>
                    <p className="text-sm text-gray-400 mb-6">
                        Vous jouez les <span className="font-semibold text-amber-400">{playerColor === "white" ? "Blancs" : "Noirs"}</span>
                    </p>

                    {!isReady ? (
                        <motion.div
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            transition={{ type: "spring", stiffness: 400, damping: 17 }}
                        >
                            <Button
                                variant="primary"
                                size="lg"
                                onClick={handleReady}
                                className="w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 shadow-lg hover:shadow-xl transform transition-all duration-200 hover:scale-105 active:scale-95"
                                leftIcon={<Wifi className="w-5 h-5" />}
                            >
                                PRET
                            </Button>
                        </motion.div>
                    ) : (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5 }}
                            className="flex flex-col items-center gap-3 py-4"
                        >
                            <motion.div
                                animate={{ scale: [1, 1.2, 1] }}
                                transition={{ duration: 1, repeat: Infinity }}
                                className="w-12 h-12 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center shadow-lg"
                            >
                                <Wifi className="w-6 h-6 text-white" />
                            </motion.div>
                            <p className="text-lg font-semibold text-green-400">Vous êtes prêt</p>
                            <p className="text-sm text-gray-400">En attente de l'adversaire...</p>
                        </motion.div>
                    )}
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

    const [mounted, setMounted] = useState(false);
    const [timer, setTimer] = useState(30);

    useEffect(() => {
        setMounted(true);
    }, []);

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

    console.log("GameOverScreen render check:", { mounted, winner, playerColor, forfeit, isWinner, isDraw, timer });

    const getMessage = () => {
        if (isDraw) return "Match nul !";
        if (forfeit) return isWinner ? "Victoire par forfait !" : "Defaite par forfait";
        return isWinner ? "Victoire !" : "Defaite";
    };

    if (!mounted) {
        console.log("GameOverScreen: not mounted yet");
        return null;
    }

    return (
        <div className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ type: "spring", stiffness: 300, damping: 20 }}
                className="max-w-sm w-full relative z-[101]"
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

                    <div className="mt-8 pt-6 border-t border-white/10 space-y-4">
                        <Button
                            variant="primary"
                            className="w-full bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 font-bold py-6 text-lg"
                            onClick={onTimerComplete}
                        >
                            REJOUER
                        </Button>

                        <p className="text-xs text-gray-500 flex items-center justify-center gap-2">
                            <Clock className="w-3 h-3 animate-pulse" />
                            <span>
                                Retour automatique dans{" "}
                                <span className="font-bold text-amber-500">{timer}s</span>
                            </span>
                        </p>
                    </div>
                </Card>
            </motion.div>
        </div>
    );
}
