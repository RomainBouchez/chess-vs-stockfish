"use client";

import { ReactNode, CSSProperties } from "react";
import { motion } from "framer-motion";

type CardVariant = "default" | "elevated" | "outlined" | "gradient";

interface CardProps {
    variant?: CardVariant;
    children: ReactNode;
    noPadding?: boolean;
    className?: string;
    style?: CSSProperties;
}

const variantStyles: Record<CardVariant, CSSProperties> = {
    default: {
        background: "rgba(255, 255, 255, 0.05)",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
    },
    elevated: {
        background: "linear-gradient(to bottom right, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05))",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
    },
    outlined: {
        background: "transparent",
        border: "2px solid rgba(255, 255, 255, 0.2)",
        backdropFilter: "blur(4px)",
        WebkitBackdropFilter: "blur(4px)",
    },
    gradient: {
        background: "linear-gradient(to bottom right, rgba(245, 158, 11, 0.1), rgba(234, 88, 12, 0.05), transparent)",
        border: "1px solid rgba(245, 158, 11, 0.2)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
    },
};

export default function Card({
    variant = "default",
    children,
    noPadding = false,
    className = "",
    style,
}: CardProps) {
    const baseStyle: CSSProperties = {
        borderRadius: "16px",
        padding: noPadding ? 0 : "24px",
        ...variantStyles[variant],
        ...style,
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className={className}
            style={baseStyle}
        >
            {children}
        </motion.div>
    );
}

export { Card };
export type { CardProps, CardVariant };
