import { useEffect } from "react";
import { useLocation } from "wouter";
import { motion } from "framer-motion";
import { Zap, Chrome } from "lucide-react";
import { Button } from "@/components/ui/button";
import { BackgroundOrbs } from "@/components/BackgroundOrbs";
import { useAuth } from "@/contexts/AuthContext";

export default function LoginPage() {
  const { session, loading, signInWithGoogle } = useAuth();
  const [, setLocation] = useLocation();

  useEffect(() => {
    if (!loading && session) {
      setLocation("/dashboard");
    }
  }, [session, loading, setLocation]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background relative overflow-hidden">
      <BackgroundOrbs />

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="relative z-10 w-full max-w-md mx-4"
      >
        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-8 shadow-2xl">
          <div className="flex flex-col items-center gap-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center border border-primary/30">
                <Zap className="w-5 h-5 text-primary" />
              </div>
              <span className="text-2xl font-bold tracking-tight bg-gradient-to-r from-white to-white/70 bg-clip-text text-transparent">
                FounderOS AI
              </span>
            </div>

            <div className="text-center">
              <h1 className="text-xl font-semibold text-foreground mb-2">
                Welcome back
              </h1>
              <p className="text-sm text-muted-foreground">
                Sign in to access your startup mission control
              </p>
            </div>

            <div className="w-full h-px bg-white/10" />

            <Button
              onClick={signInWithGoogle}
              variant="outline"
              size="lg"
              className="w-full gap-3 bg-white/5 border-white/15 hover:bg-white/10 hover:border-white/25 text-foreground font-medium transition-all duration-200 h-12"
              data-testid="button-google-signin"
            >
              <Chrome className="w-5 h-5" />
              Continue with Google
            </Button>

            <p className="text-xs text-muted-foreground text-center">
              By continuing, you agree to our Terms of Service and Privacy Policy.
            </p>
          </div>
        </div>

        <p className="text-center text-xs text-muted-foreground mt-6">
          New to FounderOS? Your account is created automatically on first sign-in.
        </p>
      </motion.div>
    </div>
  );
}
