import { Link } from 'react-router-dom'
import { FileText, Settings, BarChart } from 'lucide-react'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'

const HomePage = () => {
  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-6 lg:p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold">Content Scorecard</h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Evaluate and improve your content with AI-powered analysis and actionable feedback
          </p>
          <div className="flex justify-center gap-4 pt-4">
            <Link to="/analyze">
              <Button size="lg" className="gap-2">
                <FileText className="h-5 w-5" />
                Analyze Content
              </Button>
            </Link>
            <Link to="/settings">
              <Button size="lg" variant="outline" className="gap-2">
                <Settings className="h-5 w-5" />
                Configure Settings
              </Button>
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Content Analysis
              </CardTitle>
              <CardDescription>
                Submit your content for comprehensive evaluation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Upload files or paste text to receive detailed feedback on clarity, accuracy, engagement, and more.
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart className="h-5 w-5" />
                Detailed Reports
              </CardTitle>
              <CardDescription>
                Get actionable insights and recommendations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                View comprehensive reports with scores, visualizations, and specific examples of what works and what could be improved.
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Customizable Settings
              </CardTitle>
              <CardDescription>
                Configure the tool to your specific needs
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Choose between different LLM providers, adjust evaluation parameters, and customize the analysis to your content type.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default HomePage