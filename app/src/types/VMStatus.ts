export enum VMStatus {
  RUNNING = 'running',
  STOPPED = 'stopped',
  PAUSED = 'paused',
  UNKNOWN = 'unknown'
}

export type VMStatusString = 'running' | 'stopped' | 'paused' | 'unknown';
