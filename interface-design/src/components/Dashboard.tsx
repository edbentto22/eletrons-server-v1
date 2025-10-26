import { useState, useEffect } from 'react';
import { TrainingJob } from '../types/training';
import { mockJobs, mockSystemResources, getJobStats } from '../lib/mockData';
import { listJobs } from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { JobCard } from './JobCard';
import { SystemResources } from './SystemResources';
import { Activity, Clock, CheckCircle2, XCircle, RefreshCw } from 'lucide-react';

interface DashboardProps {
  onViewJob: (jobId: string) => void;
}

export function Dashboard({ onViewJob }: DashboardProps) {
  const [jobs, setJobs] = useState<TrainingJob[]>(mockJobs);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  // Fetch jobs from API if available
  useEffect(() => {
    (async () => {
      const liveJobs = await listJobs();
      if (liveJobs && Array.isArray(liveJobs) && liveJobs.length > 0) {
        setJobs(liveJobs);
      }
    })();
  }, []);

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setJobs((prevJobs) =>
        prevJobs.map((job) => {
          if (job.status === 'training' && job.current_epoch < job.total_epochs) {
            const newEpoch = Math.min(job.current_epoch + 1, job.total_epochs);
            const newProgress = (newEpoch / job.total_epochs) * 100;
            return {
              ...job,
              current_epoch: newEpoch,
              progress: newProgress,
              metrics: {
                ...job.metrics,
                current: job.metrics.current ? {
                  ...job.metrics.current,
                  mAP50: Math.min(job.metrics.current.mAP50 + Math.random() * 0.005, 0.99),
                  box_loss: Math.max(job.metrics.current.box_loss - Math.random() * 0.001, 0.01),
                } : undefined,
              },
              eta_seconds: job.eta_seconds ? Math.max(job.eta_seconds - 30, 0) : 0,
            };
          }
          return job;
        })
      );
      setLastUpdate(new Date());
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const stats = getJobStats(jobs);
  const activeJobs = jobs.filter((j) => j.status === 'training');
  const queuedJobs = jobs.filter((j) => j.status === 'queued');

  return (
    <div className="min-h-screen bg-background">
      <div className="container max-w-7xl mx-auto p-6 space-y-6 animate-fadeIn">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="flex items-center gap-3">
              <span className="text-4xl">🎯</span>
              <span>YOLO Training Server</span>
            </h1>
            <p className="text-muted-foreground mt-2">
              Servidor de Treinamento Ultralytics YOLO com FastAPI
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="default" className="bg-green-500 hover:bg-green-600 text-white px-3 py-1.5">
              <div className="w-2 h-2 rounded-full bg-white mr-2 animate-pulse" />
              Sistema Online
            </Badge>
            <div className="text-sm text-muted-foreground flex items-center gap-2 bg-muted px-3 py-1.5 rounded-lg">
              <RefreshCw className="w-3.5 h-3.5" />
              <span>{lastUpdate.toLocaleTimeString('pt-BR')}</span>
            </div>
          </div>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="border-l-4 border-l-blue-500">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2 text-muted-foreground">
                <Activity className="w-4 h-4 text-blue-500" />
                Jobs Ativos
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-4xl">{stats.active}</div>
              <p className="text-xs text-muted-foreground mt-1">em treinamento</p>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-yellow-500">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2 text-muted-foreground">
                <Clock className="w-4 h-4 text-yellow-500" />
                Na Fila
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-4xl">{stats.queued}</div>
              <p className="text-xs text-muted-foreground mt-1">aguardando GPU</p>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-green-500">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2 text-muted-foreground">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                Concluídos
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-4xl">{stats.completed}</div>
              <p className="text-xs text-muted-foreground mt-1">com sucesso</p>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-red-500">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2 text-muted-foreground">
                <XCircle className="w-4 h-4 text-red-500" />
                Falhas
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-4xl">{stats.failed}</div>
              <p className="text-xs text-muted-foreground mt-1">erros registrados</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Active Jobs */}
          <div className="lg:col-span-2 space-y-6">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <span className="text-2xl">🔥</span>
                <h2>Jobs em Treinamento</h2>
              </div>
              {activeJobs.length > 0 ? (
                <div className="grid gap-4">
                  {activeJobs.map((job) => (
                    <JobCard key={job.job_id} job={job} onViewDetails={onViewJob} />
                  ))}
                </div>
              ) : (
                <Card className="border-dashed">
                  <CardContent className="p-12 text-center">
                    <div className="text-4xl mb-3 opacity-20">⏸️</div>
                    <p className="text-muted-foreground">Nenhum job em treinamento no momento</p>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Queued Jobs */}
            {queuedJobs.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-2xl">⏳</span>
                  <h2>Jobs na Fila</h2>
                </div>
                <Card>
                  <CardContent className="p-4">
                    <ul className="space-y-2">
                      {queuedJobs.map((job, index) => (
                        <li
                          key={job.job_id}
                          className="flex items-center justify-between p-4 rounded-lg hover:bg-accent cursor-pointer transition-all duration-200 group border border-transparent hover:border-border"
                          onClick={() => onViewJob(job.job_id)}
                        >
                          <div className="flex items-center gap-3">
                            <Badge variant="secondary" className="px-2.5">#{index + 1}</Badge>
                            <div>
                              <p className="group-hover:text-foreground transition-colors">{job.model_name}</p>
                              <p className="text-sm text-muted-foreground">
                                {job.total_epochs} épocas • {job.dataset_info.total_images} imagens
                              </p>
                            </div>
                          </div>
                          <Badge variant="outline" className="text-yellow-600 border-yellow-600">
                            Aguardando
                          </Badge>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>

          {/* System Resources */}
          <div>
            <SystemResources resources={mockSystemResources} />
          </div>
        </div>
      </div>
    </div>
  );
}