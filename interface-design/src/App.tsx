import { useState } from 'react';
import { Dashboard } from './components/Dashboard';
import { JobDetail } from './components/JobDetail';
import { useJobs } from './hooks/useJobs';

export default function App() {
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const { jobs } = useJobs();

  const selectedJob = selectedJobId 
    ? jobs.find((job) => job.id === selectedJobId)
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
