import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Terminal, FolderOpen, FileCode, Play, Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface CommandResult {
  action: string;
  parameters: any;
  message: string;
  executable: boolean;
  code?: string;
  error?: string;
}

const PCControlMode = () => {
  const [command, setCommand] = useState("");
  const [output, setOutput] = useState<string[]>([
    "JARIS PC Control - AI-Powered System Ready",
    "Type commands to control your system with AI assistance",
    "Examples:",
    "  • 'create folder MyProject'",
    "  • 'create file app.py with a Flask hello world'",
    "  • 'write JavaScript code to fetch data from an API'",
    "  • 'explain how React hooks work'",
  ]);
  const [isExecuting, setIsExecuting] = useState(false);
  const { toast } = useToast();

  const executeCommand = async () => {
    if (!command.trim()) return;

    setOutput((prev) => [...prev, `> ${command}`]);
    setIsExecuting(true);
    
    try {
      const response = await fetch('/api/command/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command }),
      });

      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.error || 'Failed to execute command');
      }

      // Display command output
      if (result.output) {
        setOutput(prev => [...prev, result.output]);
      }
      
      // Show success message
      setOutput(prev => [...prev, "✓ Command executed successfully"]);
      
      toast({
        title: "Command Executed",
        description: "The command was executed successfully",
      });

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Unknown error";
      setOutput((prev) => [...prev, `❌ Error: ${errorMessage}`]);
      
      toast({
        title: "Execution Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsExecuting(false);
      setCommand("");
    }
  };

  const quickActions = [
    { 
      label: "Create React Component", 
      icon: FileCode, 
      command: "create file Button.tsx with a React button component using TypeScript" 
    },
    { 
      label: "Generate Python Script", 
      icon: FileCode, 
      command: "write Python code to read a CSV file and calculate averages" 
    },
    { 
      label: "Explain Concept", 
      icon: FolderOpen, 
      command: "explain what async/await is in JavaScript" 
    },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {quickActions.map((action, idx) => (
          <Card
            key={idx}
            className="p-4 bg-card border-border hover:border-primary transition-all cursor-pointer shadow-glow hover:shadow-glow-strong group"
            onClick={() => {
              setCommand(action.command);
            }}
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/20 group-hover:bg-primary/30 transition-colors">
                <action.icon className="w-5 h-5 text-primary" />
              </div>
              <span className="font-medium text-sm">{action.label}</span>
            </div>
          </Card>
        ))}
      </div>

      {/* Terminal Output */}
      <Card className="bg-card border-border shadow-glow">
        <div className="p-4 border-b border-border flex items-center gap-2">
          <Terminal className="w-5 h-5 text-primary animate-glow-pulse" />
          <span className="font-mono font-medium">AI-Powered Terminal</span>
          {isExecuting && (
            <Loader2 className="w-4 h-4 text-primary animate-spin ml-auto" />
          )}
        </div>
        
        <ScrollArea className="h-[400px] p-4">
          <div className="font-mono text-sm space-y-2">
            {output.map((line, idx) => (
              <div
                key={idx}
                className={`animate-slide-in ${
                  line.startsWith(">")
                    ? "text-primary font-semibold"
                    : line.startsWith("🤖")
                    ? "text-cyan-400"
                    : line.startsWith("✓")
                    ? "text-green-400"
                    : line.startsWith("❌")
                    ? "text-red-400"
                    : line.startsWith("ℹ️")
                    ? "text-yellow-400"
                    : line.startsWith("📝") || line.startsWith("📄")
                    ? "text-blue-400 font-semibold"
                    : line.startsWith("  •")
                    ? "text-muted-foreground ml-4"
                    : "text-foreground"
                }`}
              >
                {line}
              </div>
            ))}
          </div>
        </ScrollArea>

        <div className="p-4 border-t border-border">
          <div className="flex gap-2">
            <Input
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !isExecuting) {
                  executeCommand();
                }
              }}
              placeholder="Enter command or ask AI to generate code..."
              className="font-mono bg-secondary border-border focus:border-primary"
              disabled={isExecuting}
            />
            <Button 
              onClick={executeCommand} 
              className="shadow-glow"
              disabled={isExecuting || !command.trim()}
            >
              {isExecuting ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Play className="w-4 h-4 mr-2" />
              )}
              Execute
            </Button>
          </div>
        </div>
      </Card>

      {/* Info Card */}
      <Card className="p-4 bg-secondary/50 border-border">
        <p className="text-sm text-muted-foreground">
          <strong className="text-primary">✨ AI-Powered:</strong> This PC Control uses AI to understand natural language commands 
          and generate code. Try asking it to create files, generate code, or explain concepts. 
          In a desktop app, these would execute real system operations.
        </p>
      </Card>
    </div>
  );
};

export default PCControlMode;
