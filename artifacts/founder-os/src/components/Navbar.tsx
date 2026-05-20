import { Link } from "wouter";
import { Zap } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Navbar() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-background/50 backdrop-blur-md border-b border-white/10">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group" data-testid="link-home">
          <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center border border-primary/30 group-hover:border-primary/50 transition-colors">
            <Zap className="w-4 h-4 text-primary" />
          </div>
          <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white to-white/70 bg-clip-text text-transparent">FounderOS AI</span>
        </Link>
        <div className="flex items-center gap-6">
          <div className="hidden md:flex items-center gap-6 text-sm text-muted-foreground">
            <Link href="/#features" className="hover:text-foreground transition-colors" data-testid="link-features">Features</Link>
            <Link href="/#pricing" className="hover:text-foreground transition-colors" data-testid="link-pricing">Pricing</Link>
            <Link href="/#about" className="hover:text-foreground transition-colors" data-testid="link-about">About</Link>
          </div>
          <Link href="/dashboard" data-testid="link-get-started">
            <Button className="bg-primary hover:bg-primary/90 text-primary-foreground font-medium border border-primary-foreground/10" data-testid="button-get-started">
              Get Started
            </Button>
          </Link>
        </div>
      </div>
    </nav>
  );
}