interface BaseBadgeProps { children: string; variant?: "blue" | "green" | "gray" }
export function BaseBadge({ children, variant = "blue" }: BaseBadgeProps) { return <span className={`rounded-full px-2 py-1 text-xs ${variant === "green" ? "bg-green-100 text-green-800" : variant === "gray" ? "bg-gray-100 text-gray-700" : "bg-blue-100 text-blue-800"}`}>{children}</span>; }
