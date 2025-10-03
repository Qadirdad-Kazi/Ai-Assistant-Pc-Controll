'use client';

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Mic, MicOff, Send, Volume2, VolumeX, Brain } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useSafeSettings } from "@/hooks/useSafeSettings";

interface Message {
  role: "user" | "assistant";
  content: string;
}


const AIMode = () => {
  const [isMounted, setIsMounted] = useState(false);
  const { settings, isInitialized } = useSafeSettings();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();
  const recognitionRef = useRef<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Set isMounted to true on mount (client-side only)
  useEffect(() => {
    setIsMounted(true);
  }, []);
  
  // Get the model from settings with a default fallback
  const model = settings?.model || 'llama3';
  
  // Check if we're still loading
  const isLoadingState = !isMounted || !isInitialized;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize speech recognition
  useEffect(() => {
    if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;

      recognitionRef.current.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript);
        setIsListening(false);
      };

      recognitionRef.current.onerror = () => {
        setIsListening(false);
        toast({
          title: "Voice input error",
          description: "Could not recognize speech. Please try again.",
          variant: "destructive",
        });
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }
  }, [toast]);

  const toggleVoiceInput = () => {
    if (!recognitionRef.current) {
      toast({
        title: "Voice not supported",
        description: "Speech recognition is not supported in this browser.",
        variant: "destructive",
      });
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  const speak = (text: string) => {
    if ("speechSynthesis" in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      window.speechSynthesis.speak(utterance);
    }
  };

  const stopSpeaking = () => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = { role: "user", content: input };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: updatedMessages,
          model: model
        }),
      });

      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(errorData || 'Failed to get response from AI');
      }

      const data = await response.json();
      
      // Add the assistant's response to the messages
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.content || 'I apologize, but I encountered an error processing your request.'
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      
      // Speak the response if speech is enabled
      if (settings.voiceEnabled && assistantMessage.content) {
        speak(assistantMessage.content);
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "An error occurred";
      
      toast({
        title: "AI Error",
        description: errorMessage,
        variant: "destructive",
      });
      
      // Add an error message to the chat
      const errorMessageObj: Message = {
        role: 'assistant',
        content: `I encountered an error: ${errorMessage}`
      };
      setMessages(prev => [...prev, errorMessageObj]);
    } finally {
      setIsLoading(false);
    }
  };

  // Show loading state if not mounted or settings not initialized
  if (isLoadingState) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-200px)] max-w-4xl mx-auto">
      <Card className="bg-card border-border shadow-glow p-6">
        {/* Chat Messages */}
        <div className="h-[500px] overflow-y-auto mb-4 space-y-4 pr-2">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
              <Brain className="w-16 h-16 mx-auto mb-4 animate-glow-pulse text-primary" />
              <p className="text-lg">Ask me anything...</p>
              <p className="text-sm mt-2">Use voice or text to interact</p>
            </div>
          )}
          {messages.map((message, idx) => (
            <div
              key={idx}
              className={`flex ${message.role === "user" ? "justify-end" : "justify-start"} animate-slide-in`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-4 ${
                  message.role === "user"
                    ? "bg-primary text-primary-foreground shadow-glow"
                    : "bg-secondary text-secondary-foreground"
                }`}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start animate-slide-in">
              <div className="bg-secondary text-secondary-foreground rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
                  <div className="w-2 h-2 bg-primary rounded-full animate-pulse delay-75" />
                  <div className="w-2 h-2 bg-primary rounded-full animate-pulse delay-150" />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="flex gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            placeholder="Type your message or use voice input..."
            className="resize-none bg-secondary border-border focus:border-primary transition-colors"
            rows={3}
          />
          <div className="flex flex-col gap-2">
            <Button
              onClick={toggleVoiceInput}
              variant={isListening ? "default" : "secondary"}
              size="icon"
              className={isListening ? "shadow-glow-strong animate-glow-pulse" : ""}
            >
              {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </Button>
            <Button
              onClick={isSpeaking ? stopSpeaking : sendMessage}
              variant="default"
              size="icon"
              disabled={isLoading}
              className="shadow-glow"
            >
              {isSpeaking ? <VolumeX className="w-5 h-5" /> : <Send className="w-5 h-5" />}
            </Button>
          </div>
        </div>

        {/* Status Indicators */}
        <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center gap-4">
            {isListening && (
              <span className="flex items-center gap-2 text-primary animate-glow-pulse">
                <span className="w-2 h-2 bg-primary rounded-full" />
                Listening...
              </span>
            )}
            {isSpeaking && (
              <span className="flex items-center gap-2 text-primary animate-glow-pulse">
                <Volume2 className="w-4 h-4" />
                Speaking...
              </span>
            )}
          </div>
          <span>Powered by Lovable AI</span>
        </div>
      </Card>
    </div>
  );
};

export default AIMode;
