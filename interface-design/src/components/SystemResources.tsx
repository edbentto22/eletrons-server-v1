import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { SystemResources as SystemResourcesType } from '../types/training';
import { Cpu, HardDrive, Monitor, Thermometer, Loader2 } from 'lucide-react';

interface SystemResourcesProps {
  resources: SystemResourcesType;
}

export function SystemResources({ resources }: SystemResourcesProps) {
  if (!resources) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-blue-500" />
            Recursos do Sistema
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-muted-foreground py-8">
            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2" />
            <p>Carregando recursos do sistema...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const getTemperatureColor = (temp: number) => {
    if (temp > 80) return 'text-red-500';
    if (temp > 70) return 'text-orange-500';
    if (temp > 60) return 'text-yellow-500';
    return 'text-green-500';
  };

  const getUtilizationColor = (util: number) => {
    if (util > 90) return 'text-red-500';
    if (util > 70) return 'text-orange-500';
    if (util > 50) return 'text-yellow-500';
    return 'text-green-500';
  };

  // Verificar se resources.gpu existe antes de acessar suas propriedades
  const gpuInfo = resources.gpu ? resources.gpu : null;

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
        {resources.gpu ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-950/30">
                  <Monitor className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <p className="text-sm">{gpuInfo ? gpuInfo.name : 'GPU não disponível'}</p>
                  <p className="text-xs text-muted-foreground">Placa de Vídeo</p>
                </div>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-muted">
                <Thermometer className={`w-4 h-4 ${gpuInfo ? getTemperatureColor(gpuInfo.temperature) : 'text-gray-400'}`} />
                <span className={`text-sm ${gpuInfo ? getTemperatureColor(gpuInfo.temperature) : 'text-gray-400'}`}>
                  {gpuInfo ? `${gpuInfo.temperature}°C` : 'N/A'}
                </span>
              </div>
            </div>
            
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-muted-foreground">Utilização</span>
                  <span className="font-mono">{gpuInfo ? gpuInfo.utilization.toFixed(0) + '%' : 'N/A'}</span>
                </div>
                <div className="relative">
                  <Progress value={gpuInfo ? gpuInfo.utilization : 0} className="h-2.5" />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-muted-foreground">Memória VRAM</span>
                  <span className="font-mono">
                    {gpuInfo ? `${gpuInfo.memory_used.toFixed(1)} / ${gpuInfo.memory_total.toFixed(1)} GB` : 'N/A'}
                  </span>
                </div>
                <div className="relative">
                  <Progress 
                    value={gpuInfo ? (gpuInfo.memory_used / gpuInfo.memory_total) * 100 : 0} 
                    className="h-2.5" 
                  />
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {gpuInfo ? `${((gpuInfo.memory_used / gpuInfo.memory_total) * 100).toFixed(0)}% em uso` : 'N/A'}
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-lg bg-gray-100 dark:bg-gray-950/30">
                  <Monitor className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                </div>
                <div>
                  <p className="text-sm">GPU não disponível</p>
                  <p className="text-xs text-muted-foreground">Placa de Vídeo</p>
                </div>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-muted">
                <Thermometer className="w-4 h-4 text-gray-400" />
                <span className="text-sm text-gray-400">N/A</span>
              </div>
            </div>
            <div className="text-center py-4">
              <p className="text-sm text-muted-foreground">
                GPU não detectada ou não disponível
              </p>
            </div>
          </div>
        )}

        <div className="border-t pt-4" />

        {/* CPU */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-950/30">
              <Cpu className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-sm">Processador</p>
              <p className="text-xs text-muted-foreground">CPU ({resources.cpu.cores} cores)</p>
            </div>
          </div>
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-muted-foreground">Utilização</span>
              <span className="font-mono">{resources.cpu.usage_percent.toFixed(1)}%</span>
            </div>
            <Progress value={resources.cpu.usage_percent} className="h-2.5" />
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
                {(resources.memory.used / 1024).toFixed(1)} / {(resources.memory.total / 1024).toFixed(1)} GB
              </span>
            </div>
            <Progress 
              value={resources.memory.usage_percent} 
              className="h-2.5" 
            />
            <p className="text-xs text-muted-foreground mt-1">
              {resources.memory.usage_percent.toFixed(0)}% em uso
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}