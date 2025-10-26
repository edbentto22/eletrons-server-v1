export type JobStatus = 'pending' | 'queued' | 'training' | 'completed' | 'failed' | 'cancelled';

export interface TrainingMetrics {
  current?: {
    box_loss: number;
    cls_loss: number;
    dfl_loss: number;
    precision: number;
    recall: number;
    mAP50: number;
    mAP50_95: number;
  };
  best?: {
    mAP50: number;
    mAP50_95: number;
    epoch: number;
  };
}

export interface TrainingJob {
  job_id: string;
  model_name: string;
  status: JobStatus;
  progress: number;
  current_epoch: number;
  total_epochs: number;
  metrics: TrainingMetrics;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  eta_seconds?: number;
  config: {
    base_model: string;
    image_size: number;
    batch_size: number;
    learning_rate: number;
    optimizer: string;
  };
  dataset_info: {
    total_images: number;
    train_images: number;
    val_images: number;
    classes: string[];
  };
  error_message?: string;
}

export interface SystemResources {
  gpu: {
    name: string;
    utilization: number;
    memory_used: number;
    memory_total: number;
    temperature: number;
  };
  cpu: {
    utilization: number;
  };
  ram: {
    used: number;
    total: number;
  };
}

export interface ProgressUpdate {
  epoch: number;
  progress: number;
  metrics: TrainingMetrics;
  eta_seconds: number;
}
