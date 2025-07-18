import React, { useState } from 'react';
import { Badge } from './badge';
import { Button } from './button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './collapsible';
import { Progress } from './progress';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface MetricResult {
  metric: {
    name: string;
    description: string;
    category: string;
    weight: number;
  };
  score: number;
  reasoning: string;
  improvement_advice: string;
  positive_examples?: string[];
  improvement_examples?: string[];
  confidence: number;
}

interface MetricResultCardProps {
  metricResult: MetricResult;
  expanded?: boolean;
  onToggle?: (metricName: string) => void;
}

function getScoreColor(score: number) {
  if (score >= 4) return "text-green-600 bg-green-50 border-green-200";
  if (score >= 3) return "text-yellow-600 bg-yellow-50 border-yellow-200";
  if (score >= 2) return "text-orange-600 bg-orange-50 border-orange-200";
  return "text-red-600 bg-red-50 border-red-200";
}

const MetricResultCard: React.FC<MetricResultCardProps> = ({ 
  metricResult, 
  expanded = false,
  onToggle 
}) => {
  const [isExpanded, setIsExpanded] = useState(expanded);
  
  const handleToggle = () => {
    const newExpandedState = !isExpanded;
    setIsExpanded(newExpandedState);
    if (onToggle) {
      onToggle(metricResult.metric.name);
    }
  };
  
  const scoreColorClass = getScoreColor(metricResult.score);
  
  return (
    <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
      <CollapsibleTrigger asChild>
        <Button
          variant="ghost"
          className="w-full justify-between p-4 h-auto"
          onClick={handleToggle}
        >
          <div className="flex items-center justify-between w-full">
            <div className="text-left">
              <div className="font-medium capitalize">{metricResult.metric.name.replace(/_/g, " ")}</div>
              <div className="text-sm text-muted-foreground">{metricResult.metric.description}</div>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant="outline" className="text-xs">
                Weight: {(metricResult.metric.weight * 100).toFixed(0)}%
              </Badge>
              <div className={`inline-flex items-center gap-2 rounded-lg border ${scoreColorClass} text-sm font-medium px-2 py-1`}>
                <span>{metricResult.score.toFixed(1)}</span>
              </div>
              {isExpanded ? (
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
            <p className="text-sm text-muted-foreground leading-relaxed">{metricResult.reasoning}</p>
          </div>

          {/* Improvement Advice */}
          <div>
            <h4 className="font-medium mb-2">Improvement Recommendations</h4>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {metricResult.improvement_advice}
            </p>
          </div>

          {/* Examples */}
          {metricResult.positive_examples && metricResult.positive_examples.length > 0 && (
            <div>
              <h4 className="font-medium mb-2 text-green-700">Positive Examples</h4>
              <div className="space-y-2">
                {metricResult.positive_examples.map((example, idx) => (
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

          {metricResult.improvement_examples && metricResult.improvement_examples.length > 0 && (
            <div>
              <h4 className="font-medium mb-2 text-orange-700">Areas for Improvement</h4>
              <div className="space-y-2">
                {metricResult.improvement_examples.map((example, idx) => (
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
            <Progress value={metricResult.confidence * 100} className="w-20 h-2" />
            <span>{(metricResult.confidence * 100).toFixed(0)}%</span>
          </div>
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
};

export default MetricResultCard;