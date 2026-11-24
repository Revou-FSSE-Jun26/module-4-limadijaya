"use client";
import { useEffect, useState } from "react";
import { apiClient } from "@/lib/apiClient";
import { useAuth } from "@/context/AuthContext";
export interface Notification { id: string; message: string; is_read: boolean }
export function useNotifications() { const { token } = useAuth(); const [notifications, setNotifications] = useState<Notification[]>([]); useEffect(() => { if (!token) return; const load = () => apiClient<Notification[]>("/notifications", {}, token).then(setNotifications).catch(() => undefined); load(); const timer = window.setInterval(load, 30000); return () => window.clearInterval(timer); }, [token]); return { notifications, unreadCount: notifications.filter(item => !item.is_read).length }; }
