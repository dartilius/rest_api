import {
  CanActivate,
  ExecutionContext,
  Injectable,
  ServiceUnavailableException,
  UnauthorizedException,
} from '@nestjs/common';
import type { Request } from 'express';
import {
  DjangoJwtVerifier,
  type AuthenticatedSiteUser,
  InvalidDjangoJwtError,
  JwtAuthConfigurationError,
} from './django-jwt-verifier.service';

type AuthenticatedRequest = Request & { user?: AuthenticatedSiteUser };

@Injectable()
export class DjangoJwtAuthGuard implements CanActivate {
  constructor(private readonly verifier: DjangoJwtVerifier) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest<AuthenticatedRequest>();
    const token = this.extractAccessToken(request.headers.authorization);
    if (!token) throw this.unauthorized();

    try {
      request.user = await this.verifier.verifyAccessToken(token);
      return true;
    } catch (error) {
      if (error instanceof JwtAuthConfigurationError) {
        throw new ServiceUnavailableException({
          code: 'AUTH_NOT_CONFIGURED',
          message: 'JWT verification is not configured.',
        });
      }
      if (error instanceof InvalidDjangoJwtError) throw this.unauthorized();
      throw error;
    }
  }

  private extractAccessToken(header: string | undefined): string | undefined {
    const [scheme, token, extra] = header?.split(' ') ?? [];
    return scheme === 'access_token' && token && !extra ? token : undefined;
  }

  private unauthorized(): UnauthorizedException {
    return new UnauthorizedException({
      code: 'UNAUTHORIZED',
      message: 'Authentication required.',
    });
  }
}
