import { useState } from 'react';
import { Dashboard } from './components/Dashboard';
import { JobDetail } from './components/JobDetail';
import { mockJobs } from './lib/mockData';

export default function App() {
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);

  const selectedJob = selectedJobId 
    ? mockJobs.find((job) => job.job_id === selectedJobId)
    : null;

  return (
    <div className="min-h-screen">
      {selectedJob ? (
        <JobDetail 
          job={selectedJob} 
          onBack={() => setSelectedJobId(null)} 
        />
      ) : (
        <Dashboard onViewJob={setSelectedJobId} />
      )}
    </div>
  );
}
