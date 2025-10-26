import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { SystemResources as SystemResourcesType } from '../types/training';
import { Cpu, HardDrive, Monitor, Thermometer } from 'lucide-react';

interface SystemResourcesProps {
  resources: SystemResourcesType;
}

export function SystemResources({ resources }: SystemResourcesProps) {
  const getTemperatureColor = (temp: number) => {
    if (temp > 80) return 'text-red-500';
    if (temp > 70) return 'text-orange-500';
    return 'text-green-500';
  };

  const getUtilizationColor = (util: number) => {
    if (util > 90) return 'bg-red-500';
    if (util > 70) return 'bg-orange-500';
    return 'bg-primary';
  };

  return (
    <Card className="sticky top-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Cpu className="w-5 h-5" />
          Recursos do Sistema
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* GPU */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-950/30">
                <Monitor className="w-4 h-4 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-sm">{resources.gpu.name}</p>
                <p className="text-xs text-muted-foreground">Placa de Vídeo</p>
              </div>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-muted">
              <Thermometer className={`w-4 h-4 ${getTemperatureColor(resources.gpu.temperature)}`} />
              <span className={`text-sm ${getTemperatureColor(resources.gpu.temperature)}`}>
                {resources.gpu.temperature}°C
              </span>
            </div>
          </div>
          
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-muted-foreground">Utilização</span>
                <span className="font-mono">{resources.gpu.utilization.toFixed(0)}%</span>
              </div>
              <div className="relative">
                <Progress value={resources.gpu.utilization} className="h-2.5" />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-muted-foreground">Memória VRAM</span>
                <span className="font-mono">
                  {resources.gpu.memory_used.toFixed(1)} / {resources.gpu.memory_total.toFixed(1)} GB
                </span>
              </div>
              <div className="relative">
                <Progress 
                  value={(resources.gpu.memory_used / resources.gpu.memory_total) * 100} 
                  className="h-2.5" 
                />
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {((resources.gpu.memory_used / resources.gpu.memory_total) * 100).toFixed(0)}% em uso
              </p>
            </div>
          </div>
        </div>

        <div className="border-t pt-4" />

        {/* CPU */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-950/30">
              <Cpu className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-sm">Processador</p>
              <p className="text-xs text-muted-foreground">CPU</p>
            </div>
          </div>
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-muted-foreground">Utilização</span>
              <span className="font-mono">{resources.cpu.utilization}%</span>
            </div>
            <Progress value={resources.cpu.utilization} className="h-2.5" />
          </div>
        </div>

        <div className="border-t pt-4" />

        {/* RAM */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-green-100 dark:bg-green-950/30">
              <HardDrive className="w-4 h-4 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p className="text-sm">Memória RAM</p>
              <p className="text-xs text-muted-foreground">Sistema</p>
            </div>
          </div>
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-muted-foreground">Utilização</span>
              <span className="font-mono">
                {resources.ram.used.toFixed(1)} / {resources.ram.total.toFixed(1)} GB
              </span>
            </div>
            <Progress 
              value={(resources.ram.used / resources.ram.total) * 100} 
              className="h-2.5" 
            />
            <p className="text-xs text-muted-foreground mt-1">
              {((resources.ram.used / resources.ram.total) * 100).toFixed(0)}% em uso
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}