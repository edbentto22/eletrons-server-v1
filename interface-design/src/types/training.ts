export type JobStatus = 'pending' | 'queued' | 'training' | 'completed' | 'failed' | 'cancelled';

export interface TrainingMetrics {
  epoch?: number;
  total_epochs?: number;
  train_loss?: number;
  val_loss?: number;
  precision?: number;
  recall?: number;
  map50?: number;
  map50_95?: number;
  learning_rate?: number;
  eta?: string;
}

export interface BestMetrics {
  precision?: number;
  recall?: number;
  map50?: number;
  map50_95?: number;
}

export interface TrainingConfig {
  base_model: string;
  epochs: number;
  batch_size: number;
  image_size: number;
  learning_rate: number;
  optimizer: string;
  device: string;
  workers: number;
  patience: number;
  save_period: number;
  augment: boolean;
  mosaic: number;
  mixup: number;
  copy_paste: number;
}

export interface DatasetInfo {
  name: string;
  path: string;
  classes: string[];
  train_images: number;
  val_images: number;
  test_images: number;
}

export interface TrainingJob {
  id: string;
  name: string;
  status: JobStatus;
  config: TrainingConfig;
  dataset: DatasetInfo;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  current_epoch: number;
  progress_percent: number;
  metrics?: TrainingMetrics | null;
  best_metrics?: BestMetrics | null;
  model_path?: string | null;
  weights_path?: string | null;
  logs_path?: string | null;
  error_message?: string | null;
}

export interface SystemResources {
  timestamp: string;
  cpu: {
    cores: number;
    threads: number;
    usage_percent: number;
    frequency?: number | null;
    temperature?: number | null;
  };
  memory: {
    total: number;
    used: number;
    free: number;
    available: number;
    usage_percent: number;
  };
  gpu?: {
    name: string;
    utilization: number;
    memory_used: number;
    memory_total: number;
    temperature: number;
  } | null;
  disk: Array<{
    path: string;
    total: number;
    used: number;
    free: number;
    usage_percent: number;
  }>;
}

export interface ProgressUpdate {
  epoch: number;
  progress: number;
  metrics: TrainingMetrics;
  eta_seconds: number;
}
