"""
Monitor de Sistema - Recursos de Hardware
Baseado no PRD - Seção 5: Monitoramento de Recursos
"""

import asyncio
import logging
import platform
from datetime import datetime
from typing import List, Optional

import psutil
import torch
from app.models.system import SystemResources, GPUInfo, CPUInfo, MemoryInfo, DiskInfo, SystemStatus
from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    logger.warning("GPUtil não disponível - monitoramento de GPU desabilitado")

try:
    import py3nvml.py3nvml as nvml
    nvml.nvmlInit()
    NVML_AVAILABLE = True
except Exception:
    NVML_AVAILABLE = False
    logger.warning("NVML não disponível - informações detalhadas de GPU desabilitadas")


class SystemMonitor:
    """Monitor de recursos do sistema"""
    
    def __init__(self):
        self.running = False
        self.start_time = datetime.now()
        self._last_resources: Optional[SystemResources] = None
        
    async def start(self):
        """Iniciar monitoramento"""
        self.running = True
        self.start_time = datetime.now()
        logger.info("🔍 Monitor de sistema iniciado")
        
    async def stop(self):
        """Parar monitoramento"""
        self.running = False
        logger.info("🛑 Monitor de sistema parado")
        
    def get_timestamp(self) -> datetime:
        """Obter timestamp atual"""
        return datetime.now()
        
    async def get_cpu_info(self) -> CPUInfo:
        """Obter informações da CPU"""
        try:
            # Uso da CPU (média de 1 segundo)
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Informações básicas
            cpu_count = psutil.cpu_count(logical=False)  # Cores físicos
            cpu_threads = psutil.cpu_count(logical=True)  # Threads lógicas
            
            # Frequência
            cpu_freq = psutil.cpu_freq()
            frequency = cpu_freq.current if cpu_freq else None
            
            # Temperatura (se disponível)
            temperature = None
            try:
                if hasattr(psutil, "sensors_temperatures"):
                    temps = psutil.sensors_temperatures()
                    if temps:
                        # Tentar obter temperatura da CPU
                        for name, entries in temps.items():
                            if "cpu" in name.lower() or "core" in name.lower():
                                if entries:
                                    temperature = entries[0].current
                                    break
            except Exception:
                pass
                
            return CPUInfo(
                cores=cpu_count or 1,
                threads=cpu_threads or 1,
                usage_percent=cpu_percent,
                frequency=frequency,
                temperature=temperature
            )
            
        except Exception as e:
            logger.error(f"Erro ao obter informações da CPU: {e}")
            return CPUInfo(cores=1, threads=1, usage_percent=0.0)
    
    async def get_memory_info(self) -> MemoryInfo:
        """Obter informações da memória"""
        try:
            memory = psutil.virtual_memory()
            
            return MemoryInfo(
                total=int(memory.total / 1024 / 1024),  # MB
                used=int(memory.used / 1024 / 1024),    # MB
                free=int(memory.free / 1024 / 1024),    # MB
                available=int(memory.available / 1024 / 1024),  # MB
                usage_percent=memory.percent
            )
            
        except Exception as e:
            logger.error(f"Erro ao obter informações da memória: {e}")
            return MemoryInfo(total=0, used=0, free=0, available=0, usage_percent=0.0)
    
    async def get_gpu_info(self) -> Optional[List[GPUInfo]]:
        """Obter informações das GPUs"""
        if not GPU_AVAILABLE:
            return None
            
        try:
            gpus = []
            
            # Verificar se PyTorch detecta CUDA
            cuda_available = torch.cuda.is_available()
            if not cuda_available:
                return None
                
            # Usar GPUtil para informações básicas
            gpu_list = GPUtil.getGPUs()
            
            for i, gpu in enumerate(gpu_list):
                gpu_info = GPUInfo(
                    id=i,
                    name=gpu.name,
                    memory_total=int(gpu.memoryTotal),
                    memory_used=int(gpu.memoryUsed),
                    memory_free=int(gpu.memoryFree),
                    utilization=gpu.load * 100,
                    temperature=gpu.temperature if hasattr(gpu, 'temperature') else None,
                    available=True
                )
                
                # Tentar obter informações adicionais com NVML
                if NVML_AVAILABLE:
                    try:
                        handle = nvml.nvmlDeviceGetHandleByIndex(i)
                        
                        # Consumo de energia
                        try:
                            power = nvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # mW para W
                            gpu_info.power_draw = power
                        except:
                            pass
                            
                        # Temperatura mais precisa
                        try:
                            temp = nvml.nvmlDeviceGetTemperature(handle, nvml.NVML_TEMPERATURE_GPU)
                            gpu_info.temperature = temp
                        except:
                            pass
                            
                    except Exception as e:
                        logger.debug(f"Erro ao obter informações NVML para GPU {i}: {e}")
                
                gpus.append(gpu_info)
                
            return gpus if gpus else None
            
        except Exception as e:
            logger.error(f"Erro ao obter informações das GPUs: {e}")
            return None
    
    async def get_disk_info(self) -> Optional[List[DiskInfo]]:
        """Obter informações dos discos"""
        try:
            disks = []
            
            # Obter informações dos pontos de montagem
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    disk_info = DiskInfo(
                        path=partition.mountpoint,
                        total=int(usage.total / 1024 / 1024),  # MB
                        used=int(usage.used / 1024 / 1024),    # MB
                        free=int(usage.free / 1024 / 1024),    # MB
                        usage_percent=(usage.used / usage.total) * 100
                    )
                    
                    disks.append(disk_info)
                    
                except PermissionError:
                    # Ignorar partições sem permissão
                    continue
                except Exception as e:
                    logger.debug(f"Erro ao obter informações do disco {partition.mountpoint}: {e}")
                    continue
                    
            return disks if disks else None
            
        except Exception as e:
            logger.error(f"Erro ao obter informações dos discos: {e}")
            return None
    
    async def get_resources(self) -> SystemResources:
        """Obter recursos completos do sistema"""
        try:
            # Obter informações de todos os componentes
            cpu_info = await self.get_cpu_info()
            memory_info = await self.get_memory_info()
            gpu_info = await self.get_gpu_info()
            disk_info = await self.get_disk_info()
            
            resources = SystemResources(
                timestamp=self.get_timestamp(),
                cpu=cpu_info,
                memory=memory_info,
                gpu=gpu_info,
                disk=disk_info
            )
            
            # Cache do último resultado
            self._last_resources = resources
            
            return resources
            
        except Exception as e:
            logger.error(f"Erro ao obter recursos do sistema: {e}")
            
            # Retornar recursos mínimos em caso de erro
            return SystemResources(
                timestamp=self.get_timestamp(),
                cpu=CPUInfo(cores=1, threads=1, usage_percent=0.0),
                memory=MemoryInfo(total=0, used=0, free=0, available=0, usage_percent=0.0)
            )
    
    async def get_system_status(self, active_jobs: int = 0, total_jobs: int = 0) -> SystemStatus:
        """Obter status geral do sistema"""
        try:
            # Uptime
            uptime = (datetime.now() - self.start_time).total_seconds()
            
            # Load average (apenas em sistemas Unix)
            load_average = None
            try:
                if hasattr(psutil, "getloadavg"):
                    load_average = list(psutil.getloadavg())
            except Exception:
                pass
            
            # Verificar se GPU está disponível
            gpu_available = False
            if torch.cuda.is_available():
                gpu_available = True
            
            # Obter recursos atuais
            resources = await self.get_resources()
            
            # Determinar status
            status = "healthy"
            warnings = []
            
            # Verificar uso de memória
            if resources.memory.usage_percent > 90:
                status = "critical"
                warnings.append("Uso de memória crítico (>90%)")
            elif resources.memory.usage_percent > 80:
                status = "warning"
                warnings.append("Uso de memória alto (>80%)")
            
            # Verificar uso de CPU
            if resources.cpu.usage_percent > 95:
                status = "critical"
                warnings.append("Uso de CPU crítico (>95%)")
            elif resources.cpu.usage_percent > 85:
                if status != "critical":
                    status = "warning"
                warnings.append("Uso de CPU alto (>85%)")
            
            # Verificar GPU se disponível
            if resources.gpu:
                for gpu in resources.gpu:
                    if gpu.memory_usage_percent > settings.GPU_MEMORY_THRESHOLD * 100:
                        status = "critical"
                        warnings.append(f"GPU {gpu.id} com memória crítica ({gpu.memory_usage_percent:.1f}%)")
            
            return SystemStatus(
                status=status,
                uptime=uptime,
                load_average=load_average,
                active_jobs=active_jobs,
                total_jobs=total_jobs,
                gpu_available=gpu_available,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Erro ao obter status do sistema: {e}")
            return SystemStatus(
                status="error",
                uptime=0.0,
                active_jobs=active_jobs,
                total_jobs=total_jobs,
                gpu_available=False,
                warnings=[f"Erro no monitoramento: {str(e)}"]
            )