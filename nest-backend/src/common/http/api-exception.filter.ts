import { ArgumentsHost, Catch, ExceptionFilter, HttpException, HttpStatus, Logger } from '@nestjs/common';

type HttpResponse = {
  status(code: number): HttpResponse;
  json(body: unknown): void;
};

type ErrorPayload = { code?: string; message?: string | string[] };

@Catch()
export class ApiExceptionFilter implements ExceptionFilter {
  private readonly logger = new Logger(ApiExceptionFilter.name);

  catch(exception: unknown, host: ArgumentsHost): void {
    const response = host.switchToHttp().getResponse<HttpResponse>();
    const status = exception instanceof HttpException
      ? exception.getStatus()
      : HttpStatus.INTERNAL_SERVER_ERROR;
    const payload = exception instanceof HttpException ? exception.getResponse() : undefined;
    const details = typeof payload === 'object' && payload !== null ? payload as ErrorPayload : {};
    const message = Array.isArray(details.message)
      ? 'Request validation failed.'
      : details.message ?? (status === HttpStatus.INTERNAL_SERVER_ERROR ? 'Internal server error.' : 'Request failed.');

    if (status >= HttpStatus.INTERNAL_SERVER_ERROR) {
      this.logger.error('Unhandled request error', exception instanceof Error ? exception.stack : undefined);
    }

    response.status(status).json({
      error: {
        code: details.code ?? this.defaultCode(status),
        message,
      },
    });
  }

  private defaultCode(status: number): string {
    if (status === HttpStatus.BAD_REQUEST) return 'VALIDATION_ERROR';
    if (status === HttpStatus.UNAUTHORIZED) return 'UNAUTHORIZED';
    if (status === HttpStatus.FORBIDDEN) return 'FORBIDDEN';
    if (status === HttpStatus.NOT_FOUND) return 'NOT_FOUND';
    return status >= HttpStatus.INTERNAL_SERVER_ERROR ? 'INTERNAL_ERROR' : 'REQUEST_ERROR';
  }
}
