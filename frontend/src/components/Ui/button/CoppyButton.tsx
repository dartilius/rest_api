import ActionButton from './ActionButton'

export const CopyButton = ({
	onCopy,
	label,
	disabled,
}: {
	onCopy: () => void
	label: string
	disabled?: boolean
}) => (
	<div>
		<ActionButton
			variant='warning'
			onClick={onCopy}
			style={{ width: '100%' }}
			disabled={disabled}
		>
			{label}
		</ActionButton>
	</div>
)
