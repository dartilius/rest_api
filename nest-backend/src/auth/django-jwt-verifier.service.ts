import { Inject, Injectable } from '@nestjs/common';
import { readFileSync } from 'node:fs';
import {
  decodeProtectedHeader,
  importSPKI,
  jwtVerify,
  type JWTPayload,
} from 'jose';

export type AuthenticatedSiteUser = {
  id: string;
  role?: string;
  tokenVersion: 'rs256' | 'legacy-hs256';
};

export type DjangoJwtConfig = {
  issuer: string;
  audience: string;
  publicKeyPem?: string;
  legacySecret?: string;
  legacyAcceptUntil?: Date;
};

export const DJANGO_JWT_CONFIG = Symbol('DJANGO_JWT_CONFIG');

export class JwtAuthConfigurationError extends Error {}
export class InvalidDjangoJwtError extends Error {}

function parseLegacyDeadline(value: string | undefined): Date | undefined {
  if (!value) return undefined;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.valueOf())) {
    throw new JwtAuthConfigurationError('JWT_LEGACY_HS256_ACCEPT_UNTIL must be an ISO-8601 timestamp.');
  }
  return parsed;
}

export function djangoJwtConfigFromEnvironment(): DjangoJwtConfig {
  const publicKeyPath = process.env.JWT_PUBLIC_KEY_PATH;
  return {
    issuer: process.env.JWT_ISSUER ?? 'rmc-django',
    audience: process.env.JWT_AUDIENCE ?? 'rmc-site-api',
    publicKeyPem: publicKeyPath ? readFileSync(publicKeyPath, 'utf8') : undefined,
    legacySecret: process.env.JWT_LEGACY_HS256_SECRET,
    legacyAcceptUntil: parseLegacyDeadline(process.env.JWT_LEGACY_HS256_ACCEPT_UNTIL),
  };
}

@Injectable()
export class DjangoJwtVerifier {
  private readonly publicKey: ReturnType<typeof importSPKI> | undefined;

  constructor(@Inject(DJANGO_JWT_CONFIG) private readonly config: DjangoJwtConfig) {
    this.publicKey = config.publicKeyPem
      ? importSPKI(config.publicKeyPem, 'RS256')
      : undefined;
  }

  async verifyAccessToken(token: string): Promise<AuthenticatedSiteUser> {
    let algorithm: string | undefined;
    try {
      algorithm = decodeProtectedHeader(token).alg;
    } catch {
      throw new InvalidDjangoJwtError('JWT header is invalid.');
    }

    if (algorithm === 'RS256') return this.verifyRs256(token);
    if (algorithm === 'HS256') return this.verifyLegacyHs256(token);
    throw new InvalidDjangoJwtError('JWT algorithm is not allowed.');
  }

  private async verifyRs256(token: string): Promise<AuthenticatedSiteUser> {
    if (!this.publicKey) {
      throw new JwtAuthConfigurationError('JWT_PUBLIC_KEY_PATH is not configured.');
    }

    try {
      const { payload } = await jwtVerify(token, await this.publicKey, {
        algorithms: ['RS256'],
        issuer: this.config.issuer,
        audience: this.config.audience,
      });
      return this.toRs256User(payload);
    } catch (error) {
      if (error instanceof JwtAuthConfigurationError) throw error;
      throw new InvalidDjangoJwtError('RS256 access token is invalid.');
    }
  }

  private async verifyLegacyHs256(token: string): Promise<AuthenticatedSiteUser> {
    const { legacySecret, legacyAcceptUntil } = this.config;
    if (!legacySecret || !legacyAcceptUntil || legacyAcceptUntil <= new Date()) {
      throw new InvalidDjangoJwtError('Legacy JWT support is unavailable.');
    }

    try {
      const { payload } = await jwtVerify(token, new TextEncoder().encode(legacySecret), {
        algorithms: ['HS256'],
      });
      if (payload.token_type !== 'access' || typeof payload.user_id !== 'string' || !payload.user_id) {
        throw new InvalidDjangoJwtError('Legacy JWT claims are invalid.');
      }
      return { id: payload.user_id, tokenVersion: 'legacy-hs256' };
    } catch (error) {
      if (error instanceof InvalidDjangoJwtError) throw error;
      throw new InvalidDjangoJwtError('Legacy access token is invalid.');
    }
  }

  private toRs256User(payload: JWTPayload): AuthenticatedSiteUser {
    if (payload.token_type !== 'access' || typeof payload.sub !== 'string' || !payload.sub) {
      throw new InvalidDjangoJwtError('RS256 JWT claims are invalid.');
    }
    if (payload.role !== undefined && typeof payload.role !== 'string') {
      throw new InvalidDjangoJwtError('RS256 JWT role claim is invalid.');
    }
    return {
      id: payload.sub,
      role: payload.role,
      tokenVersion: 'rs256',
    };
  }
}
