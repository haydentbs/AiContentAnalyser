import { useState, useEffect } from "react"
import { useParams, Link } from "react-router-dom"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Badge } from "../components/ui/badge"
import { Button } from "../components/ui/button"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "../components/ui/collapsible"
import { Progress } from "../components/ui/progress"
import { Separator } from "../components/ui/separator"
import { Alert, AlertDescription } from "../components/ui/alert"
import {
  ChevronDown,
  ChevronUp,
  FileText,
  Calendar,
  Hash,
  Clock,
  TrendingUp,
  TrendingDown,
  Minus,
  ArrowLeft,
  Download,
  Loader2,
  AlertCircle
} from "lucide-react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs"
import GaugeChart from "../components/ui/GaugeChart"
import RadarChart from "../components/ui/RadarChart"
import MetricResultCard from "../components/ui/MetricResultCard"
import { useToast } from "../components/ui/use-toast"
import apiClient from "../api/client"
import { EvaluationResult } from "../types/api"



function getScoreColor(score: number) {
  if (score >= 4) return "text-green-600 bg-green-50 border-green-200"
  if (score >= 3) return "text-yellow-600 bg-yellow-50 border-yellow-200"
  if (score >= 2) return "text-orange-600 bg-orange-50 border-orange-200"
  return "text-red-600 bg-red-50 border-red-200"
}

function getScoreIcon(score: number) {
  if (score >= 3.5) return <TrendingUp className="w-4 h-4" />
  if (score >= 2.5) return <Minus className="w-4 h-4" />
  return <TrendingDown className="w-4 h-4" />
}

function ScoreDisplay({ score, size = "default" }: { score: number; size?: "default" | "large" }) {
  const colorClass = getScoreColor(score)
  const sizeClass = size === "large" ? "text-2xl font-bold px-4 py-2" : "text-sm font-medium px-2 py-1"

  return (
    <div className={`inline-flex items-center gap-2 rounded-lg border ${colorClass} ${sizeClass}`}>
      {getScoreIcon(score)}
      <span>{score.toFixed(1)}</span>
    </div>
  )
}

