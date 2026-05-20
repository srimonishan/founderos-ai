import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { ReactNode } from "react";

interface StatCardProps {
  title: string;
  value: string;
  icon: ReactNode;
  trend?: string;
  delay?: number;
}

export function StatCard({ title, value, icon, trend, delay = 0 }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, delay }}
    >
      <Card className="bg-white/5 backdrop-blur-md border border-white/10 overflow-hidden relative group">
        <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
        <CardContent className="p-5 flex items-center justify-between relative z-10">
          <div className="flex flex-col gap-1">
            <span className="text-sm font-medium text-muted-foreground">{title}</span>
            <div className="flex items-end gap-2">
              <span className="text-2xl font-bold tracking-tight text-foreground">{value}</span>
              {trend && <span className="text-xs font-medium text-emerald-400 mb-1">{trend}</span>}
            </div>
          </div>
          <div className="w-10 h-10 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-muted-foreground">
            {icon}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}