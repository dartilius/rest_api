import { Type } from 'class-transformer';
import { IsInt, IsOptional, IsString, Max, MaxLength, Min } from 'class-validator';

export class UserQueryDto {
  @IsOptional() @IsString() @MaxLength(255)
  search?: string;

  @IsOptional() @IsString() @MaxLength(32)
  role?: string;

  @IsOptional() @Type(() => Number) @IsInt() @Min(1) @Max(100)
  limit = 24;

  @IsOptional() @Type(() => Number) @IsInt() @Min(0)
  offset = 0;
}
