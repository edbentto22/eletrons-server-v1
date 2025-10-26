import { TrainingJob, SystemResources } from '../types/training';

export const mockJobs: TrainingJob[] = [
  {
    job_id: '550e8400-e29b-41d4-a716-446655440000',
    model_name: 'poste-detector-v1',
    status: 'training',
    progress: 65,
    current_epoch: 65,
    total_epochs: 100,
    metrics: {
      current: {
        box_loss: 0.02347,
        cls_loss: 0.01562,
        dfl_loss: 0.00891,
        precision: 0.8765,
        recall: 0.8342,
        mAP50: 0.8914,
        mAP50_95: 0.7234,
      },
      best: {
        mAP50: 0.8954,
        mAP50_95: 0.7289,
        epoch: 62,
      },
    },
    created_at: '2025-10-26T10:30:00Z',
    started_at: '2025-10-26T10:31:00Z',
    eta_seconds: 1320,
    config: {
      base_model: 'yolov8n.pt',
      image_size: 640,
      batch_size: 16,
      learning_rate: 0.01,
      optimizer: 'AdamW',
    },
    dataset_info: {
      total_images: 1500,
      train_images: 1200,
      val_images: 300,
      classes: ['poste', 'transformador', 'cabo'],
    },
  },
  {
    job_id: '660e8400-e29b-41d4-a716-446655440001',
    model_name: 'cabo-detector-v2',
    status: 'training',
    progress: 18,
    current_epoch: 18,
    total_epochs: 100,
    metrics: {
      current: {
        box_loss: 0.04523,
        cls_loss: 0.02891,
        dfl_loss: 0.01234,
        precision: 0.7234,
        recall: 0.6891,
        mAP50: 0.7234,
        mAP50_95: 0.5623,
      },
      best: {
        mAP50: 0.7289,
        mAP50_95: 0.5701,
        epoch: 16,
      },
    },
    created_at: '2025-10-26T11:00:00Z',
    started_at: '2025-10-26T11:02:00Z',
    eta_seconds: 4500,
    config: {
      base_model: 'yolov8s.pt',
      image_size: 640,
      batch_size: 8,
      learning_rate: 0.005,
      optimizer: 'AdamW',
    },
    dataset_info: {
      total_images: 2400,
      train_images: 1920,
      val_images: 480,
      classes: ['cabo'],
    },
  },
  {
    job_id: '770e8400-e29b-41d4-a716-446655440002',
    model_name: 'transformador-v3',
    status: 'queued',
    progress: 0,
    current_epoch: 0,
    total_epochs: 150,
    metrics: {},
    created_at: '2025-10-26T11:30:00Z',
    config: {
      base_model: 'yolov8m.pt',
      image_size: 640,
      batch_size: 16,
      learning_rate: 0.01,
      optimizer: 'AdamW',
    },
    dataset_info: {
      total_images: 3200,
      train_images: 2560,
      val_images: 640,
      classes: ['transformador'],
    },
  },
  {
    job_id: '880e8400-e29b-41d4-a716-446655440003',
    model_name: 'multi-class-v1',
    status: 'queued',
    progress: 0,
    current_epoch: 0,
    total_epochs: 200,
    metrics: {},
    created_at: '2025-10-26T11:45:00Z',
    config: {
      base_model: 'yolov8l.pt',
      image_size: 1280,
      batch_size: 4,
      learning_rate: 0.001,
      optimizer: 'SGD',
    },
    dataset_info: {
      total_images: 5000,
      train_images: 4000,
      val_images: 1000,
      classes: ['poste', 'transformador', 'cabo', 'isolador', 'cruzeta'],
    },
  },
  {
    job_id: '990e8400-e29b-41d4-a716-446655440004',
    model_name: 'defect-detector',
    status: 'queued',
    progress: 0,
    current_epoch: 0,
    total_epochs: 100,
    metrics: {},
    created_at: '2025-10-26T12:00:00Z',
    config: {
      base_model: 'yolov8n.pt',
      image_size: 640,
      batch_size: 16,
      learning_rate: 0.01,
      optimizer: 'AdamW',
    },
    dataset_info: {
      total_images: 800,
      train_images: 640,
      val_images: 160,
      classes: ['rachadura', 'corrosao', 'quebrado'],
    },
  },
  {
    job_id: 'aa0e8400-e29b-41d4-a716-446655440005',
    model_name: 'poste-detector-v0',
    status: 'completed',
    progress: 100,
    current_epoch: 100,
    total_epochs: 100,
    metrics: {
      current: {
        box_loss: 0.01234,
        cls_loss: 0.00891,
        dfl_loss: 0.00567,
        precision: 0.9234,
        recall: 0.8956,
        mAP50: 0.9456,
        mAP50_95: 0.8123,
      },
      best: {
        mAP50: 0.9456,
        mAP50_95: 0.8123,
        epoch: 98,
      },
    },
    created_at: '2025-10-25T14:00:00Z',
    started_at: '2025-10-25T14:01:00Z',
    completed_at: '2025-10-25T15:30:00Z',
    config: {
      base_model: 'yolov8n.pt',
      image_size: 640,
      batch_size: 16,
      learning_rate: 0.01,
      optimizer: 'AdamW',
    },
    dataset_info: {
      total_images: 1000,
      train_images: 800,
      val_images: 200,
      classes: ['poste'],
    },
  },
];

export const mockSystemResources: SystemResources = {
  gpu: {
    name: 'NVIDIA RTX 4090',
    utilization: 87.5,
    memory_used: 12.3,
    memory_total: 24.0,
    temperature: 72,
  },
  cpu: {
    utilization: 45,
  },
  ram: {
    used: 28.4,
    total: 64.0,
  },
};

export const getJobStats = (jobs: TrainingJob[]) => {
  return {
    active: jobs.filter((j) => j.status === 'training').length,
    queued: jobs.filter((j) => j.status === 'queued').length,
    completed: jobs.filter((j) => j.status === 'completed').length,
    failed: jobs.filter((j) => j.status === 'failed').length,
  };
};

export const formatETA = (seconds: number): string => {
  if (!seconds) return '--';
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
};

export const formatDuration = (start: string, end?: string): string => {
  const startTime = new Date(start).getTime();
  const endTime = end ? new Date(end).getTime() : Date.now();
  const diff = Math.floor((endTime - startTime) / 1000);
  
  return formatETA(diff);
};
