import { Link, useLocation } from "wouter";
import { Zap, LogOut, LayoutDashboard } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/contexts/AuthContext";

export function Navbar() {
  const { session, user, signOut } = useAuth();
  const [, setLocation] = useLocation();

  const avatarUrl = user?.user_metadata?.avatar_url as string | undefined;
  const fullName = (user?.user_metadata?.full_name as string) ?? user?.email ?? "User";
  const initials = fullName
    .split(" ")
    .map((n: string) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  const handleSignOut = async () => {
    await signOut();
    setLocation("/");
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-background/50 backdrop-blur-md border-b border-white/10">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group" data-testid="link-home">
          <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center border border-primary/30 group-hover:border-primary/50 transition-colors">
            <Zap className="w-4 h-4 text-primary" />
          </div>
          <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white to-white/70 bg-clip-text text-transparent">
            FounderOS AI
          </span>
        </Link>

        <div className="flex items-center gap-6">
          {!session && (
            <div className="hidden md:flex items-center gap-6 text-sm text-muted-foreground">
              <Link href="/#features" className="hover:text-foreground transition-colors" data-testid="link-features">Features</Link>
              <Link href="/#pricing" className="hover:text-foreground transition-colors" data-testid="link-pricing">Pricing</Link>
              <Link href="/#about" className="hover:text-foreground transition-colors" data-testid="link-about">About</Link>
            </div>
          )}

          {session ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  className="flex items-center gap-2 rounded-full outline-none ring-offset-background focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                  data-testid="button-user-menu"
                >
                  <Avatar className="w-8 h-8 border border-white/20">
                    <AvatarImage src={avatarUrl} alt={fullName} />
                    <AvatarFallback className="bg-primary/20 text-primary text-xs">{initials}</AvatarFallback>
                  </Avatar>
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-52 bg-background/80 backdrop-blur-md border-white/10">
                <div className="px-3 py-2">
                  <p className="text-sm font-medium truncate">{fullName}</p>
                  <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                </div>
                <DropdownMenuSeparator className="bg-white/10" />
                <DropdownMenuItem
                  onClick={() => setLocation("/dashboard")}
                  className="gap-2 cursor-pointer focus:bg-white/5"
                  data-testid="menu-item-dashboard"
                >
                  <LayoutDashboard className="w-4 h-4" />
                  Dashboard
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-white/10" />
                <DropdownMenuItem
                  onClick={handleSignOut}
                  className="gap-2 cursor-pointer text-destructive focus:text-destructive focus:bg-destructive/10"
                  data-testid="button-signout"
                >
                  <LogOut className="w-4 h-4" />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Link href="/login" data-testid="link-get-started">
              <Button
                className="bg-primary hover:bg-primary/90 text-primary-foreground font-medium border border-primary-foreground/10"
                data-testid="button-get-started"
              >
                Get Started
              </Button>
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
