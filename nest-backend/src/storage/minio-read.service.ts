import { Injectable, Logger } from '@nestjs/common';
import { GetObjectCommand, S3Client } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';

const MAX_PRESIGNED_TTL_SECONDS = 7 * 24 * 60 * 60;

function required(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing required environment variable: ${name}`);
  return value;
}

function parsePort(value: string | undefined): number {
  const port = Number(value ?? '9000');
  if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('MINIO_PORT must be a valid TCP port');
  return port;
}

function parseTtl(value: string | undefined): number {
  const ttl = Number(value ?? '900');
  if (!Number.isInteger(ttl) || ttl < 1 || ttl > MAX_PRESIGNED_TTL_SECONDS) {
    throw new Error(`MINIO_PRESIGNED_URL_TTL_SECONDS must be between 1 and ${MAX_PRESIGNED_TTL_SECONDS}`);
  }
  return ttl;
}

@Injectable()
export class MinioReadService {
  private readonly logger = new Logger(MinioReadService.name);
  private readonly bucket = required('MINIO_MEDIA_BUCKET');
  private readonly ttlSeconds = parseTtl(process.env.MINIO_PRESIGNED_URL_TTL_SECONDS);
  private readonly client = new S3Client({
    region: process.env.MINIO_REGION ?? 'us-east-1',
    endpoint: `${process.env.MINIO_USE_SSL === 'true' ? 'https' : 'http'}://${required('MINIO_ENDPOINT')}:${parsePort(process.env.MINIO_PORT)}`,
    forcePathStyle: true,
    credentials: {
      accessKeyId: required('MINIO_ACCESS_KEY'),
      secretAccessKey: required('MINIO_SECRET_KEY'),
    },
  });

  async getReadUrl(objectKey: string | null): Promise<string | null> {
    if (!objectKey) return null;

    try {
      return await getSignedUrl(
        this.client,
        new GetObjectCommand({ Bucket: this.bucket, Key: objectKey }),
        { expiresIn: this.ttlSeconds },
      );
    } catch (error) {
      // The catalogue remains usable when a single media object is unavailable.
      this.logger.warn(`Could not create a media URL for object ${objectKey}: ${error instanceof Error ? error.message : 'unknown error'}`);
      return null;
    }
  }
}
