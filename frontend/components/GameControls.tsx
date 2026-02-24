"use client";

import { useState, CSSProperties } from "react";
import { Settings, RefreshCw, Bot, Gamepad2, Wifi } from "lucide-react";
import { Button, Card } from "@/components/ui";
import { motion } from "framer-motion";
import { BACKEND_API } from "@/lib/socket";

interface GameControlsProps {
    onReset: () => void;
    onOpenSettings: () => void;
    robotConnected: boolean;
    onRobotConnectionChange?: (connected: boolean) => void;
}

export default function GameControls({ onReset, onOpenSettings, robotConnected, onRobotConnectionChange }: GameControlsProps) {
    const [isRobotLoading, setIsRobotLoading] = useState(false);

    const toggleRobot = async () => {
        setIsRobotLoading(true);
        try {
            const endpoint = robotConnected
                ? `${BACKEND_API}/api/robot/disconnect`
                : `${BACKEND_API}/api/robot/connect`;
            const res = await fetch(endpoint, { method: "POST" });
            if (res.ok) {
                onRobotConnectionChange?.(!robotConnected);
            }
        } catch (e) {
            console.error(e);
        } finally {
            setIsRobotLoading(false);
        }
    };

    const headerStyle: CSSProperties = {
        display: "flex",
        alignItems: "center",
        gap: "12px",
        marginBottom: "24px",
    };

    const iconBoxStyle: CSSProperties = {
        width: 40,
        height: 40,
        borderRadius: "12px",
        background: "linear-gradient(to bottom right, rgba(245, 158, 11, 0.2), rgba(234, 88, 12, 0.1))",
        border: "1px solid rgba(245, 158, 11, 0.2)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
    };

    const buttonsContainerStyle: CSSProperties = {
        display: "flex",
        flexDirection: "column",
        gap: "12px",
    };

    const dividerStyle: CSSProperties = {
        position: "relative",
        padding: "8px 0",
    };

    const dividerLineStyle: CSSProperties = {
        position: "absolute",
        inset: 0,
        display: "flex",
        alignItems: "center",
    };

    const dividerInnerLineStyle: CSSProperties = {
        width: "100%",
        borderTop: "1px solid rgba(255, 255, 255, 0.05)",
    };

    const dividerTextContainerStyle: CSSProperties = {
        position: "relative",
        display: "flex",
        justifyContent: "center",
    };

    const dividerTextStyle: CSSProperties = {
        padding: "0 12px",
        fontSize: "10px",
        textTransform: "uppercase",
        letterSpacing: "0.1em",
        color: "#4b5563",
        background: "#1a1a2e",
    };

    const statusContainerStyle: CSSProperties = {
        marginTop: "20px",
        paddingTop: "16px",
        borderTop: "1px solid rgba(255, 255, 255, 0.05)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: "10px",
        fontSize: "12px",
        fontWeight: 500,
        transition: "color 0.5s",
        color: robotConnected ? "#4ade80" : "#4b5563",
    };

    const statusDotStyle: CSSProperties = {
        width: 10,
        height: 10,
        borderRadius: "9999px",
        background: robotConnected ? "#22c55e" : "#374151",
        boxShadow: robotConnected ? "0 0 10px rgba(34, 197, 94, 0.6)" : "none",
    };

    return (
        <Card variant="elevated" style={{ overflow: "hidden" }}>
            {/* Header */}
            <div style={headerStyle}>
                <div style={iconBoxStyle}>
                    <Gamepad2 style={{ width: 20, height: 20, color: "#f59e0b" }} />
                </div>
                <div>
                    <h2 style={{ fontSize: "18px", fontWeight: "bold", color: "white" }}>Control Center</h2>
                    <p style={{ fontSize: "12px", color: "#6b7280" }}>Manage your game</p>
                </div>
            </div>

            {/* Actions */}
            <div style={buttonsContainerStyle}>
                <Button
                    onClick={onReset}
                    variant="primary"
                    size="lg"
                    leftIcon={<RefreshCw style={{ width: 20, height: 20 }} />}
                    style={{ width: "100%" }}
                >
                    New Game
                </Button>

                <Button
                    onClick={onOpenSettings}
                    variant="secondary"
                    size="lg"
                    leftIcon={<Settings style={{ width: 20, height: 20 }} />}
                    style={{ width: "100%" }}
                >
                    Engine Settings
                </Button>

                {/* Divider */}
                <div style={dividerStyle}>
                    <div style={dividerLineStyle}>
                        <div style={dividerInnerLineStyle} />
                    </div>
                    <div style={dividerTextContainerStyle}>
                        <span style={dividerTextStyle}>Hardware</span>
                    </div>
                </div>

                {/* Robot Connection Button */}
                <motion.div
                    animate={robotConnected ? { scale: [1, 1.02, 1] } : {}}
                    transition={{ duration: 0.3 }}
                >
                    <Button
                        onClick={toggleRobot}
                        isLoading={isRobotLoading}
                        variant={robotConnected ? "success" : "secondary"}
                        size="lg"
                        leftIcon={
                            robotConnected
                                ? <Wifi style={{ width: 20, height: 20 }} />
                                : <Bot style={{ width: 20, height: 20 }} />
                        }
                        style={{
                            width: "100%",
                            boxShadow: robotConnected ? "0 0 20px rgba(34, 197, 94, 0.4)" : undefined,
                        }}
                    >
                        {robotConnected ? "Robot Connected" : "Connect Robot"}
                    </Button>
                </motion.div>
            </div>

            {/* Status Indicator */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                style={statusContainerStyle}
            >
                <motion.div
                    animate={robotConnected ? {
                        scale: [1, 1.2, 1],
                        opacity: [1, 0.7, 1]
                    } : {}}
                    transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: "easeInOut"
                    }}
                    style={statusDotStyle}
                />
                <span style={{ textTransform: "uppercase", letterSpacing: "0.1em" }}>
                    {robotConnected ? "System Online" : "System Standby"}
                </span>
                {robotConnected && (
                    <Wifi style={{ width: 14, height: 14, color: "#22c55e" }} />
                )}
            </motion.div>
        </Card>
    );
}
