import { Controller, Get, Header, HttpCode, Param, Query, Req, UseGuards } from '@nestjs/common'
import {
	ApiBearerAuth,
	ApiNotFoundResponse,
	ApiOkResponse,
	ApiOperation,
	ApiTags,
} from '@nestjs/swagger'
import type { Request } from 'express'
import { DjangoJwtAuthGuard } from '../auth/django-jwt-auth.guard'
import type { AuthenticatedSiteUser } from '../auth/django-jwt-verifier.service'
import { UserQueryDto } from './dto/user-query.dto'
import { UsersService, type UserResponse, type UsersListResponse } from './users.service'

type SiteRequest = Request & { user: AuthenticatedSiteUser }

@ApiTags('Users')
@ApiBearerAuth('django-access-token')
@UseGuards(DjangoJwtAuthGuard)
@Controller('users')
export class UsersController {
	constructor(private readonly users: UsersService) {}
	@Get('me')
	@HttpCode(200)
	@Header('Cache-Control', 'no-store')
	@ApiOperation({ summary: 'Профиль текущего пользователя / Get current user profile' })
	@ApiOkResponse({
		description: 'Active Django user profile without credentials or 1C tokens.',
		example: {
			id: '00000000-0000-4000-8000-000000000301',
			email: 'person@example.test',
			phoneNumber: '+79990000000',
			fullName: { firstName: 'Иван', lastName: 'Иванов', middleName: null },
			role: 'ordinary',
			avatar: null,
			created: '2026-03-01T00:00:00+00:00',
			code1c: 'USER-1',
		},
	})
	me(@Req() request: SiteRequest): Promise<UserResponse> {
		return this.users.me(request.user)
	}
	@Get()
	@HttpCode(200)
	@Header('Cache-Control', 'no-store')
	@ApiOperation({ summary: 'Пользователи для сотрудника / List users for an employee' })
	list(@Req() request: SiteRequest, @Query() query: UserQueryDto): Promise<UsersListResponse> {
		return this.users.list(request.user, query)
	}
	@Get(':identifier')
	@HttpCode(200)
	@Header('Cache-Control', 'no-store')
	@ApiOperation({ summary: 'Пользователь по UUID или коду 1С / Get user for an employee' })
	@ApiNotFoundResponse({ description: 'User is absent or inaccessible.' })
	findOne(
		@Req() request: SiteRequest,
		@Param('identifier') identifier: string,
	): Promise<UserResponse> {
		return this.users.findOne(request.user, identifier)
	}
}
