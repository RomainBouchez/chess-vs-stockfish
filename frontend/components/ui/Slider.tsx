"use client";

import { CSSProperties } from "react";
import { motion } from "framer-motion";

interface SliderProps {
    value: number;
    onChange: (value: number) => void;
    min: number;
    max: number;
    step?: number;
    label?: string;
    showValue?: boolean;
    valueFormatter?: (value: number) => string;
    description?: string;
}

export default function Slider({
    value,
    onChange,
    min,
    max,
    step = 1,
    label,
    showValue = true,
    valueFormatter = (v) => v.toString(),
    description
}: SliderProps) {
    const percentage = ((value - min) / (max - min)) * 100;

    const containerStyle: CSSProperties = {
        display: "flex",
        flexDirection: "column",
        gap: "16px",
    };

    const headerStyle: CSSProperties = {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-end",
    };

    const labelStyle: CSSProperties = {
        fontSize: "14px",
        fontWeight: 500,
        color: "#d1d5db",
    };

    const valueStyle: CSSProperties = {
        fontSize: "30px",
        fontWeight: 700,
        background: "linear-gradient(to right, #fbbf24, #f97316)",
        WebkitBackgroundClip: "text",
        WebkitTextFillColor: "transparent",
        backgroundClip: "text",
    };

    const descriptionStyle: CSSProperties = {
        fontSize: "12px",
        color: "#6b7280",
        marginTop: "2px",
    };

    const trackContainerStyle: CSSProperties = {
        position: "relative",
        height: "12px",
    };

    const trackBackgroundStyle: CSSProperties = {
        position: "absolute",
        inset: 0,
        background: "rgba(255, 255, 255, 0.1)",
        borderRadius: "9999px",
        overflow: "hidden",
    };

    const filledTrackStyle: CSSProperties = {
        height: "100%",
        background: "linear-gradient(to right, #f59e0b, #f97316)",
        borderRadius: "9999px 9999px",
        position: "relative",
    };

    const glowStyle: CSSProperties = {
        position: "absolute",
        right: 0,
        top: "50%",
        transform: "translateY(-50%)",
        width: "16px",
        height: "16px",
        background: "rgba(251, 191, 36, 0.5)",
        borderRadius: "9999px",
        filter: "blur(8px)",
    };

    const inputStyle: CSSProperties = {
        position: "absolute",
        inset: 0,
        width: "100%",
        height: "100%",
        opacity: 0,
        cursor: "pointer",
        zIndex: 10,
    };

    const thumbStyle: CSSProperties = {
        position: "absolute",
        top: "-50%",
        left: `${percentage}%`,
        transform: "translate(-50%, -50%)",
        width: "30px",
        height: "20px",
        pointerEvents: "none",
    };

    const thumbInnerStyle: CSSProperties = {
        width: "100%",
        height: "100%",
        background: "white",
        borderRadius: "9999px",
        boxShadow: "0 4px 6px -1px rgba(245, 158, 11, 0.3)",
        border: "2px solid #f59e0b",
        transition: "transform 0.2s",
    };

    const labelsStyle: CSSProperties = {
        display: "flex",
        justifyContent: "space-between",
        fontSize: "12px",
        color: "#6b7280",
        fontFamily: "monospace",
        padding: "0 4px",
    };

    return (
        <div style={containerStyle}>
            {(label || showValue) && (
                <div style={headerStyle}>
                    {label && <label style={labelStyle}>{label}</label>}
                    {showValue && (
                        <div style={{ textAlign: "right" }}>
                            <motion.span
                                key={value}
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                style={valueStyle}
                            >
                                {valueFormatter(value)}
                            </motion.span>
                            {description && (
                                <motion.div
                                    key={description}
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    style={descriptionStyle}
                                >
                                    {description}
                                </motion.div>
                            )}
                        </div>
                    )}
                </div>
            )}

            <div style={trackContainerStyle}>
                <div style={trackBackgroundStyle}>
                    <motion.div
                        style={filledTrackStyle}
                        initial={{ width: 0 }}
                        animate={{ width: `calc(${percentage}% + 10px)` }}
                        transition={{ type: "spring", stiffness: 2800, damping: 40 }}
                    >
                        <div style={glowStyle} />
                    </motion.div>
                </div>

                <input
                    type="range"
                    min={min}
                    max={max}
                    step={step}
                    value={value}
                    onChange={(e) => onChange(Number(e.target.value))}
                    style={inputStyle}
                />

                <motion.div
                    style={thumbStyle}
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                >
                    <div style={thumbInnerStyle} />
                </motion.div>
            </div>

            <div style={labelsStyle}>
                <span>{valueFormatter(min)}</span>
                <span>{valueFormatter(max)}</span>
            </div>
        </div>
    );
}

export { Slider };
export type { SliderProps };
