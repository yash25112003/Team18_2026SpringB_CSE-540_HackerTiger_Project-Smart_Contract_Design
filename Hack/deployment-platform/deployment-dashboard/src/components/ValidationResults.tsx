import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { CheckCircle, XCircle, AlertTriangle, Shield, Users, Target } from "lucide-react";

interface ValidationResult {
  verdict: string;
  valid: boolean;
  ai_score: number;
  consensus_score: number;
  top_reason: string;
  agent_count: number;
  validation_summary?: {
    total_agents: number;
    passed_agents: number;
    failed_agents: number;
  };
}

interface ValidationResultsProps {
  validation: ValidationResult;
  loading?: boolean;
}

export default function ValidationResults({ validation, loading = false }: ValidationResultsProps) {
  const [loadingProgress, setLoadingProgress] = React.useState(0);
  const [loadingMessage, setLoadingMessage] = React.useState("Initializing validation...");

  React.useEffect(() => {
    if (loading) {
      setLoadingProgress(0);
      setLoadingMessage("Initializing validation...");
      
      const messages = [
        { progress: 15, message: "Analyzing security patterns..." },
        { progress: 30, message: "Running compliance checks..." },
        { progress: 45, message: "Evaluating threat models..." },
        { progress: 60, message: "Checking privacy controls..." },
        { progress: 75, message: "Validating dependencies..." },
        { progress: 90, message: "Generating consensus..." },
        { progress: 99, message: "Finalizing results..." }
      ];

      let currentIndex = 0;
      const interval = setInterval(() => {
        if (currentIndex < messages.length) {
          setLoadingProgress(messages[currentIndex].progress);
          setLoadingMessage(messages[currentIndex].message);
          currentIndex++;
        } else {
          clearInterval(interval);
        }
      }, 800);

      return () => clearInterval(interval);
    }
  }, [loading]);

  if (loading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 animate-pulse" />
            Validating Repository...
          </CardTitle>
          <CardDescription>
            Running multi-agent security validation
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                <span className="text-sm text-gray-600">{loadingMessage}</span>
              </div>
              <span className="text-sm font-semibold text-blue-600">{loadingProgress}%</span>
            </div>
            <div className="relative">
              <Progress value={loadingProgress} className="w-full h-3" />
              <div 
                className="absolute top-0 left-0 h-3 bg-blue-600 rounded-full transition-all duration-500"
                style={{ width: `${loadingProgress}%` }}
              />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const getVerdictIcon = () => {
    switch (validation.verdict.toLowerCase()) {
      case 'valid':
        return <CheckCircle className="h-6 w-6 text-green-600" />;
      case 'invalid':
        return <XCircle className="h-6 w-6 text-red-600" />;
      case 'quarantined':
        return <AlertTriangle className="h-6 w-6 text-yellow-600" />;
      default:
        return <Shield className="h-6 w-6 text-gray-600" />;
    }
  };

  const getVerdictColor = () => {
    switch (validation.verdict.toLowerCase()) {
      case 'valid':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'invalid':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'quarantined':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getProgressColor = (score: number) => {
    if (score >= 0.8) return 'bg-green-600';
    if (score >= 0.6) return 'bg-yellow-600';
    return 'bg-red-600';
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-3">
          {getVerdictIcon()}
          <span>Validation Results</span>
          <Badge className={`${getVerdictColor()} font-semibold`}>
            {validation.verdict}
          </Badge>
        </CardTitle>
        <CardDescription>
          Multi-agent blockchain security validation completed
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* AI Score */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-gray-600" />
              <span className="font-medium">AI Security Score</span>
            </div>
            <span className={`font-bold ${getScoreColor(validation.ai_score)}`}>
              {(validation.ai_score * 100).toFixed(0)}%
            </span>
          </div>
          <div className="relative">
            <Progress 
              value={validation.ai_score * 100} 
              className="w-full h-3"
            />
            <div 
              className={`absolute top-0 left-0 h-3 rounded-full transition-all duration-500 ${getProgressColor(validation.ai_score)}`}
              style={{ width: `${validation.ai_score * 100}%` }}
            />
          </div>
        </div>

        {/* Consensus Score */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-gray-600" />
              <span className="font-medium">Agent Consensus</span>
            </div>
            <span className={`font-bold ${getScoreColor(validation.consensus_score)}`}>
              {(validation.consensus_score * 100).toFixed(0)}%
            </span>
          </div>
          <div className="relative">
            <Progress 
              value={validation.consensus_score * 100} 
              className="w-full h-3"
            />
            <div 
              className={`absolute top-0 left-0 h-3 rounded-full transition-all duration-500 ${getProgressColor(validation.consensus_score)}`}
              style={{ width: `${validation.consensus_score * 100}%` }}
            />
          </div>
        </div>

        {/* Agent Summary */}
        {validation.validation_summary && (
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-700">
                {validation.validation_summary.total_agents}
              </div>
              <div className="text-sm text-gray-600">Total Parameters</div>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {validation.validation_summary.passed_agents}
              </div>
              <div className="text-sm text-green-600">Passed</div>
            </div>
            <div className="text-center p-3 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-600">
                {validation.validation_summary.failed_agents}
              </div>
              <div className="text-sm text-red-600">Failed</div>
            </div>
          </div>
        )}

        {/* Top Reason */}
        <div className="p-4 bg-gray-50 rounded-lg">
          <h4 className="font-medium text-gray-900 mb-2">Primary Finding</h4>
          <p className="text-gray-700 text-sm leading-relaxed">
            {validation.top_reason}
          </p>
        </div>

        {/* Validation Details */}
        <div className="text-xs text-gray-500 space-y-1">
          <div>Validated by {validation.agent_count} security agents</div>
          <div>Blockchain guardrails: {validation.valid ? 'PASSED' : 'FAILED'}</div>
        </div>
      </CardContent>
    </Card>
  );
}
