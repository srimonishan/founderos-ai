import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowUpRight } from "lucide-react";

interface IdeaCardProps {
  title: string;
  category: string;
  score: number;
  status: 'analyzing' | 'ready' | 'processing';
  delay?: number;
}

export function IdeaCard({ title, category, score, status, delay = 0 }: IdeaCardProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'ready': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'analyzing': return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'processing': return 'bg-primary/20 text-primary border-primary/30';
      default: return 'bg-white/10 text-white border-white/20';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay }}
      whileHover={{ scale: 1.02 }}
      className="cursor-pointer"
      data-testid={`idea-card-${title.toLowerCase().replace(/\s+/g, '-')}`}
    >
      <Card className="bg-white/5 backdrop-blur-md border border-white/10 hover:border-primary/50 transition-colors">
        <CardContent className="p-4 flex items-center justify-between">
          <div className="flex flex-col gap-1 flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h4 className="font-medium text-foreground truncate">{title}</h4>
              <Badge variant="outline" className={`text-[10px] px-1.5 py-0 ${getStatusColor()}`}>
                {status.toUpperCase()}
              </Badge>
            </div>
            <span className="text-xs text-muted-foreground">{category}</span>
          </div>
          <div className="flex items-center gap-4 pl-4 border-l border-white/10 ml-4">
            <div className="flex flex-col items-end">
              <span className="text-[10px] text-muted-foreground font-medium uppercase tracking-wider">Score</span>
              <span className="text-lg font-bold text-foreground">{score}</span>
            </div>
            <ArrowUpRight className="w-4 h-4 text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}