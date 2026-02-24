"use client";

import { useState, useEffect, CSSProperties } from "react";
import { Cpu, Zap, Brain, Crown, Sparkles, LucideIcon } from "lucide-react";
import { Modal, Button, Slider } from "@/components/ui";
import { motion } from "framer-motion";
import { BACKEND_API } from "@/lib/socket";

interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
}

interface SkillLevel {
    min: number;
    max: number;
    label: string;
    icon: LucideIcon;
    color: string;
    bg: string;
    border: string;
}

const skillLevels: SkillLevel[] = [
    { min: 1350, max: 1499, label: "Beginner", icon: Sparkles, color: "#4ade80", bg: "rgba(34, 197, 94, 0.1)", border: "rgba(34, 197, 94, 0.2)" },
    { min: 1500, max: 1799, label: "Intermediate", icon: Zap, color: "#60a5fa", bg: "rgba(59, 130, 246, 0.1)", border: "rgba(59, 130, 246, 0.2)" },
    { min: 1800, max: 2199, label: "Advanced", icon: Brain, color: "#c084fc", bg: "rgba(168, 85, 247, 0.1)", border: "rgba(168, 85, 247, 0.2)" },
    { min: 2200, max: 2599, label: "Expert", icon: Cpu, color: "#fb923c", bg: "rgba(249, 115, 22, 0.1)", border: "rgba(249, 115, 22, 0.2)" },
    { min: 2600, max: 3200, label: "Grandmaster", icon: Crown, color: "#fbbf24", bg: "rgba(245, 158, 11, 0.1)", border: "rgba(245, 158, 11, 0.2)" },
];

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
    const [elo, setElo] = useState(2000);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        if (isOpen) {
            fetch(`${BACKEND_API}/api/settings`)
                .then(res => res.json())
                .then(data => {
                    if (data.elo) setElo(data.elo);
                })
                .catch(err => console.error("Failed to fetch settings", err));
        }
    }, [isOpen]);

    const handleSave = async () => {
        setIsLoading(true);
        try {
            await fetch(`${BACKEND_API}/api/settings`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ elo })
            });
            onClose();
        } catch (e) {
            console.error("Failed to save settings", e);
        } finally {
            setIsLoading(false);
        }
    };

    const getCurrentSkill = () => {
        return skillLevels.find(s => elo >= s.min && elo <= s.max) || skillLevels[2];
    };

    const currentSkill = getCurrentSkill();
    const SkillIcon = currentSkill.icon;

    const titleStyle: CSSProperties = {
        display: "flex",
        alignItems: "center",
        gap: "12px",
    };

    const titleIconStyle: CSSProperties = {
        width: 36,
        height: 36,
        borderRadius: "10px",
        background: "linear-gradient(to bottom right, #f59e0b, #ea580c)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        boxShadow: "0 10px 15px -3px rgba(245, 158, 11, 0.2)",
        flexShrink: 0,
    };

    const skillIndicatorStyle: CSSProperties = {
        padding: "12px",
        borderRadius: "12px",
        border: `1px solid ${currentSkill.border}`,
        background: currentSkill.bg,
        display: "flex",
        alignItems: "center",
        gap: "12px",
    };

    const skillIconBoxStyle: CSSProperties = {
        width: 40,
        height: 40,
        borderRadius: "10px",
        background: currentSkill.bg,
        border: `1px solid ${currentSkill.border}`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
    };

    const eloDisplayStyle: CSSProperties = {
        fontSize: "24px",
        fontWeight: 900,
        background: "linear-gradient(135deg, #fbbf24, #f59e0b, #d97706)",
        WebkitBackgroundClip: "text",
        WebkitTextFillColor: "transparent",
        backgroundClip: "text",
    };

    const pillStyle = (isActive: boolean, skill: SkillLevel): CSSProperties => ({
        padding: "6px 12px",
        borderRadius: "9999px",
        fontSize: "12px",
        fontWeight: 500,
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        cursor: "pointer",
        transition: "all 0.2s",
        background: isActive ? skill.bg : "rgba(255, 255, 255, 0.05)",
        color: isActive ? skill.color : "#6b7280",
        border: `1px solid ${isActive ? skill.border : "rgba(255, 255, 255, 0.05)"}`,
    });

    const infoBoxStyle: CSSProperties = {
        position: "relative",
        overflow: "hidden",
        borderRadius: "12px",
        background: "linear-gradient(to bottom right, rgba(59, 130, 246, 0.1), rgba(168, 85, 247, 0.05))",
        border: "1px solid rgba(59, 130, 246, 0.2)",
        padding: "12px",
    };

    const infoIconStyle: CSSProperties = {
        width: 32,
        height: 32,
        borderRadius: "8px",
        background: "rgba(59, 130, 246, 0.2)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
    };

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            size="md"
            title={
                <div style={titleStyle}>
                    <div style={titleIconStyle}>
                        <Cpu style={{ width: 20, height: 20, color: "white" }} />
                    </div>
                    <div>
                        <h2 style={{ fontSize: "18px", fontWeight: "bold" }}>Engine Settings</h2>
                        <p style={{ fontSize: "12px", color: "#6b7280" }}>Configure Stockfish difficulty</p>
                    </div>
                </div>
            }
            footer={
                <>
                    <Button variant="ghost" onClick={onClose}>
                        Cancel
                    </Button>
                    <Button
                        variant="primary"
                        onClick={handleSave}
                        isLoading={isLoading}
                    >
                        Save Changes
                    </Button>
                </>
            }
        >
            <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                {/* Skill Level Indicator */}
                <motion.div
                    key={currentSkill.label}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    style={skillIndicatorStyle}
                >
                    <div style={skillIconBoxStyle}>
                        <SkillIcon style={{ width: 24, height: 24, color: currentSkill.color }} />
                    </div>
                    <div style={{ flex: 1 }}>
                        <div style={{ fontSize: "14px", fontWeight: "bold", color: currentSkill.color }}>
                            {currentSkill.label}
                        </div>
                        <div style={{ fontSize: "12px", color: "#6b7280" }}>
                            ELO Range: {currentSkill.min} - {currentSkill.max}
                        </div>
                    </div>
                    <div style={{ textAlign: "right" }}>
                        <div style={eloDisplayStyle}>
                            {elo}
                        </div>
                        <div style={{ fontSize: "10px", color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.1em" }}>
                            Current ELO
                        </div>
                    </div>
                </motion.div>

                {/* ELO Slider */}
                <Slider
                    value={elo}
                    onChange={setElo}
                    min={1350}
                    max={3200}
                    step={50}
                    label="Stockfish Strength"
                    showValue={false}
                />

                {/* Skill Level Pills */}
                <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                    {skillLevels.map((skill) => {
                        const isActive = elo >= skill.min && elo <= skill.max;
                        const Icon = skill.icon;
                        return (
                            <motion.button
                                key={skill.label}
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={() => setElo(Math.floor((skill.min + skill.max) / 2))}
                                style={pillStyle(isActive, skill)}
                            >
                                <Icon style={{ width: 12, height: 12 }} />
                                {skill.label}
                            </motion.button>
                        );
                    })}
                </div>

                {/* Info Box */}
                <div style={infoBoxStyle}>
                    <div style={{ position: "absolute", top: 0, right: 0, width: 80, height: 80, background: "rgba(59, 130, 246, 0.1)", borderRadius: "9999px", filter: "blur(32px)" }} />
                    <div style={{ position: "relative", display: "flex", gap: "12px" }}>
                        <div style={infoIconStyle}>
                            <Zap style={{ width: 16, height: 16, color: "#60a5fa" }} />
                        </div>
                        <div>
                            <p style={{ fontSize: "14px", fontWeight: 500, color: "#93c5fd", marginBottom: "4px" }}>Pro Tip</p>
                            <p style={{ fontSize: "12px", color: "#9ca3af", lineHeight: 1.6 }}>
                                Higher ELO settings make Stockfish play stronger moves with longer thinking time.
                                Start lower to practice and gradually increase as you improve.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </Modal>
    );
}
