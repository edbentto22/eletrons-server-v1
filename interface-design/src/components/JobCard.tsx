import { TrainingJob } from '../types/training';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Button } from './ui/button';
import { Activity, Clock, TrendingUp } from 'lucide-react';
import { formatETA } from '../lib/mockData';

interface JobCardProps {
  job: TrainingJob;
  onViewDetails: (jobId: string) => void;
}

export function JobCard({ job, onViewDetails }: JobCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'training':
        return 'bg-blue-500';
      case 'completed':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      case 'queued':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'training':
        return 'default';
      case 'completed':
        return 'default';
      case 'failed':
        return 'destructive';
      default:
        return 'secondary';
    }
  };

  return (
    <Card className="hover:shadow-md hover:border-foreground/20 transition-all duration-200 group">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="flex items-center gap-3 group-hover:text-primary transition-colors">
              <span>{job.model_name}</span>
              <Badge variant={getStatusBadgeVariant(job.status)} className="ml-auto">
                {job.status === 'training' && '🔥 '}
                {job.status}
              </Badge>
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1.5 font-mono">
              {job.job_id.substring(0, 8)}...
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {job.status === 'training' && (
          <>
            <div className="space-y-2.5">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">
                  Época {job.current_epoch}/{job.total_epochs}
                </span>
                <span className="font-mono">{job.progress.toFixed(1)}%</span>
              </div>
              <div className="relative">
                <Progress value={job.progress} className="h-2.5" />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 pt-2">
              <div className="flex flex-col gap-1.5 p-3 rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800">
                <div className="flex items-center gap-1.5">
                  <TrendingUp className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
                  <span className="text-xs text-muted-foreground">mAP50</span>
                </div>
                <p className="font-mono">{(job.metrics.current?.mAP50 || 0).toFixed(3)}</p>
              </div>
              <div className="flex flex-col gap-1.5 p-3 rounded-lg bg-orange-50 dark:bg-orange-950/20 border border-orange-200 dark:border-orange-800">
                <div className="flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-orange-600 dark:text-orange-400" />
                  <span className="text-xs text-muted-foreground">Loss</span>
                </div>
                <p className="font-mono">{(job.metrics.current?.box_loss || 0).toFixed(4)}</p>
              </div>
              <div className="flex flex-col gap-1.5 p-3 rounded-lg bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800">
                <div className="flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-green-600 dark:text-green-400" />
                  <span className="text-xs text-muted-foreground">ETA</span>
                </div>
                <p className="font-mono text-sm">{formatETA(job.eta_seconds || 0)}</p>
              </div>
            </div>
          </>
        )}

        {job.status === 'queued' && (
          <div className="text-sm text-muted-foreground p-4 bg-muted rounded-lg text-center">
            Aguardando GPU disponível...
          </div>
        )}

        {job.status === 'completed' && job.metrics.best && (
          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 bg-green-50 dark:bg-green-950/20 rounded-lg border border-green-200 dark:border-green-800">
              <p className="text-xs text-muted-foreground mb-1">Final mAP50</p>
              <p className="text-xl text-green-600 dark:text-green-400 font-mono">{job.metrics.best.mAP50.toFixed(3)}</p>
            </div>
            <div className="p-3 bg-muted rounded-lg border">
              <p className="text-xs text-muted-foreground mb-1">Best Epoch</p>
              <p className="text-xl font-mono">{job.metrics.best.epoch}</p>
            </div>
          </div>
        )}

        <Button
          variant="outline"
          size="sm"
          className="w-full group-hover:bg-primary group-hover:text-primary-foreground transition-colors"
          onClick={() => onViewDetails(job.job_id)}
        >
          Ver Detalhes →
        </Button>
      </CardContent>
    </Card>
  );
}