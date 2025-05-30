export function getStatusColor(statusId: number | null): string {
	if (statusId === null) {
		return 'rgba(128, 128, 128, 0.4)'
	}

	switch (statusId) {
		case 0:
			return 'rgba(0, 182, 155, 0.4)'
		case 1:
			return 'rgba(211, 163, 19, 0.4)'
		case 2:
			return 'rgba(239, 56, 40, 0.4)'
		default:
			return 'rgba(128, 128, 128, 0.4)'
	}
}
