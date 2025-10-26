import { useState, useEffect } from 'react';
import { TrainingJob } from '../types/training';
import { listJobs, getJob } from '../lib/api';

export function useJobs() {
  const [jobs, setJobs] = useState<TrainingJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        setLoading(true);
        const jobsData = await listJobs();
        if (jobsData) {
          setJobs(jobsData);
        } else {
          setError('Falha ao carregar jobs');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erro desconhecido');
      } finally {
        setLoading(false);
      }
    };

    fetchJobs();

    // Atualizar jobs a cada 10 segundos
    const interval = setInterval(fetchJobs, 10000);
    return () => clearInterval(interval);
  }, []);

  const refreshJobs = async () => {
    try {
      setLoading(true);
      const jobsData = await listJobs();
      if (jobsData) {
        setJobs(jobsData);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao atualizar jobs');
    } finally {
      setLoading(false);
    }
  };

  const getJobById = async (jobId: string) => {
    try {
      return await getJob(jobId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao buscar job');
      return null;
    }
  };

  return {
    jobs,
    loading,
    error,
    refreshJobs,
    getJobById,
  };
}

export function useJob(jobId: string) {
  const [job, setJob] = useState<TrainingJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchJob = async () => {
      if (!jobId) return;
      
      try {
        setLoading(true);
        const jobData = await getJob(jobId);
        if (jobData) {
          setJob(jobData);
        } else {
          setError('Job não encontrado');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erro ao carregar job');
      } finally {
        setLoading(false);
      }
    };

    fetchJob();

    // Atualizar job a cada 5 segundos
    const interval = setInterval(fetchJob, 5000);
    return () => clearInterval(interval);
  }, [jobId]);

  const refreshJob = async () => {
    if (!jobId) return;
    
    try {
      setLoading(true);
      const jobData = await getJob(jobId);
      if (jobData) {
        setJob(jobData);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao atualizar job');
    } finally {
      setLoading(false);
    }
  };

  return {
    job,
    loading,
    error,
    refreshJob,
  };
}