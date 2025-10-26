import { useState, useEffect } from 'react';
import { TrainingJob } from '../types/training';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { Separator } from './ui/separator';
import { MetricsChart } from './MetricsChart';
import { ArrowLeft, Download, ExternalLink, StopCircle, Clock, TrendingUp, Target, Zap } from 'lucide-react';
import { formatETA, formatDuration } from '../lib/mockData';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from './ui/alert-dialog';

interface JobDetailProps {
  job: TrainingJob;
  onBack: () => void;
}

export function JobDetail({ job: initialJob, onBack }: JobDetailProps) {
  const [job, setJob] = useState<TrainingJob>(initialJob);
  const [historicalData, setHistoricalData] = useState<Array<{
    epoch: number;
    mAP50: number;
    box_loss: number;
    precision: number;
    recall: number;
  }>>([]);

  // Generate historical data based on current epoch
  useEffect(() => {
    if (job.status === 'training' && job.current_epoch > 0) {
      const data = [];
      for (let i = 1; i <= job.current_epoch; i++) {
        const progress = i / job.current_epoch;
        data.push({
          epoch: i,
          mAP50: Math.min(0.3 + progress * 0.6 + Math.random() * 0.05, 0.95),
          box_loss: Math.max(0.08 - progress * 0.05 - Math.random() * 0.01, 0.015),
          precision: Math.min(0.5 + progress * 0.35 + Math.random() * 0.05, 0.92),
          recall: Math.min(0.45 + progress * 0.38 + Math.random() * 0.05, 0.89),
        });
      }
      setHistoricalData(data);
    }
  }, [job.current_epoch, job.status]);

  // Simulate real-time updates
  useEffect(() => {
    if (job.status !== 'training') return;

    const interval = setInterval(() => {
      setJob((prevJob) => {
        if (prevJob.current_epoch >= prevJob.total_epochs) return prevJob;

        const newEpoch = Math.min(prevJob.current_epoch + 1, prevJob.total_epochs);
        const newProgress = (newEpoch / prevJob.total_epochs) * 100;

        return {
          ...prevJob,
          current_epoch: newEpoch,
          progress: newProgress,
          metrics: {
            ...prevJob.metrics,
            current: prevJob.metrics.current ? {
              ...prevJob.metrics.current,
              mAP50: Math.min(prevJob.metrics.current.mAP50 + Math.random() * 0.005, 0.99),
              box_loss: Math.max(prevJob.metrics.current.box_loss - Math.random() * 0.001, 0.01),
              precision: Math.min(prevJob.metrics.current.precision + Math.random() * 0.003, 0.95),
              recall: Math.min(prevJob.metrics.current.recall + Math.random() * 0.004, 0.92),
            } : undefined,
          },
          eta_seconds: prevJob.eta_seconds ? Math.max(prevJob.eta_seconds - 30, 0) : 0,
        };
      });
    }, 5000);

    return () => clearInterval(interval);
  }, [job.status]);

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

  return (
    <div className="min-h-screen bg-background">
      <div className="container max-w-7xl mx-auto p-6 space-y-6 animate-fadeIn">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={onBack} className="hover:bg-accent">
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="flex-1">
            <h1 className="flex items-center gap-3">
              {job.model_name}
            </h1>
            <p className="text-muted-foreground mt-1 font-mono text-sm">ID: {job.job_id}</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="default" className="px-3 py-1.5">
              <div className={`w-2 h-2 rounded-full mr-2 ${getStatusColor(job.status)} ${job.status === 'training' ? 'animate-pulse' : ''}`} />
              {job.status}
            </Badge>
          </div>
        </div>

        {/* Progress Bar */}
        <Card className="border-l-4 border-l-primary">
          <CardContent className="p-6">
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Progresso do Treinamento</span>
                <span className="text-3xl font-mono">{job.progress.toFixed(1)}%</span>
              </div>
              <Progress value={job.progress} className="h-4" />
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Training Progress */}
            {job.status === 'training' && (
              <Card>
                <CardHeader>
                  <CardTitle>📊 Progresso do Treinamento</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <p className="text-sm text-muted-foreground">Época Atual</p>
                      <p className="text-2xl">{job.current_epoch} / {job.total_epochs}</p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-sm text-muted-foreground">Tempo Decorrido</p>
                      <p className="text-2xl">
                        {job.started_at ? formatDuration(job.started_at) : '--'}
                      </p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-sm text-muted-foreground">Tempo Restante (ETA)</p>
                      <p className="text-2xl">{formatETA(job.eta_seconds || 0)}</p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-sm text-muted-foreground">Início</p>
                      <p className="text-lg">
                        {job.started_at ? new Date(job.started_at).toLocaleString('pt-BR') : '--'}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Live Metrics */}
            {job.metrics.current && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <span className="text-xl">📈</span>
                    Métricas Atuais
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="space-y-2 p-4 rounded-lg bg-blue-50 dark:bg-blue-950/20 border-2 border-blue-200 dark:border-blue-800">
                      <div className="flex items-center gap-2">
                        <TrendingUp className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                        <p className="text-sm text-muted-foreground">mAP50</p>
                      </div>
                      <p className="text-3xl font-mono">{job.metrics.current.mAP50.toFixed(3)}</p>
                    </div>
                    <div className="space-y-2 p-4 rounded-lg bg-purple-50 dark:bg-purple-950/20 border-2 border-purple-200 dark:border-purple-800">
                      <div className="flex items-center gap-2">
                        <Target className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                        <p className="text-sm text-muted-foreground">mAP50-95</p>
                      </div>
                      <p className="text-3xl font-mono">{job.metrics.current.mAP50_95.toFixed(3)}</p>
                    </div>
                    <div className="space-y-2 p-4 rounded-lg bg-green-50 dark:bg-green-950/20 border-2 border-green-200 dark:border-green-800">
                      <div className="flex items-center gap-2">
                        <Zap className="w-4 h-4 text-green-600 dark:text-green-400" />
                        <p className="text-sm text-muted-foreground">Precision</p>
                      </div>
                      <p className="text-3xl font-mono">{job.metrics.current.precision.toFixed(3)}</p>
                    </div>
                    <div className="space-y-2 p-4 rounded-lg bg-orange-50 dark:bg-orange-950/20 border-2 border-orange-200 dark:border-orange-800">
                      <div className="flex items-center gap-2">
                        <Target className="w-4 h-4 text-orange-600 dark:text-orange-400" />
                        <p className="text-sm text-muted-foreground">Recall</p>
                      </div>
                      <p className="text-3xl font-mono">{job.metrics.current.recall.toFixed(3)}</p>
                    </div>
                    <div className="space-y-2 p-4 rounded-lg bg-muted border">
                      <p className="text-sm text-muted-foreground">Box Loss</p>
                      <p className="text-2xl font-mono">{job.metrics.current.box_loss.toFixed(4)}</p>
                    </div>
                    <div className="space-y-2 p-4 rounded-lg bg-muted border">
                      <p className="text-sm text-muted-foreground">Cls Loss</p>
                      <p className="text-2xl font-mono">{job.metrics.current.cls_loss.toFixed(4)}</p>
                    </div>
                    <div className="space-y-2 p-4 rounded-lg bg-muted border">
                      <p className="text-sm text-muted-foreground">DFL Loss</p>
                      <p className="text-2xl font-mono">{job.metrics.current.dfl_loss.toFixed(4)}</p>
                    </div>
                  </div>

                  {job.metrics.best && (
                    <>
                      <Separator className="my-6" />
                      <div>
                        <p className="text-sm text-muted-foreground mb-4 flex items-center gap-2">
                          <span className="text-lg">🏆</span>
                          Melhor Resultado
                        </p>
                        <div className="grid grid-cols-3 gap-4">
                          <div className="p-4 rounded-lg bg-green-50 dark:bg-green-950/20 border-2 border-green-600 dark:border-green-400">
                            <p className="text-sm text-muted-foreground mb-1">mAP50</p>
                            <p className="text-2xl text-green-600 dark:text-green-400 font-mono">{job.metrics.best.mAP50.toFixed(3)}</p>
                          </div>
                          <div className="p-4 rounded-lg bg-green-50 dark:bg-green-950/20 border-2 border-green-600 dark:border-green-400">
                            <p className="text-sm text-muted-foreground mb-1">mAP50-95</p>
                            <p className="text-2xl text-green-600 dark:text-green-400 font-mono">{job.metrics.best.mAP50_95.toFixed(3)}</p>
                          </div>
                          <div className="p-4 rounded-lg bg-muted border-2">
                            <p className="text-sm text-muted-foreground mb-1">Época</p>
                            <p className="text-2xl font-mono">{job.metrics.best.epoch}</p>
                          </div>
                        </div>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Charts */}
            {historicalData.length > 0 && (
              <MetricsChart data={historicalData} />
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Configuration */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <span className="text-lg">⚙️</span>
                  Configuração
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="p-3 rounded-lg bg-muted">
                  <p className="text-xs text-muted-foreground mb-1">Modelo Base</p>
                  <p className="font-mono">{job.config.base_model}</p>
                </div>
                <Separator />
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-lg bg-muted">
                    <p className="text-xs text-muted-foreground mb-1">Imagem</p>
                    <p className="font-mono">{job.config.image_size}px</p>
                  </div>
                  <div className="p-3 rounded-lg bg-muted">
                    <p className="text-xs text-muted-foreground mb-1">Batch</p>
                    <p className="font-mono">{job.config.batch_size}</p>
                  </div>
                </div>
                <Separator />
                <div className="p-3 rounded-lg bg-muted">
                  <p className="text-xs text-muted-foreground mb-1">Learning Rate</p>
                  <p className="font-mono">{job.config.learning_rate}</p>
                </div>
                <Separator />
                <div className="p-3 rounded-lg bg-muted">
                  <p className="text-xs text-muted-foreground mb-1">Otimizador</p>
                  <p className="font-mono">{job.config.optimizer}</p>
                </div>
              </CardContent>
            </Card>

            {/* Dataset Info */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <span className="text-lg">📦</span>
                  Dataset
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="p-4 rounded-lg bg-primary/10 border-2 border-primary/20">
                  <p className="text-xs text-muted-foreground mb-1">Total de Imagens</p>
                  <p className="text-3xl font-mono">{job.dataset_info.total_images}</p>
                </div>
                <Separator />
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-lg bg-muted">
                    <p className="text-xs text-muted-foreground mb-1">Treino</p>
                    <p className="text-xl font-mono">{job.dataset_info.train_images}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-muted">
                    <p className="text-xs text-muted-foreground mb-1">Validação</p>
                    <p className="text-xl font-mono">{job.dataset_info.val_images}</p>
                  </div>
                </div>
                <Separator />
                <div>
                  <p className="text-sm text-muted-foreground mb-3">Classes Detectadas</p>
                  <div className="flex flex-wrap gap-2">
                    {job.dataset_info.classes.map((cls, idx) => (
                      <Badge key={cls} variant="secondary" className="px-3 py-1">
                        {cls}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Actions */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <span className="text-lg">🎬</span>
                  Ações
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {job.status === 'training' && (
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button variant="destructive" className="w-full">
                        <StopCircle className="w-4 h-4 mr-2" />
                        Cancelar Treinamento
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Cancelar Treinamento?</AlertDialogTitle>
                        <AlertDialogDescription>
                          Esta ação não pode ser desfeita. O progresso atual será perdido e o job será marcado como cancelado.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Voltar</AlertDialogCancel>
                        <AlertDialogAction className="bg-destructive hover:bg-destructive/90">
                          Sim, Cancelar Job
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                )}
                <Button variant="outline" className="w-full">
                  <Download className="w-4 h-4 mr-2" />
                  Download Logs
                </Button>
                <Button variant="outline" className="w-full">
                  <ExternalLink className="w-4 h-4 mr-2" />
                  Ver no App Principal
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}