import type { TrainingJob, SystemResources } from '../types/training';

const BASE = import.meta.env.VITE_TRAINING_SERVER_URL;

async function safeFetch<T>(url: string, init?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(url, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(init?.headers || {}),
      },
    });
    if (!res.ok) {
      console.warn('API response not ok', res.status, url);
      return null;
    }
    return await res.json() as T;
  } catch (err) {
    console.warn('API fetch error', url, err);
    return null;
  }
}

export async function listJobs(): Promise<TrainingJob[] | null> {
  if (!BASE) return null;
  return safeFetch<TrainingJob[]>(`${BASE}/api/v1/jobs`);
}

export async function getJob(jobId: string): Promise<TrainingJob | null> {
  if (!BASE) return null;
  return safeFetch<TrainingJob>(`${BASE}/api/v1/jobs/${jobId}`);
}

export async function cancelJob(jobId: string): Promise<{ success: boolean } | null> {
  if (!BASE) return null;
  return safeFetch<{ success: boolean }>(`${BASE}/api/v1/jobs/${jobId}/cancel`, { method: 'POST' });
}

export async function createJob(payload: any): Promise<{ job_id: string } | null> {
  if (!BASE) return null;
  return safeFetch<{ job_id: string }>(`${BASE}/api/v1/train`, { method: 'POST', body: JSON.stringify(payload) });
}

export async function getSystemResources(): Promise<SystemResources | null> {
  if (!BASE) return null;
  return safeFetch<SystemResources>(`${BASE}/api/v1/system/resources`);
}

export function connectJobEvents(jobId: string): EventSource | null {
  if (!BASE) return null;
  try {
    const es = new EventSource(`${BASE}/api/v1/jobs/${jobId}/events`, { withCredentials: false });
    return es;
  } catch (err) {
    console.warn('SSE connection error', err);
    return null;
  }
}