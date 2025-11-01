import React, { useState, useEffect } from 'react';
import { Alert, Card, Badge, Spinner, Button } from 'react-bootstrap';

interface Worker {
  id: string;
  name: string;
  tokens_left: number;
  available: boolean;
  error?: string;
}

interface WorkerAvailabilityProps {
  productId?: string;
  onWorkerSelect?: (worker: Worker) => void;
}

const WorkerAvailabilityDisplay: React.FC<WorkerAvailabilityProps> = ({ 
  productId, 
  onWorkerSelect 
}) => {
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const checkAvailability = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const url = productId 
        ? `/api/vps/availability?product_id=${productId}`
        : '/api/vps/availability';
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.workers) {
        setWorkers(data.workers);
        setLastChecked(new Date());
        
        // Log debug information to console
        console.log('[DEBUG] Worker availability check:', {
          productId,
          totalWorkers: data.workers.length,
          availableWorkers: data.workers.filter((w: Worker) => w.available).length,
          totalTokens: data.tokens_left || 0,
          workers: data.workers
        });
      } else {
        setError(data.reason || 'No worker information available');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(`Failed to check worker availability: ${errorMessage}`);
      console.error('[ERROR] Worker availability check failed:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAvailability();
  }, [productId]);

  const getWorkerStatusBadge = (worker: Worker) => {
    if (worker.error) {
      return <Badge bg="danger">Error</Badge>;
    }
    if (worker.tokens_left === -1) {
      return <Badge bg="warning">Unknown</Badge>;
    }
    if (worker.available) {
      return <Badge bg="success">Available</Badge>;
    }
    return <Badge bg="secondary">Unavailable</Badge>;
  };

  const getWorkerStatusText = (worker: Worker) => {
    if (worker.error) {
      return worker.error;
    }
    if (worker.tokens_left === -1) {
      return 'Unable to check status';
    }
    if (worker.tokens_left === 0) {
      return 'No tokens available';
    }
    return `${worker.tokens_left} tokens available`;
  };

  return (
    <div className="worker-availability-display">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h5>Worker Availability</h5>
        <Button 
          variant="outline-primary" 
          size="sm" 
          onClick={checkAvailability}
          disabled={loading}
        >
          {loading ? <Spinner size="sm" /> : 'Refresh'}
        </Button>
      </div>

      {error && (
        <Alert variant="danger" className="mb-3">
          <Alert.Heading>Error</Alert.Heading>
          <p>{error}</p>
          <Button variant="outline-danger" size="sm" onClick={checkAvailability}>
            Retry
          </Button>
        </Alert>
      )}

      {lastChecked && (
        <small className="text-muted d-block mb-2">
          Last checked: {lastChecked.toLocaleTimeString()}
        </small>
      )}

      {loading && workers.length === 0 && (
        <div className="text-center py-3">
          <Spinner animation="border" />
          <p className="mt-2">Checking worker availability...</p>
        </div>
      )}

      {workers.length === 0 && !loading && !error && (
        <Alert variant="info">
          No workers found for this product.
        </Alert>
      )}

      {workers.length > 0 && (
        <div className="worker-list">
          {workers.map((worker) => (
            <Card 
              key={worker.id} 
              className={`mb-2 ${worker.available ? 'border-success' : 'border-secondary'}`}
            >
              <Card.Body className="py-2">
                <div className="d-flex justify-content-between align-items-center">
                  <div>
                    <strong>{worker.name}</strong>
                    <br />
                    <small className="text-muted">
                      {getWorkerStatusText(worker)}
                    </small>
                  </div>
                  <div className="text-end">
                    {getWorkerStatusBadge(worker)}
                    {onWorkerSelect && worker.available && (
                      <Button
                        variant="outline-primary"
                        size="sm"
                        className="ms-2"
                        onClick={() => onWorkerSelect(worker)}
                      >
                        Select
                      </Button>
                    )}
                  </div>
                </div>
              </Card.Body>
            </Card>
          ))}
          
          <div className="mt-2">
            <small className="text-muted">
              Total: {workers.length} workers, 
              Available: {workers.filter(w => w.available).length} workers,
              Total tokens: {workers.reduce((sum, w) => sum + Math.max(0, w.tokens_left), 0)}
            </small>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkerAvailabilityDisplay;