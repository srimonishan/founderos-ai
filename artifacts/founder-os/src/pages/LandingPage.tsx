import { motion } from "framer-motion";
import { Link } from "wouter";
import { ArrowRight, Lightbulb, Target, ShieldAlert, BarChart, Presentation, Cpu, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Navbar } from "@/components/Navbar";
import { BackgroundOrbs } from "@/components/BackgroundOrbs";
import { FeatureCard } from "@/components/FeatureCard";

export default function LandingPage() {
  const features = [
    { title: "Idea Validation", description: "Instantly score your startup idea against market conditions and historical success patterns.", icon: <Lightbulb /> },
    { title: "Market Analysis", description: "Deep dive into TAM, SAM, SOM with real-time data aggregation and trend prediction.", icon: <BarChart /> },
    { title: "Competitor Intel", description: "Map out the competitive landscape, identify gaps, and find your unique wedge.", icon: <Target /> },
    { title: "Risk Assessment", description: "Identify technical, execution, and market risks before they become existential threats.", icon: <ShieldAlert /> },
    { title: "Revenue Modeling", description: "Generate dynamic financial models and unit economics based on industry benchmarks.", icon: <Cpu /> },
    { title: "Pitch Deck Generator", description: "Turn validated insights into a compelling, investor-ready narrative structure.", icon: <Presentation /> }
  ];

  return (
    <div className="min-h-[100dvh] relative overflow-hidden font-sans">
      <BackgroundOrbs />
      <Navbar />
      
      <main className="pt-32 pb-20">
        <section className="container mx-auto px-4 flex flex-col items-center text-center max-w-4xl">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-sm font-medium text-muted-foreground mb-8"
          >
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            System Online. AI Ready.
          </motion.div>
          
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6"
          >
            The Command Center for <br className="hidden md:block" />
            <span className="bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">Ambitious Founders</span>
          </motion.h1>
          
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-lg md:text-xl text-muted-foreground mb-10 max-w-2xl leading-relaxed"
          >
            Transform raw ideas into validated business intelligence. FounderOS AI provides military-grade analysis, competitive intel, and strategic planning—all powered by advanced AI.
          </motion.p>
          
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center gap-4"
          >
            <Link href="/dashboard">
              <Button size="lg" className="w-full sm:w-auto text-lg h-14 px-8 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold border border-primary-foreground/10 group" data-testid="button-launch-dashboard">
                Launch Dashboard
                <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
            <Button size="lg" variant="outline" className="w-full sm:w-auto text-lg h-14 px-8 bg-white/5 hover:bg-white/10 border-white/20" data-testid="button-see-demo">
              See Demo
            </Button>
          </motion.div>
        </section>

        <motion.section 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.8 }}
          className="container mx-auto px-4 mt-20"
        >
          <div className="w-full max-w-3xl mx-auto p-4 rounded-2xl bg-white/5 backdrop-blur-md border border-white/10 flex items-center justify-between overflow-hidden relative">
            <div className="absolute inset-0 bg-gradient-to-r from-primary/10 via-secondary/10 to-primary/10 animate-pulse" />
            <div className="relative z-10 flex flex-col md:flex-row items-center justify-between w-full gap-4 text-center md:text-left">
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-widest font-semibold">Live Telemetry</p>
                <p className="text-2xl font-mono font-bold text-foreground">12,847 <span className="text-sm font-sans text-muted-foreground font-normal">ideas analyzed today</span></p>
              </div>
              <div className="h-px w-full md:h-12 md:w-px bg-white/10" />
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-widest font-semibold">AI Confidence Average</p>
                <p className="text-2xl font-mono font-bold text-emerald-400">84.2%</p>
              </div>
              <div className="h-px w-full md:h-12 md:w-px bg-white/10" />
               <div>
                <p className="text-xs text-muted-foreground uppercase tracking-widest font-semibold">System Status</p>
                <p className="text-sm font-mono font-bold text-cyan-400 flex items-center justify-center md:justify-start gap-2">
                  <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                  OPTIMAL
                </p>
              </div>
            </div>
          </div>
        </motion.section>

        <section id="features" className="container mx-auto px-4 mt-32">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Intelligence at your fingertips</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">Equip yourself with the tools needed to outmaneuver the competition and build with conviction.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
            {features.map((feature, i) => (
              <FeatureCard key={feature.title} {...feature} delay={0.2 + (i * 0.1)} />
            ))}
          </div>
        </section>
      </main>
      
      <footer className="border-t border-white/10 bg-background/80 backdrop-blur-md py-12 mt-20">
        <div className="container mx-auto px-4 text-center text-muted-foreground text-sm flex flex-col items-center gap-4">
           <div className="flex items-center gap-2 opacity-50">
            <Zap className="w-4 h-4" />
            <span className="font-bold tracking-tight">FounderOS AI</span>
          </div>
          <p>© 2025 FounderOS AI. All systems operational.</p>
        </div>
      </footer>
    </div>
  );
}