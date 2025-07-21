import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Button } from "../components/ui/button"
import { Textarea } from "../components/ui/textarea"
import { Label } from "../components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs"
import { RadioGroup, RadioGroupItem } from "../components/ui/radio-group"
import { Input } from "../components/ui/input"
import { Upload, FileText, Loader2, AlertCircle, CheckCircle, Settings } from "lucide-react"
import { Alert, AlertDescription } from "../components/ui/alert"
import apiClient from "../api/client"
import { Sample, LLMConfig } from "../types/api"
import { useToast } from "../components/ui/use-toast"

export default function AnalyzePage() {
  const [content, setContent] = useState("")
  const [file, setFile] = useState<File | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState("")
  const [samples, setSamples] = useState<Sample[]>([])
  const [selectedSampleId, setSelectedSampleId] = useState<string | null>(null)
  const [useCustomModel, setUseCustomModel] = useState(false)
  const [customLLMConfig, setCustomLLMConfig] = useState<LLMConfig>({
    provider: "openai",
    model_name: "gpt-4.1-2025-04-14",
    api_key: "",
    base_url: "",
  })
  const navigate = useNavigate()
  const { toast } = useToast()

  useEffect(() => {
    const fetchSamples = async () => {
      try {
        const fetchedSamples = await apiClient.getSamples()
        setSamples(fetchedSamples)
      } catch (err) {
        console.error("Failed to fetch samples", err)
        toast({
          title: "Error loading samples",
          description: "Could not load sample content. Please try again later.",
          variant: "destructive",
        })
      }
    }
    fetchSamples()
  }, [])

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0]
    if (selectedFile) {
      // Check file type
      const allowedTypes = [
        "text/plain",
        "text/markdown",
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      ]
      if (
        !allowedTypes.includes(selectedFile.type) &&
        !selectedFile.name.endsWith(".txt") &&
        !selectedFile.name.endsWith(".md")
      ) {
        toast({
          title: "Invalid File Type",
          description: "Please upload a text file (.txt, .md, .pdf, .doc, .docx)",
          variant: "destructive",
        })
        return
      }

      // Check file size (max 10MB)
      if (selectedFile.size > 10 * 1024 * 1024) {
        toast({
          title: "File Too Large",
          description: "File size must be less than 10MB",
          variant: "destructive",
        })
        return
      }

      setFile(selectedFile)
      setError("") // Clear any previous general error
      toast({
        title: "File Uploaded",
        description: `File '${selectedFile.name}' loaded successfully.`,
      })

      // Read file content for text files
      if (
        selectedFile.type === "text/plain" ||
        selectedFile.name.endsWith(".txt") ||
        selectedFile.name.endsWith(".md")
      ) {
        const reader = new FileReader()
        reader.onload = (e) => {
          setContent(e.target?.result as string)
        }
        reader.readAsText(selectedFile)
      }
    }
  }

  const handleAnalyze = async () => {
    if (!content.trim() && !file) {
      toast({
        title: "Missing Content",
        description: "Please provide content to analyze.",
        variant: "destructive",
      })
      return
    }

    if (content.trim().length < 50) {
      toast({
        title: "Content Too Short",
        description: "Content must be at least 50 characters long for meaningful analysis.",
        variant: "destructive",
      })
      return
    }

    setIsAnalyzing(true)
    setError("") // Clear any previous general error

    try {
      const evaluationRequest = {
        content,
        ...(useCustomModel && customLLMConfig && {
          llm: {
            provider: customLLMConfig.provider,
            model_name: customLLMConfig.model_name,
            api_key: customLLMConfig.api_key || undefined,
            base_url: customLLMConfig.base_url || undefined,
          }
        })
      }
      
      const response = await apiClient.evaluateContent(evaluationRequest)
      toast({
        title: "Analysis Complete",
        description: "Content successfully analyzed.",
      })
      navigate(`/results/${response.content_hash}`)
    } catch (err) {
      console.error("Analysis error:", err)
      toast({
        title: "Analysis Failed",
        description: "Failed to analyze content. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleClearContent = () => {
    setContent("")
    setFile(null)
    setError("")
    setSelectedSampleId(null)
    toast({
      title: "Content Cleared",
      description: "Input content has been cleared.",
    })
  }

  const handleSampleSelect = async (sampleId: string) => {
    setSelectedSampleId(sampleId)
    try {
      const sample = await apiClient.getSample(sampleId)
      setContent(sample.content)
      setError("")
      toast({
        title: "Sample Loaded",
        description: `Sample '${sample.name}' loaded successfully.`,
      })
    } catch (err) {
      console.error("Sample load error:", err)
      toast({
        title: "Error loading sample",
        description: "Failed to load sample content. Please try again.",
        variant: "destructive",
      })
    }
  }

  const handleProviderChange = (provider: "openai" | "ollama" | "lmstudio") => {
    setCustomLLMConfig({
      ...customLLMConfig,
      provider,
      model_name: provider === "openai" ? "gpt-4.1-2025-04-14" : provider === "ollama" ? "llama2" : "mistral",
      base_url: provider === "openai" ? "" : provider === "ollama" ? "http://localhost:11434" : "http://localhost:1234"
    })
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setCustomLLMConfig({
      ...customLLMConfig,
      [name]: value
    })
  }

  const wordCount = content
    .trim()
    .split(/\s+/)
    .filter((word) => word.length > 0).length
  const charCount = content.length

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-6 lg:p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-3xl font-bold flex items-center justify-center gap-2">
              <FileText className="w-8 h-8" />
              Content Analysis Tool
            </CardTitle>
            <CardDescription className="text-lg">
              Upload a file or paste your content to get comprehensive feedback on quality, clarity, and engagement
            </CardDescription>
          </CardHeader>
        </Card>

        {/* Model Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5" />
              Model Selection
            </CardTitle>
            <CardDescription>
              Choose which AI model to use for content analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="use-custom-model"
                  checked={useCustomModel}
                  onChange={(e) => setUseCustomModel(e.target.checked)}
                  className="rounded border-gray-300"
                />
                <Label htmlFor="use-custom-model">
                  Use custom model (otherwise uses default from settings)
                </Label>
              </div>

              {useCustomModel && (
                <div className="border rounded-lg p-4 space-y-4">
                  <Tabs
                    defaultValue={customLLMConfig.provider}
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
                            value={customLLMConfig.api_key || ""}
                            onChange={handleInputChange}
                          />
                        </div>

                                                 <div className="space-y-2">
                           <Label htmlFor="openai-model">Model</Label>
                           <RadioGroup
                             defaultValue={customLLMConfig.model_name}
                             onValueChange={(value) => setCustomLLMConfig({...customLLMConfig, model_name: value})}
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
                            value={customLLMConfig.base_url || ""}
                            onChange={handleInputChange}
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="ollama-model">Model</Label>
                          <RadioGroup
                            defaultValue={customLLMConfig.model_name}
                            onValueChange={(value) => setCustomLLMConfig({...customLLMConfig, model_name: value})}
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
                            value={customLLMConfig.base_url || ""}
                            onChange={handleInputChange}
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="lmstudio-model">Model</Label>
                          <Input
                            id="lmstudio-model"
                            name="model_name"
                            placeholder="Model name"
                            value={customLLMConfig.model_name || ""}
                            onChange={handleInputChange}
                          />
                        </div>
                      </div>
                    </TabsContent>
                  </Tabs>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Content Input */}
        <Card>
          <CardHeader>
            <CardTitle>Submit Content for Analysis</CardTitle>
            <CardDescription>Choose how you'd like to provide your content for analysis</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="paste" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="paste">Paste Content</TabsTrigger>
                <TabsTrigger value="upload">Upload File</TabsTrigger>
                <TabsTrigger value="sample">Sample Content</TabsTrigger>
              </TabsList>

              <TabsContent value="paste" className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="content">Content to Analyze</Label>
                  <Textarea
                    id="content"
                    placeholder="Paste your content here... (minimum 50 characters)"
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    className="min-h-[300px] resize-y"
                  />
                  <div className="flex justify-between text-sm text-muted-foreground">
                    <span>{charCount} characters</span>
                    <span>{wordCount} words</span>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="upload" className="space-y-4">
                <div className="space-y-4">
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-gray-400 transition-colors">
                    <input
                      type="file"
                      id="file-upload"
                      className="hidden"
                      onChange={handleFileUpload}
                      accept=".txt,.md,.pdf,.doc,.docx"
                    />
                    <label htmlFor="file-upload" className="cursor-pointer">
                      <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                      <div className="text-lg font-medium mb-2">{file ? file.name : "Choose a file to upload"}</div>
                      <div className="text-sm text-muted-foreground">
                        Supports: .txt, .md, .pdf, .doc, .docx (max 10MB)
                      </div>
                    </label>
                  </div>

                  {file && (
                    <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-md">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                      <span className="text-sm font-medium">File uploaded successfully</span>
                      <Button variant="ghost" size="sm" onClick={handleClearContent} className="ml-auto">
                        Remove
                      </Button>
                    </div>
                  )}

                  {content && (
                    <div className="space-y-2">
                      <Label>File Preview</Label>
                      <div className="p-3 bg-gray-50 border rounded-md max-h-40 overflow-y-auto">
                        <pre className="text-sm whitespace-pre-wrap">{content.substring(0, 500)}...</pre>
                      </div>
                      <div className="flex justify-between text-sm text-muted-foreground">
                        <span>{charCount} characters</span>
                        <span>{wordCount} words</span>
                      </div>
                    </div>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="sample" className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="sample-content">Select Sample Content</Label>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {samples.length === 0 ? (
                      <p className="text-muted-foreground">No sample content available.</p>
                    ) : (
                      samples.map((sample) => (
                        <Card
                          key={sample.id}
                          className={`cursor-pointer hover:border-primary ${selectedSampleId === sample.id ? "border-primary ring-2 ring-primary" : ""}`}
                          onClick={() => handleSampleSelect(sample.id)}
                        >
                          <CardHeader>
                            <CardTitle className="text-lg">{sample.name}</CardTitle>
                            <CardDescription>{sample.description}</CardDescription>
                          </CardHeader>
                          <CardContent>
                            <p className="text-sm text-muted-foreground line-clamp-3">{sample.content}</p>
                          </CardContent>
                        </Card>
                      ))
                    )}
                  </div>
                </div>
              </TabsContent>
            </Tabs>

            {error && (
              <Alert variant="destructive" className="mt-4">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="flex justify-between items-center mt-6">
              <Button variant="outline" onClick={handleClearContent} disabled={!content && !file}>
                Clear Content
              </Button>

              <Button
                onClick={handleAnalyze}
                disabled={(!content.trim() && !file) || isAnalyzing}
                className="min-w-[120px]"
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  "Analyze Content"
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Analysis Info */}
        <Card>
          <CardHeader>
            <CardTitle>What We Analyze</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="space-y-2">
                <h3 className="font-semibold text-green-700">Clarity</h3>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• Conciseness</li>
                  <li>• Jargon usage</li>
                  <li>• Logical structure</li>
                </ul>
              </div>
              <div className="space-y-2">
                <h3 className="font-semibold text-blue-700">Accuracy</h3>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• Data support</li>
                  <li>• Fact verification</li>
                  <li>• Source credibility</li>
                </ul>
              </div>
              <div className="space-y-2">
                <h3 className="font-semibold text-purple-700">Engagement</h3>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• Audience relevance</li>
                  <li>• Tone appropriateness</li>
                  <li>• Call to action</li>
                </ul>
              </div>
              <div className="space-y-2">
                <h3 className="font-semibold text-orange-700">Completeness</h3>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• Topic coverage</li>
                  <li>• Depth of analysis</li>
                  <li>• Context provision</li>
                </ul>
              </div>
              <div className="space-y-2">
                <h3 className="font-semibold text-red-700">Readability</h3>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• Sentence structure</li>
                  <li>• Paragraph organization</li>
                  <li>• Formatting consistency</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
