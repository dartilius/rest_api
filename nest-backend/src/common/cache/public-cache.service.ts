import { Injectable, Logger, OnModuleDestroy, OnModuleInit } from '@nestjs/common';
import { createClient, type RedisClientType } from 'redis';

const CACHE_KEY_PREFIX = 'rmc-site-api:public:v1';
const CACHE_TTL_SECONDS = 5 * 60;

type RedisCacheClient = Pick<RedisClientType, 'connect' | 'close' | 'get' | 'set' | 'on'> & {
  readonly isOpen: boolean;
  readonly isReady: boolean;
};

function normalize(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(normalize).sort((left, right) => JSON.stringify(left).localeCompare(JSON.stringify(right)));
  }
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value)
        .filter(([, nestedValue]) => nestedValue !== undefined)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, nestedValue]) => [key, normalize(nestedValue)]),
    );
  }
  return value;
}

export function publicCacheKey(endpoint: string, input: unknown): string {
  return `${CACHE_KEY_PREFIX}:${endpoint}:${JSON.stringify(normalize(input))}`;
}

@Injectable()
export class PublicCacheService implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(PublicCacheService.name);
  private readonly client: RedisCacheClient | null;
  private readonly inFlight = new Map<string, Promise<unknown>>();

  constructor() {
    const url = process.env.CACHE_REDIS_URL;
    if (!url) {
      this.client = null;
      return;
    }

    this.client = createClient({
      url,
      disableOfflineQueue: true,
      socket: { reconnectStrategy: (retries) => Math.min(retries * 50, 500) },
    }) as RedisCacheClient;
    this.client.on('error', (error: Error) => {
      this.logger.warn(`Public cache is unavailable: ${error.message}`);
    });
  }

  onModuleInit(): void {
    if (!this.client || this.client.isOpen) return;
    void this.client.connect().catch((error: unknown) => {
      this.logger.warn(`Could not connect to the public cache: ${error instanceof Error ? error.message : 'unknown error'}`);
    });
  }

  async onModuleDestroy(): Promise<void> {
    if (this.client?.isOpen) await this.client.close();
  }

  async getOrSet<T>(endpoint: string, input: unknown, load: () => Promise<T>): Promise<T> {
    const key = publicCacheKey(endpoint, input);
    const cached = await this.get<T>(key);
    if (cached !== null) return cached;

    const existing = this.inFlight.get(key) as Promise<T> | undefined;
    if (existing) return existing;

    const pending = this.loadAndCache(key, load);
    this.inFlight.set(key, pending);
    try {
      return await pending;
    } finally {
      if (this.inFlight.get(key) === pending) this.inFlight.delete(key);
    }
  }

  private async loadAndCache<T>(key: string, load: () => Promise<T>): Promise<T> {
    const value = await load();
    await this.set(key, value);
    return value;
  }

  private async get<T>(key: string): Promise<T | null> {
    if (!this.client?.isReady) return null;
    try {
      const value = await this.client.get(key);
      return value === null ? null : JSON.parse(value) as T;
    } catch (error) {
      this.logOperationFailure('read', error);
      return null;
    }
  }

  private async set<T>(key: string, value: T): Promise<void> {
    if (!this.client?.isReady) return;
    try {
      await this.client.set(key, JSON.stringify(value), { expiration: { type: 'EX', value: CACHE_TTL_SECONDS } });
    } catch (error) {
      this.logOperationFailure('write', error);
    }
  }

  private logOperationFailure(operation: 'read' | 'write', error: unknown): void {
    this.logger.warn(`Public cache ${operation} failed: ${error instanceof Error ? error.message : 'unknown error'}`);
  }
}
