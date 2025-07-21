import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Label } from "../components/ui/label"
import { RadioGroup, RadioGroupItem } from "../components/ui/radio-group"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs"
import { Settings, CheckCircle, AlertCircle, Loader2 } from "lucide-react"
import { Alert, AlertDescription } from "../components/ui/alert"
import apiClient from "../api/client"
import { AppConfig } from "../types/api"
import { useToast } from "../components/ui/use-toast"

export default function SettingsPage() {
  const [config, setConfig] = useState<AppConfig | null>(null)
  const [isTesting, setIsTesting] = useState(false)
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const data = await apiClient.getSettings()
        setConfig(data)
      } catch (error) {
        console.error("Failed to fetch settings", error)
      }
    }

    fetchSettings()
  }, [])

  const handleProviderChange = (provider: "openai" | "ollama" | "lmstudio") => {
    if (!config) return
    setConfig({
      ...config,
      llm: {
        ...config.llm,
        provider,
        model_name: provider === "openai" ? "gpt-4.1-2025-04-14" : provider === "ollama" ? "llama2" : "mistral",
        base_url: provider === "openai" ? "" : provider === "ollama" ? "http://localhost:11434" : "http://localhost:1234"
      }
    })
    setTestResult(null)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!config) return
    const { name, value } = e.target
    setConfig({
      ...config,
      llm: {
        ...config.llm,
        [name]: value
      }
    })
    setTestResult(null)
  }

  const handleTestConnection = async () => {
    if (!config) return
    setIsTesting(true)
    setTestResult(null)
    
    try {
      const result = await apiClient.testConnection({
        provider: config.llm.provider,
        model_name: config.llm.model_name,
        api_key: config.llm.api_key,
        base_url: config.llm.base_url
      })
      const success = result.success
      setTestResult({
        success,
        message: success 
          ? "Connection successful! The LLM provider is responding correctly." 
          : "Connection failed. Please check your configuration settings."
      })
      toast({
        title: success ? "Connection Successful" : "Connection Failed",
        description: success ? "The LLM provider is responding correctly." : "Please check your configuration settings.",
        variant: success ? "default" : "destructive",
      })
    } catch (error) {
      setTestResult({
        success: false,
        message: "An error occurred while testing the connection."
      })
      toast({
        title: "Connection Test Failed",
        description: "An error occurred while testing the connection.",
        variant: "destructive",
      })
    } finally {
      setIsTesting(false)
    }
  }

  const handleSaveSettings = async () => {
    if (!config) return
    setIsSaving(true)
    
    try {
      await apiClient.updateSettings({ llm: config.llm })
      toast({
        title: "Settings Saved",
        description: "Application settings updated successfully.",
      })
    } catch (error) {
      toast({
        title: "Save Failed",
        description: "Failed to save settings. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsSaving(false)
    }
  }

  if (!config) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-12 h-12 animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-6 lg:p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl font-bold flex items-center gap-2">
              <Settings className="w-6 h-6" />
              Application Settings
            </CardTitle>
            <CardDescription>
              Configure your LLM providers and application preferences
            </CardDescription>
          </CardHeader>
        </Card>

        {/* LLM Provider Settings */}
        <Card>
          <CardHeader>
            <CardTitle>LLM Provider Configuration</CardTitle>
            <CardDescription>Select and configure your preferred LLM provider</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs 
              defaultValue={config.llm.provider} 
              onValueChange={(value) => handleProviderChange(value as "openai" | "ollama" | "lmstudio")}
              className="w-full"
            >
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="openai">OpenAI</TabsTrigger>
                <TabsTrigger value="ollama">Ollama</TabsTrigger>
                <TabsTrigger value="lmstudio">LM Studio</TabsTrigger>
              </TabsList>

              <TabsContent value="openai" className="space-y-4 mt-4">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="openai-api-key">API Key</Label>
                    <Input
                      id="openai-api-key"
                      name="api_key"
                      type="password"
                      placeholder="sk-..."
                      value={config.llm.api_key || ""}
                      onChange={handleInputChange}
                    />
                    <p className="text-xs text-muted-foreground">
                      Your OpenAI API key is stored securely and used only for content evaluation.
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="openai-model">Model</Label>
                    <RadioGroup 
                      defaultValue={config.llm.model_name}
                      onValueChange={(value) => setConfig({...config, llm: {...config.llm, model_name: value}})}
                    >
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="gpt-4.1-2025-04-14" id="gpt-4.1-2025-04-14" />
                        <Label htmlFor="gpt-4.1-2025-04-14">GPT-4.1 (2025-04-14)</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="gpt-4.1-mini-2025-04-14" id="gpt-4.1-mini-2025-04-14" />
                        <Label htmlFor="gpt-4.1-mini-2025-04-14">GPT-4.1 Mini (2025-04-14)</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="gpt-4.1-nano" id="gpt-4.1-nano" />
                        <Label htmlFor="gpt-4.1-nano">GPT-4.1 Nano</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="gpt-4" id="gpt-4" />
                        <Label htmlFor="gpt-4">GPT-4</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="gpt-3.5-turbo" id="gpt-3.5-turbo" />
                        <Label htmlFor="gpt-3.5-turbo">GPT-3.5 Turbo</Label>
                      </div>
                    </RadioGroup>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="ollama" className="space-y-4 mt-4">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="ollama-url">Ollama URL</Label>
                    <Input
                      id="ollama-url"
                      name="base_url"
                      placeholder="http://localhost:11434"
                      value={config.llm.base_url || ""}
                      onChange={handleInputChange}
                    />
                    <p className="text-xs text-muted-foreground">
                      The URL where your Ollama instance is running.
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="ollama-model">Model</Label>
                    <RadioGroup 
                      defaultValue={config.llm.model_name}
                      onValueChange={(value) => setConfig({...config, llm: {...config.llm, model_name: value}})}
                    >
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="llama2" id="llama2" />
                        <Label htmlFor="llama2">Llama 2</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="mistral" id="mistral" />
                        <Label htmlFor="mistral">Mistral</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="codellama" id="codellama" />
                        <Label htmlFor="codellama">CodeLlama</Label>
                      </div>
                    </RadioGroup>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="lmstudio" className="space-y-4 mt-4">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="lmstudio-url">LM Studio URL</Label>
                    <Input
                      id="lmstudio-url"
                      name="base_url"
                      placeholder="http://localhost:1234/v1"
                      value={config.llm.base_url || ""}
                      onChange={handleInputChange}
                    />
                    <p className="text-xs text-muted-foreground">
                      The URL where your LM Studio instance is running.
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="lmstudio-model">Model</Label>
                    <Input
                      id="lmstudio-model"
                      name="model_name"
                      placeholder="Model name"
                      value={config.llm.model_name || ""}
                      onChange={handleInputChange}
                    />
                    <p className="text-xs text-muted-foreground">
                      The name of the model you have loaded in LM Studio.
                    </p>
                  </div>
                </div>
              </TabsContent>
            </Tabs>

            {testResult && (
              <Alert 
                variant={testResult.success ? "default" : "destructive"} 
                className="mt-4"
              >
                {testResult.success ? (
                  <CheckCircle className="h-4 w-4" />
                ) : (
                  <AlertCircle className="h-4 w-4" />
                )}
                <AlertDescription>{testResult.message}</AlertDescription>
              </Alert>
            )}

            <div className="flex justify-between items-center mt-6">
              <Button 
                variant="outline" 
                onClick={handleTestConnection}
                disabled={isTesting}
              >
                {isTesting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Testing...
                  </>
                ) : (
                  "Test Connection"
                )}
              </Button>

              <Button 
                onClick={handleSaveSettings}
                disabled={isSaving}
              >
                {isSaving ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  "Save Settings"
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}