export default function ResultsPage() {
  const { reportId } = useParams<{ reportId: string }>()
  const [reportData, setReportData] = useState<EvaluationResult | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const { toast } = useToast()
  const [error, setError] = useState<string | null>(null)
  const [expandedMetrics, setExpandedMetrics] = useState<Set<string>>(new Set())

  useEffect(() => {
    const fetchReport = async () => {
      if (!reportId) return
      try {
        setIsLoading(true)
        const data = await apiClient.getReport(reportId)
        setReportData(data)
      } catch (err) {
        setError("Failed to fetch report. Please try again.")
      } finally {
        setIsLoading(false)
      }
    }

    fetchReport()
  }, [reportId])

  const toggleMetric = (metricName: string) => {
    const newExpanded = new Set(expandedMetrics)
    if (newExpanded.has(metricName)) {
      newExpanded.delete(metricName)
    } else {
      newExpanded.add(metricName)
    }
    setExpandedMetrics(newExpanded)
  }

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  const handleExport = async (format: 'json' | 'markdown') => {
    if (!reportId) return
    try {
      const blob = await apiClient.exportReport(reportId, format)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${reportId}.${format === 'json' ? 'json' : 'md'}`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
      toast({
        title: "Export Successful",
        description: `Report exported as ${format.toUpperCase()}.`,
      })
    } catch (error) {
      toast({
        title: "Export Failed",
        description: "Could not export report. Please try again.",
        variant: "destructive",
      })
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-12 h-12 animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    )
  }

  if (!reportData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p>No report data found.</p>
      </div>
    )
  }

  const categoryMetrics = reportData.metric_results.reduce(
    (acc, metric) => {
      const category = metric.metric.category
      if (!acc[category]) acc[category] = []
      acc[category].push(metric)
      return acc
    },
    {} as Record<string, typeof reportData.metric_results>,
  )

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-6 lg:p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Link to="/analyze">
                    <Button variant="ghost" size="sm">
                      <ArrowLeft className="w-4 h-4 mr-2" />
                      Analyze New Content
                    </Button>
                  </Link>
                </div>
                <CardTitle className="text-2xl font-bold flex items-center gap-2">
                  <FileText className="w-6 h-6" />
                  Content Feedback Report
                </CardTitle>
                <CardDescription className="mt-2">
                  Comprehensive analysis of content quality across multiple dimensions
                </CardDescription>
              </div>
              <div className="flex flex-col items-center">
                <GaugeChart value={reportData.overall_score} size="large" />
                <div className="mt-2 font-bold text-lg">Overall Score</div>
              </div>
            </div>

            <div className="flex flex-wrap gap-4 mt-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                {formatDate(reportData.timestamp)}
              </div>
              <div className="flex items-center gap-2">
                <Hash className="w-4 h-4" />
                {reportData.content_hash.substring(0, 8)}
              </div>
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4" />
                {reportData.metadata.metrics_evaluated} metrics evaluated
              </div>
            </div>
            
            <div className="flex gap-2 mt-4">
              <Button variant="outline" size="sm" onClick={() => handleExport('json')} className="gap-2">
                <Download className="w-4 h-4" />
                Export JSON
              </Button>
              <Button variant="outline" size="sm" onClick={() => handleExport('markdown')} className="gap-2">
                <Download className="w-4 h-4" />
                Export Markdown
              </Button>
            </div>
          </CardHeader>
        </Card>

        {/* Category Scores Overview */}
        <Card>
          <CardHeader>
            <CardTitle>Category Scores</CardTitle>
            <CardDescription>Performance breakdown across key content quality dimensions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="flex justify-center">
                <RadarChart 
                  data={Object.entries(reportData.category_scores).map(([category, score]) => ({
                    category,
                    score
                  }))} 
                  size="medium"
                />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(reportData.category_scores).map(([category, score]) => (
                  <div key={category} className="text-center space-y-2">
                    <div className="capitalize font-medium text-sm text-muted-foreground">{category}</div>
                    <ScoreDisplay score={score} />
                    <Progress value={(score / 5) * 100} className="h-2" />
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Detailed Metrics by Category - Tabbed */}
        <Card>
          <CardHeader>
            <CardTitle>Detailed Analysis</CardTitle>
            <CardDescription>Explore metrics organized by category</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue={Object.keys(categoryMetrics)[0]} className="w-full">
              <TabsList className="grid w-full" style={{ gridTemplateColumns: `repeat(${Object.keys(categoryMetrics).length}, 1fr)` }}>
                {Object.keys(categoryMetrics).map((category) => {
                  const score = reportData.category_scores[category as keyof typeof reportData.category_scores];
                  const getScoreActiveColor = (s: number) => {
                    if (s >= 4) return "data-[state=active]:bg-green-100 data-[state=active]:border-green-300";
                    if (s >= 3) return "data-[state=active]:bg-yellow-100 data-[state=active]:border-yellow-300";
                    if (s >= 2) return "data-[state=active]:bg-orange-100 data-[state=active]:border-orange-300";
                    return "data-[state=active]:bg-red-100 data-[state=active]:border-red-300";
                  };
                  return (
                    <TabsTrigger
                      key={category}
                      value={category}
                      className={`capitalize flex justify-between items-center py-2 ${getScoreColor(score)} ${getScoreActiveColor(score)}`}
                    >
                      <span>{category}</span>
                      <span className="font-bold flex items-center gap-1">
                        {getScoreIcon(score)}
                        {score.toFixed(1)}
                      </span>
                    </TabsTrigger>
                  );
                })}
              </TabsList>

              {Object.entries(categoryMetrics).map(([category, metrics]) => (
                <TabsContent key={category} value={category} className="mt-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-lg font-semibold capitalize">{category}</h3>
                        <p className="text-sm text-muted-foreground">
                          {metrics.length} metric{metrics.length !== 1 ? "s" : ""} evaluated in this category
                        </p>
                      </div>
                      <ScoreDisplay score={reportData.category_scores[category as keyof typeof reportData.category_scores]} />
                    </div>

                    {metrics.map((metric, index) => (
                      <div key={metric.metric.name}>
                        <MetricResultCard 
                          metricResult={metric}
                          expanded={expandedMetrics.has(metric.metric.name)}
                          onToggle={toggleMetric}
                        />
                        {index < metrics.length - 1 && <Separator className="mt-4" />}
                      </div>
                    ))}
                  </div>
                </TabsContent>
              ))}
            </Tabs>
          </CardContent>
        </Card>

        {/* Summary */}
        <Card>
          <CardHeader>
            <CardTitle>Report Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold">{reportData.overall_score.toFixed(1)}</div>
                <div className="text-sm text-muted-foreground">Overall Score</div>
              </div>
              <div>
                <div className="text-2xl font-bold">{reportData.metadata.metrics_evaluated}</div>
                <div className="text-sm text-muted-foreground">Metrics Evaluated</div>
              </div>
              <div>
                <div className="text-2xl font-bold">{Object.keys(reportData.category_scores).length}</div>
                <div className="text-sm text-muted-foreground">Categories Analyzed</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}