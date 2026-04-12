// src/services/blockIdMonitor.ts
interface BlockInfo {
  block_id: string;
  block_hash: string;
  block_number: number;
  created_at: string;
  is_active: boolean;
  block_type: string;
  timestamp: string;
  changed: boolean;
}

interface BlockStatusResponse {
  success: boolean;
  block_info?: BlockInfo;
  error?: string;
}

type BlockChangeCallback = (blockInfo: BlockInfo) => void;

class BlockIdMonitorService {
  private baseUrl = 'http://127.0.0.1:8000/api';
  private isMonitoring = false;
  private monitoringInterval: NodeJS.Timeout | null = null;
  private callbacks: BlockChangeCallback[] = [];
  private currentBlockId: string | null = null;

  /**
   * Start monitoring Block ID changes
   */
  startMonitoring(): void {
    if (this.isMonitoring) {
      console.warn('Block ID monitoring already active');
      return;
    }

    this.isMonitoring = true;
    console.log('Starting Block ID monitoring...');

    // Poll every 5 seconds for Block ID changes
    this.monitoringInterval = setInterval(() => {
      this.checkBlockStatus();
    }, 5000);

    // Check immediately
    this.checkBlockStatus();
  }

  /**
   * Stop monitoring Block ID changes
   */
  stopMonitoring(): void {
    if (!this.isMonitoring) {
      return;
    }

    this.isMonitoring = false;
    
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }

    console.log('⏹️ Block ID monitoring stopped');
  }

  /**
   * Subscribe to Block ID changes
   */
  subscribe(callback: BlockChangeCallback): () => void {
    this.callbacks.push(callback);

    // Return unsubscribe function
    return () => {
      const index = this.callbacks.indexOf(callback);
      if (index > -1) {
        this.callbacks.splice(index, 1);
      }
    };
  }

  /**
   * Get current Block ID information
   */
  async getCurrentBlockInfo(): Promise<BlockInfo | null> {
    try {
      const response = await fetch(`${this.baseUrl}/block-status/`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: BlockStatusResponse = await response.json();
      
      if (data.success && data.block_info) {
        return data.block_info;
      }

      return null;
    } catch (error) {
      console.error('Failed to get block info:', error);
      return null;
    }
  }

  /**
   * Check Block ID status and notify subscribers of changes
   */
  private async checkBlockStatus(): Promise<void> {
    try {
      const blockInfo = await this.getCurrentBlockInfo();
      
      if (!blockInfo) {
        return;
      }

      // Check if Block ID has changed
      if (this.currentBlockId !== blockInfo.block_id) {
        const previousBlockId = this.currentBlockId;
        this.currentBlockId = blockInfo.block_id;

        // Mark as changed if this is not the first load
        if (previousBlockId !== null) {
          blockInfo.changed = true;
          console.log(`Block ID changed: ${previousBlockId} → ${blockInfo.block_id}`);
        } else {
          console.log(`Initial Block ID: ${blockInfo.block_id}`);
        }

        // Notify all subscribers
        this.notifySubscribers(blockInfo);
      }
    } catch (error) {
      console.error('Block status check failed:', error);
    }
  }

  /**
   * Notify all subscribers of Block ID changes
   */
  private notifySubscribers(blockInfo: BlockInfo): void {
    this.callbacks.forEach(callback => {
      try {
        callback(blockInfo);
      } catch (error) {
        console.error('Block change callback error:', error);
      }
    });
  }

  /**
   * Force a Block ID check
   */
  async forceCheck(): Promise<void> {
    await this.checkBlockStatus();
  }
}

// Export singleton instance
export const blockIdMonitor = new BlockIdMonitorService();
export default blockIdMonitor;
export type { BlockInfo, BlockChangeCallback };
