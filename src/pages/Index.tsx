import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Settings, Brain, Cpu } from "lucide-react";
import AIMode from "@/components/AIMode";
import PCControlMode from "@/components/PCControlMode";
import SettingsPage from "@/components/SettingsPage";

const Index = () => {
  const [activeTab, setActiveTab] = useState("ai");

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border backdrop-blur-sm bg-background/80 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-blue-500 flex items-center justify-center shadow-glow">
                <Brain className="w-6 h-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-wider">JARIS</h1>
                <p className="text-xs text-muted-foreground">Just A Rather Intelligent System</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full max-w-md mx-auto grid-cols-3 mb-8 bg-secondary/50 backdrop-blur-sm">
            <TabsTrigger value="ai" className="data-[state=active]:shadow-glow">
              <Brain className="w-4 h-4 mr-2" />
              AI Mode
            </TabsTrigger>
            <TabsTrigger value="control" className="data-[state=active]:shadow-glow">
              <Cpu className="w-4 h-4 mr-2" />
              PC Control
            </TabsTrigger>
            <TabsTrigger value="settings" className="data-[state=active]:shadow-glow">
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </TabsTrigger>
          </TabsList>

          <TabsContent value="ai" className="animate-slide-in">
            <AIMode />
          </TabsContent>

          <TabsContent value="control" className="animate-slide-in">
            <PCControlMode />
          </TabsContent>

          <TabsContent value="settings" className="animate-slide-in">
            <SettingsPage />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default Index;
