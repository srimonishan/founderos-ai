import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Loader2, Sparkles, CheckCircle2 } from "lucide-react";
import { BackgroundOrbs } from "@/components/BackgroundOrbs";
import { Sidebar } from "@/components/Sidebar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AIInsightCard } from "@/components/AIInsightCard";

const ideaSchema = z.object({
  title: z.string().min(3, "Title must be at least 3 characters"),
  category: z.string().min(1, "Please select a category"),
  description: z.string().min(20, "Description must be at least 20 characters"),
  targetMarket: z.string().min(5, "Target market is required"),
  problem: z.string().min(10, "Problem statement is required"),
});

type IdeaFormValues = z.infer<typeof ideaSchema>;

export default function IdeasPage() {
  const [analyzing, setAnalyzing] = useState(false);
  const [resultsReady, setResultsReady] = useState(false);

  const form = useForm<IdeaFormValues>({
    resolver: zodResolver(ideaSchema),
    defaultValues: {
      title: "",
      category: "",
      description: "",
      targetMarket: "",
      problem: "",
    },
  });

  const onSubmit = async (data: IdeaFormValues) => {
    setAnalyzing(true);
    // Simulate AI processing
    await new Promise(resolve => setTimeout(resolve, 3000));
    setAnalyzing(false);
    setResultsReady(true);
  };

  const mockInsights: Array<{ id: string, type: 'market' | 'competitor' | 'risk' | 'opportunity', content: string, confidence: number }> = [
    { id: "1", type: "opportunity", content: "High demand in selected target market with low AI penetration.", confidence: 89 },
    { id: "2", type: "competitor", content: "2 major incumbents exist but have low customer satisfaction scores.", confidence: 75 },
    { id: "3", type: "risk", content: "Customer acquisition cost might exceed LTV in early stages without viral loops.", confidence: 82 },
    { id: "4", type: "market", content: "TAM estimated at $4.2B, growing at 12% YoY.", confidence: 94 },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground flex">
      <BackgroundOrbs />
      <Sidebar />
      
      <main className="flex-1 ml-64 p-8 overflow-y-auto">
        <div className="max-w-4xl mx-auto">
          <header className="mb-10">
            <h1 className="text-3xl font-bold tracking-tight mb-2">Initialize New Venture</h1>
            <p className="text-muted-foreground">Submit your idea telemetry for deep neural analysis.</p>
          </header>

          <AnimatePresence mode="wait">
            {!resultsReady && !analyzing && (
              <motion.div
                key="form"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.4 }}
              >
                <Card className="bg-white/5 backdrop-blur-md border-white/10">
                  <CardContent className="p-8">
                    <Form {...form}>
                      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <FormField
                            control={form.control}
                            name="title"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel className="text-foreground/80">Project Codename</FormLabel>
                                <FormControl>
                                  <Input placeholder="e.g. FounderOS AI" className="bg-white/5 border-white/10 h-12 focus-visible:ring-primary/50" {...field} data-testid="input-title" />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                          <FormField
                            control={form.control}
                            name="category"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel className="text-foreground/80">Sector</FormLabel>
                                <Select onValueChange={field.onChange} defaultValue={field.value}>
                                  <FormControl>
                                    <SelectTrigger className="bg-white/5 border-white/10 h-12 focus:ring-primary/50" data-testid="select-category">
                                      <SelectValue placeholder="Select industry" />
                                    </SelectTrigger>
                                  </FormControl>
                                  <SelectContent className="bg-[#0a0a0f] border-white/10 text-foreground">
                                    <SelectItem value="saas">B2B SaaS</SelectItem>
                                    <SelectItem value="fintech">Fintech</SelectItem>
                                    <SelectItem value="healthtech">Healthtech</SelectItem>
                                    <SelectItem value="web3">Web3 / Crypto</SelectItem>
                                    <SelectItem value="ai">AI / Deep Tech</SelectItem>
                                  </SelectContent>
                                </Select>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                        </div>

                        <FormField
                          control={form.control}
                          name="description"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel className="text-foreground/80">Core Mechanic (How it works)</FormLabel>
                              <FormControl>
                                <Textarea 
                                  placeholder="Describe the core loop and value proposition..." 
                                  className="bg-white/5 border-white/10 min-h-[120px] resize-none focus-visible:ring-primary/50" 
                                  {...field} 
                                  data-testid="textarea-description"
                                />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                           <FormField
                            control={form.control}
                            name="problem"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel className="text-foreground/80">Problem Statement</FormLabel>
                                <FormControl>
                                  <Textarea 
                                    placeholder="What friction are you eliminating?" 
                                    className="bg-white/5 border-white/10 min-h-[100px] resize-none focus-visible:ring-primary/50" 
                                    {...field} 
                                    data-testid="textarea-problem"
                                  />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                          <FormField
                            control={form.control}
                            name="targetMarket"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel className="text-foreground/80">Target Demographic</FormLabel>
                                <FormControl>
                                  <Textarea 
                                    placeholder="Who feels this pain the most?" 
                                    className="bg-white/5 border-white/10 min-h-[100px] resize-none focus-visible:ring-primary/50" 
                                    {...field} 
                                    data-testid="textarea-target-market"
                                  />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                        </div>

                        <Button 
                          type="submit" 
                          className="w-full h-14 text-lg font-semibold bg-primary hover:bg-primary/90 text-primary-foreground border border-primary-foreground/10 group mt-4"
                          data-testid="button-analyze"
                        >
                          <Sparkles className="w-5 h-5 mr-2 text-cyan-300 group-hover:animate-pulse" />
                          Execute Neural Analysis
                        </Button>
                      </form>
                    </Form>
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {analyzing && (
              <motion.div
                key="analyzing"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center justify-center py-32"
              >
                <div className="relative">
                  <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full" />
                  <Loader2 className="w-16 h-16 text-primary animate-spin relative z-10" />
                </div>
                <h3 className="mt-8 text-2xl font-bold bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">Processing Data Matrix...</h3>
                <p className="mt-2 text-muted-foreground animate-pulse">Cross-referencing market dynamics</p>
              </motion.div>
            )}

            {resultsReady && (
              <motion.div
                key="results"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-8"
              >
                <Card className="bg-emerald-500/10 border-emerald-500/30 overflow-hidden relative">
                  <div className="absolute top-0 right-0 p-8 opacity-10">
                    <CheckCircle2 className="w-48 h-48 text-emerald-400" />
                  </div>
                  <CardContent className="p-8 relative z-10">
                    <h2 className="text-3xl font-bold text-emerald-400 mb-2">Analysis Complete</h2>
                    <p className="text-foreground/80 text-lg mb-6">Overall Viability Score: <span className="font-bold text-white text-2xl">84/100</span></p>
                    <div className="flex gap-4">
                       <Button variant="outline" className="bg-white/5 border-white/20 hover:bg-white/10" onClick={() => setResultsReady(false)} data-testid="button-new-analysis">
                        Run New Analysis
                      </Button>
                      <Button className="bg-emerald-500 hover:bg-emerald-600 text-white border-none" data-testid="button-save-project">
                        Save to Dashboard
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                <div>
                  <h3 className="text-xl font-semibold mb-6 flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-primary" />
                    Neural Insights
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {mockInsights.map((insight, i) => (
                      <AIInsightCard key={insight.id} {...insight} delay={0.1 * i} />
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}