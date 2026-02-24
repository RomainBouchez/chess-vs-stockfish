"use client";

import { io } from "socket.io-client";

// Use current page hostname for LAN support (QR codes point to LAN IP)
const BACKEND_URL = typeof window !== "undefined"
    ? `http://${window.location.hostname}:8000`
    : "http://localhost:8000";

export const BACKEND_API = BACKEND_URL;

export const socket = io(BACKEND_URL, {
    autoConnect: true,
    transports: ["websocket"],
});
