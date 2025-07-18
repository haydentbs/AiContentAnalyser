"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Upload, FileText, Loader2, AlertCircle, CheckCircle } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"

export default function AnalyzePage() {
  const [content, setContent] = useState("")
  const [file, setFile] = useState<File | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState("")
  const router = useRouter()

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
        setError("Please upload a text file (.txt, .md, .pdf, .doc, .docx)")
        return
      }

      // Check file size (max 10MB)
      if (selectedFile.size > 10 * 1024 * 1024) {
        setError("File size must be less than 10MB")
        return
      }

      setFile(selectedFile)
      setError("")

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
      setError("Please provide content to analyze")
      return
    }

    if (content.trim().length < 50) {
      setError("Content must be at least 50 characters long for meaningful analysis")
      return
    }

    setIsAnalyzing(true)
    setError("")

    try {
      // Simulate API call - in real implementation, this would send content to your analysis service
      await new Promise((resolve) => setTimeout(resolve, 3000))

      // Navigate to results page
      router.push("/")
    } catch (err) {
      setError("Failed to analyze content. Please try again.")
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleClearContent = () => {
    setContent("")
    setFile(null)
    setError("")
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

        {/* Content Input */}
        <Card>
          <CardHeader>
            <CardTitle>Submit Content for Analysis</CardTitle>
            <CardDescription>Choose how you'd like to provide your content for analysis</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="paste" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="paste">Paste Content</TabsTrigger>
                <TabsTrigger value="upload">Upload File</TabsTrigger>
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
