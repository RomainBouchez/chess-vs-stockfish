"use client";

import { CSSProperties } from "react";
import { Settings, RefreshCw, Bot, Gamepad2, Wifi, Home } from "lucide-react";
import { Button, Card } from "@/components/ui";
import { motion } from "framer-motion";

interface GameControlsProps {
    onReset: () => void;
    onOpenSettings: () => void;
    onHoming: () => void;
    onRecover: () => void;
    robotConnected: boolean;
}

export default function GameControls({ onReset, onOpenSettings, onHoming, onRecover, robotConnected }: GameControlsProps) {
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

    const robotIndicatorStyle: CSSProperties = {
        display: "flex",
        alignItems: "center",
        gap: "12px",
        padding: "12px 16px",
        borderRadius: "12px",
        border: `1px solid ${robotConnected ? "rgba(34, 197, 94, 0.3)" : "rgba(255, 255, 255, 0.06)"}`,
        background: robotConnected ? "rgba(34, 197, 94, 0.08)" : "rgba(255, 255, 255, 0.03)",
        transition: "all 0.5s",
        cursor: "default",
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

                {/* Robot Status + Homing */}
                <div style={{ display: "flex", gap: "8px", alignItems: "stretch" }}>
                    <motion.div
                        animate={robotConnected ? { scale: [1, 1.02, 1] } : {}}
                        transition={{ duration: 0.3 }}
                        style={{ ...robotIndicatorStyle, flex: 1 }}
                    >
                        <motion.div
                            animate={robotConnected ? { scale: [1, 1.15, 1], opacity: [1, 0.7, 1] } : {}}
                            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                            style={statusDotStyle}
                        />
                        {robotConnected
                            ? <Wifi style={{ width: 18, height: 18, color: "#4ade80" }} />
                            : <Bot style={{ width: 18, height: 18, color: "#4b5563" }} />
                        }
                        <span style={{ fontSize: "14px", fontWeight: 600, color: robotConnected ? "#4ade80" : "#4b5563" }}>
                            {robotConnected ? "Robot Connected" : "Robot Offline"}
                        </span>
                    </motion.div>
                    <Button
                        onClick={onHoming}
                        variant="secondary"
                        size="lg"
                        disabled={!robotConnected}
                        title="Homing (G28)"
                        style={{
                            padding: "0 14px",
                            opacity: robotConnected ? 1 : 0.4,
                            cursor: robotConnected ? "pointer" : "not-allowed",
                        }}
                    >
                        <Home style={{ width: 18, height: 18 }} />
                    </Button>
                    <Button
                        onClick={onRecover}
                        variant="secondary"
                        size="lg"
                        disabled={!robotConnected}
                        title="Récupérer le robot bloqué (M999)"
                        style={{
                            padding: "0 14px",
                            opacity: robotConnected ? 1 : 0.4,
                            cursor: robotConnected ? "pointer" : "not-allowed",
                        }}
                    >
                        <RefreshCw style={{ width: 18, height: 18 }} />
                    </Button>
                </div>
            </div>

            {/* Status Footer */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                style={statusContainerStyle}
            >
                <motion.div
                    animate={robotConnected ? { scale: [1, 1.2, 1], opacity: [1, 0.7, 1] } : {}}
                    transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
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
