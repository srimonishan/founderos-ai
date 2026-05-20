import { motion } from "framer-motion";
import { BackgroundOrbs } from "@/components/BackgroundOrbs";
import { Sidebar } from "@/components/Sidebar";
import { StatCard } from "@/components/StatCard";
import { IdeaCard } from "@/components/IdeaCard";
import { AIInsightCard } from "@/components/AIInsightCard";
import { Lightbulb, Target, ShieldAlert, BarChart } from "lucide-react";

export default function DashboardPage() {
  const stats = [
    { title: "Ideas Analyzed", value: "142", trend: "+12%", icon: <Lightbulb /> },
    { title: "Avg Success Score", value: "76.4", trend: "+4.1", icon: <Target /> },
    { title: "Market Opportunities", value: "24", trend: "+3", icon: <BarChart /> },
    { title: "Risk Factors Mitigated", value: "89", trend: "+14", icon: <ShieldAlert /> }
  ];

  const recentIdeas: Array<{ id: string, title: string, category: string, score: number, status: 'analyzing' | 'ready' | 'processing' }> = [
    { id: "1", title: "AI-Powered CRM for Dentists", category: "B2B SaaS", score: 82, status: "ready" },
    { id: "2", title: "Decentralized Energy Grid", category: "Web3/Infrastructure", score: 0, status: "analyzing" },
    { id: "3", title: "Autonomous Drone Delivery", category: "Logistics", score: 94, status: "ready" },
    { id: "4", title: "Synthetic Biology Platform", category: "Deep Tech", score: 45, status: "processing" },
  ];

  const recentInsights: Array<{ id: string, type: 'market' | 'competitor' | 'risk' | 'opportunity', content: string, confidence: number }> = [
    { id: "1", type: "market", content: "Dental CRM market is expected to grow at 14% CAGR, reaching $3.2B by 2028. High fragmentation presents consolidation opportunity.", confidence: 92 },
    { id: "2", type: "competitor", content: "Incumbents suffer from poor UX and lack of AI integration. Dentrix holds 40% market share but relies on legacy tech stack.", confidence: 88 },
    { id: "3", type: "risk", content: "Regulatory compliance (HIPAA) poses significant go-to-market barrier for AI features processing patient data.", confidence: 95 },
    { id: "4", type: "opportunity", content: "Automated billing and insurance claim reconciliation could reduce practice overhead by 30%.", confidence: 78 },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground flex">
      <BackgroundOrbs />
      <Sidebar />
      
      <main className="flex-1 ml-64 p-8 overflow-y-auto">
        <div className="max-w-6xl mx-auto">
          <header className="mb-10 flex items-center justify-between">
            <div>
              <motion.h1 
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-3xl font-bold tracking-tight mb-2"
              >
                Welcome back, Founder
              </motion.h1>
              <motion.p 
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="text-muted-foreground"
              >
                System telemetry optimal. 3 new insights generated since last login.
              </motion.p>
            </div>
            
            <motion.div 
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 }}
              className="flex items-center gap-3 px-4 py-2 rounded-lg bg-primary/10 border border-primary/20 text-primary"
            >
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-primary"></span>
              </span>
              <span className="text-sm font-medium">AI Agent Processing</span>
            </motion.div>
          </header>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
            {stats.map((stat, i) => (
              <StatCard key={stat.title} {...stat} delay={0.1 * i} />
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold">Active Ventures</h2>
              </div>
              <div className="grid gap-4">
                {recentIdeas.map((idea, i) => (
                  <IdeaCard key={idea.id} {...idea} delay={0.2 + (0.05 * i)} />
                ))}
              </div>
            </div>

            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold">Strategic Intel</h2>
              </div>
              <div className="grid gap-4">
                {recentInsights.map((insight, i) => (
                  <AIInsightCard key={insight.id} {...insight} delay={0.3 + (0.05 * i)} />
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}