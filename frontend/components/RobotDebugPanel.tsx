"use client";

/**
 * DEBUG ONLY - Robot GCode debug panel.
 * Shows all GCode commands that would be sent to the robot.
 * Remove this file after debugging.
 */

import { useEffect, useState, useRef } from "react";
import { socket } from "@/lib/socket";
import { Terminal, ChevronDown, ChevronUp, Trash2 } from "lucide-react";

interface DebugEntry {
    move: string;
    commands: string[];
    timestamp: string;
}

export default function RobotDebugPanel() {
    const [entries, setEntries] = useState<DebugEntry[]>([]);
    const [isOpen, setIsOpen] = useState(true);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        function onRobotDebug(data: { move: string; commands: string[] }) {
            const entry: DebugEntry = {
                move: data.move,
                commands: data.commands,
                timestamp: new Date().toLocaleTimeString("fr-FR"),
            };
            setEntries((prev) => [...prev, entry]);
        }

        socket.on("robot_debug", onRobotDebug);
        return () => {
            socket.off("robot_debug", onRobotDebug);
        };
    }, []);

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollRef.current && isOpen) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [entries, isOpen]);

    return (
        <div className="fixed bottom-0 left-0 right-0 z-50 pointer-events-none">
            <div className="pointer-events-auto mx-auto max-w-2xl">
                {/* Header bar */}
                <button
                    onClick={() => setIsOpen(!isOpen)}
                    className="w-full flex items-center justify-between px-3 py-1.5 bg-gray-900/95 border-t border-x border-amber-500/30 rounded-t-lg backdrop-blur-md"
                >
                    <div className="flex items-center gap-2">
                        <Terminal className="w-3.5 h-3.5 text-amber-400" />
                        <span className="text-xs font-mono font-bold text-amber-400">
                            ROBOT DEBUG
                        </span>
                        {entries.length > 0 && (
                            <span className="text-[10px] font-mono text-gray-500">
                                ({entries.length} moves)
                            </span>
                        )}
                    </div>
                    <div className="flex items-center gap-2">
                        {entries.length > 0 && (
                            <span
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setEntries([]);
                                }}
                                className="text-gray-500 hover:text-red-400 transition-colors cursor-pointer"
                            >
                                <Trash2 className="w-3 h-3" />
                            </span>
                        )}
                        {isOpen ? (
                            <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
                        ) : (
                            <ChevronUp className="w-3.5 h-3.5 text-gray-400" />
                        )}
                    </div>
                </button>

                {/* Console body */}
                {isOpen && (
                    <div
                        ref={scrollRef}
                        className="bg-gray-950/95 border-x border-b border-amber-500/20 backdrop-blur-md overflow-y-auto font-mono text-[11px] leading-relaxed"
                        style={{ maxHeight: "200px" }}
                    >
                        {entries.length === 0 ? (
                            <div className="px-3 py-4 text-gray-600 text-center">
                                En attente de coups... Jouez pour voir les commandes GCode.
                            </div>
                        ) : (
                            <div className="px-3 py-2 space-y-2">
                                {entries.map((entry, i) => (
                                    <div key={i}>
                                        {entry.commands.map((cmd, j) => {
                                            // Color coding
                                            let color = "text-gray-400";
                                            if (cmd.startsWith("---"))
                                                color = "text-amber-400 font-bold";
                                            else if (cmd.includes("GCODE >>>"))
                                                color = "text-green-400";
                                            else if (cmd.includes("[DEBUG"))
                                                color = "text-blue-400";
                                            else if (cmd.includes("ERROR"))
                                                color = "text-red-400";

                                            return (
                                                <div key={j} className={color}>
                                                    <span className="text-gray-600 mr-2">
                                                        {entry.timestamp}
                                                    </span>
                                                    {cmd}
                                                </div>
                                            );
                                        })}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
