import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { Target, TrendingUp, AlertTriangle, Lightbulb } from "lucide-react";

interface AIInsightCardProps {
  type: 'market' | 'competitor' | 'risk' | 'opportunity';
  content: string;
  confidence: number;
  delay?: number;
}

export function AIInsightCard({ type, content, confidence, delay = 0 }: AIInsightCardProps) {
  const getConfig = () => {
    switch (type) {
      case 'market': return { icon: TrendingUp, color: 'text-blue-400', bg: 'bg-blue-400/10', border: 'border-blue-400/20' };
      case 'competitor': return { icon: Target, color: 'text-violet-400', bg: 'bg-violet-400/10', border: 'border-violet-400/20' };
      case 'risk': return { icon: AlertTriangle, color: 'text-rose-400', bg: 'bg-rose-400/10', border: 'border-rose-400/20' };
      case 'opportunity': return { icon: Lightbulb, color: 'text-emerald-400', bg: 'bg-emerald-400/10', border: 'border-emerald-400/20' };
    }
  };

  const config = getConfig();
  const Icon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
    >
      <Card className={`bg-white/5 backdrop-blur-md border ${config.border}`}>
        <CardContent className="p-4 flex gap-4">
          <div className={`w-8 h-8 rounded-lg ${config.bg} ${config.color} flex items-center justify-center shrink-0`}>
            <Icon className="w-4 h-4" />
          </div>
          <div className="flex flex-col gap-2 flex-1">
            <p className="text-sm text-foreground/90 leading-relaxed">{content}</p>
            <div className="flex items-center justify-between mt-1">
              <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">{type}</span>
              <div className="flex items-center gap-1.5">
                <div className="w-16 h-1.5 bg-white/10 rounded-full overflow-hidden">
                  <div className={`h-full ${config.bg.replace('/10', '/50')}`} style={{ width: `${confidence}%` }} />
                </div>
                <span className="text-[10px] text-muted-foreground">{confidence}%</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}