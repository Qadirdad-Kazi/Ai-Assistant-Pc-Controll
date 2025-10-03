import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import { 
  Settings, 
  Save, 
  Volume2, 
  Mic, 
  Zap, 
  Loader2, 
  Palette,
  Sun,
  Moon,
  Monitor,
  Activity,
  Contrast,
  MoonStar,
  Check
} from "lucide-react";

interface OllamaModel {
  name: string;
  model: string;
  modified_at: string;
  size: number;
  digest: string;
  details: {
    parent_model: string;
    format: string;
    family: string;
    families: string[] | null;
    parameter_size: string;
    quantization_level: string;
  };
}

const SettingsPage = () => {
  const [settings, setSettings] = useState({
    // Voice Settings
    voiceEnabled: true,
    autoSpeak: true,
    volume: [80],
    micSensitivity: [70],
    
    // AI Settings
    model: "llama3",
    
    // Appearance Settings
    theme: "system",
    accentColor: "blue",
    uiDensity: "normal",
    fontFamily: "sans",
    fontSize: 16,
    lineHeight: 1.5,
    roundedCorners: true,
    borderRadius: 0.5,
    animations: true,
    reduceMotion: false,
  });
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  // Fetch available models from Ollama
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await fetch('http://localhost:11434/api/tags');
        if (!response.ok) {
          throw new Error('Failed to fetch models');
        }
        const data = await response.json();
        setModels(data.models || []);
        
        // Set the first model as default if none is selected
        if (data.models?.length > 0 && !settings.model) {
          setSettings(prev => ({
            ...prev,
            model: data.models[0].name
          }));
        }
      } catch (error) {
        console.error('Error fetching models:', error);
        toast({
          title: "Error",
          description: "Failed to load models from Ollama. Make sure Ollama is running.",
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchModels();
  }, [toast]);

  const saveSettings = () => {
    // In a real app, this would save to localStorage or backend
    localStorage.setItem("jarisSettings", JSON.stringify(settings));
    toast({
      title: "Settings Saved",
      description: "Your preferences have been saved successfully.",
    });
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <Settings className="w-8 h-8 text-primary animate-glow-pulse" />
        <div>
          <h2 className="text-2xl font-bold">System Settings</h2>
          <p className="text-sm text-muted-foreground">Configure JARIS to your preferences</p>
        </div>
      </div>

      {/* Voice Settings */}
      <Card className="p-6 bg-card border-border shadow-glow space-y-6">
        <div className="flex items-center gap-2 mb-4">
          <Volume2 className="w-5 h-5 text-primary" />
          <h3 className="text-lg font-semibold">Voice Settings</h3>
        </div>

        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="voice-enabled">Voice Input/Output</Label>
              <p className="text-sm text-muted-foreground">Enable voice recognition and text-to-speech</p>
            </div>
            <Switch
              id="voice-enabled"
              checked={settings.voiceEnabled}
              onCheckedChange={(checked) => setSettings({ ...settings, voiceEnabled: checked })}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="auto-speak">Auto-speak Responses</Label>
              <p className="text-sm text-muted-foreground">Automatically speak AI responses</p>
            </div>
            <Switch
              id="auto-speak"
              checked={settings.autoSpeak}
              onCheckedChange={(checked) => setSettings({ ...settings, autoSpeak: checked })}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="volume">Output Volume: {settings.volume[0]}%</Label>
            <Slider
              id="volume"
              value={settings.volume}
              onValueChange={(value) => setSettings({ ...settings, volume: value })}
              max={100}
              step={1}
              className="w-full"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="mic-sensitivity">Microphone Sensitivity: {settings.micSensitivity[0]}%</Label>
            <Slider
              id="mic-sensitivity"
              value={settings.micSensitivity}
              onValueChange={(value) => setSettings({ ...settings, micSensitivity: value })}
              max={100}
              step={1}
              className="w-full"
            />
          </div>
        </div>
      </Card>

      {/* AI Settings */}
      <Card className="p-6 bg-card border-border shadow-glow space-y-6">
        <div className="flex items-center gap-2 mb-4">
          <Zap className="w-5 h-5 text-primary" />
          <h3 className="text-lg font-semibold">AI Configuration</h3>
        </div>

        <div className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="model">AI Model</Label>
              {isLoading && (
                <div className="flex items-center text-sm text-muted-foreground">
                  <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                  Loading models...
                </div>
              )}
            </div>
            <Select
              value={settings.model}
              onValueChange={(value) => setSettings({ ...settings, model: value })}
              disabled={isLoading}
            >
              <SelectTrigger id="model" className="bg-secondary border-border">
                <SelectValue placeholder={
                  isLoading ? "Loading models..." : "Select a model"
                } />
              </SelectTrigger>
              <SelectContent>
                {models.length > 0 ? (
                  models.map((model) => (
                    <SelectItem 
                      key={model.name} 
                      value={model.name}
                      className="truncate"
                    >
                      {model.name} 
                      <span className="text-xs text-muted-foreground ml-2">
                        ({Math.round(model.size / 1000000000)}GB)
                      </span>
                    </SelectItem>
                  ))
                ) : (
                  <div className="p-2 text-sm text-muted-foreground">
                    {isLoading ? 'Loading...' : 'No models found. Install models in Ollama.'}
                  </div>
                )}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Powered by Ollama • Models loaded from local instance
            </p>
            <Button 
              variant="outline" 
              size="sm" 
              className="mt-2"
              onClick={() => window.open('https://ollama.com/library', '_blank')}
            >
              Download more models
            </Button>
          </div>
        </div>
      </Card>

      {/* Appearance */}
      <Card className="p-6 bg-card border-border shadow-glow space-y-6">
        <div className="flex items-center gap-2 mb-6">
          <div className="p-2 rounded-lg bg-primary/10">
            <Palette className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h3 className="text-lg font-semibold">Appearance</h3>
            <p className="text-sm text-muted-foreground">Customize the look and feel of JARIS</p>
          </div>
        </div>

        <div className="space-y-6">
          {/* Theme Selection */}
          <div className="space-y-2">
            <Label>Theme</Label>
            <div className="grid grid-cols-3 gap-4 mt-2">
              {[
                { value: 'system', label: 'System', icon: Monitor },
                { value: 'light', label: 'Light', icon: Sun },
                { value: 'dark', label: 'Dark', icon: Moon },
                { value: 'jarvis', label: 'JARVIS', icon: Activity },
                { value: 'contrast', label: 'High Contrast', icon: Contrast },
                { value: 'blue-light', label: 'Blue Light', icon: MoonStar }
              ].map((theme) => (
                <button
                  key={theme.value}
                  onClick={() => setSettings({ ...settings, theme: theme.value })}
                  className={`flex flex-col items-center justify-center p-4 rounded-lg border-2 transition-all ${
                    settings.theme === theme.value 
                      ? 'border-primary bg-primary/10' 
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  <theme.icon className={`w-6 h-6 mb-2 ${
                    settings.theme === theme.value ? 'text-primary' : 'text-muted-foreground'
                  }`} />
                  <span className="text-sm">{theme.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Accent Color */}
          <div className="space-y-2">
            <Label>Accent Color</Label>
            <div className="flex flex-wrap gap-2 mt-2">
              {[
                { value: 'blue', color: 'bg-blue-500' },
                { value: 'green', color: 'bg-emerald-500' },
                { value: 'violet', color: 'bg-violet-500' },
                { value: 'rose', color: 'bg-rose-500' },
                { value: 'amber', color: 'bg-amber-500' },
                { value: 'custom', color: 'bg-gradient-to-r from-pink-500 to-yellow-500' }
              ].map((color) => (
                <button
                  key={color.value}
                  onClick={() => setSettings({ ...settings, accentColor: color.value })}
                  className={`w-10 h-10 rounded-full ${color.color} border-2 ${
                    settings.accentColor === color.value 
                      ? 'ring-2 ring-offset-2 ring-primary' 
                      : 'border-transparent hover:ring-2 hover:ring-offset-2 hover:ring-primary/50'
                  }`}
                  aria-label={`${color.value} theme`}
                />
              ))}
            </div>
          </div>

          {/* UI Density */}
          <div className="space-y-2">
            <Label>UI Density</Label>
            <div className="flex gap-4 mt-2">
              {[
                { value: 'compact', label: 'Compact' },
                { value: 'normal', label: 'Normal' },
                { value: 'comfortable', label: 'Comfortable' }
              ].map((density) => (
                <Button
                  key={density.value}
                  variant={settings.uiDensity === density.value ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSettings({ ...settings, uiDensity: density.value })}
                >
                  {density.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Font Settings */}
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Font Family</Label>
              <Select
                value={settings.fontFamily}
                onValueChange={(value) => setSettings({ ...settings, fontFamily: value })}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select font" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="sans">System (Sans-serif)</SelectItem>
                  <SelectItem value="serif">Serif</SelectItem>
                  <SelectItem value="mono">Monospace</SelectItem>
                  <SelectItem value="inter">Inter</SelectItem>
                  <SelectItem value="roboto">Roboto</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="font-size">Font Size: {settings.fontSize}px</Label>
                <Slider
                  id="font-size"
                  min={12}
                  max={24}
                  step={1}
                  value={[settings.fontSize]}
                  onValueChange={(value) => setSettings({ ...settings, fontSize: value[0] })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="line-height">Line Height: {settings.lineHeight}</Label>
                <Slider
                  id="line-height"
                  min={1}
                  max={3}
                  step={0.1}
                  value={[settings.lineHeight]}
                  onValueChange={(value) => setSettings({ ...settings, lineHeight: value[0] })}
                />
              </div>
            </div>
          </div>

          {/* Advanced Appearance */}
          <div className="space-y-4 pt-4 border-t border-border">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Rounded Corners</Label>
                <p className="text-sm text-muted-foreground">Enable rounded corners for UI elements</p>
              </div>
              <Switch
                checked={settings.roundedCorners}
                onCheckedChange={(checked) => setSettings({ ...settings, roundedCorners: checked })}
              />
            </div>

            {settings.roundedCorners && (
              <div className="pl-8 space-y-2">
                <Label>Border Radius: {settings.borderRadius}rem</Label>
                <Slider
                  min={0}
                  max={2}
                  step={0.1}
                  value={[settings.borderRadius]}
                  onValueChange={(value) => setSettings({ ...settings, borderRadius: value[0] })}
                />
              </div>
            )}

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Animations</Label>
                <p className="text-sm text-muted-foreground">Enable UI animations and transitions</p>
              </div>
              <Switch
                checked={settings.animations}
                onCheckedChange={(checked) => setSettings({ ...settings, animations: checked })}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Reduce Motion</Label>
                <p className="text-sm text-muted-foreground">Reduce or remove animations</p>
              </div>
              <Switch
                checked={settings.reduceMotion}
                onCheckedChange={(checked) => setSettings({ ...settings, reduceMotion: checked })}
              />
            </div>
          </div>
        </div>
      </Card>

      {/* Save Button */}
      <Button onClick={saveSettings} className="w-full shadow-glow-strong" size="lg">
        <Save className="w-5 h-5 mr-2" />
        Save Settings
      </Button>

      {/* Info */}
      <Card className="p-4 bg-secondary/50 border-border">
        <p className="text-sm text-muted-foreground">
          Settings are saved locally. The AI is powered by Lovable Cloud for seamless integration 
          without external setup.
        </p>
      </Card>
    </div>
  );
};

export default SettingsPage;
