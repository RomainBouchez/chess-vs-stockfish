"use client";

import { forwardRef, ReactNode, CSSProperties } from "react";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger" | "success" | "outline";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps {
    variant?: ButtonVariant;
    size?: ButtonSize;
    isLoading?: boolean;
    leftIcon?: ReactNode;
    rightIcon?: ReactNode;
    children: ReactNode;
    onClick?: () => void;
    disabled?: boolean;
    style?: CSSProperties;
    className?: string;
    type?: "button" | "submit" | "reset";
}

const variantStyles: Record<ButtonVariant, CSSProperties> = {
    primary: {
        background: "linear-gradient(to right, #f59e0b, #ea580c, #f59e0b)",
        color: "white",
        fontWeight: 600,
        boxShadow: "0 10px 15px -3px rgba(245, 158, 11, 0.25)",
        border: "1px solid rgba(251, 191, 36, 0.2)",
    },
    secondary: {
        background: "rgba(255, 255, 255, 0.05)",
        color: "#d1d5db",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        backdropFilter: "blur(4px)",
    },
    ghost: {
        background: "transparent",
        color: "#9ca3af",
        border: "1px solid transparent",
    },
    danger: {
        background: "linear-gradient(to right, #dc2626, #e11d48)",
        color: "white",
        fontWeight: 600,
        boxShadow: "0 10px 15px -3px rgba(239, 68, 68, 0.25)",
        border: "1px solid rgba(248, 113, 113, 0.2)",
    },
    success: {
        background: "linear-gradient(to right, #059669, #16a34a)",
        color: "white",
        fontWeight: 600,
        boxShadow: "0 10px 15px -3px rgba(16, 185, 129, 0.25)",
        border: "1px solid rgba(52, 211, 153, 0.2)",
    },
    outline: {
        background: "transparent",
        color: "#f59e0b",
        border: "2px solid rgba(245, 158, 11, 0.5)",
    },
};

const sizeStyles: Record<ButtonSize, CSSProperties> = {
    sm: { padding: "6px 12px", fontSize: "14px", borderRadius: "8px", gap: "6px" },
    md: { padding: "10px 16px", fontSize: "14px", borderRadius: "12px", gap: "8px" },
    lg: { padding: "14px 24px", fontSize: "16px", borderRadius: "12px", gap: "10px" },
};

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
    (
        {
            variant = "primary",
            size = "md",
            isLoading = false,
            leftIcon,
            rightIcon,
            children,
            className = "",
            disabled,
            style,
            onClick,
            type = "button",
        },
        ref
    ) => {
        const baseStyle: CSSProperties = {
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: 500,
            transition: "all 0.3s ease-out",
            cursor: disabled || isLoading ? "not-allowed" : "pointer",
            opacity: disabled || isLoading ? 0.5 : 1,
            ...variantStyles[variant],
            ...sizeStyles[size],
            ...style,
        };

        return (
            <motion.button
                ref={ref}
                type={type}
                whileHover={!disabled && !isLoading ? { scale: 1.02 } : {}}
                whileTap={!disabled && !isLoading ? { scale: 0.98 } : {}}
                transition={{ type: "spring", stiffness: 400, damping: 17 }}
                disabled={disabled || isLoading}
                onClick={onClick}
                className={className}
                style={baseStyle}
            >
                {isLoading ? (
                    <>
                        <Loader2 style={{ width: 16, height: 16, animation: "spin 1s linear infinite" }} />
                        <span>Loading...</span>
                    </>
                ) : (
                    <>
                        {leftIcon && <span style={{ flexShrink: 0 }}>{leftIcon}</span>}
                        {children}
                        {rightIcon && <span style={{ flexShrink: 0 }}>{rightIcon}</span>}
                    </>
                )}
            </motion.button>
        );
    }
);

Button.displayName = "Button";

export default Button;
export { Button };
export type { ButtonProps, ButtonVariant, ButtonSize };
