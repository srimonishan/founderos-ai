import { Link, useLocation } from "wouter";
import { Zap, LayoutDashboard, Lightbulb, BrainCircuit, BarChart3, Settings, LogOut } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

export function Sidebar() {
  const [location] = useLocation();

  const links = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/ideas", label: "My Ideas", icon: Lightbulb },
    { href: "#", label: "AI Insights", icon: BrainCircuit },
    { href: "#", label: "Market Data", icon: BarChart3 },
    { href: "#", label: "Settings", icon: Settings },
  ];

  return (
    <aside className="w-64 h-screen fixed left-0 top-0 border-r border-white/10 bg-background/50 backdrop-blur-md flex flex-col z-40">
      <div className="h-16 flex items-center px-6 border-b border-white/10">
        <Link href="/" className="flex items-center gap-2 group" data-testid="link-home-sidebar">
          <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center border border-primary/30 group-hover:border-primary/50 transition-colors">
            <Zap className="w-4 h-4 text-primary" />
          </div>
          <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white to-white/70 bg-clip-text text-transparent">FounderOS</span>
        </Link>
      </div>

      <div className="flex-1 py-6 px-3 flex flex-col gap-1">
        {links.map((link) => {
          const isActive = location === link.href;
          const Icon = link.icon;
          return (
            <Link key={link.label} href={link.href} className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${isActive ? 'bg-primary/10 text-primary font-medium' : 'text-muted-foreground hover:bg-white/5 hover:text-foreground'}`} data-testid={`link-sidebar-${link.label.toLowerCase().replace(' ', '-')}`}>
              <Icon className="w-4 h-4" />
              <span className="text-sm">{link.label}</span>
            </Link>
          );
        })}
      </div>

      <div className="p-4 border-t border-white/10">
        <div className="flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-white/5 transition-colors cursor-pointer" data-testid="user-profile">
          <Avatar className="w-8 h-8 border border-white/20">
            <AvatarImage src="" />
            <AvatarFallback className="bg-primary/20 text-primary text-xs">JD</AvatarFallback>
          </Avatar>
          <div className="flex flex-col flex-1 overflow-hidden">
            <span className="text-sm font-medium truncate">Jane Doe</span>
            <span className="text-xs text-muted-foreground truncate">jane@founder.os</span>
          </div>
          <LogOut className="w-4 h-4 text-muted-foreground" />
        </div>
      </div>
    </aside>
  );
}