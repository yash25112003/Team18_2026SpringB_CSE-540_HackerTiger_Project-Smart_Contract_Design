// src/components/BlockIdDisplay.tsx
import React, { useState, useEffect } from 'react';
import { blockIdMonitor, type BlockInfo } from '@/services/blockIdMonitor';

interface BlockIdDisplayProps {
  className?: string;
  showDetails?: boolean;
  format?: 'short' | 'full';
  blockId?: string;
  blockNumber?: number;
  isActive?: boolean;
}

const BlockIdDisplay: React.FC<BlockIdDisplayProps> = ({ 
  className = '', 
  showDetails = false,
  format = 'short',
  blockId,
  blockNumber,
  isActive
}) => {
  const [blockInfo, setBlockInfo] = useState<BlockInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [lastChanged, setLastChanged] = useState<Date | null>(null);
  const [progress, setProgress] = useState(0);

  // Simulate dynamic loading progress
  useEffect(() => {
    if (isLoading) {
      setProgress(0);
      const interval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 99) return 99;
          // Random increment that slows down as it gets closer to 100
          const remaining = 100 - prev;
          const increment = Math.max(1, Math.floor(Math.random() * (remaining / 3)));
          return Math.min(99, prev + increment);
        });
      }, 150);
      return () => clearInterval(interval);
    } else {
      setProgress(100);
    }
  }, [isLoading]);

  // Handle controlled mode (props provided)
  useEffect(() => {
    if (blockId) {
      const newInfo: BlockInfo = {
        block_id: blockId,
        block_hash: blockId, // Assuming ID is hash for display
        block_number: blockNumber || 0,
        created_at: new Date().toISOString(),
        is_active: isActive ?? true,
        block_type: 'deployment',
        timestamp: new Date().toISOString(),
        changed: blockInfo?.block_id !== blockId
      };
      
      if (blockInfo?.block_id !== blockId) {
        setLastChanged(new Date());
      }
      
      setBlockInfo(newInfo);
      
      // Ensure loading state persists long enough to see animation
      if (isLoading) {
        setTimeout(() => setIsLoading(false), 800);
      } else {
        setIsLoading(false);
      }
      return;
    }
  }, [blockId, blockNumber, isActive]);

  useEffect(() => {
    // Skip internal monitoring if controlled via props
    if (blockId) return;

    // Subscribe to Block ID changes
    const unsubscribe = blockIdMonitor.subscribe((newBlockInfo) => {
      setBlockInfo(newBlockInfo);
      setIsLoading(false);
      
      if (newBlockInfo.changed) {
        setLastChanged(new Date());
        
        // Show notification for Block ID changes
        if ('Notification' in window && Notification.permission === 'granted') {
          new Notification('Block ID Updated', {
            body: `New Block ID: ${newBlockInfo.block_id}`,
            icon: '/favicon.ico'
          });
        }
      }
    });

    // Start monitoring if not already active
    blockIdMonitor.startMonitoring();

    // Cleanup
    return () => {
      unsubscribe();
    };
  }, [blockId]); // Re-run if blockId prop changes (switching modes)

  // Request notification permission
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  if (isLoading) {
    return (
      <div className={`flex flex-col gap-1.5 min-w-[160px] ${className}`}>
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 animate-spin rounded-full border-2 border-blue-400 border-t-transparent" />
            <span className="text-xs text-gray-400">Syncing Block...</span>
          </div>
          <span className="text-xs font-mono text-blue-400">{progress}%</span>
        </div>
        <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
          <div 
            className="h-full bg-blue-400 transition-all duration-300 ease-out shadow-[0_0_8px_rgba(96,165,250,0.6)]"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    );
  }

  if (!blockInfo) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <div className="h-2 w-2 rounded-full bg-red-400" />
        <span className="text-sm text-red-500">No Block ID found</span>
      </div>
    );
  }

  const formatBlockId = (id: string) => {
    if (format === 'short') {
      return `${id.substring(0, 8)}...${id.substring(id.length - 8)}`;
    }
    return id;
  };

  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString();
  };

  return (
    <div className={`${className}`}>
      <div className="flex items-center gap-2">
        <div className={`h-2 w-2 rounded-full ${blockInfo.is_active ? 'bg-green-400' : 'bg-gray-400'} ${lastChanged ? 'animate-pulse-green' : ''}`} />
        <div className="flex flex-col">
          <div className="flex items-center gap-2">
            <span className="text-sm font-mono">
              {formatBlockId(blockInfo.block_id)}
            </span>
            {lastChanged && (
              <span className="text-xs text-green-500 animate-fade-in">
                Updated!
              </span>
            )}
          </div>
          
          {showDetails && (
            <div className="text-xs text-gray-500 mt-1">
              <div>Block #{blockInfo.block_number} • {blockInfo.block_type}</div>
              <div>Created: {formatTime(blockInfo.created_at)}</div>
              {lastChanged && (
                <div className="text-green-500">
                  Last changed: {lastChanged.toLocaleTimeString()}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      
      {lastChanged && (
        <div className="mt-2 text-xs text-green-600 font-medium animate-fade-in">
          Block ID automatically updated every 30 seconds.
        </div>
      )}
    </div>
  );
};

export default BlockIdDisplay;

// CSS for animations (add to your global CSS)
const styles = `
@keyframes fade-in {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse-green {
  0% { background-color: rgb(34, 197, 94); }
  50% { background-color: rgb(16, 185, 129); }
  100% { background-color: rgb(34, 197, 94); }
}

.animate-fade-in {
  animation: fade-in 0.5s ease-out;
}

.animate-pulse-green {
  animation: pulse-green 1s ease-in-out;
}
`;
