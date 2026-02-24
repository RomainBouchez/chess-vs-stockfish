"use client";

import { ReactNode, useEffect, CSSProperties } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";

interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    title?: ReactNode;
    children: ReactNode;
    footer?: ReactNode;
    size?: "sm" | "md" | "lg" | "xl";
    showCloseButton?: boolean;
}

const sizeWidths: Record<string, string> = {
    sm: "384px",
    md: "448px",
    lg: "512px",
    xl: "576px"
};

const overlayStyle: CSSProperties = {
    position: "fixed",
    inset: 0,
    zIndex: 50,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "16px",
};

const backdropStyle: CSSProperties = {
    position: "absolute",
    inset: 0,
    background: "rgba(0, 0, 0, 0.7)",
    backdropFilter: "blur(8px)",
    WebkitBackdropFilter: "blur(8px)",
};

const headerStyle: CSSProperties = {
    padding: "16px 20px",
    borderBottom: "1px solid rgba(255, 255, 255, 0.05)",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    background: "rgba(255, 255, 255, 0.02)",
    flexShrink: 0,
};

const closeButtonStyle: CSSProperties = {
    width: 32,
    height: 32,
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "#9ca3af",
    background: "rgba(255, 255, 255, 0.05)",
    border: "none",
    cursor: "pointer",
    transition: "all 0.2s",
};

const bodyStyle: CSSProperties = {
    padding: "20px",
    overflowY: "auto",
    flex: 1,
    minHeight: 0,
};

const footerStyle: CSSProperties = {
    padding: "12px 20px",
    borderTop: "1px solid rgba(255, 255, 255, 0.05)",
    background: "rgba(0, 0, 0, 0.2)",
    display: "flex",
    alignItems: "center",
    justifyContent: "flex-end",
    gap: "12px",
    flexShrink: 0,
};

const glowLineStyle: CSSProperties = {
    position: "absolute",
    top: 0,
    left: "50%",
    transform: "translateX(-50%)",
    width: "75%",
    height: "1px",
    background: "linear-gradient(to right, transparent, rgba(245, 158, 11, 0.5), transparent)",
};

export default function Modal({
    isOpen,
    onClose,
    title,
    children,
    footer,
    size = "md",
    showCloseButton = true
}: ModalProps) {
    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === "Escape") onClose();
        };

        if (isOpen) {
            document.addEventListener("keydown", handleEscape);
            document.body.style.overflow = "hidden";
        }

        return () => {
            document.removeEventListener("keydown", handleEscape);
            document.body.style.overflow = "unset";
        };
    }, [isOpen, onClose]);

    const modalContainerStyle: CSSProperties = {
        width: "100%",
        maxWidth: sizeWidths[size],
        maxHeight: "calc(100vh - 32px)",
        background: "linear-gradient(to bottom, #1a1a2e, #16162a)",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        borderRadius: "24px",
        boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
        overflow: "hidden",
        position: "relative",
        zIndex: 10,
        display: "flex",
        flexDirection: "column",
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <div style={overlayStyle}>
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        onClick={onClose}
                        style={backdropStyle}
                    />

                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        transition={{ type: "spring", stiffness: 300, damping: 25 }}
                        style={modalContainerStyle}
                    >
                        <div style={glowLineStyle} />

                        {(title || showCloseButton) && (
                            <div style={headerStyle}>
                                {title && (
                                    <div style={{ fontSize: "20px", fontWeight: "bold", color: "white" }}>
                                        {title}
                                    </div>
                                )}
                                {showCloseButton && (
                                    <motion.button
                                        whileHover={{ scale: 1.1, rotate: 90, background: "rgba(255,255,255,0.1)" }}
                                        whileTap={{ scale: 0.9 }}
                                        onClick={onClose}
                                        style={closeButtonStyle}
                                    >
                                        <X size={18} />
                                    </motion.button>
                                )}
                            </div>
                        )}

                        <div style={bodyStyle}>
                            {children}
                        </div>

                        {footer && (
                            <div style={footerStyle}>
                                {footer}
                            </div>
                        )}
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
}

export { Modal };
export type { ModalProps };
