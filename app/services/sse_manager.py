"""
Gerenciador de Server-Sent Events (SSE)
Baseado no PRD - Seção 9: Atualizações em Tempo Real
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Any, Optional
from fastapi import Request
from fastapi.responses import StreamingResponse

logger = logging.getLogger("sse")


class SSEManager:
    """Gerenciador de conexões SSE"""
    
    def __init__(self):
        # Conexões ativas por tipo
        self.connections: Dict[str, Set[asyncio.Queue]] = {
            "jobs": set(),
            "system": set(),
            "training": set()
        }
        
        # Filas por job específico
        self.job_connections: Dict[str, Set[asyncio.Queue]] = {}
        
        # Último estado conhecido (para novos clientes)
        self.last_state: Dict[str, Any] = {}
        
        logger.info("📡 SSE Manager inicializado")
        
    async def add_connection(self, connection_type: str, queue: asyncio.Queue, job_id: Optional[str] = None):
        """Adicionar nova conexão SSE"""
        try:
            if connection_type in self.connections:
                self.connections[connection_type].add(queue)
                
            # Conexão específica para job
            if job_id:
                if job_id not in self.job_connections:
                    self.job_connections[job_id] = set()
                self.job_connections[job_id].add(queue)
                
            # Enviar estado inicial se disponível
            if connection_type in self.last_state:
                await self._send_to_queue(queue, {
                    "type": f"{connection_type}_state",
                    "data": self.last_state[connection_type],
                    "timestamp": datetime.now().isoformat()
                })
                
            logger.info(f"➕ Nova conexão SSE: {connection_type}" + (f" (job: {job_id})" if job_id else ""))
            
        except Exception as e:
            logger.error(f"Erro ao adicionar conexão SSE: {e}")
            
    async def remove_connection(self, connection_type: str, queue: asyncio.Queue, job_id: Optional[str] = None):
        """Remover conexão SSE"""
        try:
            if connection_type in self.connections:
                self.connections[connection_type].discard(queue)
                
            if job_id and job_id in self.job_connections:
                self.job_connections[job_id].discard(queue)
                
                # Limpar se não há mais conexões para este job
                if not self.job_connections[job_id]:
                    del self.job_connections[job_id]
                    
            logger.info(f"➖ Conexão SSE removida: {connection_type}" + (f" (job: {job_id})" if job_id else ""))
            
        except Exception as e:
            logger.error(f"Erro ao remover conexão SSE: {e}")
            
    async def broadcast_job_update(self, job_id: str, event_type: str, data: Any):
        """Enviar atualização para todas as conexões de jobs"""
        message = {
            "type": "job_update",
            "job_id": job_id,
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Enviar para conexões gerais de jobs
        await self._broadcast_to_type("jobs", message)
        
        # Enviar para conexões específicas do job
        if job_id in self.job_connections:
            await self._broadcast_to_job(job_id, message)
            
        # Atualizar último estado
        if "jobs" not in self.last_state:
            self.last_state["jobs"] = {}
        self.last_state["jobs"][job_id] = message
        
    async def broadcast_training_metrics(self, job_id: str, metrics: Dict[str, Any]):
        """Enviar métricas de treinamento"""
        message = {
            "type": "training_metrics",
            "job_id": job_id,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
        # Enviar para conexões de treinamento
        await self._broadcast_to_type("training", message)
        
        # Enviar para conexões específicas do job
        if job_id in self.job_connections:
            await self._broadcast_to_job(job_id, message)
            
    async def broadcast_system_update(self, system_data: Dict[str, Any]):
        """Enviar atualização do sistema"""
        message = {
            "type": "system_update",
            "data": system_data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self._broadcast_to_type("system", message)
        
        # Atualizar último estado
        self.last_state["system"] = system_data
        
    async def _broadcast_to_type(self, connection_type: str, message: Dict[str, Any]):
        """Enviar mensagem para todas as conexões de um tipo"""
        if connection_type not in self.connections:
            return
            
        dead_connections = set()
        
        for queue in self.connections[connection_type].copy():
            try:
                await self._send_to_queue(queue, message)
            except Exception as e:
                logger.warning(f"Conexão SSE morta detectada ({connection_type}): {e}")
                dead_connections.add(queue)
                
        # Remover conexões mortas
        for queue in dead_connections:
            self.connections[connection_type].discard(queue)
            
    async def _broadcast_to_job(self, job_id: str, message: Dict[str, Any]):
        """Enviar mensagem para conexões específicas de um job"""
        if job_id not in self.job_connections:
            return
            
        dead_connections = set()
        
        for queue in self.job_connections[job_id].copy():
            try:
                await self._send_to_queue(queue, message)
            except Exception as e:
                logger.warning(f"Conexão SSE morta detectada (job {job_id}): {e}")
                dead_connections.add(queue)
                
        # Remover conexões mortas
        for queue in dead_connections:
            self.job_connections[job_id].discard(queue)
            
    async def _send_to_queue(self, queue: asyncio.Queue, message: Dict[str, Any]):
        """Enviar mensagem para uma fila específica"""
        try:
            # Formato SSE
            sse_data = f"data: {json.dumps(message, ensure_ascii=False)}\n\n"
            await queue.put(sse_data)
        except asyncio.QueueFull:
            logger.warning("Fila SSE cheia - descartando mensagem")
        except Exception as e:
            logger.error(f"Erro ao enviar para fila SSE: {e}")
            raise
            
    async def create_event_stream(self, connection_type: str, job_id: Optional[str] = None):
        """Criar stream de eventos SSE"""
        queue = asyncio.Queue(maxsize=100)
        
        try:
            # Adicionar conexão
            await self.add_connection(connection_type, queue, job_id)
            
            # Enviar evento de conexão estabelecida
            await self._send_to_queue(queue, {
                "type": "connected",
                "connection_type": connection_type,
                "job_id": job_id,
                "timestamp": datetime.now().isoformat()
            })
            
            # Stream de eventos
            while True:
                try:
                    # Aguardar próximo evento com timeout
                    data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield data
                    
                except asyncio.TimeoutError:
                    # Enviar heartbeat para manter conexão viva
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
                    
        except asyncio.CancelledError:
            logger.info(f"Stream SSE cancelado: {connection_type}" + (f" (job: {job_id})" if job_id else ""))
            
        except Exception as e:
            logger.error(f"Erro no stream SSE: {e}")
            
        finally:
            # Remover conexão
            await self.remove_connection(connection_type, queue, job_id)
            
    def get_stats(self) -> Dict[str, Any]:
        """Obter estatísticas das conexões SSE"""
        stats = {
            "total_connections": sum(len(conns) for conns in self.connections.values()),
            "connections_by_type": {
                conn_type: len(conns) for conn_type, conns in self.connections.items()
            },
            "job_connections": {
                job_id: len(conns) for job_id, conns in self.job_connections.items()
            },
            "active_jobs": len(self.job_connections)
        }
        
        return stats
        
    async def cleanup(self):
        """Limpeza ao finalizar"""
        try:
            # Enviar mensagem de desconexão para todas as conexões
            disconnect_message = {
                "type": "server_shutdown",
                "message": "Servidor sendo reiniciado",
                "timestamp": datetime.now().isoformat()
            }
            
            for connection_type in self.connections:
                await self._broadcast_to_type(connection_type, disconnect_message)
                
            # Limpar todas as conexões
            for connection_type in self.connections:
                self.connections[connection_type].clear()
                
            self.job_connections.clear()
            
            logger.info("🧹 SSE Manager finalizado")
            
        except Exception as e:
            logger.error(f"Erro no cleanup do SSE Manager: {e}")


# Instância global do gerenciador SSE
sse_manager = SSEManager()


async def create_sse_response(connection_type: str, job_id: Optional[str] = None) -> StreamingResponse:
    """Criar resposta SSE"""
    return StreamingResponse(
        sse_manager.create_event_stream(connection_type, job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )