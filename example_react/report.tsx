"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
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
} from "lucide-react"
import reportData from "@/data/report.json"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import Link from "next/link"

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

export default function FeedbackReport() {
  const [expandedMetrics, setExpandedMetrics] = useState<Set<string>>(new Set())

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
                  <Link href="/analyze">
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
              <ScoreDisplay score={reportData.overall_score} size="large" />
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
          </CardHeader>
        </Card>

        {/* Category Scores Overview */}
        <Card>
          <CardHeader>
            <CardTitle>Category Scores</CardTitle>
            <CardDescription>Performance breakdown across key content quality dimensions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              {Object.entries(reportData.category_scores).map(([category, score]) => (
                <div key={category} className="text-center space-y-2">
                  <div className="capitalize font-medium text-sm text-muted-foreground">{category}</div>
                  <ScoreDisplay score={score} />
                  <Progress value={(score / 5) * 100} className="h-2" />
                </div>
              ))}
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
              <TabsList className="grid w-full grid-cols-5">
                {Object.keys(categoryMetrics).map((category) => (
                  <TabsTrigger key={category} value={category} className="capitalize">
                    <div className="flex items-center gap-2">
                      {category}
                      <ScoreDisplay
                        score={reportData.category_scores[category as keyof typeof reportData.category_scores]}
                      />
                    </div>
                  </TabsTrigger>
                ))}
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
                    </div>

                    {metrics.map((metric, index) => (
                      <div key={metric.metric.name}>
                        <Collapsible>
                          <CollapsibleTrigger asChild>
                            <Button
                              variant="ghost"
                              className="w-full justify-between p-4 h-auto"
                              onClick={() => toggleMetric(metric.metric.name)}
                            >
                              <div className="flex items-center justify-between w-full">
                                <div className="text-left">
                                  <div className="font-medium capitalize">{metric.metric.name.replace("_", " ")}</div>
                                  <div className="text-sm text-muted-foreground">{metric.metric.description}</div>
                                </div>
                                <div className="flex items-center gap-3">
                                  <Badge variant="outline" className="text-xs">
                                    Weight: {(metric.metric.weight * 100).toFixed(0)}%
                                  </Badge>
                                  <ScoreDisplay score={metric.score} />
                                  {expandedMetrics.has(metric.metric.name) ? (
                                    <ChevronUp className="w-4 h-4" />
                                  ) : (
                                    <ChevronDown className="w-4 h-4" />
                                  )}
                                </div>
                              </div>
                            </Button>
                          </CollapsibleTrigger>
                          <CollapsibleContent className="px-4 pb-4">
                            <div className="space-y-4 mt-4">
                              {/* Reasoning */}
                              <div>
                                <h4 className="font-medium mb-2">Analysis</h4>
                                <p className="text-sm text-muted-foreground leading-relaxed">{metric.reasoning}</p>
                              </div>

                              {/* Improvement Advice */}
                              <div>
                                <h4 className="font-medium mb-2">Improvement Recommendations</h4>
                                <p className="text-sm text-muted-foreground leading-relaxed">
                                  {metric.improvement_advice}
                                </p>
                              </div>

                              {/* Examples */}
                              {metric.positive_examples && metric.positive_examples.length > 0 && (
                                <div>
                                  <h4 className="font-medium mb-2 text-green-700">Positive Examples</h4>
                                  <div className="space-y-2">
                                    {metric.positive_examples.map((example, idx) => (
                                      <div
                                        key={idx}
                                        className="text-sm p-3 bg-green-50 border border-green-200 rounded-md"
                                      >
                                        "{example}"
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {metric.improvement_examples && metric.improvement_examples.length > 0 && (
                                <div>
                                  <h4 className="font-medium mb-2 text-orange-700">Areas for Improvement</h4>
                                  <div className="space-y-2">
                                    {metric.improvement_examples.map((example, idx) => (
                                      <div
                                        key={idx}
                                        className="text-sm p-3 bg-orange-50 border border-orange-200 rounded-md"
                                      >
                                        "{example}"
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Confidence */}
                              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                <span>Confidence Level:</span>
                                <Progress value={metric.confidence * 100} className="w-20 h-2" />
                                <span>{(metric.confidence * 100).toFixed(0)}%</span>
                              </div>
                            </div>
                          </CollapsibleContent>
                        </Collapsible>
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
